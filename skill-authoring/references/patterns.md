# Skill Patterns

## Template Pattern

Provide output templates when consistent format matters.

### Strict Template

Use when format must be exact:

```markdown
## Report Structure

ALWAYS use this exact structure:

# [Analysis Title]

## Executive Summary
[One-paragraph overview]

## Key Findings
- Finding 1 with data
- Finding 2 with data

## Recommendations
1. Specific action
2. Specific action
```

### Flexible Template

Use when adaptation is appropriate:

```markdown
## Report Structure

Sensible default, adapt as needed:

# [Analysis Title]

## Executive Summary
[Overview - length varies by complexity]

## Findings
[Adapt sections to what you discover]

## Recommendations  
[Tailor to context]
```

## Examples Pattern

Show input/output pairs when quality depends on demonstration:

```markdown
## Commit Message Format

**Example 1:**
Input: Added user authentication with JWT tokens
Output:
```
feat(auth): implement JWT-based authentication

Add login endpoint and token validation middleware
```

**Example 2:**
Input: Fixed date display bug in reports  
Output:
```
fix(reports): correct date formatting in timezone conversion

Use UTC timestamps consistently across report generation
```

Follow: type(scope): summary, then detailed explanation.
```

**When to use examples:**
- Format has nuances text can't capture
- Pattern recognition easier than rule following
- Edge cases need demonstration

## Sequential Workflow Pattern

For multi-step processes:

```markdown
## PDF Form Filling

1. **Analyze form** - `python scripts/analyze.py input.pdf`
2. **Create mapping** - Edit `fields.json` with values
3. **Validate** - `python scripts/validate.py fields.json`
4. **Fill form** - `python scripts/fill.py input.pdf fields.json output.pdf`
5. **Verify** - `python scripts/verify.py output.pdf`
```

## Conditional Workflow Pattern

For branching logic:

```markdown
## Document Processing

**Creating new content?** → Follow "Creation Workflow" below
**Editing existing?** → Follow "Editing Workflow" below

### Creation Workflow
1. Determine structure
2. Generate content
3. Format and save

### Editing Workflow
1. Load existing document
2. Identify changes
3. Apply modifications
4. Preserve formatting
```

## Checklist Pattern

For complex multi-step tasks:

```markdown
## Migration Checklist

Copy and track progress:

- [ ] Step 1: Backup database
- [ ] Step 2: Run migration script
- [ ] Step 3: Validate output
- [ ] Step 4: Update configuration
- [ ] Step 5: Verify in staging

### Step 1: Backup Database

Run: `./scripts/backup.sh`

Expected output: `backup-YYYY-MM-DD.sql` created

### Step 2: Run Migration
...
```

## Default + Escape Hatch Pattern

Provide one default, one alternative:

```markdown
## Text Extraction

Use pdfplumber for text extraction:

```python
import pdfplumber
with pdfplumber.open("file.pdf") as pdf:
    text = pdf.pages[0].extract_text()
```

**For scanned PDFs requiring OCR**, use pdf2image + pytesseract instead.
```

**Don't** list 5 alternatives and say "choose based on needs" — causes decision paralysis.

## Router Pattern

For complex skills with multiple workflows:

```markdown
---
name: project-management
description: Manages project tasks, planning, and reviews. Use when planning features, tracking progress, or reviewing work.
---

# Project Management

## Core Principles

[Principles that ALWAYS apply, inline here]

## What Would You Like To Do?

1. **Plan a feature** - Break down requirements
2. **Track progress** - Update task status  
3. **Review work** - Code review checklist

## Routing

| Choice | Workflow |
|--------|----------|
| 1, "plan", "feature" | [workflows/planning.md](workflows/planning.md) |
| 2, "track", "progress" | [workflows/tracking.md](workflows/tracking.md) |
| 3, "review" | [workflows/review.md](workflows/review.md) |

## Reference Index

- [references/templates.md](references/templates.md) - Document templates
- [references/standards.md](references/standards.md) - Quality standards
```

### Router Directory Structure

```
project-management/
├── SKILL.md                    # Router + core principles
├── workflows/
│   ├── planning.md
│   ├── tracking.md
│   └── review.md
└── references/
    ├── templates.md
    └── standards.md
```

### Workflow File Structure

```markdown
# Workflow: Feature Planning

## Required Reading

Load these first:
- [references/templates.md](../references/templates.md)

## Process

1. Gather requirements
2. Break into tasks
3. Estimate effort
4. Create timeline

## Success Criteria

- [ ] Requirements documented
- [ ] Tasks created with estimates
- [ ] Timeline approved
```

## Validation Pattern

For skills with validation steps:

```markdown
## Validation

After changes, validate immediately:

```bash
python scripts/validate.py output/
```

**Fix errors before continuing.** Common errors:

| Error | Meaning | Fix |
|-------|---------|-----|
| Field not found | Wrong field name | Check available fields in schema |
| Type mismatch | Wrong data type | Convert to expected type |
| Missing required | Required field empty | Provide value |

Only proceed when validation passes with zero errors.
```

## Degrees of Freedom

Match specificity to task fragility:

| Freedom | Format | When |
|---------|--------|------|
| **High** | Text instructions | Multiple valid approaches |
| **Medium** | Pseudocode with params | Preferred pattern, some variation OK |
| **Low** | Exact scripts | Fragile operations, consistency critical |

**High freedom example:**
```markdown
Create a summary that captures the key points and recommendations.
```

**Low freedom example:**
```markdown
Run exactly: `python scripts/process.py --input data.json --output result.json --validate`
```
