# Collaborative Judgment — defaults

Loaded by Config Resolution when a project has no override, or as the base layer under an overlay.

---

## 1. The presentation format

Use this shape. It is short on purpose: the user should be able to answer from a phone.

```markdown
**Decision: <the question, in one line>**
_Reversibility: one-way / reversible_ · _Blocking: yes / no_

**A. <name>** — <what it means in this codebase, one or two sentences>
  · Gains: <the specific benefit>
  · Costs: <the specific cost>
  · Fits when: <the condition that makes this right>

**B. <name>** — …

**Recommendation: A**, because <the reason grounded in this project's constraints>.
```

Rules that matter more than the layout:

- **Name options after what they are**, not "Option 1 / Option 2". `A. Synchronous call with a
  circuit breaker` is answerable; `Option 1` requires scrolling back.
- **One line of consequence beats a paragraph of theory.** The user knows what a saga is. They do
  not know that in *this* service it means the `orders` table gains a state machine and three new
  compensating handlers.
- **State what happens if they do not answer.** If you will proceed with the recommendation, say
  so — that turns a blocking question into an informed default.

## 2. Reversibility, and how much ceremony a decision deserves

| Class | Examples | Ceremony |
|---|---|---|
| **One-way** | Public API shape, published event schema, which service owns a piece of data, service boundaries, choice of datastore semantics | Always present options; record in `.msskills/decisions.md`; do not proceed on assumption |
| **Costly to reverse** | Sync vs async integration, orchestration vs choreography, consistency model, auth model | Present options; recommend; proceed on the recommendation only if the user said to keep moving |
| **Reversible** | Internal class structure, library choice behind a port, retry parameters, log format | Decide; state the choice in one line; move on |
| **Trivial** | Naming, file layout, formatting | Decide silently; follow existing conventions |

The failure mode in both directions is real. Asking about trivia trains the user to stop reading
your questions. Assuming on a one-way door produces a migration.

## 3. Trade-offs that recur in microservices

When one of these surfaces, it is almost always a genuine judgment call. Present it.

| Decision | Pulls one way | Pulls the other |
|---|---|---|
| **Synchronous call vs event** | Simple to reason about, immediate consistency, easy debugging | Temporal coupling: the caller's availability is now the product of both services' |
| **Strong vs eventual consistency** | Users and auditors understand "it is correct now" | Cross-service transactions cost availability and add distributed locking |
| **Orchestration vs choreography** | An orchestrator makes the flow readable and debuggable in one place | Choreography avoids a central bottleneck but the flow exists only in everyone's heads |
| **Split a service vs keep it together** | Independent deploy and scale | Every split turns a method call into a network call with partial failure and a contract to version |
| **Shared library vs duplication** | One place to fix a bug | A shared library across services is a distributed deploy dependency; duplication is often cheaper than coupling |
| **Extend an aggregate vs add one** | Fewer moving parts, one transaction | An aggregate that grows past its invariant boundary becomes a contention hotspot |
| **Own the data vs call for it** | Owning removes a runtime dependency | Owning means replication, staleness, and a second source of truth to reconcile |
| **Fail closed vs degrade** | Failing closed protects correctness | Degrading protects availability; which one is right is a product decision, not a technical one |

For the domain reasoning behind each, defer to the skill that owns it — `service-boundaries`,
`domain-modelling`, `cqrs-and-consistency`, `resilience-patterns`, `api-contracts`.

## 4. Recording decisions

Append to `.msskills/decisions.md`, newest last. Create the file if it is absent.

```markdown
## 2026-09-05 — Order confirmation is published as an event, not a synchronous call

**Context:** Checkout must not fail when the notification service is down.
**Options considered:** Synchronous call with circuit breaker + fallback; domain event via the outbox.
**Decision:** Domain event via the transactional outbox.
**Because:** Confirmation is not required for the order to be valid; availability of checkout
outranks immediacy of the email.
**Reversibility:** Costly — consumers will bind to the event schema.
**Consequences:** Adds an outbox table and a relay; notification becomes eventually consistent;
`OrderConfirmed` is now a published contract governed by `api-contracts`.
```

When a feature design document is open, the decision goes in that document's Decisions Log instead,
and `.msskills/decisions.md` gets a one-line pointer to it. Two copies drift; a pointer does not.

**Superseding:** never edit a recorded decision. Append a new one that names the entry it replaces
and what changed. The history of why a system is shaped the way it is has more value than a tidy file.

## 5. Handling the answer

- The user picks an option → it is binding. Proceed with it, and do not re-litigate it later in
  the same session because it turned out to be more work.
- The user picks something you did not offer → record it as chosen, and say plainly if you see a
  problem with it. Once they confirm, build it.
- The user says "you decide" → take your recommendation, record it with `Decided by: agent on
  delegation`, and keep going. Delegation is an answer.
- The option proves unworkable mid-implementation → stop, say what broke the assumption, and
  re-open the decision with what you now know. Do not silently switch to option B.
