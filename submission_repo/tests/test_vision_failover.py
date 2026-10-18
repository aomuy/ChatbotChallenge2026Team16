"""Vision model failover and description cache checkpoints."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from build.images import _save_cache, _structured_cache_value, describe_all
from build.qwen_describe import (
    VisionModelsExhausted,
    describe_image,
    reset_exhausted_vision_models,
    vision_models,
)


class VisionModelListTests(unittest.TestCase):
    def test_parses_available_list(self):
        with patch.dict("os.environ", {
            "QWEN_AVAILABLE_VISION_MODELS": "'m1,m2,m3'",
        }, clear=False):
            self.assertEqual(vision_models(), ["m1", "m2", "m3"])

    def test_falls_back_to_single_vision_model(self):
        # No multi-model list: use QWEN_VISION_MODEL from the environment.
        env = {
            k: v for k, v in os.environ.items()
            if k not in ("QWEN_AVAILABLE_VISION_MODELS", "QWEN_VISION_MODEL")
        }
        env["QWEN_VISION_MODEL"] = "qwen-vl-plus"
        with patch.dict("os.environ", env, clear=True):
            self.assertEqual(vision_models(), ["qwen-vl-plus"])


class VisionFailoverTests(unittest.TestCase):
    def setUp(self):
        reset_exhausted_vision_models()

    def tearDown(self):
        reset_exhausted_vision_models()

    def test_failover_to_next_model(self):
        models = ["vision-a", "vision-b"]
        client = MagicMock()

        def create(**kwargs):
            if kwargs["model"] == "vision-a":
                raise RuntimeError("429 insufficient quota")
            resp = MagicMock()
            resp.choices = [MagicMock()]
            resp.choices[0].message.content = (
                '{"description":"ok","image_type":"photo"}')
            return resp

        client.chat.completions.create.side_effect = create
        with tempfile.NamedTemporaryFile(suffix=".jpg") as tmp:
            tmp.write(b"\xff\xd8\xff\xd9")
            tmp.flush()
            with patch("build.qwen_describe._qwen_client", return_value=client):
                text = describe_image(tmp.name, "prompt", models=models)
        self.assertIn("ok", text)
        self.assertEqual(client.chat.completions.create.call_count, 2)

    def test_all_models_exhausted(self):
        models = ["vision-a", "vision-b"]
        client = MagicMock()
        client.chat.completions.create.side_effect = RuntimeError(
            "insufficient quota")
        with tempfile.NamedTemporaryFile(suffix=".jpg") as tmp:
            tmp.write(b"\xff\xd8\xff\xd9")
            tmp.flush()
            with patch("build.qwen_describe._qwen_client", return_value=client):
                with self.assertRaises(VisionModelsExhausted):
                    describe_image(tmp.name, "prompt", models=models)


class DescribeCheckpointTests(unittest.TestCase):
    def test_save_cache_writes_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "descriptions.json"
            with patch("build.images.CACHE_PATH", path):
                _save_cache({"https://example.org/a.png": '{"description":"x"}'})
            data = json.loads(path.read_text())
            self.assertIn("https://example.org/a.png", data)

    def test_describe_all_checkpoints_after_success(self):
        structured = json.dumps({
            "description": "A room with tables",
            "image_type": "photo",
        })
        images = [{"src": "https://example.org/a.jpg", "alt": "", "caption": ""}]
        saves: list[dict] = []

        def track_save(cache):
            saves.append(dict(cache))

        with tempfile.TemporaryDirectory() as tmp:
            cache_file = Path(tmp) / "descriptions.json"
            old = os.getcwd()
            try:
                os.chdir(tmp)
                Path("data").mkdir(exist_ok=True)
                with patch("build.images.CACHE_PATH", cache_file), \
                     patch("build.images._save_cache", side_effect=track_save), \
                     patch("build.images.requests.get") as get, \
                     patch("build.images.prepare_vision_image",
                           return_value=(b"\xff\xd8\xff\xd9", ".jpg")), \
                     patch("build.images.describe_image", return_value=structured):
                    get.return_value = MagicMock(content=b"\xff\xd8\xff\xd9")
                    result = describe_all(images, limit=1)
            finally:
                os.chdir(old)

        # One flush after the success, one at normal completion.
        self.assertEqual(len(saves), 2)
        self.assertIn("https://example.org/a.jpg", result)

    def test_vision_exhausted_saves_then_raises(self):
        images = [{"src": "https://example.org/a.jpg", "alt": "", "caption": ""}]
        saves: list[dict] = []

        def track_save(cache):
            saves.append(dict(cache))

        with tempfile.TemporaryDirectory() as tmp:
            cache_file = Path(tmp) / "descriptions.json"
            old = os.getcwd()
            try:
                os.chdir(tmp)
                Path("data").mkdir(exist_ok=True)
                with patch("build.images.CACHE_PATH", cache_file), \
                     patch("build.images._save_cache", side_effect=track_save), \
                     patch("build.images.requests.get") as get, \
                     patch("build.images.prepare_vision_image",
                           return_value=(b"\xff\xd8\xff\xd9", ".jpg")), \
                     patch("build.images.describe_image",
                           side_effect=VisionModelsExhausted("done")):
                    get.return_value = MagicMock(content=b"\xff\xd8\xff\xd9")
                    with self.assertRaises(VisionModelsExhausted):
                        describe_all(images, limit=1)
            finally:
                os.chdir(old)
            self.assertGreaterEqual(len(saves), 1)

    def test_structured_cache_helper(self):
        raw = json.dumps({"description": "hi", "image_type": "poster"})
        self.assertEqual(
            _structured_cache_value(raw),
            {"description": "hi", "image_type": "poster"},
        )


if __name__ == "__main__":
    unittest.main()
