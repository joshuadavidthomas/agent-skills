# Anthropic Prompting Best Practices

Distilled from Anthropic's current documentation. Covers the Claude 4.x line
(Opus 4.7/4.6, Sonnet 4.6, Haiku 4.5). Sections are evergreen unless marked
**[version-specific]**.

Sources:
- Prompting best practices — https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-4-best-practices
- Model migration guide — https://platform.claude.com/docs/en/about-claude/models/migration-guide
- Claude Code memory (CLAUDE.md) — https://code.claude.com/docs/en/memory
- Skills — https://code.claude.com/docs/en/skills

## General Principles

### Be explicit with instructions
Current models follow instructions literally; vague requests get literal,
narrow interpretations. Ask for the behavior you want, including "above and
beyond" if you want it.

**Less effective:** "Create an analytics dashboard"
**More effective:** "Create an analytics dashboard. Include as many relevant
features and interactions as possible. Go beyond the basics."

### Add context and motivation
Explaining WHY a rule exists helps Claude generalize correctly.

**Less effective:** "NEVER use ellipses"
**More effective:** "Your response will be read aloud by a text-to-speech
engine, so never use ellipses since it cannot pronounce them."

### Be vigilant with examples
Examples are one of the most reliable steers. Use 3–5, wrapped in `<example>`
tags, diverse enough to cover edge cases, and aligned with the desired behavior
(Claude imitates patterns in examples precisely, including unintended ones).

### Structure with XML tags
Use `<instructions>`, `<context>`, `<input>` and similar to reduce
misinterpretation; nest for hierarchical content.

### Give Claude a role
A single system-prompt sentence ("You are a coding assistant specializing in
Python") focuses behavior and tone.

### Long-context placement
Put longform documents near the top, above the query and instructions; ask
Claude to quote relevant parts before reasoning on them.

## Controlling Output

- **Say what to do, not what not to do.** "Compose your response in flowing
  prose paragraphs" beats "Do not use markdown."
- **XML format indicators.** "Write the prose in `<prose>` tags."
- **Match prompt style to output.** Less markdown in the prompt → less markdown
  in the output.
- **Control verbosity explicitly.** **[version-specific]** Opus 4.7 calibrates
  response length to perceived task complexity rather than a fixed default. If a
  workflow depends on a specific length or on post-tool summaries, state it
  explicitly.

Markdown-minimizing block:
```
When writing reports or long-form content, write in clear, flowing prose using
complete paragraphs. Reserve markdown for `inline code` and code blocks. Avoid
**bold**/*italics*. Do not use lists unless presenting truly discrete items or
the user asks for a list.
```

## Tool Use and Action

- **Be explicit about act vs. advise.** "Can you suggest changes" → suggestions
  only. "Make these changes" → edits.
- Default-to-action system snippet: "By default, implement changes rather than
  only suggesting them. If intent is unclear, infer the most useful likely
  action and proceed." Conservative variant: "Do not implement unless clearly
  instructed; when ambiguous, provide information and recommendations."
- **Parallel tool calling:** "If you intend to call multiple tools and there are
  no dependencies between the calls, make all independent calls in parallel."
- **[version-specific] Dial back aggressive triggering for 4.6+.** Replace
  "CRITICAL: You MUST use this tool when…" with "Use this tool when it would
  enhance your understanding." Aggressive/`CRITICAL` language now causes
  overtriggering and upfront over-exploration.

## Thinking and Effort **[version-specific]**

This replaces the old "avoid the word *think* when extended thinking is off"
guidance, which no longer applies.

- `thinking: {type: "enabled", budget_tokens: N}` is deprecated on Sonnet 4.6
  and a 400 error on Opus 4.7. Use `thinking: {type: "adaptive"}` with the
  `effort` parameter (`low`/`medium`/`high`/`xhigh`/`max`). Opus 4.7 recommends
  `xhigh` as the default for coding and agentic work.
- Prefer general instructions over prescriptive steps. "Think thoroughly" or
  "Before you finish, verify your answer against [criteria]" usually beats a
  hand-written step-by-step plan.
- If reasoning is shallow on a complex task at `low`/`medium`, raise effort
  rather than prompting around it.

## Behavioral Shifts to Prompt Around **[version-specific]**

Applies to Opus 4.7 / Sonnet 4.6 vs. the 4.5 era:

- **More literal.** It will not silently generalize an instruction or infer
  unstated requests. State scope: "Apply this to every section, not just the
  first."
- **Less warm, more direct tone.** Add explicit style guidance if a product
  depended on warmer phrasing.
- **Built-in progress updates.** Remove old "summarize every N tool calls"
  scaffolding — it now causes over-reporting.
- **API breaking changes.** Prefilling the last assistant turn is a 400 error
  on 4.6+ (use structured outputs or system-prompt instructions instead).
  Setting `temperature`/`top_p`/`top_k` is a 400 error on Opus 4.7 — control
  behavior via prompting.

## Reliability Snippets (evergreen)

Avoid over-engineering:
```
Only make changes directly requested or clearly necessary. Don't add features,
refactor, or "improve" beyond what was asked. Don't add error handling for
scenarios that can't happen. Don't create abstractions for one-time operations
or design for hypothetical future requirements.
```

Read before proposing / minimize hallucination:
```
Never speculate about code you have not opened. If the user references a
specific file, read it before answering. Investigate relevant files before
answering questions about the codebase.
```

No hard-coding in tests:
```
Write a general-purpose solution with standard tools. Do not hard-code values
or solutions that only pass specific test inputs. If the task is infeasible,
say so rather than working around it.
```

## CLAUDE.md and Skill Files

The skill's actual job is optimizing these — apply the documented rules.

**CLAUDE.md**
- Target **under 200 lines**. For each line ask: "Would removing this cause
  Claude to make a mistake?" If not, cut it. Bloated CLAUDE.md reduces
  adherence to the instructions that matter.
- Include: commands Claude can't guess, project-specific style that differs
  from defaults, testing instructions, repo etiquette, architecture decisions,
  environment quirks, gotchas.
- Exclude: anything Claude can learn by reading code, standard conventions it
  already knows, frequently-changing detail, long tutorials, file-by-file
  descriptions, self-evident advice.
- It is delivered as a user message, not the system prompt — no guaranteed
  compliance, especially for vague/conflicting instructions.
- Emphasis markers ("IMPORTANT", "YOU MUST") are documented to improve
  adherence; use sparingly so they keep their force.
- Claude Code reads `CLAUDE.md`, not `AGENTS.md`. To reuse an existing
  `AGENTS.md`, import it with `@AGENTS.md` and add Claude-specific notes below.

**Skill files**
- `SKILL.md` is the entrypoint; keep it under 500 lines.
- `description` decides auto-activation — include keywords users would
  naturally say. `description` + `when_to_use` are truncated at **1,536
  characters** combined; put the key use case first.
- Apply the same conciseness test as CLAUDE.md: invoked skill content stays in
  context every turn, so every line is a recurring token cost. State what to
  do, not how or why.
- Facts belong in CLAUDE.md; repeated procedures/checklists belong in a skill.
