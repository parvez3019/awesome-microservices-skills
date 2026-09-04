# The Catalogue

Every skill, what it owns, and — just as importantly — what it does **not** own. The second column
is the one to read when two skills seem to overlap.

---

## Which skill owns what

Adjacent concerns are deliberately separated so that only one skill fires on a given question.

| Question | Skill |
|---|---|
| Should this be its own service? | `service-boundaries` |
| Which layer does this class belong in? | `clean-architecture` |
| Is this an entity or a value object? What is the aggregate? | `domain-modelling` |
| Why is this query slow? How do I write this migration? | `data-access` |
| Should reads come from a projection? How stale may it be? | `cqrs-and-consistency` |
| What fields does this endpoint return? Is this change breaking? | `api-contracts` |
| REST, GraphQL, gRPC, or WebSocket? | `api-protocols` |
| How do I wrap this vendor SDK? Where does the mapping go? | `infrastructure-adapters` |
| What happens when this call times out? | `resilience-patterns` |
| What happens if this runs twice? Should this type be immutable? | `idempotency-and-immutability` |
| Can this caller access this record? | `secure-service` |
| At which level should I test this? | `test-strategy` |
| Will my release break a consumer? | `contract-testing` |
| Where does this setting live? Should I add this library? | `config-and-dependencies` |
| What should we agree before writing code? | `design-first` |
| Two answers are both defensible — now what? | `collaborative-judgment` |

## Frequently confused pairs

**`service-boundaries` vs `clean-architecture`** — boundaries between *services*, versus structure
*inside* one. Services named `api`, `business-logic`, `data-access` are a layering diagram that
escaped into deployment.

**`domain-modelling` vs `data-access`** — what the types mean, versus how they are stored and
fetched. An aggregate boundary is `domain-modelling`; the N+1 loading it is `data-access`.

**`data-access` vs `cqrs-and-consistency`** — one query's correctness and speed, versus whether the
read path should be separate at all and how far it may lag.

**`api-contracts` vs `api-protocols`** — *what* crosses the boundary (fields, errors, versioning,
compatibility), versus *how* it travels (protocol choice, and each protocol's own pitfalls).

**`clean-architecture` vs `infrastructure-adapters`** — the layering rule that ports point inward,
versus the craft of actually writing the adapter that implements one.

**`resilience-patterns` vs `idempotency-and-immutability`** — the retry, the breaker, the outbox
mechanism, versus whether the operation was safe to repeat in the first place. Adding a retry to a
non-idempotent write is the failure both of them are trying to prevent, from opposite directions.

**`test-strategy` vs `contract-testing`** — proving behaviour inside one service, versus proving two
services still agree. A contract test that asserts business logic has become the wrong kind of test.

## Principles at a glance

Each principle's `SKILL.md` contains its Config Resolution, checklist, anti-pattern scan, and
ambiguity signals. The depth lives in `references/defaults.md`, loaded on demand.

| Skill | Checklist covers | Depth in references |
|---|---|---|
| [`service-boundaries`](../source/principles/service-boundaries/SKILL.md) | Business capability naming, ubiquitous language, single-writer ownership, autonomy, change coupling, chattiness, transaction fit, team fit, justified split | Finding a boundary from language and change; modular-monolith-first; context mapping patterns; data ownership per field; strangler-fig extraction; sizing |
| [`clean-architecture`](../source/principles/clean-architecture/SKILL.md) | Layer placement, dependency direction, framework isolation, ports owned inward, SOLID at both scales, testability without I/O, pattern justification | The four layers and what goes where; SOLID at class and service level; choosing a pattern from a named force; DI rules; enforcing with architecture tests |
| [`domain-modelling`](../source/principles/domain-modelling/SKILL.md) | Named invariant, valid on construction, behaviour with data, entity vs value, immutable values, primitive obsession, aggregate size, encapsulation, ubiquitous language, illegal states | The building blocks; value objects first; aggregates as consistency boundaries; domain events; making illegal states unrepresentable; when a rich model is the wrong answer |
| [`data-access`](../source/principles/data-access/SKILL.md) | Domain types returned, whole aggregates, explicit transaction boundary, no I/O in a transaction, no N+1, bounded and indexed queries, concurrency, lock order, keyset pagination, migration compatibility, cache invalidation, pool sizing | Repositories; transactions and isolation; optimistic vs pessimistic locking; query performance; connection pools; caching; expand-migrate-contract |
| [`cqrs-and-consistency`](../source/principles/cqrs-and-consistency/SKILL.md) | Level justified, smallest step, staleness budget, read-your-writes, rebuildable, idempotent projection, poison events, versioning, single ownership, copy vs replica | The five levels; projections; read-your-writes strategies; event sourcing honestly; ownership and copies; stating consistency in the contract |
| [`api-contracts`](../source/principles/api-contracts/SKILL.md) | Spec first, consumer-shaped, backward compatible, errors specified, idempotency, bounded collections, explicit types, no internal leakage, events as facts, compatibility mode | Specification formats; modelling operations; pagination; the error catalogue; idempotency keys; evolution rules; event envelopes and registry modes |
| [`api-protocols`](../source/principles/api-protocols/SKILL.md) | Shape fits, estate consistency, reachability, REST verb semantics, GraphQL limits and batching and field authorisation, gRPC deadlines and evolution, push reconnection, heartbeats, backpressure, observability | Choosing from the interaction shape; REST cache semantics; GraphQL's two failure modes; gRPC message evolution; WebSocket and SSE design order |
| [`infrastructure-adapters`](../source/principles/infrastructure-adapters/SKILL.md) | Port owned inward and domain-shaped, vendor types contained, failures translated, no business rules, resilience here only, explicit tested mapping, tolerant reader, untrusted input, injected clock, observable, tested at the wire | Port design; what belongs in an adapter; wrapping an SDK; mapping; adapter shapes per integration type; testing adapters; adapters and a service mesh |
| [`resilience-patterns`](../source/principles/resilience-patterns/SKILL.md) | Timeout, deadline propagation, retry safety and shape and classification, no nested retries, circuit breaker, isolation, fallback, idempotent consumer, no dual write, compensation, correct probes | Timeouts; retry with full jitter and budgets; breaker states and thresholds; bulkheads and shedding; fallbacks; the outbox and inbox; sagas; probes; library equivalents |
| [`idempotency-and-immutability`](../source/principles/idempotency-and-immutability/SKILL.md) | Repeat safe, mechanism named, key scoped and retained, atomic dedup, idempotent consumer, side effects counted, job safety, idempotent compensation, immutable values, no leaked mutable state, safe publication | Why repeatability is not optional; four ways to be idempotent; idempotency keys; idempotent consumers; non-database side effects; jobs; immutability; where mutability is right; append-only history |
| [`secure-service`](../source/principles/secure-service/SKILL.md) | Authenticated, object- and function-level authorisation, deny by default, input validation, injection safety, mass assignment, SSRF, external secrets, clean output and logs, transport, sensitive-flow limits, dependency integrity | The API Top 10 as checks; authentication and service identity; input, injection and output; secrets; personal data; supply chain; cheap threat modelling |
| [`test-strategy`](../source/principles/test-strategy/SKILL.md) | Right level, behaviour not implementation, one reason to fail, naming, AAA, determinism, isolation, no sleep, justified doubles, real assertions, failure paths, fails-first | The portfolio and what each level must not own; component tests in detail; test doubles; determinism causes and fixes; structure and naming; test data; coverage honestly |
| [`contract-testing`](../source/principles/contract-testing/SKILL.md) | Consumer driven, only what is used, types not values, provider states, no business logic, both sides run, real verification, deploy gated, messages covered, versioned by commit, failure paths | The full flow; writing the consumer side; provider verification; message and event contracts; versioning with branches and environments; the four variants; what contract tests are not |
| [`config-and-dependencies`](../source/principles/config-and-dependencies/SKILL.md) | Varies per deployment, not a secret, validated at startup, typed at the edge, no environment branching, documented, safe defaults, flag has an end and defaults off, dependency justified, pinned and locked, upgrade path, shared-library discipline | What is configuration; the rules; environment parity and drift; feature flags; choosing a dependency; versions, locks and updates; internal shared libraries |
| [`design-first`](../source/principles/design-first/SKILL.md) | One level per message, questions over assertions, unknowns named, grounded, decisions surfaced, recorded, gate stated, no code | Depth calibration; question banks per level; gate discipline; the blueprint document; what "no code" means at L4 |
| [`collaborative-judgment`](../source/principles/collaborative-judgment/SKILL.md) | Genuine, bounded, concrete, consequenced, reversibility marked, recommended, answerable, recorded | The presentation format; reversibility and how much ceremony a decision deserves; recurring microservices trade-offs; recording decisions; handling the answer |

## Workflows

| Skill | Gates | Produces |
|---|---|---|
| [`/design-service`](../source/workflows/design-service/SKILL.md) | Depth agreed before starting; one approval per design level | `.msskills/designs/<feature>.md` with `status: approved` |
| [`/implement-service`](../source/workflows/implement-service/SKILL.md) | Approved blueprint required; plan agreed before code; review mode chosen; any deviation stops the work | Code and tests, layer by layer, each validated before presentation |
| [`/review-service`](../source/workflows/review-service/SKILL.md) | Scope stated before starting; each finding verified against a concrete failure | Severity-ranked findings with file, line, and the principle violated |
| [`/refactor-safely`](../source/workflows/refactor-safely/SKILL.md) | Named force required; behaviour pinned before any change; green between every step | Restructured code with behaviour provably unchanged |

## Profile

| Skill | Produces |
|---|---|
| [`/stack-profile`](../source/profiles/stack-profile/SKILL.md) | `.msskills/stack.md` and a starter `.msskills/config.yaml` |

## Agent

| Agent | Used by |
|---|---|
| [`microservice-reviewer`](../agents/microservice-reviewer.md) | `/review-service`, for an independent pass with no memory of having written the code. Read-only |

## Not yet covered

Deliberate gaps, in rough priority order for future contributions:

- **`observability`** — OpenTelemetry, correlation propagation, RED/USE, SLOs and error budgets,
  cardinality discipline. Currently only touched in passing by `resilience-patterns` and
  `infrastructure-adapters`.
- **`deployment-and-release`** — blue/green, canary, rollback, and the migration compatibility
  window. Partly covered by `data-access` and `config-and-dependencies`.
- **`clean-code`** — function-level craft. Deliberately omitted so far because the existing skills
  cover the distributed-system-specific failures, and general clean code is well served elsewhere.
- **`incident-to-fix`** and **`production-readiness-review`** workflows.

See [CONTRIBUTING.md](../CONTRIBUTING.md) if you want to write one.
