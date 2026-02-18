# Debugging Skills

When a skill isn't working, diagnose systematically.

## First: Run Validation

Before debugging manually, run the validation script:

```bash
./scripts/validate.sh path/to/your-skill
```

This catches common structural issues:
- Invalid YAML syntax
- Missing required fields
- Name/directory mismatch
- Description problems

If validation passes but the skill still doesn't work, continue below.

## Skill Won't Trigger

The agent doesn't load your skill when it should.

### Check the Description

**Problem:** Description is missing the words users say.

```yaml
# User says: "help me extract text from this PDF"
# But description says:
description: Document processing capabilities.  # ❌ No matching keywords
```

**Fix:** Add the actual trigger words:
```yaml
description: Use when extracting text from PDF files, filling PDF forms, or merging documents.
```

### Check the Name

**Problem:** Skill name doesn't match directory name.

```
skills/
  pdf-processor/          # Directory
    SKILL.md              # But name field says "pdf-processing" ❌
```

**Fix:** Make them identical:
```yaml
name: pdf-processor  # Must match directory exactly
```

### Check YAML Syntax

**Problem:** Invalid YAML breaks parsing.

```yaml
---
name: my-skill
description: Does things.
  More description here.  # ❌ Unexpected indentation
---
```

**Fix:** Keep description on one line or use proper YAML multiline:
```yaml
---
name: my-skill
description: >
  Does things. More description here.
  Even more if needed.
---
```

### Check for Conflicts

**Problem:** Another skill has overlapping trigger keywords.

If two skills both match "PDF," the agent may pick the wrong one or get confused.

**Fix:** Make descriptions more specific and distinct:
```yaml
# Skill 1
description: Use when extracting text from PDFs or analyzing PDF structure.

# Skill 2  
description: Use when filling PDF forms or adding signatures to PDFs.
```

## Skill Triggers But Agent Ignores Instructions

The skill loads, but the agent doesn't follow the body.

### Check Instruction Placement

**Problem:** Critical instructions are buried too deep.

Agents may truncate long content. If your must-follow rules are on line 400, they might not be seen.

**Fix:** Put critical instructions in the first 100 lines.

### Check Instruction Clarity

**Problem:** Instructions are ambiguous or conditional without clear guidance.

```markdown
## Instructions

You might want to consider possibly using the extraction method,
unless there's a reason not to, in which case try something else.
```

**Fix:** Be direct and imperative:
```markdown
## Instructions

1. Extract text using pdfplumber
2. If extraction fails, fall back to OCR with pytesseract
3. Return extracted text as markdown
```

### Check for Competing Context

**Problem:** System prompt or conversation history contradicts your skill.

If CLAUDE.md says "always use PyPDF2" but your skill says "use pdfplumber," the agent may follow CLAUDE.md.

**Fix:** Align skill instructions with project conventions, or make the skill's approach explicit:
```markdown
**Note:** This skill uses pdfplumber regardless of project defaults because [reason].
```

## Skill Loads Too Much Context

The agent reads reference files it doesn't need.

### Check Progressive Disclosure

**Problem:** Everything is in SKILL.md instead of split into references.

**Fix:** Move detailed content to separate files:
```markdown
# In SKILL.md
For API details, see [api-reference.md](references/api-reference.md).

# Only loaded when agent needs API details
```

### Check Reference Depth

**Problem:** References link to other references, creating a chain.

```markdown
# references/api.md links to:
See [advanced-api.md](advanced-api.md) for more.

# advanced-api.md links to:
See [edge-cases.md](edge-cases.md) for more.
```

The agent may load all of them or none of them.

**Fix:** Keep references one level deep from SKILL.md:
```markdown
# SKILL.md links directly to everything needed:
- [api.md](references/api.md)
- [advanced-api.md](references/advanced-api.md)
- [edge-cases.md](references/edge-cases.md)
```

## Agent Follows Description Instead of Body

The agent does what the description says, not what the body says.

### The Workflow-in-Description Trap

**Problem:** Description summarizes the workflow, so the agent uses that as a shortcut.

```yaml
description: Processes PDFs by extracting text, then analyzing structure, then generating a summary.
```

The agent may do exactly this three-step process even if the body has a different, more nuanced workflow.

**Fix:** Description should only say *when* to use, not *how* it works:
```yaml
description: Use when processing PDF files — handles text extraction, structure analysis, and summarization.
```

## Quick Diagnostic Checklist

Run through this when any skill isn't working:

| Check | Command/Action |
|-------|----------------|
| Name matches directory? | Compare `name:` field to folder name |
| YAML valid? | Look for indentation errors, missing `---` |
| Description has trigger words? | Compare to actual user phrases |
| Description avoids workflow summary? | Look for "then," "first," "next" |
| Critical instructions early? | Check line numbers of must-follow rules |
| References one level deep? | Grep for links in reference files |
| Conflicts with other skills? | Search other descriptions for same keywords |
