"""Offline regression tests; real Chroma, explicit vectors, mocked LLM only.

Run from submission_repo: python -m unittest discover -s tests -v
"""
import json
import unittest
from unittest.mock import patch

import chromadb

from bot.answer import rag_answer, rag_answer_batch
from bot.counting import count_answer
from bot.store import count_records, filter_records, query
from build.images import description_fields, index_descriptions
from build.index import build_index


class FilteringTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = chromadb.EphemeralClient()

    def setUp(self):
        self.store = self.client.create_collection("filtering-test", embedding_function=None)
        records = []
        for i in range(19):
            records.append((f"poster-{i}", f"Poster {i}", {
                "kind": "image", "image_type": "poster", "image": f"poster/{i}",
                "url": "gallery", "year": 2025 if i < 12 else 2024,
            }))
        records.append(("poster-duplicate", "Duplicate poster", {
            "kind": "image", "image_type": "poster", "image": "poster/0",
            "url": "another-gallery", "year": 2025,
        }))
        for i in range(8):
            records.append((f"photo-{i}", "Photo shows three posters and eleven tables", {
                "kind": "image", "image_type": "photo", "image": f"photo/{i}",
                "url": "gallery", "year": 2025,
            }))
        for i, capacity in enumerate([40, 30, 12]):
            for part in range(3):
                records.append((f"venue-{i}-{part}", "Venue details with a poster mention", {
                    "kind": "text", "page_type": "venue", "url": f"venue/{i}",
                    "capacity": capacity, "position": part,
                }))
        self.store.add(ids=[r[0] for r in records], documents=[r[1] for r in records],
                       metadatas=[r[2] for r in records],
                       embeddings=[[1.0, 0.0] for _ in records])

    def tearDown(self):
        self.client.delete_collection(self.store.name)

    def test_filter_reads_every_page_and_count_deduplicates(self):
        where = {"image_type": "poster"}
        records = filter_records(self.store, where=where, batch_size=4)
        self.assertEqual(len(records), 20)
        self.assertEqual(count_records(self.store, where, batch_size=4), 20)
        self.assertEqual(count_records(self.store, where, distinct_by="image", batch_size=4), 19)

    def test_metadata_and_document_filters_compose(self):
        where = {"$and": [{"image_type": "poster"}, {"year": 2025}]}
        self.assertEqual(count_records(self.store, where, distinct_by="image", batch_size=4), 12)
        records = filter_records(self.store, {"kind": "image"},
                                 {"$contains": "eleven tables"}, batch_size=3)
        self.assertEqual(len(records), 8)
        self.assertTrue(all(r["metadata"]["image_type"] == "photo" for r in records))

    def test_empty_results_and_exact_page_boundary(self):
        self.assertEqual(count_records(self.store, {"image_type": "logo"}, distinct_by="image"), 0)
        self.assertEqual(filter_records(self.store, {"image_type": "logo"}), [])
        self.assertEqual(len(filter_records(self.store, {"image_type": "photo"}, batch_size=4)), 8)
        with self.assertRaises(ValueError):
            filter_records(self.store, batch_size=0)

    def test_page_count_does_not_count_chunks(self):
        where = {"$and": [{"page_type": "venue"}, {"capacity": {"$gte": 30}}]}
        self.assertEqual(count_records(self.store, where, distinct_by="url", batch_size=2), 2)
        with self.assertRaises(ValueError):
            count_records(self.store, {"kind": "text"}, distinct_by="image")

    def test_search_accepts_filters_before_top_k(self):
        with patch("bot.store.embed", return_value=[[1.0, 0.0]]):
            hits = query(self.store, "tables", k=3, where={"kind": "image"},
                         where_document={"$contains": "eleven tables"})
        self.assertEqual(len(hits), 3)
        self.assertTrue(all(hit["metadata"]["image_type"] == "photo" for hit in hits))

    def test_count_route_returns_database_number_without_search(self):
        plan = json.dumps({"entity": "image", "where": {"image_type": "poster"}})
        for question in ["How many posters are indexed?", "有多少张海报？", "一共有幾張海報？"]:
            with self.subTest(question=question), \
                    patch("bot.counting.get_store", return_value=self.store), \
                    patch("bot.counting.chat", return_value=plan), \
                    patch("bot.answer.retrieve") as retrieve, \
                    patch("bot.answer.chat") as answer_chat:
                self.assertEqual(rag_answer(question), "19")
                retrieve.assert_not_called()
                answer_chat.assert_not_called()

    def test_year_and_numeric_metadata_plans(self):
        plans = [
            ({"entity": "image", "where": {"$and": [
                {"image_type": "poster"}, {"year": 2025}]}}, "12"),
            ({"entity": "page", "where": {"$and": [
                {"page_type": "venue"}, {"capacity": {"$gte": 30}}]}}, "2"),
            ({"entity": "image", "where": {"image_type": "logo"}}, "0"),
        ]
        for plan, expected in plans:
            with self.subTest(plan=plan), patch("bot.counting.chat", return_value=json.dumps(plan)):
                self.assertEqual(count_answer("How many?", self.store), expected)

    def test_bad_or_unsupported_plans_fall_back(self):
        responses = ["invalid JSON", "[]", '{"entity":null}',
                     '{"entity":"image","where":{"invented":"poster"}}',
                     '{"entity":"image","where":{}}',
                     '{"entity":"image","where":{"year":{"$bad":2025}}}']
        for response in responses:
            with self.subTest(response=response), patch("bot.counting.chat", return_value=response):
                self.assertIsNone(count_answer("How many posters?", self.store))

    def test_legacy_or_unknown_types_do_not_undercount(self):
        for metadata in [
            {"kind": "image", "image": "legacy"},
            {"kind": "image", "image": "legacy", "image_type": "unknown"},
        ]:
            self.store.upsert(ids=["legacy"], documents=["Maybe a poster"],
                              metadatas=[metadata], embeddings=[[1.0, 0.0]])
            with patch("bot.counting.chat", return_value=json.dumps({
                "entity": "image", "where": {"image_type": "poster"}})):
                self.assertIsNone(count_answer("How many posters?", self.store))

    def test_ordinary_question_skips_count_planner(self):
        with patch("bot.counting.get_store") as store, patch("bot.counting.chat") as chat:
            self.assertIsNone(count_answer("What colour are the lockers?"))
            store.assert_not_called()
            chat.assert_not_called()

    def test_physical_count_uses_evidence_instead_of_record_count(self):
        with patch("bot.counting.get_store", return_value=self.store), \
                patch("bot.counting.chat", return_value='{"entity":null}'), \
                patch("bot.answer.retrieve", return_value=[{
                    "text": "The photo shows 11 tables", "metadata": {"url": "gallery"}}]), \
                patch("bot.answer.chat", return_value="11") as chat:
            self.assertEqual(rag_answer("How many tables are in the photo?"), "11")
            self.assertIn("partial search", chat.call_args.args[0][0]["content"])

    def test_batch_preserves_input_order(self):
        with patch("bot.answer.rag_answer", side_effect=lambda q: {"one": "1", "two": "2"}[q]):
            self.assertEqual(rag_answer_batch(["two", "one", "two"]), ["2", "1", "2"])


class IngestionTests(unittest.TestCase):
    def test_structured_and_legacy_descriptions(self):
        structured = {"image_type": "poster", "description": "Open day 2025"}
        self.assertEqual(description_fields(json.dumps(structured)), ("Open day 2025", "poster"))
        self.assertEqual(description_fields("```json\n" + json.dumps(structured) + "\n```"),
                         ("Open day 2025", "poster"))
        self.assertEqual(description_fields("A photo containing posters"),
                         ("A photo containing posters", "unknown"))
        self.assertEqual(description_fields({"description": "Unclassified", "image_type": []}),
                         ("Unclassified", "unknown"))

    def test_image_metadata_is_indexed_without_guessing_legacy_type(self):
        images = [{"src": "poster.png", "page": "gallery", "image_type": "poster", "year": 2025}]
        with patch("build.images.get_store"), patch("build.images.add_to_store") as add:
            index_descriptions({"poster.png": "Legacy description", "photo.png": json.dumps({
                "image_type": "photo", "description": "Three posters in a room"})}, images)
        metadata = add.call_args.args[2]
        self.assertEqual(metadata[0]["image_type"], "poster")
        self.assertEqual(metadata[0]["year"], 2025)
        self.assertEqual(metadata[1]["image_type"], "photo")
        self.assertEqual(metadata[1]["image"], "photo.png")

    def test_page_metadata_is_preserved_for_all_chunks(self):
        pages = [{"url": "venue/1", "text": "venue details " * 200,
                  "page_type": "venue", "capacity": 40, "year": 2025, "images": []}]
        with patch("build.index.get_store"), patch("build.index.add_to_store") as add:
            build_index(pages)
        metadata = add.call_args.args[2]
        self.assertGreater(len(metadata), 1)
        self.assertTrue(all(m["capacity"] == 40 and m["page_type"] == "venue" for m in metadata))
        self.assertTrue(all("text" not in m and "images" not in m for m in metadata))


if __name__ == "__main__":
    unittest.main()
