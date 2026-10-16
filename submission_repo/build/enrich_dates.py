"""Enrich pages.json with event_start / event_end from three sources.

Run after scrape, before index:

    python -m build.enrich_dates --limit 5

Resumable: pages with event_start+event_end or event_date_status are skipped.
Re-process by deleting those fields on the page in pages.json.
Sources (cross-checked): scraped text Date:/Dates: lines, HTML structured
data (re-fetch), and a Qwen date-model extract with quota failover.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from build.qwen_chat import DateModelsExhausted, chat_date

PAGES_PATH = Path("data/pages.json")
IMAGES_PATH = Path("data/images.json")
REVIEW_PATH = Path("data/date_review.jsonl")
MISSING_PATH = Path("data/date_missing.jsonl")

# Terminal outcomes without dates — stored so resume does not re-queue forever.
STATUS_VALUES = frozenset({"hub", "missing", "single_source", "conflict"})

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
    """Return {pair, hub} from Qwen date models (failover on quota).

    Raises DateModelsExhausted when every configured model is out of tokens.
    Other API failures yield a null LLM source so text/HTML can still decide.
    """
    text = _page_text(page, limit=3500)
    try:
        response = chat_date([
            {"role": "system", "content": LLM_PROMPT},
            {"role": "user", "content": text},
        ], max_tokens=256)
    except DateModelsExhausted:
        raise
    except Exception as exc:
        print(f"LLM extract failed for {page.get('url', '?')}: {exc}")
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


def is_finished(page: dict) -> bool:
    """True if this page should be skipped on resume."""
    if page.get("event_start") and page.get("event_end"):
        return True
    status = page.get("event_date_status")
    return isinstance(status, str) and status in STATUS_VALUES


def unfinished_pages(pages: list[dict], limit: int | None = None) -> list[dict]:
    """Pages still needing enrichment, optionally capped."""
    work = [p for p in pages if not is_finished(p)]
    if limit is not None:
        return work[:limit]
    return work


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


def apply_decision(page: dict, decision: dict, text_result: dict,
                   llm_result: dict) -> dict | None:
    """Mutate page from a resolver decision; return a log row or None."""
    page.pop("event_start", None)
    page.pop("event_end", None)
    page.pop("event_date_status", None)

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
        # Conflict-with-text-win still has dates; log but no status needed.
        if decision["log"] == "review":
            return row
        return None

    # No dates written — mark terminal status for resume skip.
    reason = decision["reason"]
    if reason == "no_dates":
        page["event_date_status"] = "missing"
    elif reason in STATUS_VALUES:
        page["event_date_status"] = reason
    else:
        page["event_date_status"] = "missing"

    if decision["log"] in ("review", "missing"):
        return row
    return None


def enrich_one_page(
    page: dict,
    *,
    html_fetcher=None,
    llm_extractor=None,
) -> tuple[dict, dict | None, str | None]:
    """Enrich a single page in place.

    Returns (page, log_row_or_None, log_kind) where log_kind is
    'review', 'missing', or None.
    """
    if html_fetcher is None:
        html_fetcher = fetch_html_dates
    if llm_extractor is None:
        llm_extractor = extract_llm_dates

    text_result = parse_text_dates(page)
    html_pair = html_fetcher(page["url"])
    llm_result = llm_extractor(page)
    decision = resolve_dates(text_result, html_pair, llm_result)
    row = apply_decision(page, decision, text_result, llm_result)
    log_kind = decision.get("log")
    return page, row, log_kind


def enrich_pages(
    pages: list[dict],
    *,
    html_fetcher=None,
    llm_extractor=None,
) -> tuple[list[dict], list[dict], list[dict]]:
    """Enrich pages; return (pages, review_rows, missing_rows).

    Pass html_fetcher / llm_extractor callables to inject test doubles.
    Re-runs every page in the list (caller should pass unfinished only).
    """
    review_rows: list[dict] = []
    missing_rows: list[dict] = []
    enriched: list[dict] = []

    for page in pages:
        page = dict(page)
        page, row, log_kind = enrich_one_page(
            page, html_fetcher=html_fetcher, llm_extractor=llm_extractor)
        if row and log_kind == "review":
            review_rows.append(row)
        elif row and log_kind == "missing":
            missing_rows.append(row)
        enriched.append(page)

    return enriched, review_rows, missing_rows


def save_checkpoint(
    pages: list[dict],
    review_rows: list[dict] | None = None,
    missing_rows: list[dict] | None = None,
) -> None:
    """Write pages.json, inherit image dates, append any new log rows."""
    PAGES_PATH.parent.mkdir(parents=True, exist_ok=True)
    PAGES_PATH.write_text(json.dumps(pages, indent=1, ensure_ascii=False))
    if IMAGES_PATH.exists():
        images = json.loads(IMAGES_PATH.read_text())
        images_out = inherit_image_dates(pages, images)
        IMAGES_PATH.write_text(json.dumps(images_out, indent=1, ensure_ascii=False))
    for row in review_rows or []:
        _append_jsonl(REVIEW_PATH, row)
    for row in missing_rows or []:
        _append_jsonl(MISSING_PATH, row)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Enrich pages/images with event dates (resumable)")
    parser.add_argument("--skip-html", action="store_true", help="Do not re-fetch HTML")
    parser.add_argument("--skip-llm", action="store_true", help="Do not call the LLM")
    parser.add_argument(
        "--limit", type=int, default=None,
        help="Max unfinished pages to process this run (skips pages that "
             "already have event_start+event_end or event_date_status)",
    )
    args = parser.parse_args(argv)

    pages = json.loads(PAGES_PATH.read_text())
    by_url = {p["url"]: p for p in pages}
    work = unfinished_pages(pages, limit=args.limit)
    print(f"unfinished: {len([p for p in pages if not is_finished(p)])}; "
          f"processing this run: {len(work)}")

    html_fetcher = (lambda url: None) if args.skip_html else fetch_html_dates
    llm_extractor = (
        (lambda page: {"pair": None, "hub": False, "raw": None})
        if args.skip_llm else extract_llm_dates
    )

    pending_review: list[dict] = []
    pending_missing: list[dict] = []
    processed = 0

    def flush() -> None:
        nonlocal pending_review, pending_missing
        save_checkpoint(pages, pending_review, pending_missing)
        pending_review, pending_missing = [], []

    try:
        for page in work:
            live = by_url[page["url"]]
            try:
                _, row, log_kind = enrich_one_page(
                    live, html_fetcher=html_fetcher, llm_extractor=llm_extractor)
            except DateModelsExhausted as exc:
                print(f"stopping: {exc}")
                flush()
                dated = sum(1 for p in pages if p.get("event_start"))
                print(f"checkpoint saved after {processed} pages "
                      f"({dated} dated total)")
                return 0
            if row and log_kind == "review":
                pending_review.append(row)
            elif row and log_kind == "missing":
                pending_missing.append(row)
            processed += 1
            flush()
            print(f"[{processed}/{len(work)}] {live['url']}")
    except KeyboardInterrupt:
        print("interrupted; saving checkpoint")
        flush()
        return 130
    except Exception as exc:
        print(f"fatal error after {processed} pages: {exc}")
        flush()
        raise

    dated = sum(1 for p in pages if p.get("event_start"))
    print(f"done: processed {processed}; pages with dates: {dated}/{len(pages)}")
    print(f"review log: {REVIEW_PATH}")
    print(f"missing log: {MISSING_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
