# Application Design

Guidance for dashboards, admin interfaces, internal tools, and SaaS products. The philosophy: **precision and restraint in service of function.**

Users live in these interfaces. They return daily, learn the patterns, build muscle memory. The design should disappear — enabling work without friction or distraction.


## Design Directions

Pick a direction that fits the product. Or blend two. But commit.

| Direction | Feel | Best For |
|-----------|------|----------|
| **Precision & Density** | Tight, technical, monochrome | Developer tools, admin dashboards |
| **Warmth & Approachability** | Generous spacing, soft shadows | Collaborative tools, consumer apps |
| **Sophistication & Trust** | Cool tones, layered depth | Finance, enterprise B2B |
| **Boldness & Clarity** | High contrast, dramatic space | Modern dashboards, data-heavy apps |
| **Utility & Function** | Muted, functional density | GitHub-style tools |
| **Data & Analysis** | Chart-optimized, numbers-first | Analytics, BI tools |


## Color Foundation

Don't default. Consider the product:

- **Warm foundations** (creams, warm grays) — approachable, comfortable, human
- **Cool foundations** (slate, blue-gray) — professional, trustworthy, serious
- **Pure neutrals** (true grays, black/white) — minimal, bold, technical
- **Tinted foundations** (slight color cast) — distinctive, memorable, branded

**Light or dark?** Dark feels technical, focused, premium. Light feels open, approachable, clean. Choose based on context, not preference.

**One accent color for interactive elements.** Pick one that means something: blue for trust, green for growth, orange for energy, violet for creativity. Semantic colors (error red, success green, warning amber) are separate — they communicate state, not brand.

### Color for Meaning Only

Gray builds structure. Color only appears when it communicates: status, action, error, success. Decorative color is noise.

Ask whether each use of color is earning its place. Score bars don't need color-coding by performance — a single muted color works. Grade badges don't need traffic-light colors — typography can do the hierarchy work.

Look at how GitHub renders tables and lists: almost entirely monochrome, with color reserved for status indicators and actionable elements.


## Layout Approach

The content should drive the layout:

- **Dense grids** for information-heavy interfaces where users scan and compare
- **Generous spacing** for focused tasks where users need to concentrate
- **Sidebar navigation** for multi-section apps with many destinations
- **Top navigation** for simpler tools with fewer sections
- **Split panels** for list-detail patterns where context matters


## Navigation Context

Screens need grounding. A data table floating in space feels like a component demo, not a product. Include:

- **Navigation** — sidebar or top nav showing where you are in the app
- **Location indicator** — breadcrumbs, page title, or active nav state
- **User context** — who's logged in, what workspace/organization

When building sidebars, consider using the same background as the main content area. Linear, Supabase, and Vercel use a subtle border for separation rather than different background colors. This reduces visual weight and feels more unified.


## Typography Choices

Typography sets tone:

- **System fonts** — fast, native, invisible (good for utility-focused products)
- **Geometric sans** (Geist, Inter) — modern, clean, technical
- **Humanist sans** (SF Pro, Satoshi) — warmer, more approachable
- **Monospace influence** — technical, developer-focused, data-heavy

For application UI, readability and function matter more than expression. Save the interesting fonts for marketing.


## Card Layouts

Monotonous card layouts are lazy design. A metric card doesn't have to look like a plan card doesn't have to look like a settings card.

Design each card's internal structure for its specific content — sparklines for metrics, avatar stacks for teams, progress rings for completion, two-column splits for comparison.

Keep the surface treatment consistent: same border weight, shadow depth, corner radius, padding scale. Cohesion comes from the container chrome, not from forcing every card into the same layout template.


## Animation in Applications

Restrained. Functional. Never distracting.

- 150ms for micro-interactions (hover states, button presses)
- 200ms for transitions (panel opens, tab switches)
- Minimal spring physics — subtle easing is fine, but bouncy effects feel unserious
- No decorative animation — everything should communicate state change

Animation should feel like the interface responding, not performing.


## Application Anti-Patterns

Beyond the universal anti-patterns:

- **Decorative gradients** — gradients for visual interest rather than meaning
- **Excessive white space** — generous spacing is good; wasted space is not
- **Competing visual hierarchies** — one thing should be primary
- **Fancy fonts in UI** — save expression for marketing
- **Animation for delight** — in work tools, animation is for feedback
- **Color without meaning** — every colored element should communicate something
- **Missing interaction states** — hover, focus, disabled, loading, error
- **Large radius on small elements**
- **Pure white cards on colored backgrounds**
- **Gradients and color for decoration** — color should mean something


## The Standard

Application interfaces should feel like precision instruments. Every element considered, nothing decorative, the design invisible until you notice how well everything works.

Think Linear, Notion, Stripe Dashboard — interfaces that feel inevitable, like there was no other way they could have been designed.
