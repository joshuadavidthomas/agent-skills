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

## Learnings (from the svelte5 + sveltekit + jj + skill-authoring + frontend-design-principles passes)

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
  both by owner decision. Do not chase 100% by degrading intentional content.
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
| improving-prompts | — | 1/1 | Refs clean. Review pending. |
| writing-error-messages | — | 2/2 | Refs clean. Review pending. |
| writing-cli-skills | — | 1/1 | Dir-pointer; effectively clean. Review pending. |
| grug-brained-dev | — | n/a | No references dir. Review pending. |
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

1. **Quick wins** — no-refs and tiny-refs skills likely already strong:
   grug-brained-dev, researching-codebases, writing-clearly-and-concisely,
   improving-prompts, writing-error-messages, writing-cli-skills. Review, apply
   levers only if a sub-criterion is below 3/3. ("Likely strong" keeps being
   wrong — treat every skill as unverified until `tessl` + a real link check
   say so. jj had 12 genuine broken nav links; skill-authoring had a 2/3
   description + a code-fence false-positive; frontend-design-principles was
   74% needing a full 209→116-line rewrite. None were pure quick wins. The
   "tiny-refs ⇒ easy" heuristic has a 0% hit rate so far.)
2. **One genuine fix** — coolify-compose (wire or drop `official-docs.md`),
   plus its review.
3. **Soft gap** — crafting-effective-readmes (`using-references.md` wiring) +
   review; diataxis review (refs benign).
4. **Design-aware** — rust, salsa: review for Content; audit references via the
   actual hub navigation, not BFS. Largest effort, likely lowest yield.
