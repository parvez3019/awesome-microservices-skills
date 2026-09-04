---
name: api-protocols
description: "Choose the right protocol for an interface and use it the way it was designed to be used. Covers REST resource and cache semantics, GraphQL schema design with N+1 batching, depth and complexity limits and persisted queries, gRPC service and message design with streaming and deadlines, WebSockets and Server-Sent Events for push with reconnection, heartbeats and backpressure, and the selection criteria between them. Use when starting a new interface, adding a subscription or stream, exposing an internal service, or when the user says 'REST', 'GraphQL', 'gRPC', 'WebSocket', 'SSE', 'streaming', 'real time', or 'which protocol'. This skill governs protocol choice and protocol-specific craft — contract shape, versioning and error semantics belong to api-contracts."
license: MIT
---

# API Protocols

Most protocol arguments are really arguments about defaults. REST is right until a client needs
nine round trips to render a screen. GraphQL is right until you discover every field is now a
potential N+1 and nobody can cache anything. gRPC is right until a browser needs to call it. A
WebSocket is right until you realise you have built a stateful service and nobody planned for
reconnection.

Pick from the interaction shape, not from familiarity — then use the protocol properly, because
each one has a small set of mistakes that everybody makes once.

## Config Resolution

1. Read `.msskills/config.yaml` in the repo root; look up `paths.protocols`.
2. A custom document exists at that path → read its frontmatter `mode`:
   - `override` → use it alone; ignore the defaults below.
   - `overlay` (default, or no `mode` key) → read [defaults](./references/defaults.md) first, then
     apply the custom document's sections on top, matched by exact heading; new sections append.
3. A path is configured but no file exists there → say which path is missing, then use the defaults.
4. No config file or no `paths.protocols` key → use [defaults](./references/defaults.md).
5. `.msskills/stack.md` exists → use its recorded API style and tooling. An estate that is REST
   everywhere has a strong consistency argument that outweighs a marginal fit elsewhere; say so
   rather than proposing a second style casually.

## Self-Validation Checklist

**STOP before starting a new interface, or changing how an existing one is exposed. Verify every
check. Fix failures before presenting.**

1. **SHAPE FITS**: Does the protocol match the interaction — request/response, aggregation across
   many resources, high-volume internal calls, or server-initiated push? A mismatch here is paid
   for daily.
2. **ESTATE CONSISTENT**: Does this match what the rest of the estate uses? A second protocol needs
   a reason stronger than preference — it doubles tooling, client libraries, observability, and
   auth integration.
3. **REACHABLE BY THE CALLER**: Can the intended client actually speak it — browser, mobile,
   partner, batch job — without a gateway you have not planned?
4. **REST — RESOURCE AND VERB CORRECT**: Do methods carry their standard semantics, is `GET` free
   of side effects, and are `PUT` and `DELETE` idempotent? Cache headers set deliberately, not by
   default?
5. **GRAPHQL — BOUNDED**: Are query depth, complexity, and result size limited, and is
   introspection restricted in production? Without these, one client query can take the service
   down.
6. **GRAPHQL — BATCHED**: Is every resolver that fetches per-parent batched, so a list of 100 items
   does not become 100 queries? (see `data-access`)
7. **GRAPHQL — AUTHORISED PER FIELD**: Is authorisation applied at the field and object level, not
   only at the query entry point? A graph makes every edge a potential access path
   (see `secure-service`).
8. **GRPC — DEADLINES PROPAGATED**: Does every call carry a deadline, and is the remaining budget
   passed downstream? (see `resilience-patterns`)
9. **GRPC — MESSAGES EVOLVABLE**: Are field numbers never reused, removed fields reserved, and
   `required` avoided? Are streams bounded and cancellable?
10. **PUSH — RECONNECTION DESIGNED**: For WebSocket or SSE, what happens on disconnect — does the
    client resume from a position, or silently lose messages? Reconnection with backoff and jitter
    and a resume token is part of the design, not an afterthought.
11. **PUSH — HEARTBEAT AND TIMEOUT**: Is there a heartbeat so half-open connections are detected,
    and an idle timeout so abandoned ones are reclaimed?
12. **PUSH — BACKPRESSURE**: What happens when the server produces faster than the client consumes?
    An unbounded per-connection buffer is an out-of-memory error waiting for a slow client.
13. **PUSH — AUTHORISED AT UPGRADE AND AFTER**: Is the connection authenticated at handshake, is
    every subscription authorised, and what happens when the token expires mid-connection?
14. **OBSERVABLE**: Can you see per-operation latency and errors? A single `/graphql` endpoint or
    one long-lived socket hides everything unless instrumented by operation name.

All checks pass → state "Protocol holds: <protocol> for <interaction shape>, limits set."

## Active Anti-Pattern Scan

Any box you can check is a defect. Fix it before presenting.

- [ ] **Protocol by Habit**: chosen because it is familiar, with no reference to the interaction
      shape → state the shape and re-choose.
- [ ] **RPC over REST**: `POST /api/doSomething` with a verb-shaped body, ignoring resources and
      status codes → either model the resource or use an actual RPC protocol.
- [ ] **Side-Effecting GET**: a read method that mutates state → it will be retried, prefetched, and
      cached.
- [ ] **GraphQL Without Limits**: no depth, complexity, or size limit → one nested query exhausts
      the service.
- [ ] **Resolver N+1**: a per-parent fetch with no batching → the standard GraphQL performance
      failure.
- [ ] **Entry-Point-Only Authorisation** in a graph → authorise per field and per object.
- [ ] **Public Introspection**: the full schema exposed in production to unauthenticated callers.
- [ ] **`200 OK` With Errors Only**: GraphQL's partial-error model applied so that failures are
      invisible to monitoring → surface them in metrics and logs explicitly.
- [ ] **gRPC Without Deadlines**: calls with no deadline, so a hung server holds the caller.
- [ ] **Reused Field Number** in protobuf, or a removed field not reserved → silent data corruption
      for old clients.
- [ ] **Browser-Facing gRPC** with no gateway or web transport planned.
- [ ] **WebSocket for Request/Response**: a socket used to make ordinary calls → you have rebuilt
      HTTP without its tooling, caching, or load balancing.
- [ ] **No Resume Semantics**: a stream that drops messages on reconnect with no way to catch up.
- [ ] **Unbounded Connection Buffer**: no backpressure for a slow consumer.
- [ ] **Sticky State in a Socket**: per-connection state held in one instance's memory, so a
      restart or rebalance loses it.
- [ ] **Polling Where Push Was Needed** — or push where a 30-second poll would have done. Both are
      real; the second is far more common.

## Ambiguity Signals

Route these through `collaborative-judgment`. Each has two defensible answers.

- **REST or GraphQL for a client-facing API.** GraphQL removes over-fetching and round trips for
  varied clients, and costs caching simplicity, per-field authorisation, and a new performance
  failure mode. Weakest when there is one client whose needs are known.
- **gRPC or REST between internal services.** gRPC gives schema-first contracts, streaming, and
  lower overhead; REST gives universal tooling, easy debugging, and no code generation step.
- **WebSocket or SSE for push.** SSE is one-directional, plain HTTP, auto-reconnecting, and much
  simpler to operate. Use WebSocket only when the client genuinely needs to send frequently too.
- **Push or poll.** A 5–30 second poll is stateless, trivially scalable, and adequate far more
  often than teams assume. Push is worth it for genuine real-time.
- **A second protocol in the estate.** Consistency is worth a great deal; so is fitting the
  problem. Say what the second one costs before adding it.
- **Schema-first or code-first.** Schema-first makes the contract deliberate and adds a generation
  step; code-first is fast and lets the implementation define the contract by accident.
