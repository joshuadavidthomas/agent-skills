# agent-skills

A collection of skills for agentic LLM tools, following the [Agent Skills specification](https://agentskills.io/specification).

## Installation

- **Agent-specific**
  - [Claude Code](#claude-code)
  - [OpenCode](#opencode)
- **Package managers**
  - [dotagents](#dotagents)
  - [OpenSkills](#openskills)
  - [skills.sh](#skillssh)

### Agent-specific

#### Claude Code

Install from the plugin marketplace:

```bash
/plugin marketplace add joshuadavidthomas/agent-skills
```

Install an individual skill plugin (recommended). Plugin names match skill directory names (for example `sveltekit`, `skill-authoring`, `writing-cli-skills`):

```bash
/plugin install reducing-entropy@joshthomas-agent-skills
```

Or install the bundle with all skills:

```bash
/plugin install all@joshthomas-agent-skills
```

CLI equivalent:

```bash
claude plugin install reducing-entropy@joshthomas-agent-skills --scope project
```

Requires Claude Code v1.0.33 or later.

#### OpenCode


Clone this repo and symlink the skills you want:

```bash
git clone https://github.com/joshuadavidthomas/agent-skills.git
cd agent-skills
mkdir -p ~/.config/opencode/skills
ln -s "$PWD/reducing-entropy" ~/.config/opencode/skills/reducing-entropy
```

OpenCode also discovers skills from `.opencode/skills`, `.claude/skills`, and `.agents/skills` in your project.

Requires OpenCode v1.0.190 or later, which has native skill loading built in. [`opencode-agent-skills`](https://github.com/joshuadavidthomas/opencode-agent-skills) is still available if you are stuck on an older version or if you want its specific loading behavior.

### Package managers

#### dotagents

Install with [dotagents](https://github.com/getsentry/dotagents):

```bash
npx @sentry/dotagents add joshuadavidthomas/agent-skills
```

Or install an individual skill:

```bash
npx @sentry/dotagents add joshuadavidthomas/agent-skills --name reducing-entropy
```

#### OpenSkills

Install with [OpenSkills](https://github.com/numman-ali/openskills):

```bash
npx openskills install joshuadavidthomas/agent-skills
npx openskills sync
```

Use `--global` to install into `~/.claude/skills`.

#### skills.sh

Install with [skills.sh](https://skills.sh/docs):

```bash
npx skills add joshuadavidthomas/agent-skills
```

## Usage

Skills are model-invoked—the agent decides when to use them based on your request and the skill's description. You can also explicitly ask for a skill:

> Use the reducing-entropy skill to review this refactor

or reference it by name when relevant to your task.

## Skills

### [ai-writing-tropes](./ai-writing-tropes/)

Detect and eliminate common AI writing tropes from prose. Comprehensive catalog of patterns (word choice, sentence structure, paragraph layout, tone, formatting, composition) that mark AI-generated writing, with a self-check workflow. Source: [tropes.fyi](https://tropes.fyi).

### [coolify-compose](./coolify-compose/)

Convert Docker Compose files to Coolify templates for both raw-compose and repository deployment modes. Covers Coolify magic variables (`SERVICE_URL_*`, `SERVICE_PASSWORD_*`), health checks, and common conversion/troubleshooting patterns.

### [crafting-effective-readmes](./crafting-effective-readmes/)

Guides you through writing READMEs matched to your audience and project type. Different audiences need different information—a contributor to an OSS project needs different context than future-you opening a config folder.

Uses a structured process to identify task type (creating, adding, updating, or reviewing) and ask relevant questions before drafting.

Includes:

- Templates for open source, personal, internal, and config projects
- Section checklist showing which sections matter for each project type
- Style guide covering common mistakes
- Reference materials: Standard README spec (with examples), "Art of README", and Make a README guide

### [diataxis](./diataxis/)

Apply the Diátaxis framework for documentation structure and writing. Helps classify and produce tutorials, how-to guides, reference, and explanation docs.

### [frontend-design-principles](./frontend-design-principles/)

Design-focused frontend skill for producing intentional, non-generic interfaces. Includes required discovery gates, signature-definition workflow, and self-review checks before presenting UI output.

### [grug-brained-dev](./grug-brained-dev/)

Cognitive interrupt skill for code that looks clean but feels painful to change: too fancy, too abstract, too many files, too many helpers, too many layers, or too well-factored into the wrong boxes. Grug fights complexity demon by forcing big brain AI into smol brain posture: what thing, thing do what, where meat, why five caves?

Uses Grug voice, no-hard-pivot rules, cave-painting names, helper-rent tests, future-rock checks, Chesterton's Fence, locality of behavior, real-seam testing, and near-shore refactoring to turn smart-looking architecture into boring code that tells the truth.

### [jj](./jj/)

Jujutsu (jj) version control for Git-compatible repos. Covers the mental model (working copy as commit, change IDs, mutable history), agent-specific rules (always `-m`, no interactive commands), daily workflows, and progressive deep dives into revsets/filesets/templates, bookmarks and sharing, history rewriting, workspaces for parallel agents, and configuration.

Includes 13 reference files covering Git-to-jj command mapping, revset/fileset/template language specs, bookmark management, GitHub workflows, conflict handling, and more.

### [rust](./rust/)

Rust guidance for idiomatic API design and implementation across ownership, errors, traits, type design, async/Tokio, atomics, unsafe, macros, testing, performance, serde, interop, and project structure.

### [salsa](./salsa/)

Salsa guidance for building incremental Rust systems: databases, tracked functions, input/tracked/interned structs, query pipelines, accumulators, cancellation, LSP integration, memory management, cycles, durability, and production architecture.

### [improve](./improve/)

Survey a codebase as a senior advisor — strictly read-only — and turn the highest-value findings into implementation plans for other agents to execute. Four phases: recon (including the project's domain docs and ADRs), parallel category audits from a playbook, vetting every finding against the actual code, then handing the selected findings to the [writing-plans](./writing-plans/) skill for the plan artifacts.

Supports effort levels (`quick`/`standard`/`deep`), single-category focus, branch-scoped audits, and a roadmap/direction mode. Findings are evidence-backed (`file:line`), ordered by leverage, and "not worth doing" is a recorded verdict.

### [improving-prompts](./improving-prompts/)

Apply Anthropic's documented Claude 4.5 best practices to CLAUDE.md, AGENTS.md, custom commands, and skill files. Uses actual guidance from Anthropic instead of inventing improvements.

The key constraint: don't change anything until you understand what specific behavior is failing. Provides a quick reference table mapping common issues to fixes, plus defensive tables of rationalizations and red flags to prevent agents from bypassing the requirement for concrete issues.

### [reducing-entropy](./reducing-entropy/)

Helps you evaluate designs, review code, and refactor with a bias toward deletion. The core question: "What does the codebase look like *after*?"

Uses a "Three Questions" framework: What's the smallest codebase that solves this? Does the change result in less total code? What can we delete?

Includes "mindsets" with references of ideas and writings from Rich Hickey (simplicity vs. ease), Simon Willison (PAGNI—what's expensive to add later), and data-oriented design principles. Loads at least one mindset before starting.

### [researching-codebases](./researching-codebases/)

Coordinate parallel sub-agents to answer complex codebase questions that span multiple files or require tracing through code. Supports checking existing research before starting new investigations.

Includes:

- Agent definitions for code-locator (fast/cheap), code-analyzer (thorough), code-pattern-finder, and web-searcher
- Agent selection guide with cost/performance tradeoffs
- Scripts for managing research memory in `.research/` or `~/.research/`: list, search, read, promote
- Output format specification for research documents

> [!NOTE]
> Requires installing agent definitions to your CLI tool. See the [agents README](researching-codebases/agents/README.md).

### [skill-authoring](./skill-authoring/)

Create, synthesize, test, debug, review, and refine agent skills. Uses a job-selection table to route agents to the right workflow, covers high-signal descriptions, progressive disclosure, source-backed synthesis, provenance, activation testing, and failure-driven refinement.

### [svelte5](./svelte5/)

Svelte 5 guidance covering runes (`$state`, `$derived`, `$effect`, `$props`, `$bindable`), class-based state patterns, context API usage, and Svelte 4→5 migration defaults.

### [sveltekit](./sveltekit/)

SvelteKit routing, layouts, data loading, actions, authentication patterns, form validation, and remote functions (`command()`, `query()`, `form()`).

### [writing-clearly-and-concisely](./writing-clearly-and-concisely/)

Strunk's rules for clear prose, plus patterns to avoid in AI-generated writing. Use whenever you're writing text humans will read—documentation, commit messages, error messages, explanations, UI copy.

Includes the full *Elements of Style* (1918) split into loadable sections covering grammar, composition, form, and word choice.

Also includes a comprehensive guide to AI writing patterns Wikipedia editors developed to detect generated submissions—covering puffery (*pivotal*, *testament*), overused vocabulary (*delve*, *leverage*, *multifaceted*), and formatting tells.

### [writing-error-messages](./writing-error-messages/)

Write and review human-facing software error messages: UI failures, form validation, auth and account-recovery copy, retry/support paths, CLI errors, and API errors humans will read.

Focuses on making errors specific, actionable, non-blaming, accessible, and safe. Includes the important security exception for authentication and recovery flows, where generic messages may be required to avoid account enumeration.

### [writing-cli-skills](./writing-cli-skills/)

Guide for building high-quality skills around CLI tools. Emphasizes hands-on tool usage, practical command organization, progressive disclosure, and review checklists.

### [writing-plans](./writing-plans/)

Write self-contained implementation plan files that a fresh, possibly weaker executor can run without the author's context. Splits decided work into PR-sized, independently-landable plans — intent-based (sketches over implementations), with verification gates, STOP conditions, drift checks, and maintenance notes.

Includes templates for individual plans, the effort-level index (status table, dependency notes, bounded reconciliation log), and design-fork memos — the round-trip where an executor hits an unanticipated fork, hands back a description of the state and desired outcome, and the planner answers with a researched, evidence-backed verdict.

## Acknowledgements

This collection includes and adapts work from several sources.

### ai-writing-tropes

AI writing tropes skill from [Xe/site](https://github.com/Xe/site) (zlib, Christine Dodrill). Content sourced from [tropes.fyi](https://tropes.fyi).

### crafting-effective-readmes

Reference materials include:

- [Art of README](https://github.com/hackergrrl/art-of-readme) by Kira (CC BY 2.0)
- [Standard README](https://github.com/RichardLitt/standard-readme) by Richard Littauer (MIT)
- [Make a README](https://github.com/dguo/make-a-readme) by Danny Guo (MIT)

### diataxis

Reference content derived from the [Diátaxis documentation framework](https://diataxis.fr/) ([repo](https://github.com/evildmp/diataxis-documentation-framework)) by [Daniele Procida](https://vurt.eu) ([CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)).

### frontend-design-principles

Adapted from:

- The [frontend-design](https://github.com/anthropics/skills/tree/main/frontend-design) skill in [anthropics/skills](https://github.com/anthropics/skills) (Apache 2.0)
- [Dammyjay93/interface-design](https://github.com/Dammyjay93/interface-design) (MIT, Damola Akinleye)
- [Teaching Claude to Design Better: Improving Anthropic's Frontend Design Skill](https://www.justinwetch.com/blog/improvingclaudefrontend) ([relevant PR](https://github.com/anthropics/skills/pull/210)) by Justin Wetch

### grug-brained-dev

Inspired by [The Grug Brained Developer](https://grugbrain.dev/), a funny-looking but painfully useful guide to fighting complexity demons with smol brain humility, plain names, saying no, delayed factoring, real cut points, small refactors, and suspicion of premature abstraction. This adaptation aims to make coding agents inhabit the Grug posture, not just summarize the article.

### improve

Adapts the advisor workflow and audit playbook from [shadcn's `improve` skill](https://github.com/shadcn/improve) (MIT), with the domain-docs/ADR awareness and module-depth framing (deletion test, shallow vs. deep modules) of Matt Pocock's `improve-codebase-architecture`. The depth vocabulary traces to John Ousterhout's *A Philosophy of Software Design*.

### improving-prompts

Includes best practices from [Anthropic's Claude documentation](https://docs.anthropic.com).

### jj

Synthesizes guidance from:

- [Jujutsu](https://github.com/jj-vcs/jj) — official documentation used for reference material (Apache-2.0)
- [Steve Klabnik's Jujutsu Tutorial](https://github.com/steveklabnik/jujutsu-tutorial) — narrative tutorial providing mental model and conceptual grounding
- [jujutsu-skill](https://github.com/danverbraganza/jujutsu-skill) by Dan Verbraganza — agent-specific workflow patterns and environment rules (MIT)
- [dot-claude jj-workflow](https://github.com/TrevorS/dot-claude) by TrevorS — concise AI-focused daily workflow patterns (ISC)
- [agent-skills working-with-jj](https://github.com/YPares/agent-skills) by Yves Parès — version-aware command syntax and `JJ_CONFIG` agent configuration pattern (MIT)
- [jjtask](https://github.com/Coobaha/jjtask) by Alexander Ryzhikov — anti-patterns and gotchas for agent use (MIT)
- [sgai](https://github.com/sandgardenhq/sgai) by Sandgarden — Git-to-jj command mapping table (modified MIT)
- [dotfiles jj-history-investigation](https://github.com/edmundmiller/dotfiles) by Edmund Miller — history investigation techniques (MIT)

### reducing-entropy

Reference mindsets summarize and cite works by Rich Hickey, Simon Willison, Luke Plant, Jacob Kaplan-Moss, and others. See individual reference files for source links.

### rust

References and adapts guidance from:

- [Actors with Tokio](https://ryhl.io/blog/actors-with-tokio/) by Alice Ryhl
- [Aiming for correctness with types](https://fasterthanli.me/articles/aiming-for-correctness-with-types) by Amos Wenger (fasterthanlime)
- [Async: What is blocking?](https://ryhl.io/blog/async-what-is-blocking/) by Alice Ryhl
- [Common Rust Lifetime Misconceptions](https://github.com/pretzelhammer/rust-blog/blob/master/posts/common-rust-lifetime-misconceptions.md) by pretzelhammer (CC BY-SA 4.0)
- [Rust Atomics and Locks](https://marabos.nl/atomics/) by Mara Bos
- [Effective Rust](https://www.lurklurk.org/effective-rust/) by David Drysdale (CC BY 4.0)
- [Error Handling Survey](https://blog.yoshuawuyts.com/error-handling-survey/) by Yoshua Wuyts
- [Error Handling in Rust](https://blog.burntsushi.net/rust-error-handling/) by Andrew Gallant (BurntSushi)
- [Error handling in Rust](https://www.lpalmieri.com/posts/error-handling-rust/) by Luca Palmieri
- [Making Illegal States Unrepresentable](https://corrode.dev/blog/illegal-state/) by corrode.dev
- [Modular Errors in Rust](https://sabrinajewson.org/blog/errors) by Sabrina Jewson
- [Parse, Don't Validate](https://lexi-lambda.github.io/blog/2019/11/05/parse-don-t-validate/) by Alexis King
- [Pin](https://without.boats/blog/pin/) by Without Boats
- [Rust API Guidelines](https://github.com/rust-lang/api-guidelines) (MIT OR Apache-2.0)
- [Rust Design Patterns](https://github.com/rust-unofficial/patterns) (MPL-2.0)
- [The Rust Programming Language](https://github.com/rust-lang/book) (MIT OR Apache-2.0)
- [The Rust Reference](https://github.com/rust-lang/reference) (MIT OR Apache-2.0)
- [The Rustonomicon](https://github.com/rust-lang/nomicon) (MIT OR Apache-2.0)
- [The Typestate Pattern in Rust](https://cliffle.com/blog/rust-typestate/) by Cliff L. Biffle

### salsa

References code and patterns from:

- [BAML](https://github.com/BoundaryML/baml) (Apache-2.0)
- [Cairo](https://github.com/starkware-libs/cairo) (Apache-2.0)
- [Fe](https://github.com/argotorg/fe) (Apache-2.0)
- [Mun](https://github.com/mun-lang/mun) (MIT OR Apache-2.0)
- [Salsa](https://github.com/salsa-rs/salsa) (MIT OR Apache-2.0)
- [WGSL Analyzer](https://github.com/wgsl-analyzer/wgsl-analyzer) (MIT OR Apache-2.0)
- [django-language-server](https://github.com/joshuadavidthomas/django-language-server) (Apache-2.0)
- [rust-analyzer](https://github.com/rust-lang/rust-analyzer) (MIT OR Apache-2.0)
- [stc](https://github.com/dudykr/stc) (Apache-2.0)
- [ty](https://github.com/astral-sh/ty) / [Ruff monorepo](https://github.com/astral-sh/ruff) (MIT)

### researching-codebases

Adapted from the [commands and agents](https://github.com/humanlayer/humanlayer/tree/main/.claude) in HumanLayer (Apache 2.0).

### skill-authoring

Synthesizes skill-authoring guidance from:

- [Agent Skills specification](https://agentskills.io/specification) and docs
- [anthropics/skills](https://github.com/anthropics/skills) `skill-creator` (Apache 2.0)
- [EveryInc/compound-engineering-plugin](https://github.com/EveryInc/compound-engineering-plugin) `create-agent-skills`
- [obra/superpowers](https://github.com/obra/superpowers) `writing-skills`
- [pproenca/dot-skills](https://github.com/pproenca/dot-skills) `skill-authoring`
- [pytorch/pytorch](https://github.com/pytorch/pytorch) `.claude/skills/skill-writer`
- [getsentry/skills](https://github.com/getsentry/skills) `skill-writer` (Apache 2.0)
- David Cramer's [Skill Synthesis](https://cra.mr/skill-synthesis)

See [`skill-authoring/README.md`](skill-authoring/README.md) for the detailed source inventory and synthesis decisions.

### svelte5 and sveltekit

Reference and guidance adapted from:

- [svelte-claude-skills](https://github.com/spences10/svelte-claude-skills) by Scott Spence (MIT)
- [Svelte documentation](https://svelte.dev/docs) (MIT)
- [Modern SvelteKit Tutorial](https://github.com/stolinski/Modern-Svelte-Kit-Tutorial) by Scott Tolinski
- [Svelte Stores Streams Effect](https://github.com/bmdavis419/Svelte-Stores-Streams-Effect) by Ben Davis ([video](https://www.youtube.com/watch?v=kMBDsyozllk))

### writing-clearly-and-concisely

Adapted from [obra/the-elements-of-style](https://github.com/obra/the-elements-of-style). The 1918 *Elements of Style* text is in the public domain via [Project Gutenberg](https://www.gutenberg.org/files/37134/37134-h/37134-h.htm). The AI writing patterns guide is adapted from Wikipedia's [Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing) ([CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)).

### writing-error-messages

Synthesizes product writing and UX guidance from [Wix UX](https://wix-ux.com/when-life-gives-you-lemons-write-better-error-messages-46c5223e1a2f), [GOV.UK Design System](https://design-system.service.gov.uk/components/error-message/), [Nielsen Norman Group](https://www.nngroup.com/articles/error-message-guidelines/), [Atlassian Design](https://atlassian.design/content/designing-messages/writing-error-messages), [Microsoft Learn](https://learn.microsoft.com/en-us/windows/apps/design/style/writing-style), [Shopify Polaris](https://polaris.shopify.com/content/error-messages), and [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet).

### writing-plans

Adapts the handoff plan template and advisor-for-a-cheaper-executor framing from [shadcn's `improve` skill](https://github.com/shadcn/improve) (MIT), with inspiration from [obra/superpowers](https://github.com/obra/superpowers) `writing-plans` and the planning stages of HumanLayer's research/plan/implement workflow.

## License

Licensed under the MIT license. See the [`LICENSE`](LICENSE) file for more information.
