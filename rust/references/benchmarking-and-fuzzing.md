# Benchmarking and Fuzzing

## Criterion: Statistical Benchmarking

Criterion provides statistical analysis of benchmark results, detects performance regressions between runs, and generates HTML reports. It replaces the unstable `#[bench]` attribute with a stable, more rigorous alternative.

### Setup

```toml
# Cargo.toml
[dev-dependencies]
criterion = { version = "0.5", features = ["html_reports"] }

[[bench]]
name = "my_benchmark"
harness = false   # REQUIRED — disables the default test harness
```

Create the benchmark file at `benches/my_benchmark.rs`.

### Basic Benchmark

```rust
use criterion::{criterion_group, criterion_main, Criterion};
use std::hint::black_box;
use my_crate::fibonacci;

fn bench_fibonacci(c: &mut Criterion) {
    c.bench_function("fib 20", |b| {
        b.iter(|| fibonacci(black_box(20)))
    });
}

criterion_group!(benches, bench_fibonacci);
criterion_main!(benches);
```

**`black_box()`** — prevents the compiler from optimizing away the computation. Wrap both inputs and outputs. Without it, the compiler may constant-fold the result or eliminate dead code, producing meaningless measurements.

```rust
// WRONG — compiler may optimize away entirely
b.iter(|| fibonacci(20));

// RIGHT — input is opaque to the optimizer
b.iter(|| fibonacci(black_box(20)));

// ALSO RIGHT — prevent dead-code elimination of the result
b.iter(|| black_box(fibonacci(black_box(20))));
```

### Benchmarking with Inputs

Compare performance across different input sizes:

```rust
use criterion::{criterion_group, criterion_main, BenchmarkId, Criterion};

fn bench_sort(c: &mut Criterion) {
    let mut group = c.benchmark_group("sort");

    for size in [100, 1000, 10_000, 100_000] {
        group.bench_with_input(
            BenchmarkId::from_parameter(size),
            &size,
            |b, &size| {
                b.iter(|| {
                    let mut v: Vec<i32> = (0..size).rev().collect();
                    v.sort();
                    black_box(v);
                });
            },
        );
    }

    group.finish();
}

criterion_group!(benches, bench_sort);
criterion_main!(benches);
```

### Comparing Functions

Benchmark multiple implementations of the same operation:

```rust
fn bench_parsers(c: &mut Criterion) {
    let mut group = c.benchmark_group("parse_json");
    let input = include_str!("../fixtures/large.json");

    group.bench_function("serde_json", |b| {
        b.iter(|| serde_json::from_str::<Value>(black_box(input)).unwrap())
    });

    group.bench_function("simd_json", |b| {
        b.iter(|| {
            let mut data = input.to_owned();
            simd_json::to_borrowed_value(unsafe { data.as_bytes_mut() }).unwrap()
        })
    });

    group.finish();
}
```

### Async Benchmarks

Benchmark async code with the `async_tokio` feature:

```toml
criterion = { version = "0.5", features = ["html_reports", "async_tokio"] }
```

```rust
use criterion::async_executor::AsyncExecutor;

fn bench_async(c: &mut Criterion) {
    let rt = tokio::runtime::Runtime::new().unwrap();

    c.bench_function("async_fetch", |b| {
        b.to_async(&rt).iter(|| async {
            black_box(fetch_data().await)
        })
    });
}
```

### Running and Interpreting Results

```bash
cargo bench                        # Run all benchmarks
cargo bench -- "sort"              # Run benchmarks matching "sort"
cargo bench -- --save-baseline v1  # Save baseline for comparison
cargo bench -- --baseline v1       # Compare against saved baseline
```

Output includes:
- Mean execution time with confidence interval
- Statistical change detection (improved/regressed/no change)
- Outlier analysis (high mild, high severe)

HTML reports are saved to `target/criterion/`.

### Configuration

```rust
fn bench_configured(c: &mut Criterion) {
    let mut group = c.benchmark_group("my_group");
    group.sample_size(500);            // More samples (default: 100)
    group.measurement_time(Duration::from_secs(10)); // Longer measurement
    group.warm_up_time(Duration::from_secs(3));      // Longer warmup
    group.significance_level(0.01);    // Stricter regression detection

    group.bench_function("test", |b| b.iter(|| /* ... */));
    group.finish();
}
```

## divan: Lightweight Alternative

divan is a newer benchmarking framework with simpler setup. It uses attributes instead of macros and requires less boilerplate.

### Setup

```toml
[dev-dependencies]
divan = "0.1"

[[bench]]
name = "my_benchmark"
harness = false
```

### Basic Usage

```rust
fn main() {
    divan::main();
}

#[divan::bench]
fn bench_sort() -> Vec<i32> {
    let mut v: Vec<i32> = (0..1000).rev().collect();
    v.sort();
    v  // return value acts as black_box
}

#[divan::bench(args = [100, 1000, 10_000])]
fn bench_sort_sizes(n: usize) -> Vec<i32> {
    let mut v: Vec<i32> = (0..n).rev().collect();
    v.sort();
    v
}
```

**divan vs criterion:**
- divan: simpler API, attribute macros, return-value-as-black-box, less config
- criterion: statistical analysis, HTML reports, baseline comparisons, async support
- Use criterion for serious regression tracking; divan for quick measurements

## cargo-fuzz: Fuzz Testing

Fuzz testing feeds pseudo-random data to your code to discover panics, crashes, and undefined behavior. It's most valuable for code that processes untrusted input: parsers, deserializers, protocol handlers, codecs.

### Setup

```bash
cargo install cargo-fuzz
cargo fuzz init                    # Creates fuzz/ directory
cargo fuzz add parse_input         # Adds a new fuzz target
```

This creates:

```text
fuzz/
├── Cargo.toml
└── fuzz_targets/
    └── parse_input.rs
```

### Writing a Fuzz Target

```rust
// fuzz/fuzz_targets/parse_input.rs
#![no_main]
use libfuzzer_sys::fuzz_target;

fuzz_target!(|data: &[u8]| {
    if let Ok(s) = std::str::from_utf8(data) {
        // This should never panic, regardless of input
        let _ = my_crate::parse(s);
    }
});
```

**The contract:** The fuzz target should not panic for any input. If it does, the fuzzer saves the crashing input to `fuzz/artifacts/` for reproduction.

### Structure-Aware Fuzzing

Generate structured inputs instead of raw bytes using `Arbitrary`:

```toml
# fuzz/Cargo.toml
[dependencies]
arbitrary = { version = "1", features = ["derive"] }
```

```rust
use arbitrary::Arbitrary;

#[derive(Debug, Arbitrary)]
struct FuzzInput {
    name: String,
    age: u8,
    tags: Vec<String>,
}

fuzz_target!(|input: FuzzInput| {
    let _ = my_crate::process_user(input.name, input.age, input.tags);
});
```

Structure-aware fuzzing is more effective than raw bytes — the fuzzer explores meaningful input space instead of wasting cycles on unparseable noise.

### Running the Fuzzer

```bash
cargo +nightly fuzz run parse_input              # Run until stopped (Ctrl+C)
cargo +nightly fuzz run parse_input -- -max_len=1024  # Limit input size
cargo +nightly fuzz run parse_input -- -runs=10000    # Fixed number of runs
```

**Requires nightly** due to `libfuzzer_sys` instrumentation.

### Reproducing Crashes

```bash
# Crashes saved to fuzz/artifacts/parse_input/
cargo +nightly fuzz run parse_input fuzz/artifacts/parse_input/crash-abc123
```

### Fuzz Corpus Management

The fuzzer builds a corpus of interesting inputs in `fuzz/corpus/<target>/`. This corpus improves over time. Commit it to version control for regression testing:

```bash
# Run the fuzzer (builds corpus)
cargo +nightly fuzz run parse_input

# Later, replay the corpus as a regression suite
cargo +nightly fuzz run parse_input fuzz/corpus/parse_input/
```

### Coverage Analysis

Check which code paths the fuzzer has explored:

```bash
cargo +nightly fuzz coverage parse_input
```

Generates coverage data you can view with `llvm-cov`.

### CI Integration

Run the fuzzer for a fixed time in CI to catch regressions:

```bash
cargo +nightly fuzz run parse_input -- -max_total_time=60  # 60 seconds
```

### What to Fuzz

Prioritize code that processes untrusted input:

| Component | Why fuzz it |
|-----------|-------------|
| Parsers (JSON, YAML, custom formats) | Malformed input shouldn't crash |
| Deserializers (serde impls) | All byte sequences should be handled |
| Protocol handlers (HTTP, websocket) | Adversarial messages shouldn't panic |
| Compression/decompression | Corrupted data shouldn't cause UB |
| Crypto operations | Edge cases in padding, key sizes |
| Image/media decoders | Malformed files shouldn't crash |

**Authority:** Rust Fuzz Book; cargo-fuzz docs; libFuzzer (LLVM project). Fuzzing has found thousands of real bugs in production Rust crates — see the [Trophy Case](https://github.com/rust-fuzz/trophy-case).
