"""Deterministic keyword router for RAG Chroma `where` filters.

Chooses kind=image (optionally with image_type) or kind=text from question
cues. Default is no filter when nothing matches. Image cues beat text cues.
"""
from __future__ import annotations

import re

# Ordered: first match wins for stable $in lists when several types hit.
_IMAGE_TYPE_CUES: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("poster", re.compile(r"\bposters?\b", re.IGNORECASE)),
    ("diagram", re.compile(r"\b(diagrams?|charts?|figures?)\b", re.IGNORECASE)),
    ("logo", re.compile(r"\blogos?\b", re.IGNORECASE)),
    ("map", re.compile(r"\bmaps?\b", re.IGNORECASE)),
    ("signage", re.compile(r"\b(signage|signs?)\b", re.IGNORECASE)),
    ("photo", re.compile(
        r"\b(photos?|photographs?|pictures?)\b", re.IGNORECASE)),
)

_IMAGE_MODALITY = re.compile(
    r"\b(in the (image|photo|picture|poster)|visible in|shown in)\b|"
    r"\bwhat does .{0,40}\bshow\b|"
    r"\b(images?|photos?|photographs?|pictures?|posters?|diagrams?|"
    r"logos?|maps?|signage|signs?)\b",
    re.IGNORECASE,
)

_TEXT_MODALITY = re.compile(
    r"\b(banned|allowed|prohibited|forbidden)\b|"
    r"\b(safety|rules?|policy|policies|manual)\b|"
    r"\bhow (do|to|can)\b|"
    r"\bopening hours\b|"
    r"\b(book|booking|bookings)\b|"
    r"\bmaterials?\b|"
    r"\binterest groups?\b|"
    r"\blaser cutter\b|"
    r"\bfunding scheme\b|"
    r"激光|禁止|截止日期",
    re.IGNORECASE,
)

# Venue / sign questions whose answers live in image descriptions (W2 Lv3/Lv5),
# even when the user never says "photo" or "poster".
_PLACE_VISUAL = re.compile(
    r"\bmakerspace\b|"
    r"\bbrainstorming\b|"
    r"\bgallery\b|"
    r"\bwhiteboard\b|"
    r"\b(on the wall|behind the (wall|seating|brainstorming)|wall behind)\b|"
    r"\bthree words\b|"
    r"墙上|墙后|头脑风暴|白板上|走廊 gallery|办公室外",
    re.IGNORECASE,
)


def _matched_image_types(question: str) -> list[str]:
    """Return unique image_type values whose cues appear, in cue-table order."""
    types: list[str] = []
    for image_type, pattern in _IMAGE_TYPE_CUES:
        if pattern.search(question) and image_type not in types:
            types.append(image_type)
    return types


def retrieval_where(question: str) -> dict | None:
    """Return a Chroma metadata filter for RAG, or None for unfiltered search."""
    if not question or not question.strip():
        return None

    types = _matched_image_types(question)
    image_cue = bool(types) or bool(_IMAGE_MODALITY.search(question))
    place_visual = bool(_PLACE_VISUAL.search(question))
    text_cue = bool(_TEXT_MODALITY.search(question))

    if image_cue:
        if len(types) == 1:
            return {"$and": [{"kind": "image"}, {"image_type": types[0]}]}
        if len(types) > 1:
            return {"$and": [
                {"kind": "image"},
                {"image_type": {"$in": types}},
            ]}
        return {"kind": "image"}

    if place_visual:
        return {"kind": "image"}

    if text_cue:
        return {"kind": "text"}

    return None
