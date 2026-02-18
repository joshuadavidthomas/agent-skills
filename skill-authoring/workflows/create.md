# Creating a New Skill

Step-by-step workflow for building a skill from scratch.

## Quick Start with Scripts

Scaffold a new skill instantly:

```bash
python scripts/init.py my-skill-name
python scripts/init.py my-skill-name --path ~/.claude/skills  # custom location
python scripts/init.py my-skill-name --router                  # router pattern
```

This creates the directory structure with a template SKILL.md. Then customize from there.

To validate your skill before deployment:

```bash
./scripts/validate.sh path/to/my-skill
```

---

## Manual Approach

If you prefer to build from scratch, or want to understand what the scripts do:

## Before You Start

Answer these questions:

1. **What problem does this skill solve?** Be specific. "Helps with documents" is too vague. "Extracts text from PDFs and fills form fields" is concrete.

2. **What would a user say to trigger this?** Write down 5-10 actual phrases. These become your description keywords.

3. **Does this already exist?** Check if another skill covers this. Overlapping skills create activation conflicts.

4. **Is this reusable?** If it's a one-off solution or project-specific convention, put it in CLAUDE.md instead.

## Step 1: Scaffold the Structure

```bash
mkdir -p skills/your-skill-name
```

Create SKILL.md with minimal frontmatter:

```yaml
---
name: your-skill-name
description: [Leave blank for now]
---

# Your Skill Name

[Body content will go here]
```

The name must:
- Use lowercase letters, numbers, and hyphens only
- Match the directory name exactly
- Be under 64 characters

## Step 2: Write the Description

This is the most important step. The description determines whether your skill ever gets used.

**Start with trigger phrases.** Look at the phrases you wrote down in "Before You Start." Turn them into a description:

```yaml
# If users say: "help me with PDFs", "extract text from this PDF", 
# "fill out this form", "merge these PDFs"

description: Use when working with PDF files — extracts text, fills forms, merges documents. Handles .pdf files.
```

**Formula:** `Use when [triggering conditions] — [capabilities]. [File types/contexts].`

**Check yourself:**
- [ ] Starts with "Use when" or similar trigger language
- [ ] Contains words users actually say
- [ ] Does NOT summarize the workflow step-by-step
- [ ] Written in third person (no "I" or "you")
- [ ] Under 1024 characters

## Step 3: Write the Body

Follow the Orient → Instruct → Show → Warn pattern:

```markdown
# Your Skill Name

Brief orientation: what this is and what problem it solves.

## Instructions

1. First step in imperative mood
2. Second step with clear expected outcome
3. Third step

## Example

**Input:** [Concrete example of what user provides]

**Process:** [What the agent does]

**Output:** [What the result looks like]

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| [Thing that goes wrong] | [How to avoid or recover] |
```

**Keep it lean.** Only add context the agent doesn't already have. Target <500 lines.

## Step 4: Add Supporting Files (If Needed)

Only create these if your skill needs them:

**references/** — Detailed documentation loaded on demand
```markdown
For API details, see [api-reference.md](references/api-reference.md).
```

**scripts/** — Code that gets executed, not read
```markdown
Run the extraction script:
\`\`\`bash
python scripts/extract.py input.pdf
\`\`\`
```

**assets/** — Templates, images for output (not loaded into context)

## Step 5: Test Activation

Before testing behavior, test that the skill actually triggers.

Try these prompts and verify the skill activates:
- Each trigger phrase you wrote down
- Synonyms and variations
- Edge cases (partial matches, typos)

**If the skill doesn't trigger:**
- Add more keywords to the description
- Check that name matches directory
- Verify YAML syntax is valid

## Step 6: Test Behavior

Now test that the skill works correctly:

1. Run through the main use case end-to-end
2. Try edge cases and error conditions
3. Verify output matches expectations
4. Check that instructions are clear (would a fresh agent understand?)

## Step 7: Iterate

Real usage reveals problems. After deploying:

1. Notice where the agent struggles
2. Add missing instructions or examples
3. Clarify ambiguous guidance
4. Update description if activation is unreliable

## Step 8: Validate

Run the validation script to catch common issues:

```bash
./scripts/validate.sh path/to/your-skill
```

This checks:
- YAML frontmatter syntax
- Required fields present
- Name matches directory
- Description length and format
- File structure

## Checklist

Before considering the skill complete:

- [ ] `./scripts/validate.sh` passes with no errors
- [ ] Name is lowercase, hyphens only, matches directory
- [ ] Description has trigger keywords users actually say
- [ ] Description does NOT summarize workflow
- [ ] Body follows Orient → Instruct → Show → Warn
- [ ] SKILL.md is under 500 lines
- [ ] References are one level deep (no nested links)
- [ ] Tested activation with 5+ trigger phrases
- [ ] Tested behavior with real use cases
- [ ] Examples are concrete, not abstract templates
