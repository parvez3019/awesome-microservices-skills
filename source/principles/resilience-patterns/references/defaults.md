# Resilience Patterns — defaults

Loaded by Config Resolution when a project has no override, or as the base layer under an overlay.

Pattern names here are deliberately generic. `.msskills/stack.md` maps them to the project's actual
libraries; §9 lists common equivalents.

---

## 1. Timeouts

The single highest-value change in most services. An unbounded call holds a thread, a connection,
and a caller — and does so for exactly as long as the dependency's worst day lasts.

- **Every** remote call: HTTP, gRPC, database query, cache, broker publish, DNS, filesystem on a
  network mount.
- Derive from the latency budget, not from a round number. If the endpoint promises p99 < 800 ms
  and makes two sequential calls, neither gets 500 ms.
- Set timeouts at **every level** the library exposes: connect, TLS handshake, socket read, and the
  overall request. A generous overall timeout with no connect timeout still hangs on a black-holed
  host.
- **Propagate the deadline.** Pass the remaining budget downstream (gRPC deadlines, a
  `grpc-timeout`-equivalent header, a context with a deadline). Work whose caller has already given
  up is pure waste, and it is waste generated exactly when the system is least able to afford it.
- The caller's timeout must be **shorter** than its own caller's remaining budget. Timeouts that
  grow as you go deeper guarantee the outermost caller gives up first while the work continues.

## 2. Retry

Retries turn transient faults into successes, and turn overload into an outage. Both are easy.

- **Only retry idempotent operations.** If it is not idempotent, add an idempotency key (see
  `api-contracts`) before retrying.
- **Only retry retryable failures:** connection errors, timeouts, 429, 502, 503, 504. Never 400,
  401, 403, 404, 409, or 422 — the answer will not change.
- **Exponential backoff with full jitter.** `sleep = random(0, min(cap, base * 2^attempt))`. Full
  jitter — a random value in the whole interval, not the interval plus a wobble — is what actually
  de-synchronises a fleet of callers that all failed at the same instant.
- **Bound the attempts.** Three total attempts is a reasonable default for a user-facing path. More
  is rarely useful: if two retries with backoff failed, the dependency is down, not blipping.
- **Budget them.** Cap retries as a fraction of overall traffic (10% is a common figure). When the
  budget is exhausted, fail fast instead of retrying. This is what prevents a struggling dependency
  from receiving *more* load precisely when it is failing.
- **Retry at exactly one layer.** Client library, gateway, service mesh, and application code each
  retrying three times is 81 requests, not 3.
- **Respect `Retry-After`.** If the server told you when to come back, obey it.

## 3. Circuit breaker

A breaker stops sending traffic to a dependency that is persistently failing, so the caller fails
fast instead of spending its own resources waiting.

| State | Behaviour | Leaves when |
|---|---|---|
| **Closed** | Calls pass through; failures counted over a rolling window | Failure rate exceeds the threshold within a minimum-volume window → Open |
| **Open** | Calls rejected immediately with the fallback; no load reaches the dependency | The open duration elapses → Half-Open |
| **Half-Open** | A small number of probe calls allowed through | Probes succeed → Closed; any probe fails → Open |

Starting points, to be tuned against real traffic:

- Failure threshold **50%** over a rolling window of the last 20–100 calls.
- A **minimum volume** before the breaker can trip — otherwise two failures out of two trip it.
- Open duration **10–60 s**, with an increasing backoff if it re-trips immediately.
- **3–5 probe calls** in half-open.
- Count **timeouts and 5xx** as failures. Do **not** count 4xx — a caller sending bad requests is
  not a sign the dependency is unhealthy.
- **One breaker per dependency**, or per endpoint if one endpoint is materially riskier. A single
  breaker across three dependencies gives you no information and trips for the wrong reason.
- **Emit state transitions as events and metrics.** A breaker that opens silently is an outage
  nobody can explain.

## 4. Bulkhead and load shedding

- **Bulkhead:** separate resource pools per dependency, so a slow one cannot consume every
  connection or thread. Implement as separate pools, or as a concurrency limit per dependency.
- **Concurrency limits** beat thread pools where the platform is async — cap in-flight calls per
  dependency and reject beyond it.
- **Rate limiting** protects *you* from callers; the breaker protects you from dependencies. Both
  are needed and they are not substitutes.
- **Load shedding:** when saturated, reject work early and cheaply rather than accepting everything
  and timing out. Shed by priority where the system has one — health checks and paying customers
  before batch and analytics.
- **Bound every queue.** An unbounded in-memory buffer converts backpressure into an out-of-memory
  kill, which loses the work *and* the process.

## 5. Fallback and graceful degradation

When protection has done its job and the call still fails, something must happen. Decide it
deliberately.

| Fallback | Right when | Cost |
|---|---|---|
| Cached value | Stale data is useful | Correctness window; must be visible |
| Default value | A sensible neutral exists (empty recommendations) | Silently wrong if the default is not neutral |
| Partial response | The page has independent sections | Consumers must handle missing pieces |
| Queue for later | The work is deferrable | Needs durability and a drain path |
| Fail fast | Correctness outranks availability | The user sees an error |

Rules: degradation is **visible** — a header, a field, a metric, a log line, so dashboards and
support can see the system is running degraded. Never serve stale data as if it were fresh. And a
fallback that itself calls a remote service needs its own timeout and breaker.

## 6. Idempotency and exactly-once

Exactly-once *delivery* does not exist across a network. Exactly-once *effect* does, and it is
built from at-least-once delivery plus an idempotent consumer.

- **Deduplicate on the message ID** in a store with a retention window longer than the maximum
  redelivery period, or
- **Make the effect naturally idempotent** — a conditional update (`WHERE status = 'PENDING'`), an
  upsert on a natural key, or a state machine that ignores transitions it has already made.
- **Inbox pattern:** record processed message IDs in the same transaction as the effect. Simple,
  durable, and the store is trivially prunable.
- Consumers must also tolerate **out-of-order** delivery. Ordering holds per partition key at best,
  and rebalances break even that.

## 7. Transactional outbox

A service that commits to its database and then publishes to a broker has two operations with no
shared transaction. Crash between them and the system is permanently inconsistent — the classic
dual-write problem, and it happens far more often than teams expect.

1. In the **same transaction** as the business change, insert the event into an `outbox` table.
2. A **relay** reads unpublished rows and publishes them to the broker.
3. On successful publish, mark the row published (or delete it).
4. The relay is at-least-once, so consumers must be idempotent (§6).

Relay options:

| Approach | Gains | Costs |
|---|---|---|
| **Polling publisher** | Simple, no extra infrastructure | Polling latency; load on the database |
| **Change data capture** | Low latency, no query load, no missed rows | Extra infrastructure and operational surface |

The **inbox** is the mirror image on the consumer side: record the message ID and the effect in one
transaction. Outbox plus inbox gives at-least-once delivery with exactly-once effect, which is what
"exactly once" actually means in practice.

## 8. Sagas

A business transaction spanning services, as a sequence of local transactions each with a
compensating action. Use one only when an invariant genuinely spans services — the better answer is
often a boundary that does not require it (see `service-boundaries`).

- **Orchestration:** a coordinator drives the steps. The flow is in one place, readable and
  debuggable; the coordinator is a component to own and scale.
- **Choreography:** each service reacts to events. No central component; the flow exists only as an
  emergent property, which makes "why did this order stall?" a research project.

Requirements either way:

- **Every step has a compensating action**, and compensation is itself idempotent and retryable.
- **Compensation is not rollback.** You cannot un-send an email; you send an apology. Model the
  semantic reversal, not a database undo.
- **Persist saga state** so it survives a crash mid-flow.
- **Handle the stuck saga.** Steps that never complete need a timeout and an operator path. Every
  saga eventually needs one.
- **Test the compensation paths.** They are the ones that only run on the worst day, which is
  exactly when nobody wants to discover they were never exercised (see `test-strategy`).

## 9. Health probes

| Probe | Answers | Must not |
|---|---|---|
| **Startup** | Has the process finished initialising? | Be confused with liveness on a slow starter |
| **Liveness** | Is this process unrecoverably broken? | Check any dependency — a restart cannot fix someone else's outage |
| **Readiness** | Can this instance serve traffic right now? | Check a *shared* downstream dependency |

The most expensive mistake here: readiness that checks a shared database. When that database blips,
every instance reports unready simultaneously, the load balancer has nowhere to send traffic, and a
recoverable dependency wobble becomes a total outage. Readiness reflects *this instance's* ability
to serve — its own connection pool, its own warm-up — not the health of the estate.

## 10. Common library equivalents

Named only as a translation aid. Follow `.msskills/stack.md`; never introduce a dependency the
project has not chosen.

| Pattern | JVM | .NET | Go | Node/TS | Platform |
|---|---|---|---|---|---|
| Breaker, retry, bulkhead | Resilience4j | Polly | `gobreaker`, `failsafe-go` | `cockatiel`, `opossum` | Service mesh (Envoy/Istio) outlier detection |
| Timeouts and deadlines | Client config, `TimeLimiter` | `HttpClient` timeout, `CancellationToken` | `context.WithTimeout` | `AbortSignal.timeout` | Mesh route timeout |
| Outbox relay | Debezium, framework outbox | Debezium, MassTransit outbox | Debezium, custom poller | Debezium, custom poller | CDC connector |
| Saga | Framework sagas, Temporal | MassTransit, Temporal | Temporal, Watermill | Temporal | Step Functions |

A service mesh can supply timeouts, retries, and outlier detection without code. It cannot supply
idempotency, fallbacks, the outbox, or compensation — those are application concerns and always
will be.
