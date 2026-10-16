"""Image pipeline. STUB. Workshop 2 blocks 2 and 3.

Describe every collected image once, cache the result, and add the
descriptions to the same store as the scraped text. Run this file
directly, after build/scrape.py and build/index.py, to add images to
data/chroma.

Never describe an image while answering a question. Ingestion time is
unlimited; runtime is 30 seconds.
"""
import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlparse

import requests

from build.qwen_describe import describe_image
from bot.store import add_to_store, get_store

# Filter scalars copied from annotated images.json onto each image record.
IMAGE_FILTER_FIELDS = ("year", "location", "category", "capacity")
_FENCED_JSON = re.compile(r"```(?:json)?\s*([\s\S]*?)\s*```", re.IGNORECASE)

IMAGE_TYPES = ("poster", "photo", "diagram", "logo", "map", "signage", "other", "unknown")

DESCRIPTION_PROMPT = """You are a meticulous spatial and visual analyst preparing image data for a RAG retrieval system.

Your goal is NOT to write a short human caption. Your goal is to extract facts that can answer specific, detailed questions.

Analyze the image and write the description field following these rules:

1. **Count and List Objects**: Count all distinct, countable objects. Specifically look for and count: tables, chairs, stools, laptops, screens, sofas, steps/stairs, storage lockers, and any notable equipment (e.g., airplanes, 3D printers, fire extinguishers). However, if any of these objects are not present in the image, do NOT count it. DO NOT mention 0,none, or nothing in the count, or "there are no tables, chairs, stools, laptops, screens, sofas, steps/stairs, storage lockers, or equipment".
2. **Transcribe Text**: Transcribe ALL VISIBLE TEXT EXACTLY as it appears. This includes signs on walls, writing on whiteboards, text on screens, text on stickers or posters (e.g., "ENGINEERING INNOVATION", "NOTICE", "Keep Clean").
3. **Describe Layout and Spatial Relationships**: Describe where things are in relation to each other. Use terms like: left, right, center, foreground, background, next to, above, below, on the wall. (e.g., "The colorful cubic sofas are in the foreground, with a large blue sign saying 'ENGINEERING INNOVATION' on the wall behind them to the right.")
4. **Color and Material**: Note the primary colors (e.g., white, gray, wood, blue, orange, yellow) and materials (e.g., carpet, wood, plastic, metal) of prominent objects.
5. **Avoid Generic Aesthetics**: Do not use phrases like "a modern room with furniture". Be extremely factual and exhaustive.
6. **No Repetition**: Do not repeat the description of the alternative text or caption unless they are too vague or not present.
7. **Clear and Concise**: Be clear and concise. Do not use any filler words or phrases. Put the analysis in the description field as dense prose or bullet points with nouns and numbers.

Also classify the image asset itself in image_type. Allowed values only:
poster, photo, diagram, logo, other, unknown.
A photo that happens to show posters is "photo", not "poster". "poster" means the indexed asset is a poster graphic. Use "unknown" only if you cannot tell.

alternative text: {alt_text}
caption: {caption}

Respond with a single JSON object only, no markdown fences, no other text:
{{"description":"<your analysis>","image_type":"<one of: poster|photo|diagram|logo|map|signage|other|unknown>"}}
Make sure your description is written as bullet points and is dense with nouns and numbers.
"""

CACHE_PATH = Path("data/descriptions.json")

# Vision API accepts only these raster formats (not SVG/BMP/ICO).
ALLOWED_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


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


def _structured_cache_value(raw: str) -> str | None:
    """Return canonical JSON for a model reply, or None if not structured."""
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
    return json.dumps(
        {"description": description, "image_type": image_type},
        ensure_ascii=False,
    )


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
    return None


def describe_all(images: list[dict], limit: int | None = None) -> dict:
    """Describe every image once, cache the result, never regenerate.

    Ingestion is free, but not if you redo it every time you change a
    line downstream. Key the cache by image URL.

    If limit is set, generate at most that many new descriptions this run.
    Already-cached images, format skips, and failures do not count.
    """
    cache = json.loads(CACHE_PATH.read_text()) if CACHE_PATH.exists() else {}
    # Drop blank entries left by older runs so they can be retried.
    cache = {k: v for k, v in cache.items() if (v or "").strip()}
    new_count = 0

    for im in images:
        if limit is not None and new_count >= limit:
            break
        src = im["src"]
        if src in cache:
            continue
        url_ext = _url_ext(src)
        if url_ext and url_ext not in ALLOWED_EXTS:
            print("skip (format):", src[:70])
            continue
        try:
            raw = requests.get(src, timeout=30).content
            sniff = _sniff_ext(raw)
            ext = sniff or (url_ext if url_ext in ALLOWED_EXTS else ".jpg")
            tmp = Path(f"data/_tmp_image{ext}")
            tmp.write_bytes(raw)
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
        except Exception as exc:
            print("failed:", src[:70], exc)

    CACHE_PATH.parent.mkdir(exist_ok=True)
    CACHE_PATH.write_text(json.dumps(cache, indent=1))
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
        metas.append(meta)
    if not texts:
        print("indexed 0 image descriptions (nothing non-empty to index)")
        return
    store = get_store(reset=False)
    add_to_store(store, texts, metas, ids=[f"img_{i}" for i in range(len(texts))])
    print(f"indexed {len(texts)} image descriptions")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Describe and index scraped images")
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Max new descriptions to generate this run (default: all)",
    )
    args = parser.parse_args()
    images = json.loads(Path("data/images.json").read_text())
    descriptions = describe_all(images, limit=args.limit)
    index_descriptions(descriptions, images)
