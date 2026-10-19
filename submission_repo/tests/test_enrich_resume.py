"""Resume, --limit, and Qwen date-model failover for enrich_dates."""
import unittest
from unittest.mock import MagicMock, patch

from build.enrich_dates import (
    enrich_one_page,
    enrich_pages,
    is_finished,
    unfinished_pages,
)
from build.qwen_chat import (
    DateModelsExhausted,
    chat_date,
    is_quota_error,
    reset_exhausted_models,
)


class FinishedSelectionTests(unittest.TestCase):
    def test_finished_with_dates_or_status(self):
        self.assertTrue(is_finished({
            "url": "a", "event_start": "2026-01-01", "event_end": "2026-01-01"}))
        self.assertTrue(is_finished({"url": "b", "event_date_status": "hub"}))
        self.assertFalse(is_finished({"url": "c"}))
        self.assertFalse(is_finished({
            "url": "d", "event_start": "2026-01-01"}))  # incomplete

    def test_unfinished_limit_skips_finished(self):
        pages = [
            {"url": "done", "event_start": "2026-01-01", "event_end": "2026-01-02"},
            {"url": "hub", "event_date_status": "hub"},
            {"url": "todo1", "sections": []},
            {"url": "todo2", "sections": []},
            {"url": "todo3", "sections": []},
        ]
        work = unfinished_pages(pages, limit=2)
        self.assertEqual([p["url"] for p in work], ["todo1", "todo2"])

    def test_deleting_fields_requeues(self):
        page = {
            "url": "x",
            "event_start": "2026-03-01",
            "event_end": "2026-03-02",
            "event_date_status": "conflict",
        }
        self.assertTrue(is_finished(page))
        page.pop("event_start")
        page.pop("event_end")
        page.pop("event_date_status")
        self.assertFalse(is_finished(page))
        self.assertEqual(unfinished_pages([page]), [page])


class StatusOnTerminalTests(unittest.TestCase):
    def test_single_source_sets_status(self):
        page = {
            "url": "https://example.org/a",
            "title": "A",
            "sections": [{"heading": "", "text": "Date: March 10, 2022"}],
        }
        out, review, missing = enrich_pages(
            [page],
            html_fetcher=lambda url: None,
            llm_extractor=lambda p: {"pair": None, "hub": False, "raw": None},
        )
        self.assertEqual(out[0].get("event_date_status"), "single_source")
        self.assertNotIn("event_start", out[0])
        self.assertEqual(len(review), 1)
        self.assertTrue(is_finished(out[0]))

    def test_agree_clears_status(self):
        pair = ("2025-03-09", "2025-03-15")
        page = {
            "url": "https://example.org/tour/",
            "title": "Tour",
            "event_date_status": "missing",
            "sections": [{"heading": "", "text": "Date: March 9 to 15, 2025"}],
        }
        out, _, _ = enrich_pages(
            [page],
            html_fetcher=lambda url: pair,
            llm_extractor=lambda p: {"pair": pair, "hub": False, "raw": {}},
        )
        self.assertEqual(out[0]["event_start"], "2025-03-09")
        self.assertNotIn("event_date_status", out[0])


class QuotaFailoverTests(unittest.TestCase):
    def setUp(self):
        reset_exhausted_models()

    def tearDown(self):
        reset_exhausted_models()

    def test_is_quota_error_detects_429_text(self):
        self.assertTrue(is_quota_error(RuntimeError("Insufficient quota")))
        self.assertTrue(is_quota_error(RuntimeError("AllocationQuota exceeded")))
        self.assertFalse(is_quota_error(RuntimeError("connection reset")))
        self.assertFalse(is_quota_error(RuntimeError(
            "Exceeded limit on max bytes per data-uri item : 20971520")))

    def test_failover_to_next_model(self):
        models = ["model-a", "model-b"]
        client = MagicMock()

        def create(**kwargs):
            if kwargs["model"] == "model-a":
                raise RuntimeError("429 insufficient quota")
            resp = MagicMock()
            resp.choices = [MagicMock()]
            resp.choices[0].message.content = '{"ok":true}'
            return resp

        client.chat.completions.create.side_effect = create
        with patch("build.qwen_chat._qwen_client", return_value=client):
            text = chat_date(
                [{"role": "user", "content": "hi"}], models=models)
        self.assertEqual(text, '{"ok":true}')
        self.assertEqual(client.chat.completions.create.call_count, 2)

    def test_all_models_exhausted(self):
        models = ["model-a", "model-b"]
        client = MagicMock()
        client.chat.completions.create.side_effect = RuntimeError(
            "insufficient quota")
        with patch("build.qwen_chat._qwen_client", return_value=client):
            with self.assertRaises(DateModelsExhausted):
                chat_date([{"role": "user", "content": "hi"}], models=models)

    def test_extract_llm_propagates_exhausted(self):
        page = {"url": "u", "title": "t", "sections": []}
        with patch("build.enrich_dates.chat_date",
                   side_effect=DateModelsExhausted("done")):
            with self.assertRaises(DateModelsExhausted):
                enrich_one_page(
                    page,
                    html_fetcher=lambda url: None,
                    llm_extractor=None,  # use real extract_llm_dates
                )


if __name__ == "__main__":
    unittest.main()
