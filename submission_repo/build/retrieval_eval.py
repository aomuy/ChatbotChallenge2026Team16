from bot.answer import retrieve, rag_answer, CONFIG
from bot.retrieval_filter import retrieval_where

# q = "Which two materials are banned from the laser cutter?"
# q = "What materials are banned from the laser cutter?"
q = "How many student interest groups are there?"   # actually there isn't an official list of student interest groups...
# q = "What are the student interest groups?"
# q = "Is HKU Robocon one of the student interest groups?"
# q = "Is HKU AI Club one of the student interest groups?"
where = retrieval_where(q)
print("WHERE:", where)
chunks = retrieve(q, k=10, where=where)   # same fetch size / filter as rag_answer

for i, c in enumerate(chunks[:CONFIG["k"]], 1):
    m = c["metadata"]
    print(f"--- #{i} dist={c['distance']:.4f} kind={m.get('kind')} ---")
    print("url:", m.get("url"))
    print("image:", m.get("image"))       # only for image docs
    print("section:", m.get("section"))   # text chunks
    print(c["text"])
    # print(c["text"][:500], "...\n" if len(c["text"]) > 500 else "\n")

print("MODEL:", rag_answer(q))