"""Image pipeline. STUB. Workshop 2 blocks 2 and 3.

Describe every collected image once, cache the result, and add the
descriptions to the same store as the scraped text. Run this file
directly, after build/scrape.py and build/index.py, to add images to
data/chroma.

Never describe an image while answering a question. Ingestion time is
unlimited; runtime is 30 seconds.
"""
import json
from pathlib import Path

import requests

from bot.llm import describe_image
from bot.store import add_to_store, get_store

IMAGE_TYPES = {"poster", "photo", "diagram", "logo", "other", "unknown"}

DESCRIPTION_PROMPT = """Describe this image as JSON only, with these fields:
{"image_type": "poster|photo|diagram|logo|other|unknown", "description": "..."}.
Use poster for an actual poster/flyer asset, not a photograph containing
posters. Use unknown if its type cannot be determined. The description must
include readable text verbatim, room/location clues, colours, and counts of
clearly visible objects (tables, chairs, printers, fire extinguishers, etc.).
Do not invent obscured text or objects. State when a count is uncertain.
"""

CACHE_PATH = Path("data/descriptions.json")


def description_fields(value) -> tuple[str, str]:
    """Accept structured vision output and existing plain-text caches."""
    if isinstance(value, str):
        raw = value.strip()
        if raw.startswith("```") and raw.endswith("```"):
            raw = "\n".join(raw.splitlines()[1:-1])
        try:
            parsed = json.loads(raw)
        except (ValueError, TypeError):
            parsed = None
    else:
        parsed = value
    if isinstance(parsed, dict) and isinstance(parsed.get("description"), str):
        image_type = parsed.get("image_type", "unknown")
        valid_type = isinstance(image_type, str) and image_type in IMAGE_TYPES
        return parsed["description"], image_type if valid_type else "unknown"
    return str(value), "unknown"


def describe_all(images: list[dict]) -> dict:
    """Describe every image once, cache the result, never regenerate.

    Ingestion is free, but not if you redo it every time you change a
    line downstream. Key the cache by image URL.
    """
    cache = json.loads(CACHE_PATH.read_text()) if CACHE_PATH.exists() else {}

    for im in images:
        src = im["src"]
        if src in cache:
            continue
        try:
            tmp = Path("data/_tmp_image")
            tmp.write_bytes(requests.get(src, timeout=30).content)
            cache[src] = describe_image(str(tmp), DESCRIPTION_PROMPT)
        except Exception as exc:
            print("failed:", src[:70], exc)

    CACHE_PATH.parent.mkdir(exist_ok=True)
    CACHE_PATH.write_text(json.dumps(cache, indent=1))
    print(f"{len(cache)} descriptions cached")
    return cache


def index_descriptions(descriptions: dict, images: list[dict]) -> None:
    """Add descriptions to the same store as the scraped text."""
    by_src = {im["src"]: im for im in images}
    texts, metas = [], []
    for src, description in descriptions.items():
        im = by_src.get(src, {})
        text, image_type = description_fields(description)
        # Explicit source annotations override vision classification.
        image_type = im.get("image_type", image_type)
        if not isinstance(image_type, str) or image_type not in IMAGE_TYPES:
            image_type = "unknown"
        # Alt text and captions are already text and cost nothing to index.
        full = " ".join(filter(None, [im.get("alt"), im.get("caption"), text]))
        texts.append(full)
        metas.append({
            **{key: value for key, value in im.items()
               if key not in {"src", "alt", "caption", "page"}
               and isinstance(value, (str, int, float, bool))},
            "url": im.get("page", src), "image": src, "kind": "image",
            "image_type": image_type,
        })
    store = get_store(reset=False)
    add_to_store(store, texts, metas, ids=[f"img_{i}" for i in range(len(texts))])
    print(f"indexed {len(texts)} image descriptions")


if __name__ == "__main__":
    images = json.loads(Path("data/images.json").read_text())
    descriptions = describe_all(images)
    index_descriptions(descriptions, images)
