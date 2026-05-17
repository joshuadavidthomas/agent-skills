# Designing Error Types in Rust

Source: [mmapped.blog — Designing error types in Rust](https://mmapped.blog/posts/12-rust-error-handling) by Roman Kashitsyn (2022-11-15)

A library-focused guide to error type design. The central principle: **be empathetic to your caller.** Every design decision flows from imagining yourself having to handle the error.

## Library vs Application

Libraries interface other code — they must provide a complete list of error cases callers cannot recover from. Applications interface humans — they resolve issues automatically or explain clearly how to fix them. This guide targets library design.

## Core Design Rules

### Prefer specific enums

Don't use `anyhow::Result` or a project-wide error enum in library APIs. Both facilitate *propagating* errors, not *handling* them. Define a specific enum per function (or tightly related group) so the type system tells callers exactly what can go wrong.

```rust
// NOT THIS — project-wide ball of mud
pub enum ProjectWideError {
    InvalidInput,
    DatabaseConnectionError,
    Unauthorized,
    FileNotFound,
}

// THIS — scoped to the operation
pub enum FrobnicateError {
    InputExceeds(u64),
    CannotFrobnicateOnMondays,
}
```

Distinct error types make testing more specific and enjoyable. The author notes: "I am still looking for Rust code that went overboard with distinct error types."

### Reserve panics for bugs in your code

`panic!` indicates bugs in *your* program, not invalid input from users. Don't rely on `# Panics` documentation — people don't read it. Use the type system to guide callers.

Panics are appropriate for:
- Internal invariant violations (`debug_assert!`)
- Post-conditions (`debug_assert!(tree.balanced())`)
- Inputs that indicate severe caller bugs (out-of-bound indices, broken `Ord` impls)

### Lift input validation (parse, don't validate)

If a function validates inputs *and* does work, extract validation into a dedicated type. This eliminates redundant validation across functions and moves errors closer to where inputs are received.

```rust
// BEFORE — send_mail validates addresses AND sends mail
pub fn send_mail(to: &str, cc: &[&str], body: &str) -> Result<(), SendMailError>

// AFTER — EmailAddress is valid by construction
pub struct EmailAddress(String);

impl std::str::FromStr for EmailAddress {
    type Err = MalformedEmailAddress;
    fn from_str(s: &str) -> Result<Self, Self::Err> { /* … */ }
}

pub fn send_mail(to: &EmailAddress, cc: &[&EmailAddress], body: &str) -> Result<(), SendMailError>
// SendMailError no longer needs a MalformedAddress variant
```

### Implement `std::error::Error`

Always implement the `Error` trait for your error types. Some callers will shove your errors into `Box<dyn Error>` or `anyhow::Result` — let them. Use `thiserror` if the boilerplate is too much.

### Define errors in terms of the problem, not the solution

Don't wrap dependency errors directly — this leaks implementation details:

```rust
// WRONG — tells callers HOW you solve it, not WHAT failed
pub enum FetchTxError {
    IoError(std::io::Error),
    HttpError(http2::Error),
    SerdeError(serde_cbor::Error),
    OpensslError(openssl::ssl::Error),
}
```

Problems with dependency-wrapping errors:
- Low-level errors travel up the stack with minimal context ("IO error: No such file or directory" — which file?)
- Callers must read transitive dependency docs to understand error cases
- Callers must add your transitive dependencies to handle your errors
- Swapping a dependency (openssl → libressl) becomes a breaking change

Instead, express failures in domain terms:

```rust
// RIGHT — tells callers WHAT failed, in domain vocabulary
pub enum FetchTxError {
    ConnectionFailed { url: String, reason: String, cause: Option<std::io::Error> },
    TxNotFound(Txid),
    InvalidEncoding { data: Bytes, error_offset: Option<usize>, error_message: String },
    MalformedPublicKey { key_bytes: Vec<u8>, reason: String },
    SignatureVerificationFailed { txid: Txid, pk: Pubkey, sig: Signature },
}
```

Benefits: callers can make rational recovery decisions (MalformedPublicKey = wrong key from user; SignatureVerificationFailed = possible tampering, try another peer). Dependencies are hidden. Tests are clearer.

### Embed errors, don't wrap them

Take error cases from third-party libraries and flatten them into your own domain-specific variants, deduplicating across dependencies:

```rust
// WRONG — wraps dependency errors, leaks implementation
pub enum VerifySigError {
    EcdsaError { source: ecdsa::Error, context: String },
    BlsError { source: bls12_381_sign::Error, context: String },
}

// RIGHT — embeds and deduplicates across dependencies
pub enum VerifySigError {
    MalformedPublicKey { pk: Bytes, reason: String },
    MalformedSignature { sig: Bytes, reason: String },
    SignatureVerificationFailed { algorithm: Algorithm, pk: Bytes, sig: Bytes, reason: String },
}
```

When wrapping is acceptable:
- `std::io::Error` with enough context (operation + paths) — it's familiar and carries OS error codes
- Converting lower-level errors to strings and attaching to descriptive variants (check for sensitive data leaks)

Why not `Box<dyn Error>` for flexibility?
- If callers need programmatic access, embed the relevant bits instead of forcing downcasts
- Downcasting requires matching semver versions of transitive dependencies
- Boxed errors can't be cloned or serialized (the author's errors often cross process boundaries)

## Key Insight

Most error design problems stem from the same root: **making error cases easy for the code author at the expense of the caller.** The antidote is empathy — imagine yourself handling the error. Could you write robust recovery code? Could you translate it into a message the end user can understand?

## Further Reading (from the post)

### Catch me if you can (Teller, Spiwack, Varoquaux, 2008)

[Paper (PDF via archive.org)](https://web.archive.org/web/20110818020758/http://www.univ-orleans.fr/lifo/Members/David.Teller/publications/ml2008.pdf)

An OCaml research paper demonstrating how to build type-safe, composable error handling using an error monad combined with polymorphic variants. The core problem: ML-style exceptions are untyped (the compiler can't check that all error cases are handled), while heavyweight sum types (one big enum) don't compose across libraries without a "composability nightmare" — you must manually inject disjoint error types into a common super-type.

Their solution uses OCaml's polymorphic variants (lightweight, structurally-typed tags that compose automatically) as the error type parameter of a `Result`-like monad. The compiler infers the complete set of error cases from the code and enforces exhaustive pattern matching — incomplete error handling is a compile-time error. They also demonstrate hierarchical error classes (e.g., "overflow during addition" as a subclass of "overflow") using nested polymorphic variant tags.

**Relevance to Rust:** Rust's `Result<T, E>` with concrete enum error types is the direct descendant of this lineage. Rust doesn't have polymorphic variants, so we use explicit enum types per function — which is exactly the "heavyweight sum type" approach the paper criticizes for not composing. The practical takeaway: Rust's per-function error enums are the right trade-off (explicit > implicit), but be aware of the composition cost. When errors need to cross abstraction boundaries, embed/flatten variants from lower layers rather than wrapping them (the mmapped.blog "embed, don't wrap" rule) — this is the manual version of what polymorphic variants do automatically.

### Error vs. Exception (Haskell Wiki)

[Article](https://wiki.haskell.org/Error_vs._Exception)

Distinguishes two fundamentally different failure modes that are often conflated:

- **Errors** (in Haskell terminology) = programmer bugs. Can be *prevented* by cheap upfront checks (e.g., bounds checking before array access). If they occur, the program's invariants are already violated — recovery is unreliable. The correct response is to terminate (or at minimum, abort the current operation).
- **Exceptions** (in Haskell terminology) = expected but irregular runtime conditions. *Cannot* be prevented by upfront checks alone because the world can change between check and use (e.g., file permissions can change between a permission check and a write). Programs must be *adapted* to handle them.

The article argues that treating errors like exceptions (catching bugs and trying to continue) risks silent data corruption. Conversely, treating exceptions like errors (panicking on file-not-found) makes programs unnecessarily fragile.

**Relevance to Rust:** This maps directly to Rust's `panic!` vs `Result` split:
- `panic!` = errors (bugs, invariant violations) — the Haskell Wiki's "errors"
- `Result<T, E>` = exceptions (expected failures) — the Haskell Wiki's "exceptions"

The key insight for Rust practitioners: the boundary between the two isn't always obvious. The article's heuristic helps — "can this be prevented by a cheap check the caller controls?" If yes, it's a bug (panic/assert). If no (I/O, network, user input, anything involving the external world), it's an expected condition (return `Result`). This reinforces the mmapped.blog rule "reserve panics for bugs in your code."

### Parse, don't validate (Alexis King, 2019)

[Blog post](https://lexi-lambda.github.io/blog/2019/11/05/parse-don-t-validate/)

The theoretical foundation for the mmapped.blog "lift input validation" rule (the `EmailAddress` newtype example). Covered in detail in [type-design.md](../type-design.md).

### The Trouble with Typed Errors (Matt Parsons, 2018)

[Blog post](https://www.parsonsmatt.org/2018/11/03/trouble_with_typed_errors.html)

Argues that monolithic error types (one big enum with every possible error case) are fundamentally dishonest — they claim a function can produce errors it never actually does. If `foo` doesn't do I/O, but the crate-wide `Error` enum includes `FileNotFound`, callers must write dead match arms for impossible cases. Worse, the compiler can't catch it when someone later modifies `foo` to throw a new error — the dead arm silently becomes load-bearing.

Parsons' ideal: **every error type should have a single constructor** (no sum types for errors). Compose them using nested `Either` types or (in Haskell) type class constraints that are order-independent and allow "plucking" individual error cases from a set. His `plucky` library automates this via generic programming.

**Relevance to Rust:** Rust doesn't have the type-level machinery for Parsons' `plucky` approach, but the diagnosis is directly applicable:
- A crate-wide `Error` enum with 15 variants is the exact anti-pattern Parsons describes. Each function claims it can produce all 15 errors — most are lies.
- The Rust-practical solution (from mmapped.blog and [error-handling.md](../error-handling.md)): scope error types to the function or tightly-related group. `ConnectError` for connection functions, `QueryError` for query functions. Each type is honest about its failure modes.
- The trade-off Rust accepts: manual composition at boundaries (converting `ConnectError` into a broader `ServiceError` via `From` or `map_err`). This is more boilerplate than Parsons' Haskell solution, but it's explicit and greppable.
