"""Qwen / DashScope chat client for date enrichment (ingestion only).

Uses QWEN_AVAILABLE_DATE_MODELS left-to-right. On quota/token exhaustion for
the current model, advances to the next. When every model is exhausted,
raises DateModelsExhausted.
"""
from __future__ import annotations

import os
import re
from typing import Iterable

from openai import OpenAI, RateLimitError

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

QWEN_BASE_URL = os.getenv(
    "QWEN_BASE_URL",
    "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
)
_QWEN_KEY = os.environ.get("QWEN_API_KEY", "").strip()

_QUOTA_HINTS = re.compile(
    r"insufficient|quota|rate.?limit|allocation.?quota|token|billing|"
    r"exceed|exhausted|balance|credit|429",
    re.IGNORECASE,
)
# Payload-size errors contain "exceed" but are not quota; do not burn models.
_NOT_QUOTA = re.compile(
    r"data-?uri|max bytes per data|max_bytes|payload.?too.?large",
    re.IGNORECASE,
)

_client: OpenAI | None = None
# Models already known to be out of quota this process; skip on later pages.
_exhausted_models: set[str] = set()


class DateModelsExhausted(RuntimeError):
    """All configured date models have run out of tokens/quota."""


def date_models() -> list[str]:
    """Parse QWEN_AVAILABLE_DATE_MODELS (comma-separated, optional quotes)."""
    raw = os.getenv("QWEN_AVAILABLE_DATE_MODELS", "").strip().strip("'\"")
    if not raw:
        # Sensible single default if env unset.
        return ["qwen-plus"]
    return [part.strip().strip("'\"") for part in raw.split(",") if part.strip()]


def _qwen_client() -> OpenAI:
    global _client
    if _client is None:
        if not _QWEN_KEY:
            raise RuntimeError(
                "QWEN_API_KEY is not set. Add it to .env (see .env.example) "
                "before running build/enrich_dates.py."
            )
        _client = OpenAI(api_key=_QWEN_KEY, base_url=QWEN_BASE_URL)
    return _client


def is_quota_error(exc: BaseException) -> bool:
    """True when the error means this model has no remaining quota/tokens."""
    if isinstance(exc, RateLimitError):
        return True
    status = getattr(exc, "status_code", None)
    if status == 429:
        return True
    text = str(exc)
    code = ""
    body = getattr(exc, "body", None)
    if isinstance(body, dict):
        err = body.get("error") or body
        if isinstance(err, dict):
            code = str(err.get("code") or err.get("type") or "")
            text = f"{text} {err.get('message', '')} {code}"
    if _NOT_QUOTA.search(text) or _NOT_QUOTA.search(code):
        return False
    return bool(_QUOTA_HINTS.search(text) or _QUOTA_HINTS.search(code))


def reset_exhausted_models() -> None:
    """Clear process-local exhausted set (for tests)."""
    _exhausted_models.clear()


def mark_exhausted(models: Iterable[str]) -> None:
    _exhausted_models.update(models)


def chat_date(messages: list[dict], max_tokens: int = 256,
              models: list[str] | None = None) -> str:
    """Chat completion trying date models left to right.

    Skips models already marked exhausted in this process. On quota errors,
    marks the model exhausted and tries the next. Raises DateModelsExhausted
    when none remain. Other API errors are re-raised after one retry on the
    same model fails.
    """
    ordered = models if models is not None else date_models()
    remaining = [m for m in ordered if m not in _exhausted_models]
    if not remaining:
        raise DateModelsExhausted(
            f"All date models exhausted: {', '.join(ordered) or '(none configured)'}"
        )

    last_exc: BaseException | None = None
    for model in remaining:
        for attempt in range(2):
            try:
                r = _qwen_client().chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=0.0,
                )
                return r.choices[0].message.content or ""
            except Exception as exc:
                last_exc = exc
                if is_quota_error(exc):
                    _exhausted_models.add(model)
                    print(f"date model exhausted, falling back: {model} ({exc})")
                    break  # next model
                if attempt == 0:
                    continue  # one retry for transient non-quota errors
                raise
    raise DateModelsExhausted(
        f"All date models exhausted: {', '.join(ordered)}"
    ) from last_exc
