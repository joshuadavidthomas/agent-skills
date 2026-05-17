
# Salsa Production Patterns: From Simple to Sophisticated

Every Salsa project goes through a "complexity cliff" where the patterns that were approachable and clear in the prototype (Level 1) start to hit performance or memory ceilings as the project scales (Levels 2 & 3).

## Level 1: The Approachable Foundation
*Focus: Developer velocity and correctness.*

In this stage, you follow the "textbook" Salsa patterns. The goal is to get a working incremental system with minimal boilerplate.

- **Patterns:**
    - **`#[salsa::accumulator]`** for all diagnostics.
    - **`#[salsa::tracked]` structs** for every entity (Functions, Classes, Modules).
    - **Flat Database trait** or 1-2 layers of traits.
    - **On-demand execution** — queries run when the user (or LSP) asks.
- **References:**
    - **BAML**: Clean, intuitive use of tracked structs.
    - **django-language-server (early)**: Simplest complete example of a layered trait DB.

## Level 2: The Efficiency Wall
*Focus: Resource management and cache tuning.*

As the project grows to hundreds of files, memory usage and the "keystroke lag" become the primary concerns.

- **Patterns:**
    - **LRU Caching:** Bounding memory by evicting old ASTs/results (`lru=128`).
    - **Durability Tuning:** Marking stable data (stdlib, config) as `HIGH` durability to skip revalidation.
    - **`no_eq` for Whitespace Resilience:** Preventing a single blank line from invalidating the entire downstream query graph.
    - **Position-Independent IR:** Moving away from byte-offsets in intermediate stages to maximize reuse.
- **References:**
    - **rust-analyzer**: The gold standard for LRU tuning and developer-facing performance.

## Level 3: The Massive Scale
*Focus: Architecture refinement and sub-millisecond responsiveness.*

At the scale of millions of lines of code or thousands of recursive types, even standard Salsa overhead must be optimized away.

- **Patterns:**
    - **Return-Value Pyramids:** Replacing accumulators with `Result<T, Vec<Diag>>` to enable "Early Cutoff."
    - **Interned IDs ("No Tracked Structs"):** Using `#[salsa::interned]` IDs for everything to reduce per-struct overhead.
    - **The "Files Side-Table":** Managing file identity in a `DashMap` outside Salsa to scale discovery independently of content.
    - **"Immortal" Revisions:** Using `revisions = usize::MAX` to freeze core language elements.
    - **Snapshot Concurrency:** Using `CloneableDatabase` + `Rayon` for parallel cache priming ("warm-up").
    - **Manual Cancellation:** Injecting `unwind_if_revision_cancelled()` in expensive CPU-bound scans.
- **References:**
    - **ty**: Demonstrates the "zero tracked structs" pattern and massive cycle handling (60+ sites).
    - **Cairo**: Showcases immortal interning, parallel warm-ups, and diagnostic pyramids.

## Maturity Matrix

| Feature | Level 1: Approachable | Level 2: Efficient | Level 3: Massive |
| :--- | :--- | :--- | :--- |
| **Diagnostics** | Accumulators | Accumulators + LRU | Return Pyramids (Early Cutoff) |
| **Entities** | Tracked Structs | Tracked Structs | Interned IDs (Lean) |
| **Memory** | Unbounded | LRU Eviction | Side-Tables + LRU |
| **Identity** | Salsa-owned discovery | Salsa-owned discovery | External Side-Tables (`DashMap`) |
| **Stability** | Default revisions | Backdating (`no_eq`) | "Immortal" Revisions (`usize::MAX`) |
| **Concurrency** | Single-threaded | Single-threaded | Parallel Warm-ups (`Rayon`) |

## How to Manage the Graduation

1.  **Don't over-engineer early.** Start at Level 1. Accumulators and tracked structs are easier to debug and write.
2.  **Monitor the "keystroke cascade."** If adding a space at the top of a file makes the whole LSP lag, move to Level 2 (`no_eq` or position-independent IR).
3.  **Watch the heap.** If memory usage grows linearly with every file opened, implement LRU limits.
4.  **Refactor identity last.** Moving from tracked structs to interned IDs is a major refactor. Only do it if profiling shows the Salsa overhead itself is a bottleneck.

→ For more on specific Level 3 patterns, see [database-architecture.md](database-architecture.md) (side-tables), [memory-management.md](memory-management.md) (immortality), and [accumulators.md](accumulators.md) (diagnostic pyramids).
