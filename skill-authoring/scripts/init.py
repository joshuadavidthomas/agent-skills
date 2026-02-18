#!/usr/bin/env python3
"""
Initialize a new skill with template structure.

Usage:
    python init.py <skill-name> [--path <directory>] [--router]
    
Examples:
    python init.py pdf-processor
    python init.py pdf-processor --path ~/.claude/skills
    python init.py project-manager --router
"""

import sys
import argparse
from pathlib import Path


SIMPLE_TEMPLATE = '''---
name: {name}
description: [What it does]. Use when [trigger conditions].
---

# {title}

## Quick Start

[Immediate actionable example - what to do first]

## Instructions

1. [First step]
2. [Second step]
3. [Third step]

## Examples

**Example 1:**

Input: [description]

Output:
```
[result]
```

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| [Common error] | [How to fix] |
'''


ROUTER_TEMPLATE = '''---
name: {name}
description: [What it does]. Use when [trigger conditions].
---

# {title}

## Core Principles

[Principles that ALWAYS apply, regardless of workflow]

1. **[First principle]** - [Explanation]
2. **[Second principle]** - [Explanation]

## What Would You Like To Do?

1. **[First option]** - [Brief description]
2. **[Second option]** - [Brief description]
3. **[Third option]** - [Brief description]

## Routing

| Choice | Workflow |
|--------|----------|
| 1, "[keywords]" | [workflows/first.md](workflows/first.md) |
| 2, "[keywords]" | [workflows/second.md](workflows/second.md) |
| 3, "[keywords]" | [workflows/third.md](workflows/third.md) |

## References

| When | Load |
|------|------|
| [Condition] | [references/topic.md](references/topic.md) |
'''


WORKFLOW_TEMPLATE = '''# Workflow: {title}

## Process

1. **[First step]**
   
   [Instructions]

2. **[Second step]**
   
   [Instructions]

3. **[Third step]**
   
   [Instructions]

## Success Criteria

- [ ] [First criterion]
- [ ] [Second criterion]
- [ ] [Third criterion]
'''


REFERENCE_TEMPLATE = '''# {title}

## Overview

[What this reference covers]

## [Section 1]

[Content]

## [Section 2]

[Content]
'''


def title_case(name: str) -> str:
    """Convert hyphenated name to Title Case."""
    return ' '.join(word.capitalize() for word in name.split('-'))


def init_skill(name: str, path: Path, router: bool = False) -> Path:
    """
    Initialize a new skill directory.
    
    Returns:
        Path to created skill directory
    """
    skill_dir = path / name
    
    if skill_dir.exists():
        raise ValueError(f"Directory already exists: {skill_dir}")
    
    # Create directory structure
    skill_dir.mkdir(parents=True)
    
    if router:
        (skill_dir / "workflows").mkdir()
        (skill_dir / "references").mkdir()
    
    # Write SKILL.md
    template = ROUTER_TEMPLATE if router else SIMPLE_TEMPLATE
    content = template.format(name=name, title=title_case(name))
    (skill_dir / "SKILL.md").write_text(content)
    
    if router:
        # Write example workflow
        workflow_content = WORKFLOW_TEMPLATE.format(title="First Workflow")
        (skill_dir / "workflows" / "first.md").write_text(workflow_content)
        
        # Write example reference
        reference_content = REFERENCE_TEMPLATE.format(title="Topic Reference")
        (skill_dir / "references" / "topic.md").write_text(reference_content)
    
    return skill_dir


def main():
    parser = argparse.ArgumentParser(
        description="Initialize a new skill with template structure."
    )
    parser.add_argument(
        "name",
        help="Skill name (lowercase-with-hyphens)"
    )
    parser.add_argument(
        "--path",
        type=Path,
        default=Path.home() / ".claude" / "skills",
        help="Directory to create skill in (default: ~/.claude/skills)"
    )
    parser.add_argument(
        "--router",
        action="store_true",
        help="Create router skill with workflows/ and references/"
    )
    
    args = parser.parse_args()
    
    # Validate name
    import re
    if not re.match(r'^[a-z0-9-]+$', args.name):
        print(f"Error: name must be lowercase letters, numbers, and hyphens only")
        sys.exit(1)
    
    if args.name.startswith('-') or args.name.endswith('-') or '--' in args.name:
        print(f"Error: name cannot start/end with hyphen or contain consecutive hyphens")
        sys.exit(1)
    
    try:
        skill_dir = init_skill(args.name, args.path, args.router)
        
        print(f"✓ Created skill: {skill_dir}")
        print()
        print("Files created:")
        for f in sorted(skill_dir.rglob("*")):
            if f.is_file():
                rel = f.relative_to(skill_dir)
                print(f"  {rel}")
        print()
        print("Next steps:")
        print("  1. Edit SKILL.md - fill in description and instructions")
        print("  2. Run validate.py to check structure")
        print("  3. Test activation with real user phrases")
        
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
