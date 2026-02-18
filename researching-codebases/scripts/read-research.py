#!/usr/bin/env python3
"""
Read the full content of a research document.

Usage:
    read-research.py <path>

Output:
    Full content of the research document with header
"""

import argparse
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Read a research document")
    parser.add_argument("path", help="Full path to the research document")
    args = parser.parse_args()

    file_path = Path(args.path)

    # Validate path is in a research directory
    project_research = Path.cwd() / ".research"
    global_research = Path.home() / ".research"

    is_project = str(file_path).startswith(str(project_research))
    is_global = str(file_path).startswith(str(global_research))

    if not is_project and not is_global:
        print(
            f"Error: Path must be in a research directory (.research/ or ~/.research/)",
            file=sys.stderr,
        )
        sys.exit(1)

    if not file_path.exists():
        print(f"Error: Research document not found at {file_path}", file=sys.stderr)
        sys.exit(1)

    try:
        content = file_path.read_text()
        location = "project" if is_project else "global"

        print(f"# {file_path.name} ({location})")
        print()
        print(content)
    except Exception as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
