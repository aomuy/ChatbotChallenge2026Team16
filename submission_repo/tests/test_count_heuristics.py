"""Heuristics that do not need openai or chromadb."""
import unittest

from bot.count_heuristics import (
    canonical_image,
    infer_year,
    poster_year_from_records,
    printer_fleet_from_records,
    room_object_from_records,
)


class InferYearTests(unittest.TestCase):
    def test_metadata_int_and_url(self):
        self.assertEqual(infer_year({"year": 2025}), 2025)
        self.assertEqual(infer_year({
            "image": "https://x/wp-content/uploads/2024/08/p.png",
        }), 2024)
        self.assertIsNone(infer_year({"image": "https://x/logo.png"}))


class PosterYearCountTests(unittest.TestCase):
    def test_canonical_strips_wordpress_size_suffix(self):
        self.assertEqual(
            canonical_image(
                "https://innoacademy.engg.hku.hk/wp-content/uploads/"
                "2025/10/Nocodile-workshop-poster-768x1024.jpg"
            ),
            "https://innoacademy.engg.hku.hk/wp-content/uploads/"
            "2025/10/Nocodile-workshop-poster.jpg",
        )

    def test_counts_2025_posters_from_url_year(self):
        rows = [
            {"id": "a", "metadata": {
                "kind": "image", "image_type": "poster",
                "url": "https://innoacademy.engg.hku.hk/workshop/",
                "image": "https://innoacademy.engg.hku.hk/wp-content/"
                         "uploads/2025/01/a.png"}},
            {"id": "a2", "metadata": {
                "kind": "image", "image_type": "poster",
                "url": "https://innoacademy.engg.hku.hk/workshop/",
                "image": "https://innoacademy.engg.hku.hk/wp-content/"
                         "uploads/2025/01/a-1024x724.png"}},
            {"id": "b", "metadata": {
                "kind": "image", "image_type": "poster",
                "url": "https://innoacademy.engg.hku.hk/workshop/",
                "image": "https://innoacademy.engg.hku.hk/wp-content/"
                         "uploads/2024/01/b.png"}},
            {"id": "c", "metadata": {
                "kind": "image", "image_type": "photo",
                "url": "https://innoacademy.engg.hku.hk/workshop/",
                "image": "https://innoacademy.engg.hku.hk/wp-content/"
                         "uploads/2025/01/c.png"}},
            {"id": "offsite", "metadata": {
                "kind": "image", "image_type": "poster",
                "url": "https://innowings.engg.hku.hk/",
                "image": "https://innowings.engg.hku.hk/wp-content/"
                         "uploads/2025/01/other.png"}},
            {"id": "d", "metadata": {
                "kind": "image", "image_type": "poster",
                "url": "https://innoacademy.engg.hku.hk/workshop/",
                "image": "https://innoacademy.engg.hku.hk/wp-content/"
                         "uploads/2025/06/Poster-1.png"}},
        ]
        self.assertEqual(
            poster_year_from_records(
                "How many workshop posters are on the Innovation Academy "
                "websites for 2025?",
                rows,
            ),
            "2",
        )


class RoomObjectCountTests(unittest.TestCase):
    def test_max_table_count_in_makerspace_description(self):
        rows = [
            {"text": "Cafe: 2 tables", "metadata": {"kind": "image"}},
            {"text": "Makerspace A. 8 light-wood-topped high workbench tables "
                     "and eleven chairs.",
             "metadata": {"kind": "image"}},
        ]
        self.assertEqual(
            room_object_from_records("How many tables are in Makerspace A?", rows),
            "8",
        )

    def test_word_number_chairs(self):
        rows = [{"text": "Makerspace A has eleven chairs around the tables.",
                 "metadata": {"kind": "image"}}]
        self.assertEqual(
            room_object_from_records("How many chairs are in Makerspace A?", rows),
            "11",
        )


class PrinterFleetTests(unittest.TestCase):
    def test_sums_model_counts(self):
        rows = [{
            "text": "4 Prusa MK4, 2 Bambu X1C, 1 Formlabs Form 4",
            "metadata": {"kind": "text"},
        }]
        self.assertEqual(
            printer_fleet_from_records(
                "How many 3D printers does the Centre run in total?",
                rows,
            ),
            "7",
        )

    def test_counts_distinct_named_models_when_no_quantities(self):
        rows = [
            {"text": "Bambu Lab P1S", "metadata": {
                "kind": "image",
                "image": "https://innowings.engg.hku.hk/p1s.jpg"}},
            {"text": "Bambu Lab X1C", "metadata": {"kind": "text"}},
            {"text": "Bambu Lab H2D", "metadata": {"kind": "text"}},
            {"text": "Formlabs Form 4", "metadata": {"kind": "text"}},
        ]
        self.assertEqual(
            printer_fleet_from_records(
                "How many 3D printers does the Centre run in total?",
                rows,
            ),
            "4",
        )


if __name__ == "__main__":
    unittest.main()
