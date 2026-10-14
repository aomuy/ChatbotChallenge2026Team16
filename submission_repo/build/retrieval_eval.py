from bot.answer import retrieve, rag_answer, CONFIG

q = "Which two materials are banned from the laser cutter?"
# q = "What are materials banned from the laser cutter?"
# q = "What student interest groups are there?"
# q = "What are the student interest groups?"
# q = "Is HKU Robocon one of the student interest groups?"
# q = "Is HKU AI Club one of the student interest groups?"
chunks = retrieve(q, k=10)   # same fetch size as rag_answer

for i, c in enumerate(chunks[:CONFIG["k"]], 1):
    m = c["metadata"]
    print(f"--- #{i} dist={c['distance']:.4f} kind={m.get('kind')} ---")
    print("url:", m.get("url"))
    print("image:", m.get("image"))       # only for image docs
    print("section:", m.get("section"))   # text chunks
    print(c["text"])
    # print(c["text"][:500], "...\n" if len(c["text"]) > 500 else "\n")

print("MODEL:", rag_answer(q))