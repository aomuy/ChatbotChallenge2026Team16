"""Convert/compress images and oversized-original logging."""
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from build.images import (
    MAX_DATA_URI_BYTES,
    data_uri_nbytes,
    prepare_vision_image,
)
from build.qwen_chat import is_quota_error


def _png_bytes(width: int, height: int, color=(0, 128, 255)) -> bytes:
    img = Image.new("RGB", (width, height), color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _bmp_bytes(width: int = 32, height: int = 24) -> bytes:
    img = Image.new("RGB", (width, height), (10, 20, 30))
    buf = io.BytesIO()
    img.save(buf, format="BMP")
    return buf.getvalue()


class DataUriSizeTests(unittest.TestCase):
    def test_data_uri_nbytes_grows_with_payload(self):
        small = data_uri_nbytes(b"abc", "image/jpeg")
        large = data_uri_nbytes(b"abc" * 1000, "image/jpeg")
        self.assertGreater(large, small)
        self.assertGreater(small, len(b"abc"))


class PrepareVisionImageTests(unittest.TestCase):
    def test_converts_bmp_to_jpeg(self):
        raw = _bmp_bytes()
        out = prepare_vision_image(raw, src="https://example.org/x.bmp")
        self.assertIsNotNone(out)
        payload, ext = out
        self.assertEqual(ext, ".jpg")
        self.assertEqual(payload[:3], b"\xff\xd8\xff")
        self.assertLess(data_uri_nbytes(payload, "image/jpeg"), MAX_DATA_URI_BYTES)

    def test_skips_svg(self):
        self.assertIsNone(
            prepare_vision_image(
                b"<svg xmlns='http://www.w3.org/2000/svg'/>",
                src="https://example.org/a.svg",
            )
        )

    def test_compresses_large_png_under_limit(self):
        raw = _png_bytes(4000, 3000)
        out = prepare_vision_image(raw, src="https://example.org/big.png")
        self.assertIsNotNone(out)
        payload, _ = out
        self.assertLess(data_uri_nbytes(payload, "image/jpeg"), MAX_DATA_URI_BYTES)

    def test_logs_when_original_exceeds_limit(self):
        raw = _png_bytes(64, 64)
        real_nbytes = data_uri_nbytes

        def selective(payload, mime):
            # Pretend the original PNG data-URI is over the API cap.
            if mime == "image/png" and payload == raw:
                return MAX_DATA_URI_BYTES + 9000
            return real_nbytes(payload, mime)

        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "image_oversized.jsonl"
            with patch("build.images.OVERSIZED_LOG_PATH", log_path), \
                 patch("build.images.data_uri_nbytes", side_effect=selective):
                out = prepare_vision_image(
                    raw, src="https://example.org/huge.png")

            self.assertIsNotNone(out)
            lines = log_path.read_text().strip().splitlines()
            self.assertEqual(len(lines), 1)
            record = json.loads(lines[0])
            self.assertEqual(record["src"], "https://example.org/huge.png")
            self.assertGreaterEqual(
                record["estimated_data_uri_bytes"], MAX_DATA_URI_BYTES)


class QuotaErrorClassificationTests(unittest.TestCase):
    def test_data_uri_limit_is_not_quota(self):
        msg = (
            "Error code: 400 - {'error': {'message': "
            "'Exceeded limit on max bytes per data-uri item : 20971520'}}"
        )
        self.assertFalse(is_quota_error(RuntimeError(msg)))

    def test_still_detects_quota(self):
        self.assertTrue(is_quota_error(RuntimeError("Insufficient quota")))
        self.assertTrue(is_quota_error(RuntimeError("AllocationQuota exceeded")))


if __name__ == "__main__":
    unittest.main()
