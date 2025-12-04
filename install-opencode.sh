#!/usr/bin/env bash
set -euo pipefail

# Determine the directory where this script lives (repo root)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_SOURCE="$SCRIPT_DIR/skills"
OPENCODE_CONFIG="${XDG_CONFIG_HOME:-$HOME/.config}/opencode"
SKILLS_TARGET="$OPENCODE_CONFIG/skills"
AGENTS_TARGET="$OPENCODE_CONFIG/agent"

# Counters
skills_installed=0
skills_skipped=0
agents_installed=0
agents_skipped=0

# --- Skills ---

echo "Installing skills to $SKILLS_TARGET/"
echo ""

mkdir -p "$SKILLS_TARGET"

for skill_path in "$SKILLS_SOURCE"/*/; do
    [[ -d "$skill_path" ]] || continue

    skill_path="${skill_path%/}"
    skill_name="$(basename "$skill_path")"
    target_path="$SKILLS_TARGET/$skill_name"

    printf "  %s ... " "$skill_name"

    if [[ -e "$target_path" || -L "$target_path" ]]; then
        echo "skipped (already exists)"
        ((skills_skipped++)) || true
    else
        ln -s "$skill_path" "$target_path"
        echo "installed"
        ((skills_installed++)) || true
    fi
done

# --- Agents ---

echo ""
echo "Installing agents to $AGENTS_TARGET/"
echo ""

mkdir -p "$AGENTS_TARGET"

for agent_path in "$SKILLS_SOURCE"/*/agents/*.md; do
    [[ -f "$agent_path" ]] || continue

    agent_name="$(basename "$agent_path")"

    # Skip README files
    [[ "$agent_name" == "README.md" ]] && continue

    target_path="$AGENTS_TARGET/$agent_name"

    printf "  %s ... " "$agent_name"

    if [[ -e "$target_path" || -L "$target_path" ]]; then
        echo "skipped (already exists)"
        ((agents_skipped++)) || true
    else
        ln -s "$agent_path" "$target_path"
        echo "installed"
        ((agents_installed++)) || true
    fi
done

# --- Summary ---

echo ""
echo "Done: $skills_installed skills installed, $skills_skipped skipped"
echo "      $agents_installed agents installed, $agents_skipped skipped"
