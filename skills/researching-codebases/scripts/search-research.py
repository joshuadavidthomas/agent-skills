#!/usr/bin/env python3
"""
Search past research documents for a topic.

Usage:
    search-research.py <query> [--tags tag1,tag2] [--limit N]

Output:
    Matching research documents with relevance scores and snippets
"""

import argparse
import re
import sys
from pathlib import Path


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

        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            value = value[1:-1]

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


def search_content(content: str, query: str) -> list[str]:
    """Search file content for query matches. Returns up to 3 matching lines."""
    matches = []
    pattern = re.compile(re.escape(query), re.IGNORECASE)

    for idx, line in enumerate(content.split("\n"), 1):
        if pattern.search(line):
            matches.append(f"L{idx}: {line.strip()[:100]}")
            if len(matches) >= 3:
                break

    return matches


def get_research_files(directory: Path, label: str) -> list[dict]:
    """Get research files with metadata from a directory."""
    results = []

    if not directory.exists():
        return results

    for file_path in directory.glob("*.md"):
        try:
            content = file_path.read_text()
            fm = parse_frontmatter(content)

            results.append(
                {
                    "filename": file_path.name,
                    "path": str(file_path),
                    "content": content,
                    "date": fm.get("date") if fm else None,
                    "query": fm.get("query") if fm else extract_title(content),
                    "tags": fm.get("tags", []) if fm else [],
                    "label": label,
                }
            )
        except Exception:
            continue

    return results


def main():
    parser = argparse.ArgumentParser(description="Search past research documents")
    parser.add_argument("query", help="Search term or topic to find")
    parser.add_argument("--tags", help="Filter by tags (comma-separated)")
    parser.add_argument(
        "--limit", type=int, default=5, help="Maximum results (default: 5)"
    )
    args = parser.parse_args()

    project_research = Path.cwd() / ".research"
    global_research = Path.home() / ".research"

    files = []
    files.extend(get_research_files(project_research, "project"))
    files.extend(get_research_files(global_research, "global"))

    if not files:
        print(f"No research documents found.")
        return

    # Filter by tags if specified
    filter_tags = [t.strip().lower() for t in args.tags.split(",")] if args.tags else []
    if filter_tags:
        files = [
            f
            for f in files
            if any(
                any(ft.lower() in tag.lower() for tag in f["tags"])
                for ft in filter_tags
            )
        ]

    # Score and filter by query match
    search_query = args.query.lower()
    scored = []

    for f in files:
        score = 0
        matches = []

        # Check query/title match
        if search_query in f["query"].lower():
            score += 10
            matches.append(f'query: "{f["query"]}"')

        # Check tag match
        matching_tags = [t for t in f["tags"] if search_query in t.lower()]
        if matching_tags:
            score += 5 * len(matching_tags)
            matches.append(f"tags: {', '.join(matching_tags)}")

        # Check content match
        content_matches = search_content(f["content"], args.query)
        if content_matches:
            score += len(content_matches)
            matches.extend(content_matches)

        if score > 0:
            scored.append(
                {
                    "file": f,
                    "score": score,
                    "matches": matches,
                }
            )

    # Sort by score, limit
    scored.sort(key=lambda x: x["score"], reverse=True)
    scored = scored[: args.limit]

    if not scored:
        print(f'No research documents found matching "{args.query}".')
        return

    # Output
    for r in scored:
        f = r["file"]
        match_snippets = "\n    ".join(r["matches"][:4])

        print(f"{f['filename']} ({f['label']}) [score: {r['score']}]")
        print(f"  query: {f['query']}")
        print(f"  date: {f['date']}")
        print(f"  path: {f['path']}")
        print(f"  matches:")
        print(f"    {match_snippets}")
        print()


if __name__ == "__main__":
    main()
