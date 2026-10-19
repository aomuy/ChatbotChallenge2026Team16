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


def merge_empty_heading_runs(sections: list[dict]) -> list[dict]:
    """Collapse consecutive heading-only sections into one denser section.

    First heading stays as the section heading; remaining headings become
    the body (one per line). Singleton empty headings are unchanged.
    Sections that already have body text pass through as-is.
    """
    out: list[dict] = []
    i = 0
    n = len(sections)
    while i < n:
        section = sections[i]
        heading = (section.get("heading") or "").strip()
        body = (section.get("text") or "").strip()
        if body:
            out.append(section)
            i += 1
            continue

        # Consume the full run of empty-text sections.
        j = i + 1
        while j < n and not (sections[j].get("text") or "").strip():
            j += 1
        run = sections[i:j]
        if len(run) == 1:
            out.append({"heading": heading, "text": ""})
        else:
            rest = [
                (s.get("heading") or "").strip()
                for s in run[1:]
                if (s.get("heading") or "").strip()
            ]
            out.append({"heading": heading, "text": "\n".join(rest)})
        i = j
    return out


def build_index(pages: list[dict], reset: bool = True):
    texts, metas = [], []
    for page in pages:
        for section in merge_empty_heading_runs(page.get("sections", [])):
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
