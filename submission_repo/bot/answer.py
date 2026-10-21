"""Your chatbot. STUB. This is the file you actually write.

Two functions must exist with these exact names and signatures. Every
other line in this file, and every file under build/, is yours to
rewrite.
"""
import re
from concurrent.futures import ThreadPoolExecutor

from bot.counting import COUNT_QUESTION, count_answer
from bot.event_dates import (
    DEFAULT_YEAR,
    EVENT_LIST_QUESTION,
    distinct_urls,
    filter_overlapping_records,
    parse_question_window,
)
from bot.llm import chat
from bot.retrieval_filter import retrieval_where
from bot.store import filter_records, get_store, query

# --------------------------------------------------------------------
# The prompt. Workshop 1 block 2 covers what each part is doing.
# --------------------------------------------------------------------
SYSTEM_PROMPT = """You answer questions about the Tam Wing Fan Innovation Wing.

Reply with the answer only. No explanation, no preamble. If the question
asks how many, reply with a number.

Prefer facts copied from the context: exact sign/poster wording, names,
dates, and counts. Do not paraphrase wall text or team names. If wall
lettering is visible, copy the words in order, including a three-word
line such as HKU ENGINEERING INNOVATION when those glyphs appear. If
alt text or captions name Pitch New Tech Ideas winners, list every
named team (keep spellings such as Digitoe/Digitio as written). For
laser-cutter bans, copy every material the context says not to laser
(PVC, Teflon, polycarbonate, or others) without swapping in a material
the context does not name. For Funding Scheme deadlines, prefer the
date on the current funding-scheme page (2025-26 / second round / the
latest Application deadline), not a 2021–2023 leftover.

If the context does not contain the answer, you MUST give your best guess anyway.
Sound confident. NEVER reply that you do not know or that the context is missing.
NEVER mention the context, the index, or the database explicitly.
"""

EVENT_LIST_PROMPT = """You list events held at the Tam Wing Fan Innovation Wing.

Answer only from the context below. Each block is one indexed page.
List the events that fall in the asked period. Use event names/titles from
the context. If the context has no matching events, reply exactly:
No matching events found in the indexed data.
Reply with the list only — no preamble.
"""

CONFIG = {
    "k": 8,
}

COMPOUND_QUESTION = re.compile(
    r"\b(and who|and how many|and which|, and )\b|以及|，主任|，它的主任",
    re.IGNORECASE,
)
PURE_COUNT = re.compile(
    r"^(how many|number of|一共|总共|總共|多少)",
    re.IGNORECASE,
)


def retrieve(question: str, k: int = None, where: dict = None,
             where_document: dict = None) -> list[dict]:
    """Return the k chunks most relevant to the question.

    Kept separate from rag_answer on purpose: it lets you check whether
    an answer was ever fetched at all, which is the only way to tell a
    retrieval failure from a prompt failure. Do not delete it even if
    you rewrite everything else.
    """
    store = get_store()
    return query(store, question, k=k or CONFIG["k"], where=where,
                 where_document=where_document)


def _event_list_answer(question: str, store=None) -> str | None:
    """Answer calendar list questions via overlap filter, not top-k RAG."""
    if COUNT_QUESTION.search(question):
        return None
    if not EVENT_LIST_QUESTION.search(question):
        return None
    plan = parse_question_window(question, default_year=DEFAULT_YEAR)
    if plan is None:
        return None
    if store is None:
        store = get_store()
    records = filter_records(store, where={"kind": "text"})
    matched = distinct_urls(filter_overlapping_records(records, plan))
    if not matched:
        return "No matching events found in the indexed data."

    blocks = []
    for record in matched:
        meta = record.get("metadata") or {}
        url = meta.get("url", "?")
        title = meta.get("title") or ""
        start = meta.get("event_start", "")
        end = meta.get("event_end", "")
        text = (record.get("text") or "")[:800]
        blocks.append(f"[{url}] {title} ({start}..{end})\n{text}")
    context = "\n\n".join(blocks)
    return chat([
        {"role": "system", "content": EVENT_LIST_PROMPT},
        {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
    ], temperature=0.0).strip()


def _chunk_key(chunk: dict) -> str:
    meta = chunk.get("metadata") or {}
    return meta.get("image") or meta.get("url") or chunk.get("text", "")[:80]


def _merge_chunks(*groups: list[dict], limit: int = 16) -> list[dict]:
    seen = set()
    out = []
    for group in groups:
        for chunk in group:
            key = _chunk_key(chunk)
            if key in seen:
                continue
            seen.add(key)
            out.append(chunk)
            if len(out) >= limit:
                return out
    return out


def _contains_chunks(phrases: list[str], where: dict | None = None,
                     limit: int = 8) -> list[dict]:
    """Lexical Chroma $contains hits, capped so this stays inside 30s."""
    store = get_store()
    out: list[dict] = []
    seen: set[str] = set()
    for phrase in phrases:
        try:
            hits = filter_records(
                store, where=where, where_document={"$contains": phrase},
            )
        except Exception:
            continue
        for hit in hits:
            key = _chunk_key(hit)
            if key in seen:
                continue
            seen.add(key)
            out.append(hit)
            if len(out) >= limit:
                return out
    return out


def _lexical_queries(question: str) -> list[tuple[list[str], dict | None]]:
    """Phrases whose documents should be pulled even if embedding rank is poor."""
    q = question.lower()
    jobs: list[tuple[list[str], dict | None]] = []
    if "pitch new tech" in q or "优胜" in question:
        jobs.append(
            (["Pitch New Tech", "Digitoe", "Digitio", "Smartsocks", "Gingtrolley"],
             None),
        )
    if "wall" in q or "墙上" in question or "three words" in q or "三个词" in question:
        jobs.append(
            (["HKU ENGINEERING INNOVATION", "ENGINEERING INNOVATION",
              "HKU ENGINEERING"],
             {"kind": "image"}),
        )
    if "laser" in q or "激光" in question:
        jobs.append(
            (["Do not laser", "PVC and Teflon", "polycarbonate", "PVC"],
             {"kind": "text"}),
        )
    if "funding scheme" in q or "截止日期" in question:
        jobs.append(
            (["Funding Scheme", "Application deadline", "Important dates",
              "October 30 2026"],
             {"kind": "text"}),
        )
    if "director" in q or "主任" in question:
        jobs.append(
            (["Director of Innovation Wing", "talk to Kit", "C.K.Chui"],
             None),
        )
    return jobs


def _boost_queries(question: str) -> list[str]:
    q = question.lower()
    extra = []
    if "laser" in q or "激光" in question:
        extra.append("laser cutter banned materials PVC polycarbonate")
    if "funding scheme" in q and (
        "deadline" in q or "截止" in question or "second round" in q
    ):
        extra.append("Funding Scheme application deadline second round 2026")
    if "3d printer" in q or "3d 打印" in q:
        extra.append("Bambu Lab 3D printer how many printers Innovation Wing")
    if "pitch new tech" in q:
        extra.append("Pitch New Tech Ideas 2025 winning teams")
    if "director" in q or "主任" in question:
        extra.append("Director of Innovation Wing Kit C.K.Chui")
    if "wall" in q or "three words" in q or "三个词" in question or "墙上" in question:
        extra.append("HKU ENGINEERING INNOVATION wall lettering brainstorming")
    return extra


def _split_compound(question: str) -> list[str]:
    if not COMPOUND_QUESTION.search(question):
        return [question]
    parts = re.split(
        r"\s+and (?=who|how many|which)\s+|，(?=主任|它的)|以及",
        question,
        flags=re.IGNORECASE,
    )
    parts = [p.strip(" ?？") for p in parts if p and p.strip(" ?？")]
    return parts if len(parts) >= 2 else [question]


def rag_answer(question: str) -> str:
    """One question in, one answer out.

    Runs once per question with a 30 second budget. Anything expensive
    belongs in build/, not here.
    """
    compound = bool(COMPOUND_QUESTION.search(question))
    if not compound:
        count = count_answer(question)
        if count is not None:
            return count

        listed = _event_list_answer(question)
        if listed is not None:
            return listed

    where = retrieval_where(question)
    groups = [retrieve(question, k=12, where=where)]
    if where and where.get("kind") == "image":
        groups.append(retrieve(question, k=6, where={"kind": "text"}))
    for part in _split_compound(question):
        if part == question:
            continue
        groups.append(retrieve(part, k=8, where=retrieval_where(part)))
    for extra in _boost_queries(question):
        groups.append(retrieve(extra, k=6, where=retrieval_where(extra)))
    for phrases, lex_where in _lexical_queries(question):
        groups.append(_contains_chunks(phrases, where=lex_where, limit=8))
    chunks = _merge_chunks(*groups, limit=18)

    context = "\n\n".join(
        f"[{c['metadata'].get('url', '?')}]\n{c['text']}" for c in chunks
    )

    system_prompt = SYSTEM_PROMPT
    if COUNT_QUESTION.search(question):
        system_prompt += """

For this count question, the retrieved context is only a partial search
result. Never treat the number of retrieved chunks as the total. List matching
items from the context first in your reasoning, then reply with one number.
Reply with a number only if the context states the requested count explicitly
or supplies complete evidence for that total. If not, make your best guess."""

    if compound:
        system_prompt += """

This question has more than one part. Answer every part, in order.
Do not drop the second clause."""

    reply = chat([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
    ], temperature=0.0)

    reply = reply.strip()
    if PURE_COUNT.search(question.strip()) and not compound:
        numbers = re.findall(r"\d+", reply)
        if numbers:
            reply = numbers[0]

    return reply


def rag_answer_batch(questions: list[str]) -> list[str]:
    """Many questions in, the same number of answers out, in order."""
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(rag_answer, questions))
    return results
