---
name: {{skill-name}}
description: {{What it does}}. Use when {{trigger conditions}}.
---

# {{Skill Name}}

## Core Principles

{{Principles that ALWAYS apply, inline here because they must not be skipped}}

1. **{{First principle}}** - {{Explanation}}
2. **{{Second principle}}** - {{Explanation}}

## What Would You Like To Do?

1. **{{First option}}** - {{Brief description}}
2. **{{Second option}}** - {{Brief description}}
3. **{{Third option}}** - {{Brief description}}

## Routing

| Choice | Workflow |
|--------|----------|
| 1, "{{keywords}}" | [workflows/{{first}}.md](workflows/{{first}}.md) |
| 2, "{{keywords}}" | [workflows/{{second}}.md](workflows/{{second}}.md) |
| 3, "{{keywords}}" | [workflows/{{third}}.md](workflows/{{third}}.md) |

## References

| When | Load |
|------|------|
| {{Condition}} | [references/{{topic}}.md](references/{{topic}}.md) |

---

## Directory Structure

```
{{skill-name}}/
├── SKILL.md
├── workflows/
│   ├── {{first}}.md
│   ├── {{second}}.md
│   └── {{third}}.md
└── references/
    └── {{topic}}.md
```

## Workflow Template

```markdown
# Workflow: {{Title}}

## Process

1. **{{First step}}**
   
   {{Instructions}}

2. **{{Second step}}**
   
   {{Instructions}}

## Success Criteria

- [ ] {{First criterion}}
- [ ] {{Second criterion}}
```
