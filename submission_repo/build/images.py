"""Image pipeline. STUB. Workshop 2 blocks 2 and 3.

Describe every collected image once, cache the result, and add the
descriptions to the same store as the scraped text. Run this file
directly, after build/scrape.py and build/index.py, to add images to
data/chroma.

Never describe an image while answering a question. Ingestion time is
unlimited; runtime is 30 seconds.
"""
import argparse
import base64
import io
import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

import requests
from PIL import Image, UnidentifiedImageError

from build.qwen_describe import VisionModelsExhausted, describe_image
from bot.store import add_to_store, get_store

# Filter scalars copied from annotated images.json onto each image record.
IMAGE_FILTER_FIELDS = (
    "year", "location", "category", "capacity", "event_start", "event_end",
)
_FENCED_JSON = re.compile(r"```(?:json)?\s*([\s\S]*?)\s*```", re.IGNORECASE)

IMAGE_TYPES = ("poster", "photo", "diagram", "logo", "map", "signage", "other", "unknown")

DESCRIPTION_PROMPT = """You are a meticulous spatial and visual analyst preparing image data for a RAG retrieval system.

Your goal is NOT to write a short human caption. Your goal is to extract facts that can answer specific, detailed questions.

Analyze the image and write the description field following these rules:

1. **Count and List Objects**: Count ALL distinct, countable objects, including those only partly visible at the edges or in the background. Specifically look for and count: tables (every work table / workbench, even if occluded), chairs, stools, laptops, screens, sofas, steps/stairs, storage lockers, and any notable equipment (e.g., airplanes, 3D printers, fire extinguishers). However, if any of these objects are not present in the image, do NOT count it. DO NOT mention 0,none, or nothing in the count, or "there are no tables, chairs, stools, laptops, screens, sofas, steps/stairs, storage lockers, or equipment". Give one total for tables and one total for chairs/stools.
2. **Transcribe Text**: Transcribe ALL VISIBLE TEXT EXACTLY as it appears, glyph for glyph, in reading order (left to right, top to bottom). This includes large wall lettering behind seating (often three stacked words such as HKU / ENGINEERING / INNOVATION), signs, whiteboards, screens, stickers and posters (e.g., "NOTICE", "Keep Clean"). Write [unreadable] for glyphs you cannot see. Do not replace wall text with nearby labels such as BRAINSTORMING AREA.
3. **Describe Layout and Spatial Relationships**: Describe where things are in relation to each other. Use terms like: left, right, center, foreground, background, next to, above, below, on the wall. (e.g., "The colorful cubic sofas are in the foreground, with a large blue sign saying 'ENGINEERING INNOVATION' on the wall behind them to the right.")
4. **Color and Material**: Note the primary colors (e.g., white, gray, wood, blue, orange, yellow) and materials (e.g., carpet, wood, plastic, metal) of prominent objects.
5. **Avoid Generic Aesthetics**: Do not use phrases like "a modern room with furniture". Be extremely factual and exhaustive.
6. **No Repetition**: Do not repeat the description of the alternative text or caption unless they are too vague or not present.
7. **Clear and Concise**: Be clear and concise. Do not use any filler words or phrases. Put the analysis in the description field as dense prose or bullet points with nouns and numbers.

Also classify the image asset itself in image_type. Allowed values only:
poster, photo, diagram, logo, map, signage, other, unknown.
A photo that happens to show posters or signs is "photo", not "poster" or "signage".
"poster" means the indexed asset is a poster graphic. "signage" means a dedicated
sign/wayfinding graphic (not a photo of a room that contains a sign). "map" means
a floor plan, site map, or similar schematic. Use "unknown" only if you cannot tell.

alternative text: {alt_text}
caption: {caption}

Respond with a single JSON object only, no markdown fences, no other text:
{{"description":"<your analysis>","image_type":"<one of: poster|photo|diagram|logo|map|signage|other|unknown>"}}
Make sure your description is written as bullet points and is dense with nouns and numbers.
"""

CACHE_PATH = Path("data/descriptions.json")
OVERSIZED_LOG_PATH = Path("data/image_oversized.jsonl")

# Skip formats Pillow cannot rasterize without extra deps.
SKIP_EXTS = {".svg", ".ico"}

# DashScope rejects data-URI items at 20 MiB; stay strictly under.
API_DATA_URI_LIMIT = 20 * 1024 * 1024
MAX_DATA_URI_BYTES = API_DATA_URI_LIMIT - 1024
MAX_EDGE_PX = 2048
JPEG_QUALITY_START = 85
JPEG_QUALITY_MIN = 40


def _copy_scalars(source: dict, fields: tuple[str, ...]) -> dict:
    """Copy present scalar filter fields; omit missing/None/non-scalars."""
    out = {}
    for key in fields:
        if key not in source:
            continue
        value = source[key]
        if value is None or isinstance(value, (dict, list)):
            continue
        if isinstance(value, (str, int, float, bool)):
            out[key] = value
    return out


def description_fields(raw) -> tuple[str, str]:
    """Parse a cached description into (text, image_type).

    Structured JSON (optionally fenced) yields description + image_type.
    Legacy plain text and invalid types become image_type \"unknown\".
    """
    if isinstance(raw, dict):
        payload = raw
    elif isinstance(raw, str):
        text = raw.strip()
        payload = None
        fenced = _FENCED_JSON.search(text)
        candidate = fenced.group(1).strip() if fenced else text
        if candidate.startswith("{") or candidate.startswith("["):
            try:
                parsed = json.loads(candidate)
            except json.JSONDecodeError:
                parsed = None
            if isinstance(parsed, dict):
                payload = parsed
        if payload is None:
            return (text, "unknown")
    else:
        return (str(raw) if raw is not None else "", "unknown")

    description = payload.get("description", "")
    if not isinstance(description, str):
        description = str(description) if description is not None else ""
    image_type = payload.get("image_type")
    if isinstance(image_type, str) and image_type.strip().lower() in IMAGE_TYPES:
        return (description, image_type.strip().lower())
    return (description, "unknown")


def _structured_cache_value(raw: str) -> dict | None:
    """Return canonical {description, image_type} for a model reply, or None."""
    description, image_type = description_fields(raw)
    if not description.strip():
        return None
    # Reject legacy plain text: structured replies must have carried a type,
    # or at least have been JSON with a description field.
    text = (raw or "").strip()
    fenced = _FENCED_JSON.search(text)
    candidate = fenced.group(1).strip() if fenced else text
    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError:
        return None
    if not isinstance(parsed, dict) or "description" not in parsed:
        return None
    return {"description": description, "image_type": image_type}


def _url_ext(url: str) -> str:
    return Path(urlparse(url).path).suffix.lower()


def _sniff_ext(data: bytes) -> str | None:
    """Detect format from magic bytes so MIME matches the file content."""
    if data[:3] == b"\xff\xd8\xff":
        return ".jpg"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return ".png"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return ".gif"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return ".webp"
    if data[:2] == b"BM":
        return ".bmp"
    return None


def _mime_for_ext(ext: str) -> str:
    return {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".jpe": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
        ".bmp": "image/bmp",
    }.get(ext, "application/octet-stream")


def data_uri_nbytes(payload: bytes, mime: str) -> int:
    """Byte length of a data:{mime};base64,... URI for payload."""
    b64 = base64.b64encode(payload).decode("ascii")
    return len(f"data:{mime};base64,{b64}".encode("ascii"))


def _log_oversized(src: str, original_bytes: int, data_uri_bytes: int,
                   note: str = "") -> None:
    """Append one oversized original to the manual-review log."""
    OVERSIZED_LOG_PATH.parent.mkdir(exist_ok=True)
    record = {
        "src": src,
        "original_bytes": original_bytes,
        "estimated_data_uri_bytes": data_uri_bytes,
        "limit_bytes": MAX_DATA_URI_BYTES,
        "api_limit_bytes": API_DATA_URI_LIMIT,
    }
    if note:
        record["note"] = note
    with OVERSIZED_LOG_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"oversized (logged): {src[:70]} "
          f"({data_uri_bytes} data-URI bytes)")


def _pil_rgb(img: Image.Image) -> Image.Image:
    """Flatten to RGB suitable for JPEG (first frame of animated GIFs)."""
    if getattr(img, "n_frames", 1) > 1:
        img.seek(0)
    if img.mode in ("RGB",):
        return img
    if img.mode in ("RGBA", "LA") or (
        img.mode == "P" and "transparency" in img.info
    ):
        rgba = img.convert("RGBA")
        background = Image.new("RGB", rgba.size, (255, 255, 255))
        background.paste(rgba, mask=rgba.split()[-1])
        return background
    return img.convert("RGB")


def _encode_jpeg(img: Image.Image, quality: int) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality, optimize=True)
    return buf.getvalue()


def prepare_vision_image(raw: bytes, src: str = "") -> tuple[bytes, str] | None:
    """Convert/compress raw image bytes for the vision API.

    - Rasterizes BMP / mislabeled JPEG (.jpe) and other Pillow-readable formats
      to JPEG.
    - Skips SVG/ICO (and unreadable bytes).
    - Resizes and re-encodes so the data-URI stays under MAX_DATA_URI_BYTES.
    - When the *original* payload would exceed the limit, appends src to
      data/image_oversized.jsonl for manual review (still attempts compress).

    Returns (jpeg_bytes, \".jpg\") or None if the image cannot be prepared.
    """
    url_ext = _url_ext(src) if src else ""
    sniff = _sniff_ext(raw)
    if (url_ext in SKIP_EXTS) or (sniff in SKIP_EXTS):
        return None

    orig_ext = sniff or url_ext or ".bin"
    orig_mime = _mime_for_ext(orig_ext)
    orig_uri = data_uri_nbytes(raw, orig_mime if orig_mime != "application/octet-stream"
                               else "image/jpeg")
    if orig_uri >= MAX_DATA_URI_BYTES and src:
        _log_oversized(src, len(raw), orig_uri)

    try:
        img = Image.open(io.BytesIO(raw))
        img.load()
    except (UnidentifiedImageError, OSError) as exc:
        print(f"skip (unreadable): {src[:70] or '(bytes)'} ({exc})")
        return None

    rgb = _pil_rgb(img)
    # Start from a bounded edge; shrink further if still over the URI cap.
    edge = MAX_EDGE_PX
    quality = JPEG_QUALITY_START
    prepared: bytes | None = None
    for _ in range(24):
        w, h = rgb.size
        scale = min(1.0, edge / max(w, h)) if max(w, h) > 0 else 1.0
        if scale < 1.0:
            resized = rgb.resize(
                (max(1, int(w * scale)), max(1, int(h * scale))),
                Image.Resampling.LANCZOS,
            )
        else:
            resized = rgb
        prepared = _encode_jpeg(resized, quality)
        if data_uri_nbytes(prepared, "image/jpeg") < MAX_DATA_URI_BYTES:
            return prepared, ".jpg"
        if quality > JPEG_QUALITY_MIN:
            quality = max(JPEG_QUALITY_MIN, quality - 10)
        else:
            edge = max(256, int(edge * 0.75))
            quality = JPEG_QUALITY_START

    print(f"skip (still oversized after compress): {src[:70] or '(bytes)'}")
    if src and orig_uri < MAX_DATA_URI_BYTES:
        # Original was under limit but compress path somehow failed; still log.
        _log_oversized(
            src, len(raw), data_uri_nbytes(prepared or b"", "image/jpeg"),
            note="failed_to_compress_under_limit",
        )
    return None


def _save_cache(cache: dict) -> None:
    """Flush the description cache to disk."""
    CACHE_PATH.parent.mkdir(exist_ok=True)
    CACHE_PATH.write_text(json.dumps(cache, indent=1, ensure_ascii=False))


def _cache_entry_nonempty(value) -> bool:
    """True if a cache value has usable description text.

    Supports legacy plain strings and structured
    {"description": "...", "image_type": "..."}.
    """
    if value is None:
        return False
    if isinstance(value, dict):
        desc = value.get("description", "")
        return isinstance(desc, str) and bool(desc.strip())
    if isinstance(value, str):
        return bool(value.strip())
    return bool(str(value).strip())


def describe_all(images: list[dict], limit: int | None = None) -> dict:
    """Describe every image once, cache the result, never regenerate.

    Ingestion is free, but not if you redo it every time you change a
    line downstream. Key the cache by image URL.

    If limit is set, generate at most that many new descriptions this run.
    Already-cached images, format skips, and failures do not count.

    Each download is converted/compressed via prepare_vision_image so the
    vision data-URI stays under MAX_DATA_URI_BYTES. Originals that would
    exceed the limit are appended to data/image_oversized.jsonl.

    Writes data/descriptions.json after every successful new description.
    On VisionModelsExhausted or KeyboardInterrupt, flushes then re-raises.
    """
    cache = json.loads(CACHE_PATH.read_text()) if CACHE_PATH.exists() else {}
    # Drop blank entries left by older runs so they can be retried.
    cache = {k: v for k, v in cache.items() if _cache_entry_nonempty(v)}
    new_count = 0

    try:
        for im in images:
            if limit is not None and new_count >= limit:
                break
            src = im["src"]
            if src in cache:
                continue
            url_ext = _url_ext(src)
            if url_ext in SKIP_EXTS:
                print("skip (format):", src[:70])
                continue
            try:
                raw = requests.get(src, timeout=30).content
                prepared = prepare_vision_image(raw, src=src)
                if prepared is None:
                    print("skip (prepare):", src[:70])
                    continue
                payload, ext = prepared
                tmp = Path(f"data/_tmp_image{ext}")
                tmp.write_bytes(payload)
                desc = describe_image(
                    str(tmp),
                    DESCRIPTION_PROMPT.format(
                        alt_text=im.get("alt", ""),
                        caption=im.get("caption", ""),
                    ),
                )
                structured = _structured_cache_value(desc or "")
                if not structured:
                    print("unstructured or empty reply:", src[:70])
                    continue
                cache[src] = structured
                new_count += 1
                _save_cache(cache)
            except VisionModelsExhausted:
                raise
            except Exception as exc:
                print("failed:", src[:70], exc)
    except VisionModelsExhausted:
        _save_cache(cache)
        print(f"vision models exhausted; saved {len(cache)} descriptions "
              f"({new_count} new this run)")
        raise
    except KeyboardInterrupt:
        _save_cache(cache)
        print(f"interrupted; saved {len(cache)} descriptions "
              f"({new_count} new this run)")
        raise
    except Exception:
        _save_cache(cache)
        raise

    _save_cache(cache)
    print(f"{len(cache)} descriptions cached ({new_count} new)")
    return cache

# Reuse chunking function from index.py?
def index_descriptions(descriptions: dict, images: list[dict]) -> None:
    """Add descriptions to the same store as the scraped text."""
    by_src = {im["src"]: im for im in images}
    texts, metas = [], []
    for src, raw in descriptions.items():
        im = by_src.get(src, {})
        desc_text, image_type = description_fields(raw)
        # Explicit annotation on images.json wins over parsed/legacy type.
        annotated = im.get("image_type")
        if isinstance(annotated, str) and annotated.strip():
            image_type = annotated.strip()

        # Alt text and captions are already text and cost nothing to index.
        full = " ".join(filter(None, [im.get("alt"), im.get("caption"), desc_text]))

        # Azure embeddings reject empty strings (400 BadRequest).
        if not full.strip():
            continue
        texts.append(full)
        meta = {
            "url": im.get("page", src),
            "image": src,
            "kind": "image",
            "image_type": image_type,
        }
        meta.update(_copy_scalars(im, IMAGE_FILTER_FIELDS))
        _apply_url_year(meta, src)
        if image_type in ("unknown", "") and "poster" in (src or "").lower():
            meta["image_type"] = "poster"
        metas.append(meta)

    # Alt/caption-only rows so Pitch winners and labelled equipment retrieve
    # even when vision descriptions were never built on this machine.
    described = set(descriptions)
    for im in images:
        src = im.get("src") or ""
        if not src or src in described:
            continue
        alt_text = " ".join(filter(None, [im.get("alt"), im.get("caption")]))
        if not alt_text.strip():
            continue
        annotated = im.get("image_type")
        if isinstance(annotated, str) and annotated.strip():
            image_type = annotated.strip()
        elif "poster" in src.lower():
            image_type = "poster"
        else:
            image_type = "photo"
        texts.append(alt_text)
        meta = {
            "url": im.get("page", src),
            "image": src,
            "kind": "image",
            "image_type": image_type,
        }
        meta.update(_copy_scalars(im, IMAGE_FILTER_FIELDS))
        _apply_url_year(meta, src)
        metas.append(meta)

    if not texts:
        print("indexed 0 image descriptions (nothing non-empty to index)")
        return
    store = get_store(reset=False)
    add_to_store(store, texts, metas, ids=[f"img_{i}" for i in range(len(texts))])
    print(f"indexed {len(texts)} image descriptions")


def _apply_url_year(meta: dict, src: str) -> None:
    if "year" in meta:
        return
    year_match = re.search(r"/uploads/(\d{4})/", src or "")
    if year_match:
        meta["year"] = int(year_match.group(1))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Describe scraped images (optionally index into Chroma)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Max new descriptions to generate this run (default: all)",
    )
    parser.add_argument(
        "--index",
        action="store_true",
        help="Also index cached descriptions into Chroma (off by default)",
    )
    args = parser.parse_args()
    images = json.loads(Path("data/images.json").read_text())
    has_vision_key = bool(os.environ.get("QWEN_API_KEY", "").strip())
    if not has_vision_key:
        print("QWEN_API_KEY is not set. Skipping new vision descriptions. "
              "Cached data/descriptions.json (if present) can still be indexed "
              "with --index. Alt/caption-only image rows are included then.")
        descriptions = {}
        if CACHE_PATH.exists():
            descriptions = json.loads(CACHE_PATH.read_text())
        if args.index:
            index_descriptions(descriptions, images)
        sys.exit(0)
    try:
        descriptions = describe_all(images, limit=args.limit)
    except VisionModelsExhausted:
        # Cache already flushed; skip indexing this partial run.
        sys.exit(0)
    except KeyboardInterrupt:
        sys.exit(130)
    if args.index:
        index_descriptions(descriptions, images)
