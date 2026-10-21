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

    def test_makerspace_table_count_routes_to_image(self):
        self.assertEqual(
            retrieval_where("How many tables are in Makerspace A?"),
            {"kind": "image"},
        )

    def test_brainstorming_wall_routes_to_image(self):
        self.assertEqual(
            retrieval_where(
                "What three words are on the wall behind the brainstorming area?"),
            {"kind": "image"},
        )

    def test_chinese_wall_routes_to_image(self):
        self.assertEqual(
            retrieval_where("头脑风暴区后方墙上的三个词是什么？"),
            {"kind": "image"},
        )

    def test_chinese_laser_routes_to_text(self):
        self.assertEqual(
            retrieval_where("激光切割机禁止使用哪两种材料？"),
            {"kind": "text"},
        )

    def test_funding_deadline_routes_to_text(self):
        self.assertEqual(
            retrieval_where(
                "When was the deadline for the second round of the "
                "Funding Scheme in 2025-26?"
            ),
            {"kind": "text"},
        )


if __name__ == "__main__":
    unittest.main()
