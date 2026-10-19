"""Tests for event date enrichment, overlap filters, and default year."""
import unittest
from unittest.mock import patch

import chromadb

from bot.counting import count_answer
from bot.event_dates import (
    DEFAULT_YEAR,
    distinct_urls,
    filter_overlapping_records,
    month_window,
    parse_question_window,
)
from build.enrich_dates import (
    enrich_pages,
    inherit_image_dates,
    parse_text_dates,
    resolve_dates,
    _parse_date_clause,
)
from build.index import build_index
from build.images import index_descriptions


class ParseDateClauseTests(unittest.TestCase):
    def test_single_day_formats(self):
        self.assertEqual(_parse_date_clause("March 10, 2022 (Thu)"),
                         ("2022-03-10", "2022-03-10"))
        self.assertEqual(_parse_date_clause("25th April 2023 (Tuesday)"),
                         ("2023-04-25", "2023-04-25"))
        self.assertEqual(_parse_date_clause("26 March, 2026 (Thursday)"),
                         ("2026-03-26", "2026-03-26"))

    def test_ranges(self):
        self.assertEqual(_parse_date_clause("March 9 to 15, 2025"),
                         ("2025-03-09", "2025-03-15"))
        self.assertEqual(_parse_date_clause("July 5 – 18, 2025"),
                         ("2025-07-05", "2025-07-18"))
        self.assertEqual(
            _parse_date_clause("August 26, 2026 to October 2, 2026"),
            ("2026-08-26", "2026-10-02"))

    def test_fuzzy_rejected(self):
        self.assertIsNone(_parse_date_clause("Early June until early July, 2023"))


class TextParseAndResolverTests(unittest.TestCase):
    def test_hub_from_multiple_date_labels(self):
        page = {
            "url": "https://example.org/past-events/",
            "title": "Past events",
            "sections": [{
                "heading": "List",
                "text": "Date: April 25, 2023 (Tuesday)\n"
                        "Date: May 9, 2023 (Tuesday)\n",
            }],
        }
        result = parse_text_dates(page)
        self.assertTrue(result["hub"])
        self.assertIsNone(result["pair"])

    def test_single_event_range(self):
        page = {
            "url": "https://example.org/tour/",
            "title": "Tour",
            "sections": [{"heading": "", "text": "Date: March 9 to 15, 2025 Highlights:"}],
        }
        result = parse_text_dates(page)
        self.assertFalse(result["hub"])
        self.assertEqual(result["pair"], ("2025-03-09", "2025-03-15"))

    def test_agree_two_sources(self):
        text = {"pair": ("2025-03-09", "2025-03-15"), "hub": False}
        decision = resolve_dates(text, ("2025-03-09", "2025-03-15"),
                                 {"pair": ("2025-03-09", "2025-03-15"), "hub": False})
        self.assertEqual(decision["event_start"], "2025-03-09")
        self.assertIsNone(decision["log"])

    def test_conflict_prefers_text(self):
        text = {"pair": ("2025-03-09", "2025-03-15"), "hub": False}
        decision = resolve_dates(text, ("2025-03-01", "2025-03-01"),
                                 {"pair": ("2025-03-01", "2025-03-01"), "hub": False})
        self.assertEqual(decision["event_start"], "2025-03-09")
        self.assertEqual(decision["reason"], "conflict")
        self.assertEqual(decision["log"], "review")

    def test_single_source_review(self):
        text = {"pair": ("2025-03-09", "2025-03-09"), "hub": False}
        decision = resolve_dates(text, None, {"pair": None, "hub": False})
        self.assertIsNone(decision["event_start"])
        self.assertEqual(decision["reason"], "single_source")

    def test_missing_all_sources(self):
        decision = resolve_dates(
            {"pair": None, "hub": False}, None, {"pair": None, "hub": False})
        self.assertEqual(decision["log"], "missing")

    def test_hub_logged(self):
        decision = resolve_dates(
            {"pair": None, "hub": True}, ("2025-01-01", "2025-01-01"),
            {"pair": None, "hub": False})
        self.assertEqual(decision["reason"], "hub")
        self.assertIsNone(decision["event_start"])


class EnrichIntegrationTests(unittest.TestCase):
    def test_enrich_pages_writes_on_agreement(self):
        pages = [{
            "url": "https://example.org/tour/",
            "title": "Tour",
            "sections": [{"heading": "", "text": "Date: March 9 to 15, 2025"}],
        }]
        pair = ("2025-03-09", "2025-03-15")
        out, review, missing = enrich_pages(
            pages,
            html_fetcher=lambda url: pair,
            llm_extractor=lambda page: {"pair": pair, "hub": False, "raw": {}},
        )
        self.assertEqual(out[0]["event_start"], "2025-03-09")
        self.assertEqual(out[0]["event_end"], "2025-03-15")
        self.assertEqual(review, [])
        self.assertEqual(missing, [])

    def test_image_inheritance(self):
        pages = [{"url": "https://example.org/e", "event_start": "2026-03-01",
                  "event_end": "2026-03-02"}]
        images = [{"src": "a.png", "page": "https://example.org/e"},
                  {"src": "b.png", "page": "https://example.org/other"}]
        out = inherit_image_dates(pages, images)
        self.assertEqual(out[0]["event_start"], "2026-03-01")
        self.assertNotIn("event_start", out[1])


class OverlapFilterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = chromadb.EphemeralClient()

    def setUp(self):
        self.store = self.client.create_collection(
            "event-dates-test", embedding_function=None)
        records = [
            ("carnival", "Carnival", {
                "kind": "text", "url": "carnival", "title": "Carnival",
                "event_start": "2026-08-26", "event_end": "2026-10-02",
            }),
            ("tour-mar", "Tour March", {
                "kind": "text", "url": "tour-mar", "title": "Tour",
                "event_start": "2025-03-09", "event_end": "2025-03-15",
            }),
            ("talk", "Talk", {
                "kind": "text", "url": "talk", "title": "Talk",
                "event_start": "2026-03-26", "event_end": "2026-03-26",
            }),
            ("venue", "Venue page", {
                "kind": "text", "url": "venue", "title": "Venue",
            }),
        ]
        self.store.add(
            ids=[r[0] for r in records],
            documents=[r[1] for r in records],
            metadatas=[r[2] for r in records],
            embeddings=[[1.0, 0.0] for _ in records],
        )

    def tearDown(self):
        self.client.delete_collection("event-dates-test")

    def _text_records(self):
        from bot.store import filter_records
        return filter_records(self.store, where={"kind": "text"})

    def test_month_overlap_includes_multi_month(self):
        start, end = month_window(2026, 9)
        plan = {"window_start": start, "window_end": end, "mode": "overlap"}
        matched = distinct_urls(filter_overlapping_records(self._text_records(), plan))
        self.assertEqual(len(matched), 1)
        self.assertEqual(matched[0]["metadata"]["url"], "carnival")

    def test_aug_sep_range_counts_carnival_once(self):
        plan = parse_question_window("how many events between August and September 2026")
        matched = distinct_urls(filter_overlapping_records(self._text_records(), plan))
        self.assertEqual(len(matched), 1)

    def test_march_2026_default_year(self):
        plan = parse_question_window("how many events in March")
        self.assertEqual(plan["window_start"], "2026-03-01")
        self.assertEqual(plan["window_end"], "2026-03-31")
        self.assertEqual(DEFAULT_YEAR, 2026)
        matched = distinct_urls(filter_overlapping_records(self._text_records(), plan))
        self.assertEqual(len(matched), 1)
        self.assertEqual(matched[0]["metadata"]["url"], "talk")

    def test_count_answer_event_path(self):
        self.assertEqual(count_answer("How many events in March?", store=self.store), "1")
        self.assertEqual(
            count_answer("How many events between August and September 2026?",
                         store=self.store),
            "1")


class IndexCopiesEventDatesTests(unittest.TestCase):
    def test_page_and_image_event_dates_indexed(self):
        pages = [{
            "url": "https://example.org/e",
            "title": "Event",
            "event_start": "2026-03-01",
            "event_end": "2026-03-02",
            "sections": [{"heading": "Info", "text": "details " * 50}],
            "images": [],
        }]
        with patch("build.index.get_store"), patch("build.index.add_to_store") as add:
            build_index(pages)
        meta = add.call_args.args[2]
        self.assertTrue(all(m["event_start"] == "2026-03-01" for m in meta))

        images = [{"src": "a.png", "page": "https://example.org/e",
                   "event_start": "2026-03-01", "event_end": "2026-03-02"}]
        with patch("build.images.get_store"), patch("build.images.add_to_store") as add_im:
            index_descriptions({"a.png": "A photo"}, images)
        im_meta = add_im.call_args.args[2]
        self.assertEqual(im_meta[0]["event_start"], "2026-03-01")


if __name__ == "__main__":
    unittest.main()
