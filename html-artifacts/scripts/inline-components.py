#!/usr/bin/env python3
"""Inline the HTML Artifacts component stylesheet into a standalone HTML file."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

STYLE_ID = "html-artifacts-components"
STYLE_PATTERN = re.compile(
    rf'(?P<open><style\s+id=["\']{STYLE_ID}["\']\s*>).*?(?P<close></style>)',
    re.DOTALL,
)


def inline_components(artifact_path: Path, output_path: Path | None = None) -> Path:
    skill_root = Path(__file__).resolve().parent.parent
    stylesheet_path = skill_root / "assets" / "artifact-components.css"

    html = artifact_path.read_text(encoding="utf-8")
    stylesheet = stylesheet_path.read_text(encoding="utf-8").rstrip()

    def replacement(match: re.Match[str]) -> str:
        return f'{match.group("open")}\n{stylesheet}\n  {match.group("close")}'

    bundled, count = STYLE_PATTERN.subn(replacement, html)
    if count != 1:
        raise ValueError(
            f'{artifact_path} must contain exactly one <style id="{STYLE_ID}">…</style>; found {count}'
        )

    destination = output_path or artifact_path
    destination.write_text(bundled, encoding="utf-8")
    return destination


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Inline assets/artifact-components.css into a standalone HTML artifact."
    )
    parser.add_argument("artifact", type=Path, help="HTML file containing the component style tag")
    parser.add_argument("--output", type=Path, help="Write to another file instead of updating in place")
    args = parser.parse_args()

    destination = inline_components(args.artifact, args.output)
    print(destination)


if __name__ == "__main__":
    main()
