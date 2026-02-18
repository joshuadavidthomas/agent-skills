#!/usr/bin/env bash
#
# Update source skills from upstream repositories.
#
# Downloads the latest version of each source skill and replaces
# the corresponding directory in sources/.
#
# Usage:
#   ./scripts/update-sources.sh           # Update all sources
#   ./scripts/update-sources.sh anthropic # Update specific source
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
SOURCES_DIR="$SKILL_DIR/sources"

# Format: name|repo_url|branch|path_within_repo
SOURCES=(
  "anthropic|https://github.com/anthropics/skills|main|skills/skill-creator"
  "everyinc|https://github.com/EveryInc/compound-engineering-plugin|main|plugins/compound-engineering/skills/create-agent-skills"
  "obra|https://github.com/obra/superpowers|main|skills/writing-skills"
  "pproenca|https://github.com/pproenca/dot-skills|master|skills/.curated/skill-authoring"
  "pytorch|https://github.com/pytorch/pytorch|main|.claude/skills/skill-writer"
)

# Spec docs from agentskills.io - fetched directly with Accept: text/markdown
SPEC_BASE_URL="https://agentskills.io"
SPEC_PAGES=(
  "what-are-skills"
  "specification"
  "integrate-skills"
)

# skills-ref library from GitHub
SKILLS_REF_REPO="https://github.com/agentskills/agentskills"
SKILLS_REF_BRANCH="main"
SKILLS_REF_PATH="skills-ref"

update_spec() {
  local spec_dir="$SKILL_DIR/spec"
  
  echo "Updating spec from agentskills.io..."
  
  # Clear and recreate spec directory (but preserve skills-ref for separate update)
  rm -rf "${spec_dir:?}"/*.md "${spec_dir:?}"/.source 2>/dev/null || true
  mkdir -p "$spec_dir"
  
  # Fetch each page with Accept: text/markdown
  for page in "${SPEC_PAGES[@]}"; do
    echo "  Fetching: $page"
    if curl -sfH "Accept: text/markdown" "$SPEC_BASE_URL/$page" > "$spec_dir/$page.md"; then
      echo "    OK"
    else
      echo "    WARNING: Failed to fetch $page"
    fi
  done
  
  # Fetch skills-ref library from GitHub
  echo "  Fetching: skills-ref library"
  local tmp_dir
  tmp_dir="$(mktemp -d)"
  local commit
  
  git clone --depth 1 --branch "$SKILLS_REF_BRANCH" --filter=blob:none --sparse "$SKILLS_REF_REPO" "$tmp_dir/repo" 2>/dev/null
  pushd "$tmp_dir/repo" > /dev/null
  git sparse-checkout set "$SKILLS_REF_PATH" 2>/dev/null
  commit="$(git rev-parse HEAD)"
  popd > /dev/null
  
  rm -rf "$spec_dir/skills-ref"
  cp -r "$tmp_dir/repo/$SKILLS_REF_PATH" "$spec_dir/skills-ref"
  rm -rf "$tmp_dir"
  echo "    OK (commit: ${commit:0:8})"
  
  # Record provenance
  cat > "$spec_dir/.source" << EOF
source: $SPEC_BASE_URL
skills-ref: $SKILLS_REF_REPO ($SKILLS_REF_BRANCH @ $commit)
updated: $(date -Iseconds)
pages:
$(printf '  - %s\n' "${SPEC_PAGES[@]}")
EOF
  
  echo "  Done."
}

update_source() {
  local name="$1"
  local repo="$2"
  local branch="$3"
  local path="$4"
  
  local tmp_dir
  tmp_dir="$(mktemp -d)"
  trap "rm -rf '$tmp_dir'" RETURN
  
  echo "Updating $name..."
  echo "  Repo: $repo"
  echo "  Branch: $branch"
  echo "  Path: $path"
  
  # Shallow clone with sparse checkout for efficiency
  git clone --depth 1 --branch "$branch" --filter=blob:none --sparse "$repo" "$tmp_dir/repo" 2>/dev/null
  
  pushd "$tmp_dir/repo" > /dev/null
  git sparse-checkout set "$path" 2>/dev/null
  popd > /dev/null
  
  # Verify the path exists
  if [[ ! -d "$tmp_dir/repo/$path" ]]; then
    echo "  ERROR: Path '$path' not found in repository"
    return 1
  fi
  
  # Replace the source directory
  rm -rf "${SOURCES_DIR:?}/$name"
  mkdir -p "$SOURCES_DIR"
  cp -r "$tmp_dir/repo/$path" "$SOURCES_DIR/$name"
  
  # Rename SKILL.md to SKILL.reference.md to prevent Pi from discovering it
  # (Pi recursively discovers all SKILL.md files as active skills)
  if [[ -f "$SOURCES_DIR/$name/SKILL.md" ]]; then
    mv "$SOURCES_DIR/$name/SKILL.md" "$SOURCES_DIR/$name/SKILL.reference.md"
    echo "  Renamed SKILL.md → SKILL.reference.md (prevents Pi discovery)"
  fi
  
  # Record provenance
  local commit
  commit="$(git -C "$tmp_dir/repo" rev-parse HEAD)"
  cat > "$SOURCES_DIR/$name/.source" << EOF
repo: $repo
branch: $branch
path: $path
commit: $commit
updated: $(date -Iseconds)
EOF
  
  echo "  Done. Commit: ${commit:0:8}"
}

main() {
  local filter="${1:-}"
  local updated=0
  
  # Update spec if no filter or filter is "spec"
  if [[ -z "$filter" || "$filter" == "spec" ]]; then
    update_spec
    ((updated++)) || true
    echo
  fi
  
  # Skip sources if only updating spec
  if [[ "$filter" == "spec" ]]; then
    echo "Updated $updated target(s)."
    return 0
  fi
  
  # Update sources
  for source in "${SOURCES[@]}"; do
    IFS='|' read -r name repo branch path <<< "$source"
    
    # Skip if filter specified and doesn't match
    if [[ -n "$filter" && "$name" != "$filter" ]]; then
      continue
    fi
    
    if update_source "$name" "$repo" "$branch" "$path"; then
      ((updated++)) || true
    fi
    echo
  done
  
  if [[ $updated -eq 0 ]]; then
    echo "Unknown target: $filter"
    echo "Available: spec, anthropic, everyinc, obra, pproenca, pytorch"
    exit 1
  fi
  
  echo "Updated $updated target(s)."
}

main "$@"
