"""Unit tests for hardcoded RAG retrieval_where routing."""
import unittest

from bot.retrieval_filter import retrieval_where


class RetrievalWhereTests(unittest.TestCase):
    def test_banned_materials_routes_to_text(self):
        self.assertEqual(
            retrieval_where(
                "Which two materials are banned from the laser cutter?"),
            {"kind": "text"},
        )

    def test_visible_in_photo_routes_to_image_photo(self):
        self.assertEqual(
            retrieval_where("How many tables are visible in the photo?"),
            {"$and": [{"kind": "image"}, {"image_type": "photo"}]},
        )

    def test_poster_routes_to_image_poster(self):
        self.assertEqual(
            retrieval_where("What does the poster say?"),
            {"$and": [{"kind": "image"}, {"image_type": "poster"}]},
        )

    def test_interest_groups_routes_to_text(self):
        self.assertEqual(
            retrieval_where("What student interest groups are there?"),
            {"kind": "text"},
        )

    def test_no_cue_returns_none(self):
        self.assertIsNone(retrieval_where("Who is the director?"))

    def test_image_cue_wins_over_text_cue(self):
        self.assertEqual(
            retrieval_where(
                "Are banned materials visible in the photo?"),
            {"$and": [{"kind": "image"}, {"image_type": "photo"}]},
        )

    def test_multiple_image_types_use_in(self):
        self.assertEqual(
            retrieval_where("Show me posters and diagrams of the lab"),
            {"$and": [
                {"kind": "image"},
                {"image_type": {"$in": ["poster", "diagram"]}},
            ]},
        )

    def test_generic_image_cue_without_type(self):
        self.assertEqual(
            retrieval_where("What is shown in the image?"),
            {"kind": "image"},
        )


if __name__ == "__main__":
    unittest.main()
