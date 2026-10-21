"""Deterministic count plans that do not call the LLM or Chroma client."""
from __future__ import annotations

import re

YEAR_IN_URL = re.compile(r"/uploads/(\d{4})/")
YEAR_IN_QUESTION = re.compile(r"\b(20\d{2})\b")
WP_SIZE = re.compile(r"-\d{2,4}x\d{2,4}(?=\.[A-Za-z0-9]+$)")
WP_SCALED = re.compile(r"-scaled(?=\.[A-Za-z0-9]+$)")
ACADEMY = re.compile(
    r"innovation academy|innoacademy|学院网站|學院網站", re.IGNORECASE
)
WORKSHOP_POSTER_COUNT = re.compile(
    r"workshop posters?|"
    r"posters? on the Innovation Academy|"
    r"Innovation Academy.{0,80}posters?|"
    r"工作坊海报|工作坊海報",
    re.IGNORECASE,
)
ROOM_OBJECT_COUNT = re.compile(
    r"makerspace|brainstorming|gallery|print room|north wall|"
    r"头脑风暴|北墙",
    re.IGNORECASE,
)
TABLE_NOUNS = (
    "tables", "table", "work tables", "worktables", "workbenches",
    "workbench", "桌子",
)
CHAIR_NOUNS = ("chairs", "chair", "stools", "stool", "椅子")
PRINTER_NOUNS = ("3d printers", "3d printer", "printers", "printer")
PRINTER_FLEET = re.compile(
    r"(3d printers?|3d 打印).{0,30}(in total|does the centre|does the center)|"
    r"(centre|center|中心).{0,20}(3d printers?|3d 打印)|"
    r"一共.{0,10}(3d )?打印",
    re.IGNORECASE,
)
NUMBER_NOUN = re.compile(
    r"(\d+|eleven|twelve|ten|nine|eight)\s+"
    r"(?:[A-Za-z][A-Za-z\-]*\s+){0,8}?"
    r"(tables?|chairs?|stools?|workbenches?|work\s+tables?|"
    r"3d printers?|printers?)",
    re.IGNORECASE,
)
WORD_NUMBERS = {
    "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
}
MODEL_COUNT = re.compile(
    r"(\d+)\s*[x×]?\s*(Prusa|Bambu|Formlabs|Form\s*4|MK4|X1C)",
    re.IGNORECASE,
)
EXPLICIT_FLEET = re.compile(
    r"(?:runs?|operates?|total of)\s+(\d+)\s+3d printers?",
    re.IGNORECASE,
)
PRINTER_MODEL = re.compile(
    r"Prusa\s*(?:MK[34]|i3)?|"
    r"Bambu(?:\s*Lab)?\s*(?:P1S|P1P|X1C|H2D)|"
    r"Formlabs\s*Form\s*4|Form\s*4",
    re.IGNORECASE,
)


def canonical_image(src: str) -> str:
    """Collapse WordPress resized copies onto one asset identity."""
    value = (src or "").split("?")[0]
    value = WP_SIZE.sub("", value)
    value = WP_SCALED.sub("", value)
    return value


def infer_year(meta: dict) -> int | None:
    """Year from metadata or a WordPress /uploads/YYYY/ URL."""
    value = meta.get("year") if meta else None
    if isinstance(value, int) and 1990 < value < 2100:
        return value
    if isinstance(value, str) and value.isdigit():
        year = int(value)
        if 1990 < year < 2100:
            return year
    for key in ("image", "url"):
        match = YEAR_IN_URL.search(str((meta or {}).get(key) or ""))
        if match:
            year = int(match.group(1))
            if 1990 < year < 2100:
                return year
    return None


def is_poster(meta: dict) -> bool:
    image_type = str(meta.get("image_type") or "").lower()
    src = str(meta.get("image") or meta.get("url") or "").lower()
    return image_type == "poster" or "poster" in src


def _on_academy(meta: dict) -> bool:
    blob = " ".join(
        str((meta or {}).get(key) or "") for key in ("url", "image", "page")
    ).lower()
    return "innoacademy" in blob


def poster_year_from_records(question: str, records) -> str | None:
    if not WORKSHOP_POSTER_COUNT.search(question):
        return None
    year_match = YEAR_IN_QUESTION.search(question)
    want_year = int(year_match.group(1)) if year_match else None
    academy_only = bool(ACADEMY.search(question))
    seen: set[str] = set()
    for record in records:
        meta = record.get("metadata") or {}
        if not is_poster(meta):
            continue
        if academy_only and not _on_academy(meta):
            continue
        if want_year is not None and infer_year(meta) != want_year:
            continue
        ident = canonical_image(str(meta.get("image") or record.get("id") or ""))
        if not ident or ident in seen:
            continue
        seen.add(ident)
    return str(len(seen)) if seen else None


def _as_int(token: str) -> int:
    key = token.lower()
    if key in WORD_NUMBERS:
        return WORD_NUMBERS[key]
    return int(token)


def object_mentions(text: str, nouns: tuple[str, ...]) -> list[int]:
    found: list[int] = []
    lower_nouns = tuple(n.lower() for n in nouns)
    for match in NUMBER_NOUN.finditer(text or ""):
        token = match.group(2).lower()
        if token in lower_nouns or any(
            token.startswith(n.rstrip("s")) or n.startswith(token.rstrip("s"))
            for n in lower_nouns
        ):
            found.append(_as_int(match.group(1)))
    return found


def room_object_from_records(question: str, records) -> str | None:
    if not ROOM_OBJECT_COUNT.search(question):
        return None
    q = question.lower()
    if any(w in q or w in question for w in ("table", "桌子")):
        nouns = TABLE_NOUNS
    elif any(w in q or w in question for w in ("chair", "stool", "椅子")):
        nouns = CHAIR_NOUNS
    elif "printer" in q or "打印" in question:
        nouns = PRINTER_NOUNS
    else:
        return None
    needle = "makerspace" if "makerspace" in q else (
        "brainstorm" if "brainstorm" in q or "头脑风暴" in question else ""
    )
    counts: list[int] = []
    for record in records:
        text = record.get("text") or ""
        if needle and needle not in text.lower():
            continue
        counts.extend(object_mentions(text, nouns))
    if not counts:
        return None
    return str(max(counts))


def printer_fleet_from_records(question: str, records) -> str | None:
    if not PRINTER_FLEET.search(question):
        return None
    fleet = 0
    explicit: list[int] = []
    models: set[str] = set()
    for record in records:
        text = record.get("text") or ""
        meta = record.get("metadata") or {}
        blob = " ".join(
            [text, str(meta.get("image") or ""), str(meta.get("url") or "")]
        )
        for match in MODEL_COUNT.finditer(text):
            fleet += int(match.group(1))
        for match in EXPLICIT_FLEET.finditer(text):
            explicit.append(int(match.group(1)))
        for match in PRINTER_MODEL.finditer(blob):
            models.add(re.sub(r"\s+", " ", match.group(0)).strip().lower())
    if explicit:
        return str(max(explicit))
    if fleet:
        return str(fleet)
    return str(len(models)) if models else None
