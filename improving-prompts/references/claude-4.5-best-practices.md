# Claude 4.5 Prompting Best Practices

Source: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-4-best-practices

## General Principles

### Be Explicit with Instructions
Claude 4.x models respond well to clear, explicit instructions. Being specific about your desired output enhances results. If you want "above and beyond" behavior from previous Claude models, explicitly request it.

**Less effective:** "Create an analytics dashboard"

**More effective:** "Create an analytics dashboard. Include as many relevant features and interactions as possible. Go beyond the basics to create a fully-featured implementation."

### Add Context to Improve Performance
Providing context or motivation behind instructions helps Claude 4.x models better understand goals. Explain WHY a behavior is important.

**Less effective:** "NEVER use ellipses"

**More effective:** "Your response will be read aloud by a text-to-speech engine, so never use ellipses since the text-to-speech engine will not know how to pronounce them."

Claude generalizes from explanations.

### Be Vigilant with Examples & Details
Claude 4.x models pay close attention to examples as part of precise instruction following. Ensure examples align with desired behaviors and minimize behaviors you want to avoid.

## Communication Style

Claude 4.5 models have more concise, natural communication:
- More direct and grounded (fact-based, not self-celebratory)
- More conversational (fluent, less machine-like)
- Less verbose (may skip summaries for efficiency unless prompted)

## Tool Usage Patterns

Claude 4.5 models follow instructions precisely. Be explicit about whether to act or advise:

**"Can you suggest some changes"** → Claude will only suggest
**"Make these changes"** → Claude will implement

To make Claude proactive by default, add to system prompt:
```
By default, implement changes rather than only suggesting them. If the user's intent is unclear, infer the most useful likely action and proceed.
```

To make Claude conservative by default:
```
Do not jump into implementation unless clearly instructed. When ambiguous, default to providing information and recommendations rather than taking action.
```

## Controlling Output Format

1. **Tell Claude what to do instead of what not to do**
   - Instead of: "Do not use markdown"
   - Try: "Your response should be composed of smoothly flowing prose paragraphs."

2. **Use XML format indicators**
   - Try: "Write the prose sections in <smoothly_flowing_prose_paragraphs> tags."

3. **Match prompt style to desired output**
   - Removing markdown from your prompt can reduce markdown in output

4. **Explicit formatting guidance** to minimize markdown:
```
When writing reports or long-form content, write in clear, flowing prose using complete paragraphs and sentences. Reserve markdown primarily for `inline code` and code blocks. Avoid using **bold** and *italics*. DO NOT use ordered or unordered lists unless presenting truly discrete items or user explicitly requests a list.
```

## Verbosity Control

Claude 4.5 models tend toward efficiency and may skip verbal summaries after tool calls. If you want updates:

```
After completing a task that involves tool use, provide a quick summary of the work you've done.
```

## Thinking Sensitivity

When extended thinking is disabled, Claude Opus 4.5 is sensitive to the word "think" and variants. Replace with:
- "consider"
- "believe"
- "evaluate"
- "assess"
- "determine"

## Parallel Tool Calling

Claude 4.x models excel at parallel tool execution. To maximize:
```
If you intend to call multiple tools and there are no dependencies between the calls, make all independent calls in parallel. Prioritize calling tools simultaneously whenever the actions can be done in parallel.
```

To reduce parallel execution:
```
Execute operations sequentially with brief pauses between each step to ensure stability.
```

## Avoiding Overengineering

Claude 4.x models can sometimes overengineer. To prevent:
```
Avoid over-engineering. Only make changes that are directly requested or clearly necessary. Keep solutions simple and focused.

Don't add features, refactor code, or make "improvements" beyond what was asked. A bug fix doesn't need surrounding code cleaned up.

Don't add error handling for scenarios that can't happen. Trust internal code and framework guarantees.

Don't create helpers or abstractions for one-time operations. Don't design for hypothetical future requirements.
```

## Code Exploration

If Claude proposes solutions without reading code:
```
ALWAYS read and understand relevant files before proposing code edits. Do not speculate about code you have not inspected. Be rigorous and persistent in searching code for key facts.
```

## Minimizing Hallucinations

```
Never speculate about code you have not opened. If the user references a specific file, you MUST read the file before answering. Make sure to investigate and read relevant files BEFORE answering questions about the codebase.
```

## Avoiding Hard-Coding in Tests

```
Write a high-quality, general-purpose solution using standard tools. Do not hard-code values or create solutions that only work for specific test inputs. Implement the actual logic that solves the problem generally.

If the task is unreasonable or infeasible, inform me rather than working around it.
```

## Migration Considerations

When migrating to Claude 4.5:
1. Be specific about desired behavior
2. Add modifiers like "Go beyond the basics" or "Include as many relevant features as possible"
3. Request animations and interactive elements explicitly when desired
