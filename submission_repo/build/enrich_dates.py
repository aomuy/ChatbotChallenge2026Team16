"""Enrich pages.json with event_start / event_end from three sources.

Run after scrape, before index:

    python -m build.enrich_dates

Sources (cross-checked): scraped text Date:/Dates: lines, HTML structured
data (re-fetch), and an LLM extract. Images inherit dates from parent pages.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import date, datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from bot.llm import chat

PAGES_PATH = Path("data/pages.json")
IMAGES_PATH = Path("data/images.json")
REVIEW_PATH = Path("data/date_review.jsonl")
MISSING_PATH = Path("data/date_missing.jsonl")

MONTHS = {
    "january": 1, "jan": 1,
    "february": 2, "feb": 2,
    "march": 3, "mar": 3,
    "april": 4, "apr": 4,
    "may": 5,
    "june": 6, "jun": 6,
    "july": 7, "jul": 7,
    "august": 8, "aug": 8,
    "september": 9, "sep": 9, "sept": 9,
    "october": 10, "oct": 10,
    "november": 11, "nov": 11,
    "december": 12, "dec": 12,
}
_MONTH = r"(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)"
_DAY = r"(\d{1,2})(?:st|nd|rd|th)?"
_YEAR = r"(20\d{2})"

# Fuzzy month phrases we refuse to guess.
_FUZZY = re.compile(
    r"\b(early|late|mid|middle of|end of)\s+" + _MONTH,
    re.IGNORECASE,
)

_DATE_LABEL = re.compile(r"\bDate(?:s)?\s*:\s*", re.IGNORECASE)

LLM_PROMPT = """Extract the primary event date or date range for this web page.
Return JSON only, no markdown:
{"event_start":"YYYY-MM-DD"|null,"event_end":"YYYY-MM-DD"|null,"hub":true|false}

Rules:
- hub=true if the page lists multiple separate events with different dates.
- For a single multi-day event, set event_start and event_end (inclusive).
- For a single-day event, set both to the same day.
- Ignore speaker CV career years, time-of-day ranges, and unrelated years in body text.
- If unsure, return nulls and hub=false.
"""


def _page_text(page: dict, limit: int | None = None) -> str:
    parts = [page.get("title") or ""]
    for section in page.get("sections") or []:
        parts.append(section.get("heading") or "")
        parts.append(section.get("text") or "")
    text = "\n".join(p for p in parts if p)
    if limit is not None:
        return text[:limit]
    return text


def _parse_iso_fragment(value: str) -> date | None:
    value = (value or "").strip()
    if not value:
        return None
    # datetime attribute may include time.
    value = value.replace("Z", "+00:00")
    for parser in (
        lambda s: datetime.fromisoformat(s).date(),
        lambda s: date.fromisoformat(s[:10]),
        lambda s: datetime.strptime(s[:10], "%Y-%m-%d").date(),
    ):
        try:
            return parser(value)
        except (ValueError, TypeError):
            continue
    return None


def _make_date(year: int, month: int, day: int) -> date | None:
    try:
        return date(year, month, day)
    except ValueError:
        return None


def _month_num(name: str) -> int | None:
    return MONTHS.get(name.lower())


def _pair(start: date | None, end: date | None = None) -> tuple[str, str] | None:
    if start is None:
        return None
    if end is None:
        end = start
    if end < start:
        start, end = end, start
    return (start.isoformat(), end.isoformat())


def _parse_one_calendar_date(text: str) -> date | None:
    """Parse a single calendar date from a short phrase."""
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\([^)]*\)", " ", text)  # drop (Thursday) etc.
    text = re.sub(r"\b(AM|PM)\b", " ", text, flags=re.I).strip()

    patterns = [
        # March 10, 2022 / March 10 2022
        re.compile(
            rf"\b({_MONTH})\s+{_DAY},?\s+{_YEAR}\b", re.I),
        # 10 March 2022 / 10th March, 2022
        re.compile(
            rf"\b{_DAY}\s+({_MONTH})\s*,?\s*{_YEAR}\b", re.I),
        # 2022-03-10
        re.compile(r"\b(20\d{2})-(\d{2})-(\d{2})\b"),
    ]
    m = patterns[0].search(text)
    if m:
        return _make_date(int(m.group(3)), _month_num(m.group(1)), int(m.group(2)))
    m = patterns[1].search(text)
    if m:
        return _make_date(int(m.group(3)), _month_num(m.group(2)), int(m.group(1)))
    m = patterns[2].search(text)
    if m:
        return _make_date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    return None


def _parse_date_clause(clause: str) -> tuple[str, str] | None:
    """Parse one Date: value into (start, end) ISO strings, or None if fuzzy/invalid."""
    clause = re.split(r"\bTime\s*:", clause, maxsplit=1, flags=re.I)[0]
    clause = re.split(r"\bVenue\s*:", clause, maxsplit=1, flags=re.I)[0]
    clause = re.split(r"\bMode\s*:", clause, maxsplit=1, flags=re.I)[0]
    clause = re.sub(r"\s+", " ", clause).strip()
    if not clause or _FUZZY.search(clause):
        return None

    # Month Day – Day, Year  (July 5 – 18, 2025)
    m = re.search(
        rf"\b({_MONTH})\s+{_DAY}\s*[-–—]\s*{_DAY},?\s*{_YEAR}\b", clause, re.I)
    if m:
        month = _month_num(m.group(1))
        year = int(m.group(4))
        return _pair(_make_date(year, month, int(m.group(2))),
                     _make_date(year, month, int(m.group(3))))

    # Day – Day Month Year  (8-10th April 2019)
    m = re.search(
        rf"\b{_DAY}\s*[-–—]\s*{_DAY}\s+({_MONTH})\s*,?\s*{_YEAR}\b", clause, re.I)
    if m:
        month = _month_num(m.group(3))
        year = int(m.group(4))
        return _pair(_make_date(year, month, int(m.group(1))),
                     _make_date(year, month, int(m.group(2))))

    # Month Day to Month Day, Year
    m = re.search(
        rf"\b({_MONTH})\s+{_DAY}\s*(?:to|until|through|till|-|–|—)\s*"
        rf"({_MONTH})\s+{_DAY},?\s*{_YEAR}\b",
        clause, re.I)
    if m:
        y = int(m.group(5))
        return _pair(
            _make_date(y, _month_num(m.group(1)), int(m.group(2))),
            _make_date(y, _month_num(m.group(3)), int(m.group(4))),
        )

    # Month Day, Year to Month Day, Year
    m = re.search(
        rf"\b({_MONTH})\s+{_DAY},?\s*{_YEAR}\s*(?:to|until|through|till|-|–|—)\s*"
        rf"({_MONTH})\s+{_DAY},?\s*{_YEAR}\b",
        clause, re.I)
    if m:
        return _pair(
            _make_date(int(m.group(3)), _month_num(m.group(1)), int(m.group(2))),
            _make_date(int(m.group(6)), _month_num(m.group(4)), int(m.group(5))),
        )

    # Day Month Year to Day Month Year
    m = re.search(
        rf"\b{_DAY}\s+({_MONTH})\s*,?\s*{_YEAR}\s*(?:to|until|through|till|-|–|—|&)\s*"
        rf"{_DAY}\s+({_MONTH})\s*,?\s*{_YEAR}\b",
        clause, re.I)
    if m:
        return _pair(
            _make_date(int(m.group(3)), _month_num(m.group(2)), int(m.group(1))),
            _make_date(int(m.group(6)), _month_num(m.group(5)), int(m.group(4))),
        )

    # Month Day to Day, Year  (March 9 to 15, 2025) / October 12 to 19, 2025
    m = re.search(
        rf"\b({_MONTH})\s+{_DAY}\s*(?:to|until|through|till|-|–|—)\s*{_DAY},?\s*{_YEAR}\b",
        clause, re.I)
    if m:
        month = _month_num(m.group(1))
        year = int(m.group(4))
        return _pair(_make_date(year, month, int(m.group(2))),
                     _make_date(year, month, int(m.group(3))))

    # Single calendar date
    one = _parse_one_calendar_date(clause)
    return _pair(one)


def extract_date_clauses(text: str) -> list[str]:
    """Return the value text after each Date:/Dates: label."""
    clauses = []
    for m in _DATE_LABEL.finditer(text):
        rest = text[m.end():]
        # Stop at newline-ish boundary of ~200 chars or next Date:
        line = rest.split("\n", 1)[0]
        line = _DATE_LABEL.split(line, maxsplit=1)[0]
        clauses.append(line.strip()[:240])
    return clauses


def parse_text_dates(page: dict) -> dict:
    """Return {pair, dates, hub} from scraped text.

    pair: (start,end) if exactly one event interval, else None.
    dates: sorted unique ISO start days found.
    hub: True if two or more distinct event dates/intervals.
    """
    text = _page_text(page)
    clauses = extract_date_clauses(text)
    pairs: list[tuple[str, str]] = []
    for clause in clauses:
        parsed = _parse_date_clause(clause)
        if parsed:
            pairs.append(parsed)

    unique_pairs = list(dict.fromkeys(pairs))
    unique_starts = sorted({p[0] for p in unique_pairs})

    if len(unique_pairs) >= 2:
        return {"pair": None, "dates": unique_starts, "hub": True, "raw": clauses}
    if len(unique_pairs) == 1:
        return {"pair": unique_pairs[0], "dates": unique_starts, "hub": False, "raw": clauses}
    return {"pair": None, "dates": [], "hub": False, "raw": clauses}


def extract_html_dates(html: str) -> tuple[str, str] | None:
    """Pull event dates from <time datetime> and JSON-LD Event."""
    soup = BeautifulSoup(html, "html.parser")
    found: list[date] = []

    for tag in soup.select("time[datetime]"):
        d = _parse_iso_fragment(tag.get("datetime", ""))
        if d:
            found.append(d)

    for script in soup.select('script[type="application/ld+json"]'):
        raw = script.string or script.get_text() or ""
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        items = data if isinstance(data, list) else [data]
        for item in items:
            if not isinstance(item, dict):
                continue
            types = item.get("@type") or item.get("type")
            type_list = types if isinstance(types, list) else [types]
            if not any(t and "Event" in str(t) for t in type_list):
                # Still accept startDate on any node.
                pass
            for key in ("startDate", "endDate"):
                if key in item:
                    d = _parse_iso_fragment(str(item[key]))
                    if d:
                        found.append(d)

    for prop in ("event:start_time", "event:end_time"):
        tag = soup.find("meta", attrs={"property": prop})
        if tag and tag.get("content"):
            d = _parse_iso_fragment(tag["content"])
            if d:
                found.append(d)

    if not found:
        return None
    found = sorted(set(found))
    # If many distinct days from HTML, treat as ambiguous → None (hub-like)
    if len(found) > 2:
        return None
    if len(found) == 1:
        return _pair(found[0])
    return _pair(found[0], found[-1])


def fetch_html_dates(url: str, timeout: int = 20) -> tuple[str, str] | None:
    try:
        resp = requests.get(url, timeout=timeout, allow_redirects=True)
        resp.raise_for_status()
        return extract_html_dates(resp.text)
    except Exception:
        return None


def extract_llm_dates(page: dict) -> dict:
    """Return {pair, hub} from the chat model."""
    text = _page_text(page, limit=3500)
    try:
        response = chat([
            {"role": "system", "content": LLM_PROMPT},
            {"role": "user", "content": text},
        ], max_tokens=256)
    except Exception:
        return {"pair": None, "hub": False, "raw": None}

    raw = (response or "").strip()
    fenced = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw)
    if fenced:
        raw = fenced.group(1).strip()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {"pair": None, "hub": False, "raw": response}

    if not isinstance(data, dict):
        return {"pair": None, "hub": False, "raw": response}

    hub = bool(data.get("hub"))
    start = _parse_iso_fragment(str(data["event_start"])) if data.get("event_start") else None
    end = _parse_iso_fragment(str(data["event_end"])) if data.get("event_end") else None
    if start and not end:
        end = start
    if end and not start:
        start = end
    pair = _pair(start, end) if start else None
    if hub:
        pair = None
    return {"pair": pair, "hub": hub, "raw": data}


def resolve_dates(
    text_result: dict,
    html_pair: tuple[str, str] | None,
    llm_result: dict,
) -> dict:
    """Cross-check sources. Returns decision dict.

    Keys: event_start, event_end (or None), log ('review'|'missing'|None), reason, sources.
    """
    sources = {
        "text": text_result.get("pair"),
        "html": html_pair,
        "llm": None if llm_result.get("hub") else llm_result.get("pair"),
    }

    if text_result.get("hub") or llm_result.get("hub"):
        return {
            "event_start": None,
            "event_end": None,
            "log": "review",
            "reason": "hub",
            "sources": sources,
        }

    present = {name: pair for name, pair in sources.items() if pair}
    if not present:
        return {
            "event_start": None,
            "event_end": None,
            "log": "missing",
            "reason": "no_dates",
            "sources": sources,
        }
    if len(present) == 1:
        return {
            "event_start": None,
            "event_end": None,
            "log": "review",
            "reason": "single_source",
            "sources": sources,
        }

    values = list(present.values())
    if all(v == values[0] for v in values):
        start, end = values[0]
        return {
            "event_start": start,
            "event_end": end,
            "log": None,
            "reason": "agree",
            "sources": sources,
        }

    # Conflict
    if sources["text"]:
        start, end = sources["text"]
        return {
            "event_start": start,
            "event_end": end,
            "log": "review",
            "reason": "conflict",
            "sources": sources,
        }
    return {
        "event_start": None,
        "event_end": None,
        "log": "review",
        "reason": "conflict",
        "sources": sources,
    }


def _append_jsonl(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def inherit_image_dates(pages: list[dict], images: list[dict]) -> list[dict]:
    """Copy event_start/event_end from parent pages onto images."""
    by_url = {
        p["url"]: p for p in pages
        if p.get("event_start") and p.get("event_end")
    }
    out = []
    for im in images:
        im = dict(im)
        parent = by_url.get(im.get("page"))
        if parent:
            im["event_start"] = parent["event_start"]
            im["event_end"] = parent["event_end"]
        else:
            im.pop("event_start", None)
            im.pop("event_end", None)
        out.append(im)
    return out


def enrich_pages(
    pages: list[dict],
    *,
    html_fetcher=None,
    llm_extractor=None,
) -> tuple[list[dict], list[dict], list[dict]]:
    """Enrich pages; return (pages, review_rows, missing_rows).

    Pass html_fetcher / llm_extractor callables to inject test doubles.
    Defaults: re-fetch HTML and call the chat LLM.
    """
    if html_fetcher is None:
        html_fetcher = fetch_html_dates
    if llm_extractor is None:
        llm_extractor = extract_llm_dates

    review_rows: list[dict] = []
    missing_rows: list[dict] = []
    enriched: list[dict] = []

    for page in pages:
        page = dict(page)
        # Drop previous enrichment before re-running.
        page.pop("event_start", None)
        page.pop("event_end", None)

        text_result = parse_text_dates(page)
        html_pair = html_fetcher(page["url"])
        llm_result = llm_extractor(page)

        decision = resolve_dates(text_result, html_pair, llm_result)
        row = {
            "url": page["url"],
            "title": page.get("title", ""),
            "reason": decision["reason"],
            "sources": {
                k: {"event_start": v[0], "event_end": v[1]} if v else None
                for k, v in decision["sources"].items()
            },
            "text_raw": text_result.get("raw"),
            "llm_raw": llm_result.get("raw"),
        }
        if decision["event_start"] and decision["event_end"]:
            page["event_start"] = decision["event_start"]
            page["event_end"] = decision["event_end"]
        if decision["log"] == "review":
            review_rows.append(row)
        elif decision["log"] == "missing":
            missing_rows.append(row)
        enriched.append(page)

    return enriched, review_rows, missing_rows


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Enrich pages/images with event dates")
    parser.add_argument("--skip-html", action="store_true", help="Do not re-fetch HTML")
    parser.add_argument("--skip-llm", action="store_true", help="Do not call the LLM")
    parser.add_argument("--limit", type=int, default=None, help="Max pages to enrich")
    args = parser.parse_args(argv)

    pages = json.loads(PAGES_PATH.read_text())
    html_fetcher = (lambda url: None) if args.skip_html else fetch_html_dates
    llm_extractor = (
        (lambda page: {"pair": None, "hub": False, "raw": None})
        if args.skip_llm else extract_llm_dates
    )
    work = pages[: args.limit] if args.limit is not None else pages
    enriched_work, review_rows, missing_rows = enrich_pages(
        work, html_fetcher=html_fetcher, llm_extractor=llm_extractor)
    if args.limit is not None:
        pages_out = enriched_work
        for p in pages[args.limit:]:
            p = dict(p)
            p.pop("event_start", None)
            p.pop("event_end", None)
            pages_out.append(p)
    else:
        pages_out = enriched_work

    # Reset log files for this run.
    if REVIEW_PATH.exists():
        REVIEW_PATH.unlink()
    if MISSING_PATH.exists():
        MISSING_PATH.unlink()
    for row in review_rows:
        _append_jsonl(REVIEW_PATH, row)
    for row in missing_rows:
        _append_jsonl(MISSING_PATH, row)

    PAGES_PATH.write_text(json.dumps(pages_out, indent=1, ensure_ascii=False))

    if IMAGES_PATH.exists():
        images = json.loads(IMAGES_PATH.read_text())
        images_out = inherit_image_dates(pages_out, images)
        IMAGES_PATH.write_text(json.dumps(images_out, indent=1, ensure_ascii=False))
        print(f"updated {len(images_out)} images")

    dated = sum(1 for p in pages_out if p.get("event_start"))
    print(f"pages with dates: {dated}/{len(pages_out)}")
    print(f"review: {len(review_rows)} -> {REVIEW_PATH}")
    print(f"missing: {len(missing_rows)} -> {MISSING_PATH}")


if __name__ == "__main__":
    main()
