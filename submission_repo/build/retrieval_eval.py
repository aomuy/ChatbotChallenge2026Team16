from bot.answer import retrieve, rag_answer, CONFIG

q = "Which two materials are banned from the laser cutter?"
chunks = retrieve(q, k=10)   # same fetch size as rag_answer

for i, c in enumerate(chunks[:CONFIG["k"]], 1):
    m = c["metadata"]
    print(f"--- #{i} dist={c['distance']:.4f} kind={m.get('kind')} ---")
    print("url:", m.get("url"))
    print("image:", m.get("image"))       # only for image docs
    print("section:", m.get("section"))   # text chunks
    print(c["text"][:500], "...\n" if len(c["text"]) > 500 else "\n")

print("MODEL:", rag_answer(q))