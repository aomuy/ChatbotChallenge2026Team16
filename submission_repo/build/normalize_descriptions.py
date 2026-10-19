"""Normalize data/descriptions.json to a uniform object format.

The cache mixed two shapes:
  - {"description": "...", "image_type": "..."}   (dict — preferred)
  - "{\"description\": \"...\", \"image_type\": \"...\"}"  (JSON string)

index_descriptions already unwraps both via description_fields, so Chroma
indexing does not break. This script rewrites the file so every value is a
dict, matching what build.images now writes for new descriptions.

Usage:
    python -m build.normalize_descriptions
    python -m build.normalize_descriptions --dry-run
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from build.images import CACHE_PATH, description_fields


def normalize_entry(raw) -> dict | None:
    """Parse any cache value into {description, image_type}, or None if empty."""
    description, image_type = description_fields(raw)
    if not description.strip():
        return None
    return {"description": description, "image_type": image_type}


def normalize_cache(cache: dict) -> tuple[dict, dict]:
    """Return (normalized_cache, stats)."""
    out: dict = {}
    stats = {
        "total": len(cache),
        "already_dict": 0,
        "from_json_string": 0,
        "from_other": 0,
        "dropped_empty": 0,
    }
    for src, raw in cache.items():
        if isinstance(raw, dict):
            stats["already_dict"] += 1
        elif isinstance(raw, str):
            stats["from_json_string"] += 1
        else:
            stats["from_other"] += 1
        normalized = normalize_entry(raw)
        if normalized is None:
            stats["dropped_empty"] += 1
            continue
        out[src] = normalized
    return out, stats


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Normalize descriptions.json to dict values",
    )
    parser.add_argument(
        "--path",
        type=Path,
        default=CACHE_PATH,
        help=f"Cache file (default: {CACHE_PATH})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report counts without writing",
    )
    args = parser.parse_args()

    if not args.path.exists():
        raise SystemExit(f"missing cache: {args.path}")

    cache = json.loads(args.path.read_text(encoding="utf-8"))
    if not isinstance(cache, dict):
        raise SystemExit(f"expected a JSON object in {args.path}")

    normalized, stats = normalize_cache(cache)
    print(
        f"total={stats['total']} already_dict={stats['already_dict']} "
        f"from_json_string={stats['from_json_string']} "
        f"from_other={stats['from_other']} "
        f"dropped_empty={stats['dropped_empty']} "
        f"normalized={len(normalized)}"
    )
    if args.dry_run:
        print("dry-run: no write")
        return

    args.path.parent.mkdir(exist_ok=True)
    args.path.write_text(
        json.dumps(normalized, indent=1, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {len(normalized)} entries to {args.path}")


if __name__ == "__main__":
    main()
