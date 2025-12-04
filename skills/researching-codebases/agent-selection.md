# Agent Selection

## Available Agents

| Agent | Purpose | Use When | Cost |
|-------|---------|----------|------|
| `code-analyzer` | Understand HOW code works | Need implementation details, data flow, tracing | Thorough, expensive |
| `code-locator` | Find WHERE files live | Need file paths, directory structure | Fast, cheap |
| `code-pattern-finder` | Find similar implementations | Need examples to model after, with code snippets | Medium |
| `web-searcher` | External documentation | User explicitly asks, or need library/API docs | Medium |

## Selection Guide

**Start with `code-locator`** to find relevant files, then:

- Need to understand logic? → `code-analyzer`
- Need examples to copy? → `code-pattern-finder`
- Need external context? → `web-searcher` (only if user asks or library docs needed)

## Parallel vs Sequential

**Parallel** (no dependencies):
- Locating files in different areas
- Searching for different concepts
- Web research alongside code research

**Sequential** (has dependencies):
- Locate files THEN analyze them
- Find patterns THEN understand their usage

## Agent Prompt Tips

Be specific about what to return. Agents know their jobs - tell them WHAT to find, not HOW to search.

Examples:
- "Find all files related to authentication"
- "Analyze how the payment flow works in `src/payments/`, trace from entry point to database"
- "Find examples of pagination patterns with full code snippets"
- "Search for React Router authentication patterns in official docs"
