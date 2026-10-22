#!/usr/bin/env python3
"""Check local Markdown links without touching Webots or external networks."""
from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
LINK = re.compile(r'!?\[[^\]]*\]\(([^)]+)\)')
FENCE = re.compile(r'^\s*(`{3,}|~{3,})')


def broken_links(root: Path) -> list[str]:
    """Return file:line: missing local target; ignore code fences and remote URLs."""
    root = root.resolve()
    errors: list[str] = []
    for source in sorted(root.rglob("*.md")):
        if any(part in {".git", ".venv", "node_modules"} for part in source.relative_to(root).parts):
            continue
        fenced: str | None = None
        for number, line in enumerate(source.read_text(encoding="utf-8").splitlines(), 1):
            found = FENCE.match(line)
            if found:
                marker = found.group(1)
                if fenced is None:
                    fenced = marker[0]
                elif marker[0] == fenced:
                    fenced = None
                continue
            if fenced:
                continue
            for match in LINK.finditer(line):
                value = match.group(1).strip()
                if value.startswith("<") and ">" in value:
                    value = value[1:value.find(">")]
                else:
                    value = value.split(maxsplit=1)[0] if value else ""
                if not value or value.startswith("#"):
                    continue
                parsed = urlsplit(value)
                if parsed.scheme or parsed.netloc:
                    continue
                name = unquote(parsed.path)
                if not name:
                    continue
                if name.startswith("/"):
                    errors.append(f"{source.relative_to(root)}:{number}: disallowed absolute link {value}")
                    continue
                target = (source.parent / name).resolve()
                try:
                    target.relative_to(root)
                except ValueError:
                    errors.append(f"{source.relative_to(root)}:{number}: link escapes repo {value}")
                    continue
                if not target.exists():
                    errors.append(f"{source.relative_to(root)}:{number}: missing {value}")
    return errors


def main() -> int:
    errors = broken_links(ROOT)
    if errors:
        print("Markdown link validation FAIL")
        print("\n".join(errors))
        return 1
    print("Markdown link validation PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
