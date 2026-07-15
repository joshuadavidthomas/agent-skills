---
name: writing
description: General prose doctrine for anything a human will read — clear, concrete, free of ready-made phrases. Use when writing or editing documentation, explanations, summaries, commit messages, reports, or any other prose.
---

# Writing

Orwell, 1946, on bad prose: it "consists less and less of *words* chosen for the sake of their meaning, and more and more of *phrases* tacked together like the sections of a prefabricated henhouse." He was describing human writers who let stock phrases do their thinking. You are that process industrialized. Every failure this skill catalogs — the puffery, the negative parallelisms, the bold-first bullets — is a symptom of one disease: reaching for the phrase that comes easily instead of the words that carry the meaning. Ready-made phrases "will construct your sentences for you — even think your thoughts for you, to a certain extent — and at need they will perform the important service of partially concealing your meaning even from yourself."

The cure is also his: **let the meaning choose the word, and not the other way around.** Know what you are trying to say before you say it, then hunt for the words that say exactly that. A sentence that arrived fully formed probably came off the shelf. Rewrite it.

## The method

Ask of every sentence, in Orwell's words:

1. What am I trying to say?
2. What words will express it?
3. What image or idiom will make it clearer?
4. Is this image fresh enough to have an effect?

And then: Could I put it more shortly? Have I said anything that is avoidably ugly?

## The rules

1. **Never use a metaphor, simile, or other figure of speech which you are used to seeing in print.** Today: which you are used to seeing in AI output. "Tapestry", "landscape", "deep dive", "game-changer" — a phrase you have generated before has stopped being an image and become filler. (A fully dead metaphor like "iron resolution" has reverted to being an ordinary word and is fine; it is the worn-out ones in between that must go.)
2. **Never use a long word where a short one will do.** "Use", not "utilize" or "leverage". "Look at", not "delve into". "Is", not "serves as", "stands as", or "represents".
3. **If it is possible to cut a word out, always cut it out.** A sentence should contain no unnecessary words for the same reason a drawing should have no unnecessary lines and a machine no unnecessary parts. "The question as to whether" is "whether". "Owing to the fact that" is "since". "It's worth noting that X" is "X".
4. **Never use the passive where you can use the active.** "The plan was reviewed by the team" hides the actor and deadens the sentence. "The team reviewed the plan."
5. **Never use a foreign phrase, a scientific word, or a jargon word if you can think of an everyday English equivalent.** A technical term with an exact meaning is not jargon — "idempotent" has no everyday equivalent, and flattening it loses the meaning. Jargon is imprecision wearing a lab coat; swap in the everyday word only where precision survives.
6. **Put statements in positive form.** Say what is, not what is not. "Did not remember" is "forgot"; "did not have much confidence in" is "distrusted". Even a negative point lands harder stated positively: "This is backwards", not "This is not the right direction."
7. **Use definite, specific, concrete language.** "The race is not to the swift, nor the battle to the strong" says more than "success in competitive activities exhibits no tendency to be commensurate with innate capacity". Name the race, the battle, the bread. When prose goes abstract, the writer has stopped seeing what they are describing. The swap test: if the sentence could appear unchanged in any other project's README, PR, or landing page, it says nothing about yours — rewrite it or delete it.
8. **One paragraph per topic, opened by its topic sentence.** Express coordinate ideas in parallel form. Keep related words together.
9. **Place the emphatic words of a sentence at the end.** The end position is what the reader carries into the next sentence; do not spend it on qualifiers.
10. **Break any of these rules sooner than say anything outright barbarous.**

## Write for the reader

Two questions about the reader govern every piece: what do they know, and what did they come for.

**What they know.** Only what is on the page. A term you coined means nothing until you anchor it. Never lean on context the reader doesn't have — reasoning you did elsewhere, a discussion they weren't in. When clear and short conflict, choose clear.

**What they came for.** A reader is here either to do something or to understand something. Decide which before writing, and serve that need only. Theory interrupting instructions fails the person trying to act; procedure padding an explanation fails the person trying to think. One piece, one need — separate the rest, don't blend it.

## Match tone to stakes

Most work is an incremental improvement, and that is fine. Do not inflate a bug fix into a meditation on the future of software. Do not manufacture drama ("Here's the kicker"), announce that your point is obvious ("The reality is simple"), confess a bias to buy credibility, or attribute claims to unnamed experts. State the point at the size it actually is and let the evidence do the emphasizing. If the thing is important, the facts will show it.

## The tells

`references/tropes.md` is the field guide: the specific prefabricated phrases and structures that mark machine writing, with examples and fixes. The worst offenders:

| Category | Offenders |
|---|---|
| Word choice | "delve", "leverage", "robust", "tapestry", "landscape", "serves as", "quietly", "stands as a testament" |
| Sentence structure | "not X — it's Y", "Not A. Not B. Just C.", "The result? Devastating.", tricolon pileups, "-ing" tails ("highlighting its importance") |
| Tone | "Here's the kicker", "Think of it as", "Let's break this down", stakes inflation, invented concept labels |
| Formatting | em-dash pileups, bold-first bullets, emoji decoration, Title Case Headings, arrow chains in prose |
| Composition | fractal summaries, one metaphor beaten across a piece, "In conclusion", "Despite these challenges..." |

Any single trope once might be fine. A cluster is not.

## Before delivering

Reread the draft as a reader who knows only what's on the page and came for one thing. Then check:

- Does every sentence say what I actually meant, in words I chose for this sentence?
- Did I use the same sentence shape more than twice in a row?
- Is anything here only there to sound thorough, balanced, or significant?
- Could any sentence be shorter without losing meaning?
- Would a person with something to say write it this way?
