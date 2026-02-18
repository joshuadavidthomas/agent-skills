# Refining Skills From Session Learnings

When a skill misbehaves during actual use, capture the learning and fix it while context is fresh.

## When to Use This Workflow

You're in a session and:
- A skill triggered but produced wrong output
- Instructions were followed but led to unexpected results
- An edge case appeared that isn't covered
- The skill triggered when it shouldn't have (or vice versa)
- You repeatedly had to correct or clarify something

**This is different from initial testing.** You have concrete evidence from real use, not hypothetical pressure scenarios.

## The Refinement Cycle

```
Observe → Capture → Diagnose → Fix → Verify
```

Small, targeted iterations. One fix at a time.

## Step 1: Observe

Notice when something goes wrong. Watch for:

| Signal | Example |
|--------|---------|
| **Wrong output** | Skill ran but result doesn't match intent |
| **Missing step** | Had to manually do something the skill should cover |
| **Wrong skill triggered** | Asked for X, got skill for Y |
| **Skill didn't trigger** | Expected skill to load, it didn't |
| **Repeated corrections** | Keep saying "no, I meant..." |
| **Unexpected interpretation** | Skill did something surprising |

## Step 2: Capture (Before You Forget)

Document the failure **verbatim** while context is fresh:

```markdown
## Session Learning: [skill-name] - [date]

### What I asked
[Exact request that triggered the issue]

### What happened
[Exact behavior - copy/paste if possible]

### What I expected
[What should have happened]

### What I had to do instead
[Manual correction or workaround]
```

**Don't summarize.** Exact wording matters. "It didn't work right" tells you nothing tomorrow.

## Step 3: Diagnose

Identify the root cause. Most failures fall into patterns:

### Instruction Problems

| Pattern | Symptom | Fix |
|---------|---------|-----|
| **Missing instruction** | Skill didn't cover this case | Add the missing guidance |
| **Ambiguous instruction** | Multiple valid interpretations | Make one interpretation explicit |
| **Wrong order** | Steps executed in wrong sequence | Reorder or add sequencing cues |
| **Contradictory instructions** | Two rules conflict | Resolve the conflict, add priority |
| **Buried instruction** | Critical info too deep in doc | Move to first 100 lines |

### Example Problems

| Pattern | Symptom | Fix |
|---------|---------|-----|
| **No example for this case** | Edge case not shown | Add specific example |
| **Example too different** | Couldn't generalize | Add example closer to real use |
| **Example incomplete** | Missing crucial detail | Complete the example |

### Activation Problems

| Pattern | Symptom | Fix |
|---------|---------|-----|
| **Missing trigger keywords** | Skill didn't load | Add words user actually said |
| **Over-broad description** | Wrong skill triggered | Narrow with negative cases |
| **Conflicting with other skill** | Unpredictable activation | Differentiate descriptions |

### Structure Problems

| Pattern | Symptom | Fix |
|---------|---------|-----|
| **Too verbose** | Key info lost in noise | Cut ruthlessly |
| **Too minimal** | Made wrong assumptions | Add explicit guidance |
| **Poor progressive disclosure** | Loaded irrelevant reference | Restructure layers |

## Step 4: Fix (Minimal and Targeted)

**One issue, one fix.** Don't batch changes.

Read the current skill:
```bash
cat path/to/skill/SKILL.md
```

Make the smallest change that addresses the specific failure:

| Diagnosis | Minimal Fix |
|-----------|-------------|
| Missing instruction | Add 1-3 lines of guidance |
| Ambiguous instruction | Reword the specific line |
| Missing trigger keyword | Add word to description |
| Missing example | Add one targeted example |
| Buried critical info | Move section earlier |

**Resist the urge to rewrite.** You're patching, not rebuilding.

## Step 5: Verify

Test the fix in your current session if possible.

### Same-Session Verification

If the session is still active:
1. Reproduce the original scenario
2. Confirm the skill now behaves correctly
3. Spot-check a related scenario to ensure you didn't break anything

### Fresh-Context Verification

If starting a new session:
1. Trigger the skill with the exact phrase that caused the issue
2. Verify the fix worked
3. Try 2-3 variations to ensure robustness

**Don't skip verification.** An untested fix is just a hypothesis.

## Meta-Question

When a fix isn't obvious, ask yourself (or Claude):

> "How could this skill have been written differently to make the correct behavior obvious?"

Three types of answers:

| Answer | Action |
|--------|--------|
| "It WAS clear, I just didn't follow it" | Strengthen the language (MUST, NEVER, NO EXCEPTIONS) |
| "It should have said X" | Add that exact wording |
| "I didn't see section Y" | Make Y more prominent, move it earlier |

## Patterns That Require Multiple Iterations

Some issues need a few cycles:

### Development Context Blindness

**Problem:** Instructions made sense while writing but are ambiguous to a fresh context.

**Fix:** After any change, mentally reset. Read the skill as if you've never seen it. Does it still make sense?

### Rationalization Loopholes

**Problem:** Skill is clear, but there's a way to argue around it.

**Fix:** Add explicit "No exceptions" blocks:
```markdown
**No exceptions:**
- Not for "just this once"
- Not for "I already did it manually"
- Not for "this case is different"
```

### Cascading Ambiguity

**Problem:** Fixing one ambiguity reveals another.

**Fix:** This is normal. Keep iterating. Each cycle tightens the skill.

## Recording Refinements

For significant skills, keep a refinement log:

```markdown
## Refinement Log

### 2025-01-30: Ambiguous output format
- **Issue:** User asked for JSON, skill produced YAML
- **Cause:** No explicit default format specified
- **Fix:** Added "Default to JSON unless user specifies otherwise"
- **Verified:** Retested, now outputs JSON

### 2025-01-28: Missed edge case
- **Issue:** Empty input caused error instead of graceful message
- **Cause:** No instruction for empty input handling
- **Fix:** Added "For empty input, return helpful message instead of error"
- **Verified:** Tested with empty file, works
```

This log becomes invaluable when patterns emerge across multiple refinements.

## When to Stop Refining

A skill is "good enough" when:
- It handles your common cases correctly
- Edge cases fail gracefully with useful messages
- You haven't needed to correct it in the last few uses
- Activation is reliable (triggers when it should, doesn't when it shouldn't)

**Perfect is the enemy of deployed.** Ship, use, refine.

## Anti-Patterns

| Don't | Do Instead |
|-------|------------|
| Batch multiple fixes | One fix per cycle |
| Summarize the failure | Capture exact wording |
| Rewrite the whole skill | Make minimal targeted edit |
| Skip verification | Always test the fix |
| Fix hypothetical issues | Fix observed issues only |
| Wait until "later" to capture | Document immediately |

## Quick Reference

```
1. OBSERVE  - Notice something went wrong
2. CAPTURE  - Document exact failure verbatim
3. DIAGNOSE - Match to pattern (instruction/example/activation/structure)
4. FIX      - Smallest change that addresses the issue
5. VERIFY   - Test in same session or fresh context
```

Small iterations. Concrete evidence. Immediate capture. Always verify.
