# CQRS and Consistency — defaults

Loaded by Config Resolution when a project has no override, or as the base layer under an overlay.

---

## 1. The five levels

CQRS is a ladder, not a switch. Take the smallest step that solves the actual problem, and record
which level this service is on in `.msskills/stack.md`.

| Level | What it is | Adopt when | Cost |
|---|---|---|---|
| **0. One model** | The same types serve reads and writes | Default. Most services never leave | — |
| **1. Separate read queries** | Write model plus purpose-built queries returning dedicated result types, same store | The read shape differs from the aggregate shape | Small: some duplication |
| **2. Read model, same transaction** | A denormalised table maintained in the write transaction | Reads need a shape the write store cannot serve efficiently | Write amplification |
| **3. Asynchronous projections** | A separate read store updated from events | Read and write load or scaling genuinely diverge | Eventual consistency, rebuild tooling, lag monitoring |
| **4. Event sourcing + CQRS** | Events are the source of truth; all state is projected | Audit, temporal queries, or replay are requirements | Large and permanent |

**Level 1 solves most of what people reach for level 3 to fix.** A repository that has grown twenty
screen-specific finders does not need an event-driven read store; it needs its queries separated
from its aggregate loading (see `data-access`).

**Level 3 is where teams get hurt**, because it puts eventual consistency inside the user's own
session. See §3.

## 2. Read models and projections

- **Rebuildable, always.** If a projection cannot be rebuilt from its source, it is a second source
  of truth and it *will* diverge — not might. Make the rebuild a documented, exercised operation,
  not a script someone writes during an incident.
- **Versioned.** A logic change rebuilds into a new version, then switches reads over. Mutating in
  place while consumers read leaves a mix of old and new rows that nobody can reason about.
- **Idempotent.** Projections see duplicates, replays, and out-of-order delivery. Design for it
  (see `idempotency-and-immutability`).
- **No business rules.** A projection formats and denormalises. The moment it applies a rule the
  write side does not enforce, you have a second, unaudited implementation of the domain.
- **Lag is a first-class signal.** Measure it in the units the business cares about — seconds
  behind, events behind — and alert on the budget the design stated.
- **Poison events must not stop the world.** A projection that crashes on one bad event and retries
  forever stops updating for every user. Dead-letter it with enough context to replay, and keep
  going, loudly.
- **Reconcile periodically.** A scheduled comparison between projection and source turns silent
  drift into an alert instead of a customer complaint.

## 3. Read-your-writes

A user who submits a change and immediately sees the old value assumes the system lost their work.
This is the single most common way asynchronous projections reach production as a bug.

Four workable answers, in rough order of preference:

1. **Return the result from the command.** The caller does not need to re-read at all. Simple,
   and it removes the problem rather than managing it.
2. **Read from the write model for the requesting user** immediately after their own write, and
   from the projection for everyone else.
3. **Pass a version token.** The command returns a position; the read waits until the projection
   has reached it, or returns a header saying it has not.
4. **Show the change optimistically in the client** and reconcile when the projection catches up.

Whichever you choose, choose it deliberately and write it in the design. "It is usually fast
enough" is not a design — it is how the bug ships.

## 4. Event sourcing, honestly

**Right when:** a complete audit trail is a requirement rather than a preference; "what did this
look like on 3 March?" must be answerable; history must be replayed through new logic; the domain
is genuinely event-shaped — ledgers, trading, workflow engines, anything with a legal record.

**Costs, all permanent:**

- **Stored events are forever.** Their schema evolution is harder than an API's, because the past
  cannot redeploy. You will write upcasters, and you will maintain them.
- **Every query is a projection**, with its own lag, rebuild path, and failure mode.
- **Deletion is hard.** Right-to-erasure against an immutable log requires crypto-shredding or a
  design decided up front, not retrofitted (see `secure-service`).
- **Debugging changes shape** — from "look at the row" to "replay the stream".
- **Snapshots become necessary** for long-lived streams, and snapshot correctness is one more thing
  to get right.

**The usual misunderstanding:** teams adopt event sourcing because they want to *publish* what
happened. That is a different requirement, and it is met by state-based persistence plus domain
events through the transactional outbox (see `resilience-patterns`), with none of the above.

Event sourcing is also close to irreversible. Treat the decision accordingly — through
`collaborative-judgment`, recorded, with the costs written down.

## 5. Ownership and copies

One writer per piece of data (see `service-boundaries`). Everyone else obtains it one of three
ways, and the choice is **per field**, not per service:

| How | Freshness | Runtime dependency | Right for |
|---|---|---|---|
| **Query the owner** | Always current | Yes — their availability is inside yours | Data that must be current: current address, live stock |
| **Subscribe and project** | Bounded staleness | No | Data read often, tolerant of lag: product names, categories |
| **Copy at write time** | Frozen forever | No | Values that must not change after the fact: price at time of order, address at time of dispatch |

The third is the most commonly missed. An order line's price is not a stale copy of the current
price — it is the price that was agreed, and it is *correct* precisely because it never updates.
Modelling it as a replica is a bug; modelling a customer's current address as a snapshot is also a
bug. Decide which one each field is.

Never connect to another service's store, even read-only. A schema is not a contract, and the first
migration proves it.

## 6. Stating consistency in the contract

Where an operation's effect is eventual, the API should say so rather than implying completion:

- Return `202 Accepted` with a status location when the work is genuinely deferred.
- Name fields honestly — `refundInitiated`, not `refunded`, when only the request has been made.
- Document the expected settling time in the specification (see `api-contracts`).
- Give the consumer a way to observe completion: a status endpoint, an event, or a version token.

The failure mode this prevents is a consumer that treats a 200 as "done", builds a workflow on that
assumption, and breaks the first time the projection lags.
