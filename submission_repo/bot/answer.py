"""Your chatbot. STUB. This is the file you actually write.

Two functions must exist with these exact names and signatures. Every
other line in this file, and every file under build/, is yours to
rewrite.
"""
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

If the context does not contain the answer, you MUST give your best guess anyway. 
In this case you can guess without ANY evidence from the context and use your own 
knowledge. You should sound confident and do NOT let others know that you are 
referring to the context, the index, or the database.
NEVER reply that you do not know or the context does not contain the answer.
NEVER mention the context or the index EXPLICITLY in your response.
"""

EVENT_LIST_PROMPT = """You list events held at the Tam Wing Fan Innovation Wing.

Answer only from the context below. Each block is one indexed page.
List the events that fall in the asked period. Use event names/titles from
the context. If the context has no matching events, reply exactly:
No matching events found in the indexed data.
Reply with the list only — no preamble.
"""

CONFIG = {
    "k": 5,   # try 3 to 10, tuned in Workshop 1 block 5
}


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
    ]).strip()


def rag_answer(question: str) -> str:
    """One question in, one answer out.

    Runs once per question with a 30 second budget. Anything expensive
    belongs in build/, not here.
    """
    count = count_answer(question)
    if count is not None:
        return count

    listed = _event_list_answer(question)
    if listed is not None:
        return listed

    where = retrieval_where(question)
    chunks = retrieve(question, k=10, where=where)
    chunks = chunks[:CONFIG["k"]]

    context = "\n\n".join(
        f"[{c['metadata'].get('url', '?')}]\n{c['text']}" for c in chunks
    )

    system_prompt = SYSTEM_PROMPT
    if COUNT_QUESTION.search(question):
        system_prompt += """

For this count question, the retrieved context is only a partial search
result. Never treat the number of retrieved chunks, mentions, pages or
images as the total. Reply with a number only if the context states the
requested count explicitly or supplies complete evidence for that total.
If not, reply 'Cannot determine from the indexed data.' instead of guessing.
This count-specific rule overrides the guessing instruction above."""

    reply = chat([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
    ])

    #  check the format of what came back: if you asked for a
    #  number, make sure you got one, and strip any stray prose.
    reply = reply.strip()
    if any(keyword in question.lower() for keyword in ["how many", "number of", "how long", "how tall", "how wide"]):
        import re
        numbers = re.findall(r'\d+', reply)
        if numbers:
            reply = numbers[0]

    return reply


def rag_answer_batch(questions: list[str]) -> list[str]:
    """Many questions in, the same number of answers out, in order."""
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(rag_answer, questions))
    return results
