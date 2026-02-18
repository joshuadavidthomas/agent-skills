# Skill Examples

Concrete good/bad examples showing what works and why.

## Good Skill: PDF Handler

```yaml
---
name: pdf-handler
description: Use when working with PDF files, extracting text from PDFs, filling PDF forms, or merging PDF documents. Use for .pdf file operations.
---
```

```markdown
# PDF Handler

## Quick Start
Extract text: `pdf-extract input.pdf > output.txt`

## Instructions
1. Identify the PDF operation needed
2. Run the appropriate script from `scripts/`
3. Return results to user

## Common Mistakes
- Scanned PDFs need OCR first → Run `scripts/ocr.py` before extraction
```

**Why it works:**
- Description has trigger words ("PDF", "extracting", "filling", "merging", ".pdf")
- Quick Start gives immediate value
- Instructions are imperative
- Common Mistakes prevent real failures

## Bad Skill: Document Helper

```yaml
---
name: document-helper  
description: Helps users work with their documents by analyzing the content, extracting key information, and providing summaries.
---
```

**Why it fails:**
- Description summarizes workflow (Claude follows this instead of reading body)
- No trigger keywords (what file types? what operations?)
- "Helps users" is vague — what specifically?

## Bad Skill: TDD Helper

```yaml
---
name: tdd-helper
description: Use for TDD — write test first, watch it fail, write minimal code, refactor
---
```

**Why it fails:**
- Description summarizes the workflow step-by-step
- Claude may follow description instead of reading the full skill body
- Should describe *when* to use, not *how* it works

**Fixed:**
```yaml
description: Use when implementing any feature or bugfix, before writing implementation code
```
