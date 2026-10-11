"""Convert descriptions.json into a readable markdown file."""
import json
from pathlib import Path

SRC = Path(__file__).with_name("descriptions.json")
OUT = Path(__file__).with_name("descriptions.md")


def main() -> None:
    data = json.loads(SRC.read_text())
    parts = ["# Image descriptions\n"]
    for i, (url, desc) in enumerate(data.items(), start=1):
        parts.append(f"## {i}. {url}\n")
        parts.append(f"{desc.strip()}\n")
    OUT.write_text("\n".join(parts))
    print(f"Wrote {len(data)} descriptions to {OUT}")


if __name__ == "__main__":
    main()
