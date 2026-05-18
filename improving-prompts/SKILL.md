---
name: improving-prompts
description: Use when optimizing CLAUDE.md, AGENTS.md, custom commands, or skill files — diagnose the concrete failure first, then apply current documented Anthropic best practices (explicit instructions, context/motivation, examples, output and verbosity control, thinking/effort, CLAUDE.md size and skill-description rules) instead of inventing improvements. Triggers when a prompt isn't followed, a skill won't activate, CLAUDE.md is too long or ignored, or migrating prompts to current Claude models.
---

# Improving Prompts

## Overview

Apply current documented Anthropic best practices to existing prompts. Do not invent "improvements" — use the actual guidance.

## When to Use

- Optimizing CLAUDE.md or AGENTS.md files
- Improving custom command prompts
- Refining skill instructions
- Migrating prompts to current Claude models (4.x)

## When NOT to Use

- Writing new prompts from scratch (just follow best practices directly)
- The prompt is working well and the user hasn't identified issues

## The Core Problem

Without this skill, agents:
- Invent "best practices" from general knowledge
- Make structural changes without asking what's broken
- Add complexity assuming more structure = better
- Change things to demonstrate value rather than solve problems

## Stop If You Catch Yourself

These are the failure modes. If you think any of these, stop and get a concrete issue first.

| Thought | Reality |
|---------|---------|
| "It's too vague / not best-practice / inconsistent" | Not actionable. Which specific behavior fails? |
| "I have enough context" / "I'll assume the user wants…" | If you can't name the specific failure, you don't. Ask. |
| "I'm the expert" / "This is how I'd write it" | Authority doesn't bypass a concrete issue. You're not the user. |
| "Based on general best practices…" | Use *documented* practices. Cite the guidance. |
| "Structure is always better" | Structure solves structure problems, not all problems. |
| "Time pressure — demo tomorrow" | Pressure is when the worst changes get made. |
| "This is obviously an improvement" | Obvious to you ≠ solving the user's actual problem. |
| Making 10+ changes to a short prompt | Stop. What specific problem are you solving? |

## Required Process

### Step 1: Understand Before Changing

Before ANY modifications:
1. Ask what specific behaviors are underperforming
2. Ask what the prompt should achieve that it currently doesn't
3. If the user says "just improve it generally" — ask for at least one concrete issue

**What counts as a "concrete issue":**
- "Claude ignores my instruction to be concise" ✓
- "Claude suggests changes but doesn't implement them" ✓

**What does NOT count:**
- "It's too vague" ✗ (vague about what?)
- "It doesn't follow best practices" ✗ (which practice? what fails?)

Do NOT proceed with generic "improvements" based on assumptions.

### Step 2: Reference Actual Best Practices

See `references/anthropic-best-practices.md` for the full reference. Key principles:

**Be explicit with instructions:** Current models follow instructions literally — vague requests get narrow, literal interpretations. If you want "above and beyond," request it explicitly.

**State scope explicitly:** Current models won't silently generalize an instruction you gave once. "Apply this to every section, not just the first."

**Add context/motivation:** Explain WHY a rule exists, not just WHAT. Claude generalizes from explanations. "NEVER use ellipses" → "Never use ellipses because the text-to-speech engine cannot pronounce them."

**Be vigilant with examples:** Examples are imitated precisely, including unintended patterns. Use 3–5, in `<example>` tags, aligned with the desired behavior.

**Thinking & effort:** Prefer general instructions ("think thoroughly"; "verify your answer against [criteria] before finishing") over hand-written step-by-step. The old "avoid the word *think* without extended thinking" rule no longer applies — current models use adaptive thinking + `effort`.

**Control verbosity explicitly:** Opus 4.7 scales length to perceived task complexity. If the workflow needs a fixed length or post-tool summaries, say so.

**Tool usage:** "Can you suggest changes" → suggestions only. "Make these changes" → edits. Be explicit about act vs. advise.

**Dial back aggressive triggering:** Prefer "Use X when it helps" over "CRITICAL: You MUST use X" — current models overtrigger and over-explore on aggressive language.

### Step 3: Preserve What Works

- Do NOT restructure sections that aren't problematic
- Do NOT add complexity unless solving a stated problem
- Do NOT change tone/voice unless specifically requested
- Keep the user's examples if they demonstrate the right behavior

### Step 4: Propose Changes with Rationale

For each change, state:
1. What specific best practice it applies
2. What problem it solves
3. Before/after

Do NOT make changes without connecting them to documented guidance.

## Quick Reference: Issue → Fix

| Issue | Fix |
|-------|-----|
| Output too narrow / not generalized | State scope explicitly ("every section", "all cases") |
| Claude doesn't explain reasoning | Ask it to explain its reasoning, or raise `effort` |
| Claude is too verbose | "Be concise" or "Respond in X sentences" |
| Claude is too terse | "Provide detailed explanations" |
| Claude suggests but doesn't act | Change "Can you…" to imperative "Do X" |
| Instruction isn't followed | Add context for WHY it matters |
| Examples not matching output | Ensure examples show the exact desired format |
| CLAUDE.md too long / ignored | Cut lines that wouldn't cause a mistake if removed (target <200) |
