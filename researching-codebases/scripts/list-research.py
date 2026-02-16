#!/usr/bin/env python3
"""
List past research documents with metadata.

Usage:
    list-research.py [--limit N] [--location project|global|both]

Output:
    List of research documents with metadata (date, query, tags, path)
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from datetime import datetime


def parse_frontmatter(content: str) -> dict | None:
    """Parse YAML frontmatter from markdown content."""
    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return None

    yaml_text = match.group(1)
    result = {}

    for line in yaml_text.split("\n"):
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()

        # Handle quoted strings
        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            value = value[1:-1]

        # Handle arrays [a, b, c]
        if value.startswith("[") and value.endswith("]"):
            items = value[1:-1].split(",")
            result[key] = [item.strip().strip("\"'") for item in items if item.strip()]
        else:
            result[key] = value if value else None

    return result


def extract_title(content: str) -> str:
    """Extract title from content as fallback."""
    in_frontmatter = False
    for line in content.split("\n"):
        if line == "---":
            in_frontmatter = not in_frontmatter
            continue
        if in_frontmatter:
            continue
        if line.startswith("# "):
            return line[2:].strip()
        if line.strip():
            return line.strip()[:80]
    return "(untitled)"


def get_research_files(directory: Path, label: str) -> list[dict]:
    """Get research files with metadata from a directory."""
    results = []

    if not directory.exists():
        return results

    for file_path in directory.glob("*.md"):
        try:
            content = file_path.read_text()
            stat = file_path.stat()
            fm = parse_frontmatter(content)

            results.append(
                {
                    "filename": file_path.name,
                    "path": str(file_path),
                    "date": fm.get("date") if fm else stat.st_mtime,
                    "query": fm.get("query") if fm else extract_title(content),
                    "repository": fm.get("repository") if fm else None,
                    "branch": fm.get("branch") if fm else None,
                    "commit": fm.get("commit") if fm else None,
                    "cwd": fm.get("cwd") if fm else None,
                    "tags": fm.get("tags", []) if fm else [],
                    "label": label,
                }
            )
        except Exception:
            continue

    return results


def main():
    parser = argparse.ArgumentParser(description="List past research documents")
    parser.add_argument(
        "--limit", type=int, default=10, help="Maximum results (default: 10)"
    )
    parser.add_argument(
        "--location",
        choices=["project", "global", "both"],
        default="both",
        help="Which directory to search (default: both)",
    )
    args = parser.parse_args()

    project_research = Path.cwd() / ".research"
    global_research = Path.home() / ".research"

    files = []

    if args.location in ("project", "both"):
        files.extend(get_research_files(project_research, "project"))

    if args.location in ("global", "both"):
        files.extend(get_research_files(global_research, "global"))

    if not files:
        print("No research documents found.")
        return

    # Sort by date descending
    def sort_key(f):
        d = f.get("date", "")
        return d if isinstance(d, str) else ""

    files.sort(key=sort_key, reverse=True)
    files = files[: args.limit]

    # Output
    for f in files:
        tags = f", tags: {', '.join(f['tags'])}" if f["tags"] else ""
        repo = (
            f"\n  repo: {f['repository']}"
            if f["repository"] and f["repository"] != "null"
            else ""
        )
        branch = (
            f" | branch: {f['branch']}" if f["branch"] and f["branch"] != "null" else ""
        )
        commit = (
            f" | commit: {f['commit']}" if f["commit"] and f["commit"] != "null" else ""
        )

        print(f"{f['filename']} ({f['label']})")
        print(f"  query: {f['query']}")
        print(f"  date: {f['date']}{branch}{commit}{repo}{tags}")
        print(f"  path: {f['path']}")
        print()


if __name__ == "__main__":
    main()
