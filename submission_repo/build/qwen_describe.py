"""Qwen Cloud vision client for ingestion only.

Used by build/images.py. Answers and embeddings stay on Azure in bot/llm.py.

Uses QWEN_AVAILABLE_VISION_MODELS left-to-right. On quota/token exhaustion
for the current model, advances to the next. When every model is exhausted,
raises VisionModelsExhausted.
"""
from __future__ import annotations

import base64
import mimetypes
import os
from pathlib import Path
from typing import Iterable

from openai import OpenAI

from build.qwen_chat import is_quota_error

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
_exhausted_models: set[str] = set()


class VisionModelsExhausted(RuntimeError):
    """All configured vision models have run out of tokens/quota."""


def vision_models() -> list[str]:
    """Parse QWEN_AVAILABLE_VISION_MODELS; fall back to QWEN_VISION_MODEL."""
    raw = os.getenv("QWEN_AVAILABLE_VISION_MODELS", "").strip().strip("'\"")
    if raw:
        return [part.strip().strip("'\"") for part in raw.split(",") if part.strip()]
    single = (
        os.getenv("QWEN_VISION_MODEL", QWEN_VISION_MODEL) or "qwen-vl-plus"
    ).strip().strip("'\"")
    return [single] if single else ["qwen-vl-plus"]


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


def reset_exhausted_vision_models() -> None:
    """Clear process-local exhausted set (for tests)."""
    _exhausted_models.clear()


def mark_exhausted_vision(models: Iterable[str]) -> None:
    _exhausted_models.update(models)


def describe_image(image_path: str, prompt: str,
                   models: list[str] | None = None) -> str:
    """Send one image plus an instruction, trying vision models left to right.

    Skips models already marked exhausted in this process. On quota errors,
    marks the model exhausted and tries the next. Raises VisionModelsExhausted
    when none remain. Other API errors get one retry on the same model, then
    re-raise.
    """
    path = Path(image_path)
    mime = mimetypes.guess_type(path.name)[0] or "image/jpeg"
    b64 = base64.b64encode(path.read_bytes()).decode()
    messages = [{"role": "user", "content": [
        {"type": "text", "text": prompt},
        {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
    ]}]

    ordered = models if models is not None else vision_models()
    remaining = [m for m in ordered if m not in _exhausted_models]
    if not remaining:
        raise VisionModelsExhausted(
            f"All vision models exhausted: {', '.join(ordered) or '(none configured)'}"
        )

    last_exc: BaseException | None = None
    for model in remaining:
        for attempt in range(2):
            try:
                r = _qwen_client().chat.completions.create(
                    model=model,
                    max_completion_tokens=9000,
                    messages=messages,
                )
                return r.choices[0].message.content or ""
            except Exception as exc:
                last_exc = exc
                if is_quota_error(exc):
                    _exhausted_models.add(model)
                    print(f"vision model exhausted, falling back: {model} ({exc})")
                    break  # next model
                if attempt == 0:
                    continue
                raise
    raise VisionModelsExhausted(
        f"All vision models exhausted: {', '.join(ordered)}"
    ) from last_exc
