#!/usr/bin/env python3
"""
Promote a local research document to global.

Usage:
    promote-research.py <filename> [--move]

Copies (or moves) a file from .research/ to ~/.research/
"""

import argparse
import shutil
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Promote local research to global")
    parser.add_argument("filename", help="Filename to promote (from .research/)")
    parser.add_argument("--move", action="store_true", help="Move instead of copy")
    args = parser.parse_args()

    local = Path.cwd() / ".research" / args.filename
    global_dir = Path.home() / ".research"
    global_path = global_dir / args.filename

    if not local.exists():
        print(f"Error: {local} not found", file=sys.stderr)
        sys.exit(1)

    if global_path.exists():
        print(f"Error: {global_path} already exists", file=sys.stderr)
        sys.exit(1)

    global_dir.mkdir(exist_ok=True)

    if args.move:
        shutil.move(local, global_path)
        print(f"Moved to {global_path}")
    else:
        shutil.copy2(local, global_path)
        print(f"Copied to {global_path}")


if __name__ == "__main__":
    main()
