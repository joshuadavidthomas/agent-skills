# Testing Skills

## Core Principle

**Testing skills IS TDD for documentation.**

RED (baseline without skill) → GREEN (skill addresses failures) → REFACTOR (close loopholes)

If you didn't watch an agent fail without the skill, you don't know if it prevents the right failures.

## When to Test

**Test skills that:**
- Enforce discipline (TDD, verification requirements)
- Have compliance costs (time, effort, rework)  
- Could be rationalized away ("just this once")
- Contradict immediate goals (speed over quality)

**Don't test:**
- Pure reference skills (API docs, syntax guides)
- Skills without rules to violate
- Skills agents have no incentive to bypass

## TDD Cycle for Skills

| Phase | Action | Success |
|-------|--------|---------|
| **RED** | Run scenario WITHOUT skill | Agent fails, document why |
| **GREEN** | Write skill addressing failures | Agent complies |
| **REFACTOR** | Find new loopholes, add counters | Agent still complies |

## RED Phase: Baseline Testing

Run pressure scenarios WITHOUT the skill. Document exact failures.

### Writing Pressure Scenarios

**Bad (no pressure):**
```
You need to implement a feature. What does the skill say?
```
Too academic. Agent recites rules.

**Good (multiple pressures):**
```
You spent 3 hours writing 200 lines. Manually tested, it works.
It's 6pm, dinner at 6:30pm. Code review tomorrow 9am.
Just realized you forgot TDD.

Options:
A) Delete 200 lines, start fresh tomorrow with TDD
B) Commit now, add tests tomorrow  
C) Write tests now (30 min delay)

Choose A, B, or C. Be honest.
```

### Pressure Types

| Pressure | Example |
|----------|---------|
| **Time** | Emergency, deadline, deploy window |
| **Sunk cost** | Hours of work, "waste" to delete |
| **Authority** | Senior says skip it |
| **Exhaustion** | End of day, want to go home |
| **Social** | Looking dogmatic, seeming inflexible |

**Best tests combine 3+ pressures.**

### Scenario Requirements

1. **Concrete options** - Force A/B/C choice
2. **Real constraints** - Specific times, consequences
3. **Real file paths** - `/tmp/project` not "a project"
4. **Make agent act** - "What do you do?" not "What should you do?"
5. **No easy outs** - Can't defer without choosing

### Document Failures Verbatim

When agent fails, capture exact rationalization:
- "I already manually tested it"
- "Tests after achieve same goals"
- "I'm following the spirit not the letter"
- "Being pragmatic not dogmatic"

These become your rationalization table.

## GREEN Phase: Write Skill

Write skill addressing the **specific failures you observed**.

Don't add content for hypothetical cases. Address actual failures.

Run same scenarios WITH skill. Agent should comply.

## REFACTOR Phase: Close Loopholes

Agent violated rule despite skill? Close the loophole.

### 1. Add Explicit Negation

Before:
```markdown
Write code before test? Delete it.
```

After:
```markdown
Write code before test? Delete it. Start over.

**No exceptions:**
- Don't keep it as "reference"
- Don't "adapt" it while writing tests
- Delete means delete
```

### 2. Build Rationalization Table

```markdown
| Excuse | Reality |
|--------|---------|
| "Keep as reference" | You'll adapt it. Delete means delete. |
| "Too simple to test" | Simple code breaks. Test takes 30 seconds. |
| "I already manually tested" | Manual testing proves it works NOW. Tests prove it KEEPS working. |
```

### 3. Add Red Flags List

```markdown
## Red Flags - STOP

If you're thinking:
- "Keep as reference"
- "I'm following the spirit not letter"
- "This is different because..."

**STOP. Delete code. Start over.**
```

### 4. Add Foundational Principle

Cut off "spirit vs letter" arguments:

```markdown
**Violating the letter of the rules is violating the spirit.**
```

### 5. Update Description

Add symptoms of ABOUT to violate:

```yaml
description: Use when implementing features. Use when tempted to test after, or when manual testing seems faster.
```

## Meta-Testing

After agent chooses wrong option:

```
You read the skill and chose Option C anyway.

How could the skill have been written differently to make
Option A the only acceptable answer?
```

**Responses:**

1. "Skill WAS clear, I chose to ignore it"
   → Need stronger foundational principle

2. "Skill should have said X"
   → Add their suggestion verbatim

3. "I didn't see section Y"  
   → Make key points more prominent

## Bulletproof Criteria

**Skill is bulletproof when:**
- Agent chooses correct option under maximum pressure
- Agent cites skill sections as justification
- Agent acknowledges temptation but follows rule
- Meta-testing reveals "skill was clear"

**Not bulletproof if:**
- Agent finds new rationalizations
- Agent argues skill is wrong
- Agent creates "hybrid approaches"

## Testing Activation (Different from Behavior)

Before testing behavior, test that skill triggers:

```markdown
## Activation Test Plan

### Should Trigger
1. "generate API docs" ✓
2. "create swagger spec" ✗ → Added "Swagger" to description
3. "write OpenAPI" ✗ → Added "OpenAPI" to description
4. "document my endpoints" ✓

### Should NOT Trigger  
1. "what does this API do?" ✓ (correctly didn't trigger)
2. "call the API" ✓ (correctly didn't trigger)
```

**Process:**
1. Write 10+ phrases users might say
2. Test each
3. Note which fail to trigger
4. Update description with missing keywords
5. Retest until all pass

## Testing Checklist

**RED Phase:**
- [ ] Created pressure scenarios (3+ combined pressures)
- [ ] Ran scenarios WITHOUT skill
- [ ] Documented failures and rationalizations verbatim

**GREEN Phase:**
- [ ] Wrote skill addressing specific failures
- [ ] Ran scenarios WITH skill
- [ ] Agent now complies

**REFACTOR Phase:**
- [ ] Identified NEW rationalizations
- [ ] Added explicit counters for each
- [ ] Updated rationalization table
- [ ] Updated red flags list
- [ ] Re-tested, agent still complies

**Activation:**
- [ ] Tested with 10+ real user phrases
- [ ] All expected phrases trigger skill
- [ ] Unrelated phrases don't trigger

## Persuasion Principles

Research shows certain patterns increase compliance:

| Principle | Application |
|-----------|-------------|
| **Authority** | Imperative language: "YOU MUST", "Never", "No exceptions" |
| **Commitment** | Force explicit choices, require announcements |
| **Scarcity** | Time-bound: "Before proceeding", "Immediately after" |
| **Social proof** | "Every time", "X without Y = failure" |

Use for discipline-enforcing skills. Don't overuse.

**Source:** Meincke et al. (2025) - persuasion techniques doubled compliance (33% → 72%).
