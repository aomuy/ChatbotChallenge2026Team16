"""Qwen Cloud vision client for ingestion only.

Used by build/images.py. Answers and embeddings stay on Azure in bot/llm.py.
"""
import base64
import mimetypes
import os
from pathlib import Path

from openai import OpenAI

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

QWEN_BASE_URL = os.getenv(
    "QWEN_BASE_URL",
    "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
)
QWEN_VISION_MODEL = os.getenv("QWEN_VISION_MODEL", "qwen-vl-plus")
_QWEN_KEY = os.environ.get("QWEN_API_KEY", "").strip()

_client: OpenAI | None = None


def _qwen_client() -> OpenAI:
    global _client
    if _client is None:
        if not _QWEN_KEY:
            raise RuntimeError(
                "QWEN_API_KEY is not set. Add it to .env (see .env.example) "
                "before running build/images.py."
            )
        _client = OpenAI(api_key=_QWEN_KEY, base_url=QWEN_BASE_URL)
    return _client


def describe_image(image_path: str, prompt: str) -> str:
    """Send one image plus an instruction to the Qwen vision model."""
    path = Path(image_path)
    mime = mimetypes.guess_type(path.name)[0] or "image/jpeg"
    b64 = base64.b64encode(path.read_bytes()).decode()
    r = _qwen_client().chat.completions.create(
        model=QWEN_VISION_MODEL,
        max_completion_tokens=9000,
        messages=[{"role": "user", "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
        ]}],
    )
    return r.choices[0].message.content or ""
