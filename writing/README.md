# writing

An agent skill for general prose — anything a human will read.

It is built on George Orwell's "Politics and the English Language" (1946). Orwell diagnosed writers who assemble prose from "phrases tacked together like the sections of a prefabricated henhouse" instead of choosing words for their meaning; an LLM is that process industrialized. The skill treats every AI writing tell as a symptom of that one disease, and applies the same cure: let the meaning choose the word, and not the other way around.

## When to use

Use this skill for:

- Documentation, explanations, and technical writing
- Summaries, reports, and end-of-run write-ups
- Commit messages and PR descriptions
- Editing or reviewing existing prose for clarity and AI tells

For specific artifact types, more focused skills exist: `crafting-effective-readmes` for READMEs, `writing-error-messages` for error copy, `diataxis` for documentation architecture. This skill is the general doctrine underneath them.

## Structure

- `SKILL.md` — the working doctrine: the thesis, Orwell's four questions, ten rules merging Orwell and Strunk, the two reader-side questions (what they know, what they came for), tone-to-stakes discipline, a worst-offenders table, and a delivery self-check
- `references/tropes.md` — the field guide to AI writing tropes: word choice, sentence structure, paragraph structure, tone, formatting, and composition, each with examples and fixes
- `references/politics-and-the-english-language.md` — the full Orwell essay
- `references/LICENSE-tropes` — license notice for the adapted trope catalog

## Core idea

A scrupulous writer asks of every sentence: What am I trying to say? What words will express it? What image or idiom will make it clearer? Is this image fresh enough to have an effect? And then: Could I put it more shortly? Have I said anything that is avoidably ugly?

A sentence that arrived fully formed probably came off the shelf. Word bans ("no em dashes", "stop saying delve") trim the symptoms one at a time; the rules and method here go after the habit that produces them.

## The AGENTS.md / CLAUDE.md snippet

The distilled version, for pasting into a global AGENTS.md or CLAUDE.md so it applies to every session without loading the full skill:

```markdown
## Writing

Never use a phrase you are used to seeing. If a sentence came out easily, it
probably came pre-assembled — ready-made phrases think your thoughts for you.
Know what you're trying to say, then let the meaning choose the words.

- Use the shortest everyday word that covers the meaning. If a word can be
  cut, cut it.
- Active voice. Positive form. Concrete nouns over abstractions — "the race,
  the battle, the bread", not "competitive activities".
- Match tone to stakes. No puffery, no manufactured drama, no inflated
  significance. State the point; don't announce that you're about to.
- The reader knows only what's on the page: anchor coined terms, restate
  earlier reasoning instead of citing it, write the actual sentence instead
  of arrow chains and notation.
- Decide what the reader came for — to act or to understand — and serve
  that one need per piece.
- Banned on sight: "not X — it's Y", "serves as", "delve", "leverage",
  "robust", "tapestry", "landscape", "Here's the kicker", "it's worth
  noting", "In conclusion". These are symptoms — the disease is reaching
  for stock phrasing instead of thinking.
- Formatting is not emphasis: no bold-first bullets, no em-dash pileups,
  no fragments-as-paragraphs, no summary of what you just said.
- Break any of these rules sooner than write anything outright barbarous.
```

## Related skills

- [`english-please`](../english-please/) — the quick corrective for over-compressed explanations after a long run. This skill states the general principle (the reader knows only what's on the page); `english-please` is the sharp, loop-flavored version of it.
- [`diataxis`](../diataxis/) — the four documentation types and how to structure docs around them. This skill carries the generalized form of its reader-need principle (act or understand, one piece serves one need); `diataxis` owns the taxonomy.

## Sources

- George Orwell, ["Politics and the English Language"](https://www.orwellfoundation.com/the-orwell-foundation/orwell/essays-and-other-works/politics-and-the-english-language/) (1946) — included in full as a reference
- William Strunk Jr., *The Elements of Style* (1918, public domain) — composition rules distilled into the rules list
- The ai-writing-tropes skill in [Xe/site](https://github.com/Xe/site) (zlib, Christine Dodrill), content from [tropes.fyi](https://tropes.fyi) — adapted into the trope catalog
- Wikipedia's [Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing) (CC BY-SA 4.0) — production-relevant patterns folded into the trope catalog
