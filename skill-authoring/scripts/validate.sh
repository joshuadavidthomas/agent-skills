#!/usr/bin/env bash
#
# Validate a skill using skills-ref.
#
# Usage:
#   ./scripts/validate.sh <skill_directory>
#
# Requires: uv (https://docs.astral.sh/uv/)
#
# This script uses uvx to run the official skills-ref validator
# from the vendored copy in spec/skills-ref/.
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
SKILLS_REF_DIR="$SKILL_DIR/spec/skills-ref"

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <skill_directory>"
  echo ""
  echo "Example:"
  echo "  $0 path/to/my-skill"
  exit 1
fi

# Resolve to absolute path
TARGET_SKILL="$(cd "$1" 2>/dev/null && pwd || echo "$1")"

# Check if uv is available
if ! command -v uv &> /dev/null; then
  echo "Error: uv is required but not installed."
  echo "Install it from: https://docs.astral.sh/uv/"
  exit 1
fi

# Check if skills-ref is vendored
if [[ ! -d "$SKILLS_REF_DIR" ]]; then
  echo "Error: skills-ref not found at $SKILLS_REF_DIR"
  echo "Run ./scripts/update-sources.sh spec to download it."
  exit 1
fi

# Run skills-ref validate using uv
exec uv run --directory "$SKILLS_REF_DIR" skills-ref validate "$TARGET_SKILL"
