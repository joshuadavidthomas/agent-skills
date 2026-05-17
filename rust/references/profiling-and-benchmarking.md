# Profiling and Benchmarking (Practical Setup)

Do not optimize blind. Do not benchmark toy code that gets constant-folded. Use release builds, realistic inputs, and tools that produce actionable attribution.

## Baseline rules

- Always profile/benchmark `--release` unless the question is specifically about debug build latency.
- Make one change at a time and record before/after.
- Prefer sampling profilers for “what is hot?” and allocation profilers for “why is malloc hot?”.

## Release builds with profiling-friendly debug info

Enable line-level debug info in release builds so profilers can attribute work to source lines.

```toml
# Cargo.toml (workspace root)
[profile.release]
debug = "line-tables-only"
```

**Authority:** Rust Performance Book “Profiling” (Debug Info).

## Frame pointers (better stacks)

Some profilers get better stack traces with frame pointers enabled.

```bash
RUSTFLAGS="-C force-frame-pointers=yes" cargo build --release
```

**Authority:** Rust Performance Book “Profiling” (Frame pointers).

## Common profiler choices (pick based on the question)

- CPU hot paths: `perf` (Linux), Instruments (macOS), VTune (multi-platform), `samply` (multi-platform).
- Flame graphs: `cargo flamegraph` (perf/DTrace under the hood).
- Allocation hot spots: Valgrind DHAT (Linux/Unix), heaptrack/bytehound (Linux), dhat-rs (all platforms, requires code changes).
- Instruction counts / cache simulation: Callgrind/Cachegrind (Valgrind).

**Authority:** Rust Performance Book “Profiling”.

## A minimal workflow that works

1. Make sure you can reproduce the slow path with a stable command.
2. Confirm the regression exists in `--release`.
3. Collect a CPU profile and identify the top hot functions.
4. If the hot functions include `malloc/free/memcpy`, collect an allocation profile.
5. Apply one high-impact refactor (algorithm/data structure/allocation).
6. Re-run the same benchmark and record the delta.

## Benchmarking discipline

### Avoid optimizer lies

If your benchmark uses fixed small inputs, LLVM can constant-fold and you will measure “0 ns/iter”. Use `std::hint::black_box` and realistic data sizes.

```rust
use std::hint::black_box;

fn bench_target(xs: &[u64]) -> u64 {
    xs.iter().copied().sum()
}

fn run() {
    let xs = (0..10_000).collect::<Vec<_>>();
    let out = bench_target(black_box(&xs));
    black_box(out);
}
```

**Authority:** Effective Rust Item 30 (benchmarks and `black_box`).

### Prefer Criterion for stable, usable benchmarks

- Use Criterion for statistically robust benchmarking on stable Rust.
- Use `iai-callgrind` when you want instruction-level measurement and cache behavior (Linux/Unix).

See [testing.md](../testing.md) for the broader testing/benchmarking tool survey.

## Clippy for performance

Run clippy on release code and treat the “Perf” group suggestions as default refactors.

```bash
cargo clippy --release
```

**Authority:** Rust Performance Book “Linting”; Effective Rust Item 29.
