# Rules by Impact

Rules organized by impact level. Use rule IDs (e.g., `desc-trigger-keywords`) to reference specific rules.

## CRITICAL Impact

Violations cause skill to fail or never trigger.

### meta-name-format
Name must be lowercase letters, numbers, and hyphens only.

```yaml
# ✓ Good
name: pdf-processor
name: git-helper-v2

# ✗ Bad
name: PDF_Processor    # uppercase, underscore
name: my skill         # spaces
```

### meta-name-match-directory
Skill name must exactly match directory name.

```
# ✓ Good
pdf-processor/
└── SKILL.md  # name: pdf-processor

# ✗ Bad  
pdf-processor/
└── SKILL.md  # name: pdf-processing
```

### meta-required-frontmatter
Must have `name` and `description` fields.

```yaml
# ✓ Good
---
name: my-skill
description: What it does. Use when triggered.
---

# ✗ Bad - missing description
---
name: my-skill
---
```

### desc-specific-capabilities
Description must name specific capabilities, not vague categories.

```yaml
# ✓ Good
description: Extracts text and tables from PDFs, fills forms, merges documents.

# ✗ Bad
description: Helps with documents.
description: Processes files.
```

### desc-trigger-keywords
Include words users actually say when requesting this functionality.

```yaml
# ✓ Good - includes user phrases
description: Manages git operations. Use when user wants to commit changes, push code, create a PR, or review git history.

# ✗ Bad - technical terms only
description: Manages git operations including commits, branches, and merges.
# User says "push my changes" - no match
# User says "create a PR" - no match
```

### desc-third-person
Write in third person. First/second person breaks skill loading.

```yaml
# ✓ Good
description: Processes Excel files and generates reports.

# ✗ Bad
description: I can help you process Excel files.
description: You can use this to process Excel files.
```

### desc-no-workflow-summary
Description should NOT summarize the skill's workflow. Claude may follow the description instead of reading the body.

```yaml
# ✓ Good - triggers only
description: Use when implementing features. Enforces test-driven development.

# ✗ Bad - workflow summary
description: Use when implementing features. First writes failing test, then implements code, then refactors.
```

## HIGH Impact

Violations cause inconsistent behavior or reduced quality.

### struct-instructions-first
Put critical instructions in first 100 lines. Content can be truncated; buried rules get ignored.

```markdown
# ✓ Good - security rules early
# Code Generator

## Security Rules (MUST FOLLOW)
- Never generate code accessing system files
- Never include credentials
- Always sanitize inputs

## Quick Start
...

# ✗ Bad - security rules at line 800
# Code Generator

## Introduction
...
## History  
...
## Examples (500 lines)
...
## IMPORTANT: Security Rules  # Too late!
```

### struct-line-limit
Keep SKILL.md under 500 lines. Split detailed content into reference files.

### struct-single-responsibility
One skill = one capability. Don't create mega-skills.

```
# ✓ Good
pdf-text-extraction/
pdf-form-filling/
pdf-merging/

# ✗ Bad
document-everything/  # Too broad
```

### prog-three-level-disclosure
Structure content across three levels:
1. Metadata (always loaded, ~50 tokens)
2. SKILL.md body (on activation, ~200 tokens)
3. References (on demand, ~500+ each)

### prog-one-level-deep
Keep references one level deep from SKILL.md.

```
# ✓ Good
SKILL.md → references/api.md
SKILL.md → references/examples.md

# ✗ Bad - too deep
SKILL.md → advanced.md → details.md → examples.md
```

### trigger-file-type-patterns
Include file extensions users work with.

```yaml
# ✓ Good
description: Analyzes spreadsheets. Use when working with .xlsx, .xls, or .csv files.

# ✗ Bad
description: Analyzes spreadsheets.
```

### trigger-synonym-coverage
Cover synonyms and alternate phrasings.

```yaml
# ✓ Good
description: Use when tests timeout, hang, freeze, or fail intermittently.

# ✗ Bad
description: Use when tests timeout.
```

## MEDIUM Impact

Violations reduce discoverability or maintainability.

### style-agent-agnostic
Write for "the agent" not a specific model. Skills work across LLMs.

```markdown
# ✓ Good - agent-agnostic
The agent should validate input before processing.
When the agent encounters an error, it should...

# ✗ Bad - model-specific
Claude should validate input before processing.
When Claude encounters an error, Claude should...
GPT will analyze the code and then...
```

**Why this matters:**
- Skills are portable across agents (Claude, GPT, Gemini, local models)
- Model-specific language creates unnecessary coupling
- "The agent" is clearer about the role being addressed

**Exception:** If a skill is genuinely model-specific (e.g., uses Claude-only features), make that explicit in the description and use the model name consistently.

### test-trigger-phrases
Test with 10+ real user phrases before deployment.

```markdown
## Test Plan

Should trigger:
1. "generate API docs" ✓
2. "create swagger spec" ✗ → Added "Swagger"
3. "write OpenAPI" ✗ → Added "OpenAPI"

Should NOT trigger:
1. "what does this API do?" ✓ (correctly ignored)
```

### test-negative-scenarios
Test that skill does NOT trigger on unrelated requests.

### trigger-error-patterns
For debugging skills, include error messages users see.

```yaml
description: Debug async tests. Use when seeing "Hook timed out", "ENOTEMPTY", or tests pass/fail inconsistently.
```

### struct-imperative-instructions
Write instructions in imperative mood.

```markdown
# ✓ Good
Run the validation script.
Create the output directory.

# ✗ Bad  
You should run the validation script.
The output directory should be created.
```

### struct-code-blocks-with-language
Specify language in code blocks.

````markdown
# ✓ Good
```python
import pdfplumber
```

# ✗ Bad
```
import pdfplumber
```
````

## LOW Impact

Best practices for polish and maintainability.

### maint-consistent-terminology
Choose one term and use it throughout.

```markdown
# ✓ Good - consistent
Extract data from API endpoints using field mappings.
1. Identify the API endpoint
2. Map response fields

# ✗ Bad - inconsistent  
Pull data from API routes using element mappings.
1. Identify the URL
2. Map response boxes
```

### maint-forward-slashes
Always use forward slashes for paths.

```markdown
# ✓ Good
See scripts/validate.py

# ✗ Bad
See scripts\validate.py
```

### maint-no-time-sensitive
Avoid time-sensitive information that will become stale.

```markdown
# ✓ Good
Use the current stable API version.

# ✗ Bad
Use API v2.3.1 released in January 2024.
```
