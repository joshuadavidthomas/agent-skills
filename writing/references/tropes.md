# The Trope Catalog

The specific ready-made phrases and structures that mark machine writing. This is the modern edition of Orwell's catalog of tricks "by means of which the work of prose construction is habitually dodged": his dying metaphors are today's "tapestry" and "landscape"; his verbal false limbs are "serves as" and "plays a role in"; his pretentious diction is "delve" and "leverage"; his meaningless words are "robust" and "seamless".

Any single trope used once might be fine. The problem is density: multiple tropes together, or one trope repeating through a piece. When you spot one, the fix is never just deletion — ask what you were actually trying to say and write that.

## Word Choice

### "Delve" and Friends

Overused AI vocabulary. Also: "certainly", "utilize", "leverage" (as a verb), "robust", "streamline", "harness", "foster", "multifaceted".

Bad:
- "Let's delve into the details..."
- "We certainly need to leverage these robust frameworks..."

Fix: Use plain words. "Look at", "use", "strong", "simplify".

### "Tapestry" and "Landscape"

Ornate nouns where simple words work. "Tapestry" for anything interconnected, "landscape" for any field. Also: "paradigm", "synergy", "ecosystem", "realm".

Bad:
- "The rich tapestry of human experience..."
- "Navigating the complex landscape of modern AI..."

Fix: Say what you mean. "The field of AI", or just "AI".

### The "Serves As" Dodge

Replacing "is" with pompous alternatives. Also: "stands as", "marks", "represents". The repetition penalty pushes models away from basic copulas; push back.

Bad:
- "The building serves as a reminder of the city's heritage."
- "The station marks a pivotal moment in the evolution of regional transit."

Fix: Use "is". Shorter, clearer, better.

### Undue Significance

Puffing up the subject by asserting its importance to something broader. Watch for: "is a testament to", "plays a vital/pivotal/crucial role", "underscores its importance", "reflects broader trends", "enduring legacy", "indelible mark", "deeply rooted", "key turning point". Models attach these to the most mundane facts — etymology, population data, a minor product feature.

Bad:
- "This etymology highlights the enduring legacy of the community's resistance and the transformative power of unity in shaping its identity."
- "The founding of Idescat represented a significant shift toward regional statistical independence."

Fix: State the fact. If it genuinely matters to something broader, show the connection with evidence instead of asserting it.

### "Quietly" and Other Magic Adverbs

Adverbs deployed to make mundane descriptions feel significant. Also: "deeply", "fundamentally", "remarkably", "arguably".

Bad:
- "quietly orchestrating workflows, decisions, and interactions"
- "a quiet intelligence behind it"

Fix: Remove the adverb. If the thing is important, the facts will show it.

### Elegant Variation

Cycling through synonyms to avoid repeating a name: "the protagonist", "the key player", "the eponymous character" for one person; "the initiative", "the effort", "the program" for one project. A repetition-penalty artifact. Humans repeat the plain name.

Bad:
- "Vierny supported the artists... Vierny's unwavering support... her commitment culminated in the groundbreaking exhibition..." (each mention escalating in ornament)

Fix: Call the thing by its name every time. Repetition of the right word is not a flaw.

## Sentence Structure

### Negative Parallelism

"It's not X — it's Y." The single most identified AI tell. Frames every point as a surprising reframe. Includes the causal variant "not because X, but because Y".

Bad:
- "It's not bold. It's backwards."
- "Half the bugs you chase aren't in your code. They're in your head."

Fix: State the actual point directly. "This is backwards." Done.

### "Not X. Not Y. Just Z."

The dramatic countdown: negating two or more things before revealing the point.

Bad:
- "Not a bug. Not a feature. A fundamental design flaw."
- "Not ten. Not fifty. Five hundred and twenty-three lint violations."

Fix: Lead with the point. "523 lint violations across 67 files."

### "The X? A Y."

Self-posed rhetorical questions answered immediately, for drama nobody asked for.

Bad:
- "The result? Devastating."
- "The worst part? Nobody saw it coming."

Fix: Merge into one statement, or better, show why it was devastating.

### Anaphora Abuse

The same sentence opening repeated in quick succession.

Bad:
- "They assume that users will pay... They assume that developers will build... They assume that ecosystems will emerge..."

Fix: Vary the openings. Combine related points. Cut the weak ones.

### Tricolon Abuse

The rule of three, everywhere. One tricolon is elegant; three back-to-back is a pattern-recognition failure.

Bad:
- "Products impress people; platforms empower them. Products solve problems; platforms create worlds. Products scale linearly; platforms scale exponentially."

Fix: Use two items, or five. Break the rhythm. Not everything has three beats.

### Filler Transitions and Editorializing Disclaimers

Phrases that signal nothing: "It's worth noting", "Importantly", "Interestingly", "Notably". And the didactic cousin: "it's important to note/remember/consider", telling the reader what to think about a point instead of making it.

Bad:
- "It's worth noting that this approach has limitations."
- "It's important to remember that behavior may vary across platforms."

Fix: Delete the filler and state the point. "This approach has limitations."

### Superficial "-ing" Analyses

A present-participle tail tacked onto a sentence to inject shallow significance: "highlighting its importance", "reflecting broader trends", "contributing to...".

Bad:
- "contributing to the region's rich cultural heritage"
- "underscoring its role as a dynamic hub of activity and culture"

Fix: If the analysis matters, give it its own sentence with actual substance. If not, cut it.

### False Ranges

"From X to Y" where X and Y sit on no real scale — a fancy way to list two loosely related things.

Bad:
- "From innovation to implementation to cultural transformation."

Fix: Just list the things, or pick the one that matters.

### Gerund Fragment Litany

A claim followed by a stream of verbless fragments that restate it.

Bad:
- "Fixing small bugs. Writing straightforward features. Implementing well-defined tickets."

Fix: If examples help, write a real sentence. Otherwise cut — the claim already landed.

## Paragraph Structure

### Short Punchy Fragments

Very short sentences or fragments as standalone paragraphs for manufactured emphasis. No one writes first drafts this way.

Bad:
- "He published this. Openly. In a book. As a priest."
- "Platforms do."

Fix: Combine related thoughts into real paragraphs. Trust readers to follow compound sentences.

### Listicle in a Trench Coat

Numbered points dressed as prose: "The first wall is... The second wall is... The third wall is..."

Bad:
- "The second takeaway is that... The third takeaway is that..."

Fix: Write prose that actually flows between ideas, or admit it's a list and format it as one.

## Tone

### False Suspense

"Here's the kicker", "Here's the thing", "Here's where it gets interesting" — a windup before an unremarkable point.

Fix: Drop the windup. State the point.

### The Patronizing Analogy

"Think of it as..." — teacher mode by default, often producing an analogy less clear than the concept.

Fix: Explain the actual thing. If a metaphor genuinely helps, use it without the framing.

### "Imagine a World Where..."

The invitation to futurism, followed by wonderful things that happen if the reader agrees with the premise.

Fix: Describe what exists or what you are proposing. Skip the daydream.

### False Vulnerability

Performative self-awareness: "And yes, since we're being honest...", "This is not a rant; it's a diagnosis." Real vulnerability is specific and uncomfortable; this is polished and risk-free.

Fix: If you have a bias, show it through your arguments. Don't announce it for credibility.

### "The Truth Is Simple"

Asserting that a point is obvious, clear, or simple instead of proving it. If you have to say your point is clear, it isn't.

Bad:
- "History is unambiguous on this point."

Fix: Present the evidence. Let the reader decide.

### Stakes Inflation

Every argument elevated to world-historical significance. A post about API pricing becomes the fate of computing.

Bad:
- "This will fundamentally reshape how we think about everything."

Fix: Match language to actual stakes. Most things are incremental improvements, and that's fine.

### The Pedagogical Voice

"Let's break this down", "Let's unpack this", "Let's dive in" — hand-holding for expert readers.

Fix: Present the analysis. Readers don't need permission to follow along.

### Vague Attributions

Claims assigned to unnamed authorities: "experts argue", "observers note", "industry reports suggest". Often inflating one person's view into a consensus.

Fix: Name the source or drop the attribution. "A 2024 Gartner report found..." or just state the claim.

### Invented Concept Labels

Abstract problem-nouns (paradox, trap, creep, divide, inversion) appended to domain words and used as if established terms: "the supervision paradox", "workload creep". Naming a thing to skip arguing for it.

Fix: Describe the phenomenon. If the label isn't established in the field, don't pretend it is.

### Chat Leakage

Correspondence artifacts in prose meant to stand alone: "I hope this helps", "Certainly!", "You're absolutely right", "Would you like me to...", "let me know if...".

Fix: Deliverable prose has no chat frame. Cut every trace of the conversation that produced it.

## Formatting

### Em-Dash Addiction

A human might use two or three per piece; a model will use twenty.

Fix: Commas, parentheses, or separate sentences. Save the em dash for the one place it earns its keep.

### Bold-First Bullets

Every list item opening with a bolded phrase. Almost nobody formats lists this way by hand.

Bad:
- "**Security**: Environment-based configuration with..."

Fix: Write list items as sentences. If the list needs headings, use headings.

### Unicode Decoration

Arrows, smart quotes, and characters no one types. "Input → Processing → Output".

Fix: Use `->` or write "leads to". Straight quotes.

### Notation in Prose

Shorthand doing a sentence's job: arrow chains ("module name -> File"), hyphen-stacked compounds ("degrade-to-Partial escape-hatch"), bold-label headers carrying the whole argument. The writer's working notes leaking into the deliverable.

Bad:
- "Fix: config -> loader -> cache invalidation"
- "the parse-then-validate-then-normalize pipeline problem"

Fix: Write the actual sentence. "The config change invalidates the loader's cache."

### Title Case Headings

Capitalizing All Main Words In Every Heading, chatbot-style.

Fix: Sentence case, matching the document's existing convention.

### Emoji Decoration

Emojis prefixed to headings and bullets (🧠, 🚨, 🔭) to signal structure or enthusiasm.

Fix: Delete them. Structure comes from the writing.

## Composition

### Fractal Summaries

"What I'll tell you; what I'm telling you; what I just told you" — at every level of the document.

Fix: Trust readers to remember what they just read. Summarize only where the audience genuinely needs it (abstracts, executive summaries).

### The Dead Metaphor

One metaphor beaten across the entire piece, five to ten appearances.

Fix: Use a metaphor once or twice, then let it go. A later reuse should feel like a callback, not a crutch.

### Historical Analogy Stacking

Rapid-fire name-drops of companies or tech revolutions to build false authority: "Apple didn't build Uber. Facebook didn't build Spotify. Stripe didn't build Shopify."

Fix: Pick one example and go deep. One well-analyzed case beats five name-drops.

### One-Point Dilution

A single argument restated ten ways across thousands of words to feel comprehensive.

Fix: State the point. Support it. Move on. A piece with one idea should be short.

### Content Duplication

Whole sections or paragraphs repeated within the same piece — the model losing track of what it wrote.

Fix: Reread what you've written. Cut duplicates.

### The Signposted Conclusion

"In conclusion", "To sum up", "In summary". Competent writing doesn't announce that it's ending.

Fix: Write your final thought. Drop the signpost.

### "Despite These Challenges..."

The rigid formula: acknowledge problems, then immediately dismiss them into an optimistic close. Often a whole "Challenges" or "Future Outlook" section: "Despite its [praise], [subject] faces challenges... Despite these challenges, [subject] continues to thrive."

Fix: If challenges matter, discuss them seriously. If they don't, skip them. Don't use them as a speed bump on the way to optimism.

---

Sources: the trope entries are adapted from the ai-writing-tropes skill in [Xe/site](https://github.com/Xe/site) (zlib, Christine Dodrill; see LICENSE-tropes), sourced from [tropes.fyi](https://tropes.fyi), and from Wikipedia's [Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing) (CC BY-SA 4.0). Both altered here: merged, condensed, and reorganized.
