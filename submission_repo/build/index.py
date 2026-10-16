"""Indexer. Workshop 1 block 4.

Chunk the scraped text and write it to the store. Run this file
directly, after build/scrape.py, to (re)build data/chroma.

Store metadata now. Level 4 questions need to filter by year and page
type, and adding a field later means rebuilding everything.
"""
import json
from pathlib import Path

from bot.store import add_to_store, get_store

CHUNK_SIZE, OVERLAP = 800, 100

# Filter scalars copied from annotated pages.json onto every chunk.
PAGE_FILTER_FIELDS = (
    "page_type", "year", "capacity", "location", "category",
    "event_start", "event_end",
)


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


def chunk(text: str, size: int = CHUNK_SIZE, overlap: int = OVERLAP) -> list[str]:
    """Fixed-size chunks with overlap.

    Overlap exists because a fact split across a boundary is lost: a
    date at char 998 and its event name at char 1002 land in different
    chunks and neither answers the question.

    Callers that already have section structure should chunk the section
    body and prepend the section heading to each piece.
    """
    if not text or not text.strip():
        return []
    step = size - overlap
    pieces = []
    for i in range(0, len(text), step):
        pieces.append(text[i:i + size].strip())
    return [piece for piece in pieces if piece.strip()]


def build_index(pages: list[dict], reset: bool = True):
    texts, metas = [], []
    for page in pages:
        for section in page.get("sections", []):
            heading = (section.get("heading") or "").strip()
            body = section.get("text") or ""
            pieces = chunk(body) if body.strip() else ([] if not heading else [""])
            # Heading-only section: still index the heading as a chunk.
            if not pieces and heading:
                pieces = [""]
            # TODO: Try to store nested headings as h1->h2(?)
            for i, piece in enumerate(pieces):
                labeled = f"{heading}\n{piece}".strip() if heading else piece
                if not labeled:
                    continue
                texts.append(labeled)
                meta = {
                    "url":      page["url"],
                    "title":    page.get("title", ""),
                    "section":  heading,
                    "position": i,
                    "kind":     "text",
                }
                meta.update(_copy_scalars(page, PAGE_FILTER_FIELDS))
                metas.append(meta)
    store = get_store(reset=reset)
    add_to_store(store, texts, metas)
    print(f"indexed {len(texts)} chunks")
    return store


if __name__ == "__main__":
    pages = json.loads(Path("data/pages.json").read_text())
    build_index(pages)
