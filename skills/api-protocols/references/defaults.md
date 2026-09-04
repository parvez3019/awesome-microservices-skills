# API Protocols — defaults

Loaded by Config Resolution when a project has no override, or as the base layer under an overlay.

---

## 1. Choosing

Choose from the **interaction shape**, then check it against the estate's existing choice.

| The interaction | Protocol | Why |
|---|---|---|
| Client asks, server answers; resources with lifecycles | **REST** | Universal tooling, HTTP caching, every proxy understands it |
| Many varied clients needing different subsets, one round trip | **GraphQL** | Client-specified shape; removes over-fetching and chatty screens |
| High-volume internal calls, strict contracts, streaming | **gRPC** | Schema-first, efficient binary framing, first-class deadlines and streams |
| Server pushes to the client, one direction | **SSE** | Plain HTTP, auto-reconnect built in, trivial to operate |
| Both directions, frequently, low latency | **WebSocket** | Full duplex — accept the operational cost deliberately |
| Producer and consumer must be decoupled in time | **Messaging** | Not a protocol choice — a design choice (see `api-contracts`) |
| Batch or bulk transfer | **File or object storage** | An API is the wrong shape for a million rows |

Two rules that override the table:

- **Estate consistency usually wins.** A second protocol doubles the client libraries, the auth
  integration, the observability setup, the gateway configuration, and the on-call knowledge.
  Introduce one only for a force the existing protocol genuinely cannot meet.
- **Check reachability first.** A browser cannot speak gRPC without a gateway or grpc-web. A
  partner's firewall may not pass WebSockets. Solve that before designing.

## 2. REST

- **Resources are nouns; the method is the verb.** `POST /orders/{id}/cancellation`, not
  `POST /orders/cancel`. Operations with business meaning get their own sub-resource
  (see `api-contracts`).
- **Honour the method semantics.** `GET` and `HEAD` are safe and cacheable and must never mutate —
  they will be prefetched, retried, and cached whether you intended it or not. `PUT` and `DELETE`
  are idempotent. `POST` is neither, which is why it needs an idempotency key.
- **Use status codes properly.** `200` with `{"success": false}` throws away the one signal every
  proxy, client, and dashboard already understands.
- **Caching is a feature, not a default.** Set `Cache-Control` deliberately on every response,
  including `no-store` where that is right. Use `ETag` with conditional requests for large or
  frequently re-fetched resources.
- **Conditional writes** with `If-Match` give you optimistic concurrency over HTTP for free
  (see `data-access`).
- **Content negotiation stays simple.** One representation per resource unless there is a real need.
- **HTTP/2 changes the cost model.** Multiple small requests are far cheaper than they were, which
  weakens the usual argument for a bespoke aggregated endpoint.

## 3. GraphQL

GraphQL moves query planning from the server to the client. That is its value and its entire risk
profile: the client can now write a query that nobody load-tested.

**Schema design**

- Design the graph around **domain relationships**, not around the current screens. Screens change.
- **Nullability is a contract**: non-null means you can always produce a value, including when a
  downstream call fails. Over-using non-null makes one failing field null out its entire parent.
- **Enums and unions over stringly-typed fields.** Interfaces for genuine polymorphism.
- **Mutations return the modified object** plus a typed result, so the client needs no re-fetch —
  this is also the cleanest answer to read-your-writes (see `cqrs-and-consistency`).
- **Errors:** transport and validation failures use the `errors` array; expected business failures
  belong in the result type as a union, so clients handle them with the type system rather than by
  matching strings.
- **Deprecate rather than remove.** `@deprecated` plus field-level usage metrics tells you when it
  is safe to delete (see `api-contracts`).

**The two failure modes**

1. **N+1 resolvers.** A list of 100 orders whose `customer` resolver fetches per order issues 101
   queries. Every per-parent resolver must batch — collect the keys for one tick, fetch them in one
   call, distribute the results. This is not an optimisation; it is the baseline.
2. **Unbounded queries.** Without limits, a nested query is a denial of service that requires no
   special access. Enforce: **maximum depth**, **complexity/cost budget** with per-field costs,
   **maximum result size**, and **timeouts**. For a first-party client, **persisted queries** are
   the strongest answer — the server accepts only a known allowlist of query documents, which caps
   the cost and enables caching.

**Security.** Authorise at the field and object level, not at the entry point — the graph makes
every edge an access path (see `secure-service`). Disable introspection for unauthenticated callers
in production. Watch for object-level authorisation gaps reached through nested relationships,
which is the graph version of the most common API vulnerability.

**Observability.** One `/graphql` endpoint makes every dashboard useless by default. Instrument by
**operation name** and resolver, and require clients to name their operations.

## 4. gRPC

**Service and message design**

- One service per bounded capability; methods named as operations.
- **Never reuse a field number**, and always `reserved` a removed field's number and name. Reusing
  one silently corrupts data for clients built against the old schema.
- **Everything is optional in proto3 semantics** — design for absent fields rather than assuming
  presence. Avoid `required` where the syntax still offers it.
- **Wrap request and response in their own message types**, even for a single field, so fields can
  be added later without a signature change.
- **Enums start at zero with an `UNSPECIFIED` value**, so an unset field is distinguishable from
  the first real value.
- **Run `buf breaking`** (or the equivalent) in CI. Protobuf's compatibility rules are precise and
  easy to violate by accident.

**Runtime**

- **Deadlines on every call**, propagated downstream. gRPC makes this first-class; use it
  (see `resilience-patterns`).
- **Status codes carry meaning** — `NOT_FOUND`, `ALREADY_EXISTS`, `FAILED_PRECONDITION`,
  `RESOURCE_EXHAUSTED`. Map them properly instead of returning `INTERNAL` for everything, and use
  the details mechanism for structured error information.
- **Streaming needs flow control and cancellation.** A server stream with no backpressure and no
  cancellation is an unbounded buffer. Always bound the stream and honour client cancellation.
- **Load balancing is per connection, not per request**, so a long-lived channel pins to one
  backend. Use a load-balancing policy or a proxy that understands HTTP/2 — otherwise traffic
  concentrates after any restart.
- **Browsers need grpc-web or a gateway.** Decide which before designing the API.

## 5. WebSockets and SSE

Long-lived connections make a stateless service stateful. Everything below follows from that.

**Prefer SSE when the flow is server-to-client only.** It is plain HTTP, works through ordinary
proxies, reconnects automatically, and supports resumption via `Last-Event-ID` with no protocol of
your own. Most "we need WebSockets" requirements are satisfied by SSE plus ordinary POSTs.

**Design these explicitly, in this order:**

1. **Authentication at handshake**, and a decision about **token expiry mid-connection** — a
   connection opened an hour ago should not still be authorised on an expired token. Re-authenticate
   or close.
2. **Authorisation per subscription**, not just per connection.
3. **Heartbeat** in both directions, so half-open connections — the kind a network partition leaves
   behind — are detected rather than lingering.
4. **Idle timeout** so abandoned connections are reclaimed.
5. **Reconnection with exponential backoff and full jitter.** Without jitter, a server restart
   brings every client back simultaneously and the service falls over again
   (see `resilience-patterns`).
6. **Resume semantics.** A sequence number or cursor the client sends on reconnect, and a bounded
   server-side buffer to replay from. Without this, every reconnect is a silent gap.
7. **Backpressure.** Bound the per-connection outbound queue. When a slow client fills it, drop
   with a defined policy (oldest, or coalesce) and tell the client — never buffer without limit.
8. **Connection limits** per user and per instance, and a plan for what happens at the cap.

**Operationally:** connections pin clients to instances, so a deploy disconnects everyone at once —
stagger it. Per-connection state in memory is lost on restart; keep it in a shared store or make it
reconstructible. Load balancers need idle timeouts longer than your heartbeat interval, or they
will close healthy connections. And a fan-out to many connections needs a broker behind it, because
one instance holds only its own share.

**Message framing:** version the message envelope from day one; include a type field and a sequence
number. A socket protocol with no version field is impossible to evolve.
