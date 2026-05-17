# Skill Cleanup Sweep

A per-skill quality pass: run `tessl skill review`, raise the Content score, audit
reference reachability, fix genuine problems, ship one skill per PR.

Work **one skill at a time, one branch + PR per skill**. Do not batch skills.
Update the status table at the bottom as you go.

## Per-skill procedure

1. **Baseline.** `tessl skill review <skill>`. Record the score and which Content
   sub-criteria are below 3/3.
2. **Raise Content.** Apply the known levers (see Learnings). Description is
   usually already strong — do not pad it.
3. **Reference-usage audit.** Determine how this skill *surfaces* its references
   before judging anything dead (see Learnings — the convention matters). Only
   then identify true orphans.
4. **Fix.** Make the smallest change that works. Preserve evocative language and
   intentional designs. Wire genuine orphans into their natural parent; prune
   only true stale duplicates after inspecting the file.
5. **Verify.** Re-run the review until the relevant sub-criteria are 3/3. If a
   score seems implausible, run the negative-control check (see Learnings).
   Re-run the reachability audit.
6. **Ship.** Separate branch off `main`, one commit, push, open a PR scoped to
   that single skill. Then move to the next.

## Learnings (from the svelte5 + sveltekit + jj + skill-authoring + frontend-design-principles + improving-prompts + writing-error-messages + writing-cli-skills + grug-brained-dev passes)

- **The `tessl` judge is content-deterministic.** Identical content → byte-identical
  output. Re-running the same file proves nothing about robustness. To prove a
  score is real (not stale/cached), copy the skill, inject obvious bloat, and
  confirm the score drops — it does.
- **Conciseness regresses on redundant *rationale*, not on dense workflow or
  code.** Adding ❌/✅ snippets and explicit numbered workflows raised
  actionability/workflow_clarity while conciseness *held* at 3/3. Trimming
  per-principle "sentence of rationale that adds modest value" is what recovers
  conciseness. Cut explanation; keep imperative steps and minimal examples.
- **Preserve evocative framing.** A `Code smell` / `Common mistake` column is the
  asset; flattening it for a marginal token saving is a regression. Consolidate
  duplicated *artifacts*, not the vivid language.
- **Some skills have a conciseness ceiling at 2/3 by design — that is the honest
  score, not a TODO.** frontend-design-principles is a behavior-change craft
  *manifesto*; its persuasive repetition ("Where Defaults Hide", "Sameness is
  failure") is the mechanism. The rewrite cut every redundant rationale and
  belabored restatement (209→116 lines), lifting Content 55→85% (actionability
  2/3→3/3, conciseness 1/3→2/3) and Description 82→100%. The judge then kept
  asking to compress the evocative core to reach conciseness 3/3. Stop there.
  Procedure: cut all duplicated/explanatory prose first; once the only remaining
  reduction is into the vivid framing, that is the ceiling — surface it to the
  owner and ship at the honest score. Precedents now: skill-authoring 99%
  (code-fence false-positive), frontend-design-principles 94% (manifesto voice),
  improving-prompts 94% (anti-rationalization discipline mechanism + actionable
  inline summary — cutting either regresses a 3/3 sub-score). All by owner
  decision. Do not chase 100% by degrading intentional content. When the
  ceiling call is identical to a prior owner decision, apply it and surface in
  the PR — do not re-ask the same question every skill.
- **tessl cannot see content staleness — it scores structure and writing, not
  currency.** improving-prompts scored 90% while its entire premise ("apply
  *documented* Anthropic best practices") rested on Claude-4.5-era source: a
  stale "avoid the word *think*" extended-thinking section, 4.5 migration
  notes, no adaptive-thinking/effort, no current CLAUDE.md/skill rules. The
  judge is blind to this. For any "applies documented X" / "follows the spec"
  skill, independently verify the source against current upstream docs (web
  research) — a high score is not evidence the content is current. Fixing it
  is the real win even though it barely moves the score (90→94). Clean-break
  the version-pinned artifact too: renamed `claude-4.5-best-practices.md` →
  `anthropic-best-practices.md` rather than keeping a stale filename.
- **Cross-vendor guidance: harvest vendor-neutral *principles*, reject
  vendor-specific *tuning*, and re-evaluate per artifact.** "No cross-model
  section" stays correct, but the right granularity is per-artifact, not
  per-vendor: a *generic* OpenAI prompt page added nothing, yet OpenAI's GPT-5
  *Codex* guide (an agentic-coding guide; `AGENTS.md` is a cross-agent file)
  did contain one genuinely transferable idea — layered instruction files
  (repo-root global → deeper module-specific, more-specific overrides). Folded
  into the improving-prompts reference, but framed in *our* Anthropic-grounded
  terms (`.claude/rules/ paths:`, subdir `CLAUDE.md`), not as "OpenAI says".
  Reject the vendor-specific tuning: Codex preamble-cadence numbers and the
  `phase` param directly *conflict* with Claude 4.7 (which has built-in
  progress updates you should remove scaffolding for) — proof that a blended
  cross-model section would mislead. Test: would this still be true with no
  brand attached, and do our own upstream docs corroborate it? If yes, take
  the principle; if it's a number/param/cadence, leave it.
- **Two reliable levers when Content is low:**
  - actionability < 3 → add 1–3 minimal inline `❌/✅` snippets on the most
    critical principles.
  - workflow_clarity < 3 → add an explicit ordered pass plus named multi-step
    flows, each ending in a verification checkpoint.
- **A strict link-graph BFS over-reports dead references.** It only validly
  applies to skills that use per-file markdown links. Before calling anything
  dead, identify the skill's convention:
  - *per-file links* (svelte5, sveltekit, jj) — strict BFS is meaningful.
  - *dynamic discovery* (reducing-entropy: "list the files in references/") —
    nothing is dead; the agent is told to browse.
  - *hub-and-spoke corpus* (rust, salsa) — SKILL.md links topic hubs that fan
    out to spoke files; BFS mis-resolves short-name/nested links. Needs a
    design-aware trace, not mechanical wiring.
  - *cross-linked vendored doc set* (diataxis) — files link each other; reachable
    from the hubs the SKILL.md loads.
  Applying the svelte5 treatment blindly would damage intentionally-designed
  skills. svelte5 was a true fix because it used per-file links *and* had a
  genuinely orphaned hub.
- **Reachability ≠ link validity.** The refined audit's "13/13 refs clean" for
  jj was *correct* — every reference file was reachable via the bottom Reference
  Index — yet the SKILL.md still had 12 broken links: the Topics table and every
  inline "→ Deep dive" pointer linked a fictional hub layout (`git.md`,
  `sharing.md`, `history.md`, `workspaces.md`, `config.md`, bare `revsets.md`)
  that never existed. A file being reachable from *somewhere* does not mean the
  *primary navigation links resolve*. Always also run `tessl`'s `relative_links`
  check (or grep every `](...)` target against the bundle) — do not infer link
  health from a reachability count.
- **Unknown frontmatter keys may be load-bearing.** jj's `requires-path` looked
  like dead decoration (redundant with `compatibility` + description) but is
  consumed by the `skill-requires-path` pi extension in agentkit. Do not clean-
  break an unknown key; move it under `metadata:` (and add `metadata.version`,
  which tessl then requires). Confirm with the owner before assuming a key is
  inert.
- **A `relative_links` count is not automatically a defect — check the
  fences first.** tessl's link validator scans markdown link syntax *without
  stripping fenced code blocks*. jj's "12 missing" were genuine broken
  navigation links (real defect, fixed). skill-authoring's "14 missing" were
  *correct teaching examples* — `[workflows/planning.md](workflows/planning.md)`
  inside patterns.md's ```` ```markdown ```` Router Pattern block, illustrating a
  fictional skill. Before "fixing" any flagged link, grep its line and check
  whether it sits inside a ``` fence (e.g. `awk '/^```/{f=!f} /\]\(/{print
  f,$0}'`). Never corrupt a canonical example to satisfy a naive linter; a real
  router `SKILL.md` *does* use `[path](path)` tables, so rewriting the sample
  would make it wrong. Surface false-positives to the owner; ship at the honest
  score (skill-authoring shipped at 99%, 0 errors, by owner decision).
- **`dcg` commit guard gotcha.** It substring-matches dangerous tokens in the
  whole command. Avoid the word "restore" in commit messages; use repeated
  `-m` flags or a message file, never a heredoc that contains trigger words.
- **Structural split is the voice-safe lever for a monolithic
  manifesto/immersion skill.** When conciseness is at its intentional ceiling
  (2/3) *and* there is also a long-file warning + progressive_disclosure 2/3,
  do not trim the voice to chase conciseness — instead relocate the
  *reference-grade detail* (taxonomies, hunt criteria, lookup tables) verbatim
  into `references/`, keeping voice priming + workflow + output format always-
  loaded in SKILL.md. grug-brained-dev: moved the whole `## What Grug hunts`
  block out, 86%→94%, 1 warning→0, PD 2/3→3/3, Description 90%→100%, **zero
  prose change** — conciseness stayed 2/3 (honest, the origin story is the
  priming mechanism) but it was no longer the *only* lever. Prove the move is
  loss-free: `diff <(git show main:…SKILL.md | awk '/^### START/{f=1}
  /^## END/{f=0} f' | sed 's/^### /## /') <(tail -n +N references/new.md)` —
  expect only intended heading-depth + trailing-blank deltas.
- **Sanctioned path for a large verbatim extraction.** A 165-line move with
  heading normalization is too big for a safe `edit` and too transcription-
  risky to retype via `write` when the owner needs byte-identical prose. Per
  AGENTS.md: write a real one-shot script, inspect it, run it, validate
  (`diff` vs `main` + read seams + tessl), then delete it deliberately. Used
  here; script removed in the same step. Not a throwaway inline heredoc — a
  reviewed script file with an explicit lifecycle.
- **Owner-flagged-sensitive ≠ routine ceiling.** The standing rule is "when
  the ceiling call matches a prior owner decision, apply it, don't re-ask."
  But when the owner *explicitly* flags a skill ("be careful, don't impact too
  much"), that overrides the don't-re-ask shortcut: present the analysis +
  voice-safe options and let them choose scope. They picked the structural
  split here; the conciseness-ceiling call itself still followed precedent.

## Status

Reachability numbers are from the refined audit (markdown links + bare paths +
directory-pointer detection). `tessl` column is the last recorded review score;
"—" means not yet run this sweep.

| Skill | tessl | Refs | State / notes |
|---|---|---|---|
| svelte5 | 100% | 36/36 | **Done** — consolidated + full coverage. PR #15 merged. |
| sveltekit | 100% | 12/12 | **Done** — inline patterns + workflows. PR #16 open. |
| jj | 100% | 13/13, 12 links fixed | **Done** — Topics table + deep-dive pointers linked a fictional hub layout (12 broken links); repointed to real refs. `requires-path` moved to `metadata` (pi extension consumes it) + `metadata.version` added. PR #18 open. |
| skill-authoring | 99% | 3/3 | **Done** — sharpened description specificity (2/3→3/3); Content already 100%. Remaining `relative_links` warning is a tessl false-positive (router-table example links inside patterns.md code fences); left intact per owner decision, 0 errors. PR #19 open. |
| frontend-design-principles | 94% | 1/1 | **Done** — full SKILL.md rewrite 209→116 lines (cut redundant rationale, added ❌/✅ token example, sharpened description). 74%→94%: Description 100%, Content 85% (actionability/workflow/PD 3/3). conciseness 2/3 is the intentional manifesto ceiling; shipped per owner decision. PR #20 open. |
| improving-prompts | 94% | 1/1 | **Done** — **source refresh** (the real fix): de-pinned from Claude 4.5, renamed reference → `anthropic-best-practices.md`, replaced stale extended-thinking/`avoid think` + migration content with adaptive-thinking/effort + 4.6/4.7 realities + CLAUDE.md/skill rules; no cross-model section (research: not warranted). Also tessl levers (merged Rationalizations+Red Flags, 3→2 trim, de-dup). 90%→94%: Description 100%, Content 85% (actionability/workflow/PD 3/3). conciseness 2/3 = intentional discipline ceiling, per owner. Follow-up commit folds in the one vendor-neutral idea from OpenAI's GPT-5 Codex guide (layered instruction files), Anthropic-framed. PR #21 open. |
| writing-error-messages | 100% | 2/2 | **Done — no changes.** Perfect score on first review: 0 errors/warnings, Description 100%, Content 100% (all sub-criteria 3/3). Both refs surfaced via backtick-path "open when…" pointers (SKILL.md:60-61), genuinely reachable; no markdown links at all (no fence-FP surface). Verified, not assumed — no PR because there is nothing to change. |
| writing-cli-skills | 100% | 1/1 | **Done** — pre-sweep "effectively clean" was wrong: baseline 90%. Content already 100% (all 3/3); whole gap was Description 75% (specificity 2/3, trigger_term_quality 2/3). One-line frontmatter rewrite, every enumerated capability grounded in an existing section (no invented scope), added natural triggers (command-line/terminal/shell-command/binary wrapper). 90%→100%, Description→100%. PR #22 open. |
| grug-brained-dev | 94% | 1/1 | **Done** — owner-flagged sensitive (voice *is* the mechanism). 86%, 1 warning (561 lines). Voice-safe levers only: relocated whole `## What Grug hunts` subsection set verbatim → `references/hunting.md` (proved byte-identical by `diff` vs `main`: only `###`→`##` + trailing-blank tidy), kept voice priming + output format + Grug-voice pointer in SKILL.md; sharpened description to concrete discrete ops keeping Grug flavor. 86%→94%, warning→0: Description 90%→100%, Content 77%→85% (PD 2/3→**3/3**). conciseness 2/3 = intentional voice/immersion ceiling (origin story is the priming tool), per owner — not degraded. PR #23 open. |
| researching-codebases | — | n/a | No references dir. Review pending. |
| writing-clearly-and-concisely | — | n/a | No references dir. Review pending. |
| reducing-entropy | — | n/a | Dynamic `ls` discovery by design — not dead. Review pending. |
| diataxis | — | 16/17 | Cross-linked corpus; only `index.md` unused (vendored TOC, benign). Review pending. |
| crafting-effective-readmes | — | 0/5\* | Soft gap: `using-references.md` names but does not link the 5 deeper docs. Review pending. |
| coolify-compose | — | 2/3 | **Genuine orphan:** `references/official-docs.md` referenced nowhere; SKILL.md links the live URL instead. Wire it in (offline, v4.x-pinned) or delete. Review pending. |
| rust | — | hub | Hub-and-spoke (59 spoke files). Needs design-aware trace, not BFS. Likely fine (passed review in #13). |
| salsa | — | hub | Hub-and-spoke nested corpus (60 files). Design-aware trace. Likely fine (passed review in #13). |

\* reachable count from strict BFS; the 5 are deeper vendored README references.

## Suggested order

1. **"Quick wins" — there are none; treat each as unverified:**
   grug-brained-dev, researching-codebases, writing-clearly-and-concisely,
   writing-error-messages, writing-cli-skills. Review; apply levers only if a
   sub-criterion is below 3/3 — but also check source currency (tessl can't
   see staleness) and run a real link check. Track record: jj had 12 genuine
   broken nav links; skill-authoring had a 2/3 description + a code-fence
   false-positive; frontend-design-principles was 74% needing a full
   209→116-line rewrite; improving-prompts was 4.5-stale and needed a source
   refresh; writing-error-messages was genuinely clean (100% first pass, no
   change); writing-cli-skills was pre-judged "effectively clean" but baselined
   at 90% (Content 100%, Description 75%) and needed a real description rewrite;
   grug-brained-dev (no-refs, assumed simple) was 86% with a long-file warning
   and needed a structural split into a new references/ file. The "tiny-refs ⇒
   easy" heuristic is now **1/7** — still assume real work:
   the one clean skill was only *confirmable* by running the full audit
   (ref-reachability + link health + currency), and the pre-sweep Refs
   annotations ("no references dir"/"dir-pointer; effectively clean") predict
   reference *health*, not tessl *score* — Content can be 100% while
   Description sits at 75%, and a no-refs skill can still need a new ref file.
   "Clean" is a verified finding, never the default; a no-op skill still costs
   a real review, just no PR.
2. **One genuine fix** — coolify-compose (wire or drop `official-docs.md`),
   plus its review.
3. **Soft gap** — crafting-effective-readmes (`using-references.md` wiring) +
   review; diataxis review (refs benign).
4. **Design-aware** — rust, salsa: review for Content; audit references via the
   actual hub navigation, not BFS. Largest effort, likely lowest yield.
