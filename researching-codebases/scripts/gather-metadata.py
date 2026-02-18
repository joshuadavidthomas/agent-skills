#!/usr/bin/env python3
"""
Generate research document metadata.

Usage:
    run_skill_script with skill_name="researching-codebases", script_name="gather-metadata"

Output:
    Key-value pairs: date, filename_date, cwd, repository, branch, commit
"""

import subprocess
from datetime import datetime, timezone
import os


def run(cmd: list[str]) -> str:
    """Run command and return output, or empty string on failure."""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=True, timeout=5
        )
        return result.stdout.strip()
    except (
        subprocess.CalledProcessError,
        FileNotFoundError,
        subprocess.TimeoutExpired,
    ):
        return ""


def is_git_repo() -> bool:
    return run(["git", "rev-parse", "--is-inside-work-tree"]) == "true"


def main() -> None:
    now = datetime.now(timezone.utc).astimezone()

    print(f"date: {now.isoformat()}")
    print(f"filename_date: {now.strftime('%Y-%m-%d')}")
    print(f"cwd: {os.getcwd()}")

    if is_git_repo():
        repo = run(["git", "remote", "get-url", "origin"])
        branch = run(["git", "branch", "--show-current"]) or run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"]
        )
        commit = run(["git", "rev-parse", "--short", "HEAD"])
        print(f"repository: {repo or 'null'}")
        print(f"branch: {branch or 'null'}")
        print(f"commit: {commit or 'null'}")
    else:
        print("repository: null")
        print("branch: null")
        print("commit: null")


if __name__ == "__main__":
    main()
