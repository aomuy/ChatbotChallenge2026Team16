"""Event date windows and Chroma overlap filters.

Missing year in a user question defaults to DEFAULT_YEAR (2026).
Month / range questions match pages whose [event_start, event_end]
interval overlaps the query window (inclusive).
"""
from __future__ import annotations

import calendar
import re
from datetime import date

DEFAULT_YEAR = 2026

MONTH_NAMES = {
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

_MONTH_RE = re.compile(
    r"\b(" + "|".join(sorted(MONTH_NAMES, key=len, reverse=True)) + r")\b",
    re.IGNORECASE,
)
_YEAR_RE = re.compile(r"\b(20\d{2})\b")
_BETWEEN_RE = re.compile(
    r"\b(?:between|from)\s+([A-Za-z]+)\s+(?:and|to|until|through|-|–)\s+([A-Za-z]+)"
    r"(?:\s+(\d{4}))?",
    re.IGNORECASE,
)
_IN_MONTH_RE = re.compile(
    r"\b(?:in|during|of)\s+(" + "|".join(sorted(MONTH_NAMES, key=len, reverse=True)) + r")"
    r"(?:\s+(\d{4}))?\b",
    re.IGNORECASE,
)
_STARTED_RE = re.compile(
    r"\b(?:started|starts|beginning|began)\s+(?:in|on)\s+",
    re.IGNORECASE,
)
_ONLY_ON_RE = re.compile(
    r"\b(?:only\s+on|on)\s+(\d{1,2})(?:st|nd|rd|th)?\s+"
    r"(" + "|".join(sorted(MONTH_NAMES, key=len, reverse=True)) + r")"
    r"(?:\s+(\d{4}))?\b",
    re.IGNORECASE,
)

EVENT_LIST_QUESTION = re.compile(
    r"\b(what|which|list|show|name)\b.{0,40}\bevents?\b|"
    r"\bevents?\b.{0,40}\b(in|during|between|from|held)\b|"
    r"什麼活動|哪些活動|有什麼活動|有哪些活動",
    re.IGNORECASE,
)


def month_window(year: int, month: int) -> tuple[str, str]:
    """Inclusive ISO start/end for one calendar month."""
    last = calendar.monthrange(year, month)[1]
    return (date(year, month, 1).isoformat(), date(year, month, last).isoformat())


def range_window(start: date | str, end: date | str) -> tuple[str, str]:
    """Normalize an inclusive date window to ISO strings."""
    if isinstance(start, str):
        start = date.fromisoformat(start)
    if isinstance(end, str):
        end = date.fromisoformat(end)
    if end < start:
        start, end = end, start
    return (start.isoformat(), end.isoformat())


def overlaps(event_start: str, event_end: str,
             window_start: str, window_end: str) -> bool:
    """True if [event_start, event_end] overlaps [window_start, window_end].

    ISO date strings compare lexicographically. Chroma only allows $gte/$lte
    on numbers, so overlap filtering is done in Python.
    """
    return event_start <= window_end and event_end >= window_start


def where_for_plan(plan: dict) -> dict | None:
    """Optional Chroma where for equality modes; overlap uses Python."""
    mode = plan.get("mode", "overlap")
    start = plan["window_start"]
    if mode == "start_eq":
        return {"event_start": start}
    return None


def filter_overlapping_records(records: list[dict], plan: dict) -> list[dict]:
    """Keep text records whose event interval matches the question plan."""
    window_start = plan["window_start"]
    window_end = plan["window_end"]
    mode = plan.get("mode", "overlap")
    out = []
    for record in records:
        meta = record.get("metadata") or {}
        start = meta.get("event_start")
        end = meta.get("event_end")
        if not isinstance(start, str) or not isinstance(end, str):
            continue
        if mode == "start_eq":
            if start == window_start:
                out.append(record)
        elif mode == "start_in_month":
            if window_start <= start <= window_end:
                out.append(record)
        elif overlaps(start, end, window_start, window_end):
            out.append(record)
    return out


def distinct_urls(records: list[dict]) -> list[dict]:
    """One record per page URL, first wins."""
    seen: dict[str, dict] = {}
    for record in records:
        url = (record.get("metadata") or {}).get("url")
        if url and url not in seen:
            seen[url] = record
    return list(seen.values())


def _month_num(name: str) -> int | None:
    return MONTH_NAMES.get(name.strip().lower())


def parse_question_window(question: str, default_year: int = DEFAULT_YEAR
                          ) -> dict | None:
    """Resolve a user date constraint to a filter plan.

    Returns None if no calendar constraint is detected.
    Keys: window_start, window_end, mode ('overlap' | 'start_eq' | 'start_in_month').
    """
    q = question.strip()
    if not q:
        return None

    only = _ONLY_ON_RE.search(q)
    if only and (_STARTED_RE.search(q) or re.search(r"\bonly\s+on\b", q, re.I)):
        day = int(only.group(1))
        month = _month_num(only.group(2))
        year = int(only.group(3)) if only.group(3) else default_year
        if month:
            try:
                iso = date(year, month, day).isoformat()
            except ValueError:
                return None
            return {
                "window_start": iso,
                "window_end": iso,
                "mode": "start_eq",
            }

    if _STARTED_RE.search(q):
        m = _IN_MONTH_RE.search(q) or _MONTH_RE.search(q)
        if m:
            month_name = m.group(1)
            year_g = m.group(2) if m.lastindex and m.lastindex >= 2 else None
            year_m = _YEAR_RE.search(q)
            year = int(year_g) if year_g else (
                int(year_m.group(1)) if year_m else default_year)
            month = _month_num(month_name)
            if month:
                start, end = month_window(year, month)
                return {
                    "window_start": start,
                    "window_end": end,
                    "mode": "start_in_month",
                }

    between = _BETWEEN_RE.search(q)
    if between:
        m1, m2 = _month_num(between.group(1)), _month_num(between.group(2))
        year = int(between.group(3)) if between.group(3) else default_year
        year_m = _YEAR_RE.search(q)
        if not between.group(3) and year_m:
            year = int(year_m.group(1))
        if m1 and m2:
            start_m, end_m = min(m1, m2), max(m1, m2)
            s1, _ = month_window(year, start_m)
            _, e2 = month_window(year, end_m)
            return {
                "window_start": s1,
                "window_end": e2,
                "mode": "overlap",
            }

    in_month = _IN_MONTH_RE.search(q)
    if in_month:
        month = _month_num(in_month.group(1))
        year = int(in_month.group(2)) if in_month.group(2) else default_year
        if not in_month.group(2):
            year_m = _YEAR_RE.search(q)
            if year_m:
                year = int(year_m.group(1))
        if month:
            start, end = month_window(year, month)
            return {
                "window_start": start,
                "window_end": end,
                "mode": "overlap",
            }

    return None


