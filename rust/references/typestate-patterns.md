# Typestate Implementation Patterns

Deep-dive on typestate: state with data, sealed bounds, fallible transitions, and real-world examples.

## Core Principle

Typestate encodes a state machine in the type system:
- Each state is a distinct type
- Transitions consume the old state and produce the new state
- Invalid transitions don't compile — the method doesn't exist

## Pattern 1: Separate Types per State

The simplest form — each state is a completely separate struct:

```rust
pub struct FileHandle(std::fs::File);
pub struct ClosedFile { path: PathBuf }

impl FileHandle {
    pub fn close(self) -> ClosedFile {
        // self.0 is dropped here
        ClosedFile { path: /* ... */ }
    }

    pub fn read(&mut self, buf: &mut [u8]) -> io::Result<usize> {
        self.0.read(buf)
    }
}

impl ClosedFile {
    pub fn reopen(self) -> io::Result<FileHandle> {
        Ok(FileHandle(std::fs::File::open(&self.path)?))
    }
    // No read() method — can't read a closed file
}
```

**Pros:** Simple, no generics, clear separation.
**Cons:** Code duplication if states share methods. No way to write generic code over "any file state."

## Pattern 2: Generic State Parameter

Use a type parameter to represent state:

```rust
use std::marker::PhantomData;

pub struct Connection<S: ConnectionState> {
    socket: TcpStream,
    _state: PhantomData<S>,
}

// State marker types
pub struct Handshaking;
pub struct Authenticated;
pub struct Closed;

// Trait to bound valid states (optional but recommended)
pub trait ConnectionState {}
impl ConnectionState for Handshaking {}
impl ConnectionState for Authenticated {}
impl ConnectionState for Closed {}
```

**State-specific methods:**
```rust
impl Connection<Handshaking> {
    pub fn authenticate(self, creds: Credentials) -> Result<Connection<Authenticated>, AuthError> {
        // ... perform auth ...
        Ok(Connection {
            socket: self.socket,
            _state: PhantomData,
        })
    }
}

impl Connection<Authenticated> {
    pub fn send(&mut self, msg: &[u8]) -> io::Result<()> {
        self.socket.write_all(msg)
    }

    pub fn disconnect(self) -> Connection<Closed> {
        Connection {
            socket: self.socket,
            _state: PhantomData,
        }
    }
}
```

**Methods available in all states:**
```rust
impl<S: ConnectionState> Connection<S> {
    pub fn peer_addr(&self) -> io::Result<SocketAddr> {
        self.socket.peer_addr()
    }
}
```

**Methods available in a subset of states:**
```rust
pub trait ActiveState: ConnectionState {}
impl ActiveState for Handshaking {}
impl ActiveState for Authenticated {}

impl<S: ActiveState> Connection<S> {
    pub fn is_alive(&self) -> bool {
        // Check if connection is still valid
        true
    }
}
```

## Pattern 3: States with Data

State types can carry state-specific data:

```rust
pub struct Connecting {
    pub attempt: u32,
    pub started_at: Instant,
}

pub struct Connected {
    pub session_id: SessionId,
    pub authenticated_at: Instant,
}

pub struct Disconnected {
    pub reason: DisconnectReason,
}

pub struct Connection<S> {
    config: ConnectionConfig,
    state: S,  // Actual state data, not PhantomData
}

impl Connection<Connecting> {
    pub fn attempt_number(&self) -> u32 {
        self.state.attempt
    }

    pub fn succeed(self, session_id: SessionId) -> Connection<Connected> {
        Connection {
            config: self.config,
            state: Connected {
                session_id,
                authenticated_at: Instant::now(),
            },
        }
    }

    pub fn retry(self) -> Connection<Connecting> {
        Connection {
            config: self.config,
            state: Connecting {
                attempt: self.state.attempt + 1,
                started_at: Instant::now(),
            },
        }
    }
}

impl Connection<Connected> {
    pub fn session_id(&self) -> &SessionId {
        &self.state.session_id
    }
}
```

**Benefit:** State-specific data is only accessible in that state. `session_id()` exists only on `Connection<Connected>`. No Option unwrapping.

## Pattern 4: Sealed State Traits

Prevent external code from defining new states:

```rust
mod private {
    pub trait Sealed {}
}

pub trait ProtocolPhase: private::Sealed {
    fn phase_name() -> &'static str;
}

pub struct Handshake;
pub struct DataTransfer;
pub struct Shutdown;

impl private::Sealed for Handshake {}
impl private::Sealed for DataTransfer {}
impl private::Sealed for Shutdown {}

impl ProtocolPhase for Handshake {
    fn phase_name() -> &'static str { "handshake" }
}
// ... etc for other states
```

**Why seal:** If external code could add states, your state machine guarantees break. Sealing ensures exhaustive knowledge of all states.

## Pattern 5: Fallible Transitions

Transitions that can fail return `Result`:

```rust
impl Connection<Handshaking> {
    pub fn authenticate(self, creds: Credentials)
        -> Result<Connection<Authenticated>, (Connection<Handshaking>, AuthError)>
    {
        match validate_credentials(&creds) {
            Ok(session) => Ok(Connection {
                socket: self.socket,
                state: Authenticated { session },
            }),
            Err(e) => Err((
                Connection {
                    socket: self.socket,
                    state: Handshaking,  // Return to original state
                },
                e
            )),
        }
    }
}
```

**Note:** On failure, we return the original state back to the caller. The connection wasn't consumed — the caller can try again or do something else.

**Alternative:** Return to a different state on failure:

```rust
pub fn authenticate(self, creds: Credentials)
    -> Result<Connection<Authenticated>, Connection<Failed>>
{
    // On error, transition to Failed state instead of returning original
}
```

## Pattern 6: Builder-Typestate Hybrid

Combine builder pattern with typestate for required fields:

```rust
pub struct NoPort;
pub struct NoHost;
pub struct HasPort(u16);
pub struct HasHost(String);

pub struct ServerBuilder<P, H> {
    port: P,
    host: H,
    workers: Option<usize>,
}

impl ServerBuilder<NoPort, NoHost> {
    pub fn new() -> Self {
        ServerBuilder {
            port: NoPort,
            host: NoHost,
            workers: None,
        }
    }
}

impl<H> ServerBuilder<NoPort, H> {
    pub fn port(self, port: u16) -> ServerBuilder<HasPort, H> {
        ServerBuilder {
            port: HasPort(port),
            host: self.host,
            workers: self.workers,
        }
    }
}

impl<P> ServerBuilder<P, NoHost> {
    pub fn host(self, host: impl Into<String>) -> ServerBuilder<P, HasHost> {
        ServerBuilder {
            port: self.port,
            host: HasHost(host.into()),
            workers: self.workers,
        }
    }
}

impl<P, H> ServerBuilder<P, H> {
    pub fn workers(mut self, n: usize) -> Self {
        self.workers = Some(n);
        self
    }
}

// build() only available when both required fields are set
impl ServerBuilder<HasPort, HasHost> {
    pub fn build(self) -> Server {
        Server {
            port: self.port.0,
            host: self.host.0,
            workers: self.workers.unwrap_or(4),
        }
    }
}
```

**Benefit:** `build()` doesn't compile until required fields are set. No runtime checks, no `Option` unwrapping, no panics.

**Tradeoff:** Complex types, harder to read, doesn't scale to many fields. Reserve for APIs where compile-time enforcement is worth the complexity.

## Real-World Examples

### serde::Serializer

Serde's serializer is a typestate machine:

```rust
// Start: Serializer
let seq = serializer.serialize_seq(Some(3))?;  // -> SerializeSeq

// SerializeSeq state
seq.serialize_element(&1)?;
seq.serialize_element(&2)?;
seq.serialize_element(&3)?;
seq.end()?;  // -> terminal, consumes SerializeSeq
```

Can't call `serialize_seq` twice. Can't serialize elements after `end()`. Invalid sequences don't compile.

### std::process::Command

Builder with typestate-like consumption on spawn:

```rust
let mut cmd = Command::new("ls");
cmd.arg("-la");
cmd.arg("/tmp");
let child = cmd.spawn()?;  // spawn() takes &mut self — reusable builder

// But:
let output = cmd.output()?;  // output() also takes &mut self — can call after spawn
```

Command uses `&mut self` for flexibility (same builder, multiple spawns), not consuming typestate. A stricter design would consume on spawn.

### http Request/Response builders

```rust
let request = Request::builder()
    .method("POST")
    .uri("/api/users")
    .header("Content-Type", "application/json")
    .body(Body::from("{}"))?;  // build() consumes builder
```

## When NOT to Use Typestate

**Many states with complex transitions** — If you have 10 states with 30 transitions, the type explosion makes code unreadable. Use a runtime enum.

**States change frequently during maintenance** — Each state change requires updating type signatures throughout the codebase.

**States determined at runtime** — If you don't know the state at compile time (loaded from config, chosen by user), you need runtime dispatch anyway.

**Typestate shines for:**
- Linear protocols (handshake → auth → data → close)
- 2-5 states with clear, well-defined transitions
- APIs where invalid sequences are common mistakes
- Embedded/safety-critical code where compile-time guarantees matter
