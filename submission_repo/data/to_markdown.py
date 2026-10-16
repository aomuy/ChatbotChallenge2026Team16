"""Convert descriptions.json into a readable markdown file."""
import json
from pathlib import Path

SRC = Path(__file__).with_name("descriptions.json")
OUT = Path(__file__).with_name("descriptions.md")


def _format_entry(desc) -> str:
    """Render a cache value (legacy string or structured dict/JSON)."""
    if isinstance(desc, dict):
        payload = desc
    elif isinstance(desc, str):
        text = desc.strip()
        if text.startswith("{"):
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError:
                parsed = None
            if isinstance(parsed, dict) and "description" in parsed:
                payload = parsed
            else:
                return text
        else:
            return text
    else:
        return str(desc)

    image_type = payload.get("image_type", "")
    body = (payload.get("description") or "").strip()
    type_line = f"**image_type:** `{image_type}`" if image_type else "**image_type:**"
    return f"{type_line}\n\n{body}"


def main() -> None:
    data = json.loads(SRC.read_text())
    parts = ["# Image descriptions\n"]
    for i, (url, desc) in enumerate(data.items(), start=1):
        parts.append(f"## {i}. {url}\n")
        parts.append(_format_entry(desc) + "\n")
    OUT.write_text("\n".join(parts))
    print(f"Wrote {len(data)} descriptions to {OUT}")


if __name__ == "__main__":
    main()
