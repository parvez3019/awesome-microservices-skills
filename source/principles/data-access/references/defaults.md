# Data Access — defaults

Loaded by Config Resolution when a project has no override, or as the base layer under an overlay.

---

## 1. Repositories

A repository is a **collection-like interface for aggregates**, not a data-access utility.

- **One per aggregate root.** Nothing inside an aggregate gets its own repository — the root owns
  its children (see `domain-modelling`).
- **Load and store whole aggregates.** Partial loads mean the invariant cannot be enforced.
- **Return domain types.** Never an ORM entity, a lazy proxy, a result set, or a framework page
  type. The mapping is the repository's job; skipping it couples every caller to the schema.
- **The interface belongs to the application layer**, the implementation to the adapter layer
  (see `clean-architecture`). A repository interface sitting next to its SQL implementation is a
  package split, not a port.
- **Keep the interface small.** `findById`, `save`, `delete`, plus the few finders the domain
  genuinely needs.
- **Reporting queries are not repository methods.** A repository accumulating
  `findAllByStatusAndDateBetweenOrderByTotalDesc` for screens has become a query layer — separate
  those as explicit read queries returning purpose-built result types
  (see `cqrs-and-consistency`).

## 2. Transactions

- **One use case, one transaction**, opened and committed in the application layer. The boundary
  should be visible where the use case is, not inferred from annotations three classes deep.
- **Never hold a transaction across I/O.** An HTTP call inside a transaction holds locks and a
  connection for the remote service's worst-case latency. Do remote work before or after; if a
  remote result must be atomic with a local write, that is a saga, not a longer transaction
  (see `resilience-patterns`).
- **Keep them short.** Long transactions hold locks, grow undo logs, and block schema changes.
- **Never span aggregates.** Two roots in one commit means the boundary is wrong or the consistency
  is eventual.
- **Publish events through the outbox**, inside the same transaction — never a broker publish as a
  second write (see `resilience-patterns`).
- **Framework propagation is a trap.** Relying on nested or "required-new" semantics nobody can
  explain produces partial commits under failure. Be explicit.

### Isolation and anomalies

| Level | Prevents | Still possible |
|---|---|---|
| Read uncommitted | — | Dirty reads |
| Read committed | Dirty reads | Non-repeatable reads, phantoms, lost updates |
| Repeatable read | The above plus non-repeatable reads | Phantoms (in some engines), write skew |
| Serialisable | Everything | Nothing — at the cost of throughput and retries |

Practical default: **read committed plus explicit concurrency control**. Do not rely on a higher
isolation level to fix a lost update — make the update conditional and check the outcome. Engines
differ in what each level actually guarantees; verify rather than assuming.

## 3. Concurrency

**Optimistic** — a `version` column on the aggregate root, checked and incremented on write:

```sql
UPDATE orders SET status = ?, version = version + 1
WHERE id = ? AND version = ?
-- 0 rows updated → someone else won; reload and retry, or surface a 409
```

The default. Cheap under low contention, no locks held, and it makes the conflict explicit rather
than silently losing a write. The caller needs a retry or a conflict response (see `api-contracts`).

**Pessimistic** — `SELECT ... FOR UPDATE`. Right for genuinely hot rows where optimistic retries
would thrash: a counter, an inventory level, a sequence. Always with a lock timeout, and always
acquiring multiple rows in a consistent order — inconsistent lock ordering is the standard recipe
for a deadlock that only appears under concurrency.

**Conditional update** — often better than either. `WHERE status = 'PENDING'` makes the transition
itself atomic and idempotent, with no version to manage
(see `idempotency-and-immutability`).

## 4. Query performance

**The N+1 problem** is the most common performance defect in service code and the easiest to miss
locally, because ten rows hide it perfectly. It appears as a query in a loop, a lazy association
touched during mapping, or a resolver fetching per item. Fix by fetching what you need in one
query, or by batching the second query across all the identifiers at once. Assert against it: many
ORMs can count queries per test, and a test that fails when the query count exceeds a threshold
catches regressions that no code review will.

Other rules:

- **Select the columns you use.** `SELECT *` drags large columns across the wire for no reason and
  defeats covering indexes.
- **Index every predicate, join, and sort column.** Composite index order matters: equality
  predicates first, then range, then sort.
- **Read the plan** for any new query on a table that will grow. A sequential scan on a thousand
  rows is fine; the same query at ten million is an incident.
- **Every query has a limit.** Even ones you are sure return a few rows.
- **Batch writes** rather than issuing one statement per element, and bound the batch size.
- **Keyset pagination** for anything deep or changing:
  ```sql
  SELECT ... WHERE (created_at, id) < (?, ?) ORDER BY created_at DESC, id DESC LIMIT 50
  ```
  Offset pagination re-scans and discards everything before the offset, and it skips or repeats
  rows when the data changes between pages.
- **Beware the ORM's implicit behaviour**: cascades, orphan removal, dirty checking on flush, and
  automatic joins all issue statements nobody wrote. Log the generated SQL at least once for every
  new query path.

## 5. Connection pools

The pool is a hard capacity limit, and its default is almost never right.

- **Size against the database**, not the application. Total connections across all instances must
  stay comfortably under the server's limit — including replicas, migrations, and admin tools.
- **Small pools usually outperform large ones.** A database with N cores does not go faster with
  200 concurrent queries; it goes slower, with more contention.
- **Set a connection-acquisition timeout.** Without one, pool exhaustion presents as a hang rather
  than an error, and hangs cascade (see `resilience-patterns`).
- **Set a statement timeout** on the database side too, so a runaway query cannot hold a connection
  indefinitely.
- **Separate pools for separate workloads** — the request path, background jobs, and migrations
  should not compete for the same connections (a bulkhead, in `resilience-patterns` terms).
- **Monitor pool saturation and wait time.** They lead the incident by minutes.

## 6. Caching

A cache is a copy of the truth that is allowed to be wrong. Every cache needs three answers before
it is added:

1. **What invalidates it?** A TTL, an explicit eviction on write, or an event.
2. **How stale may it be?** Stated as a number, and correct for the use case.
3. **What happens on a miss storm?** When a hot key expires and a thousand requests arrive at once,
   something must collapse them — a single-flight lock or a probabilistic early refresh.

Guidance: cache-aside is the default and the easiest to reason about. Prefer a short TTL to a
clever invalidation scheme — the clever scheme is where the bugs live. Never cache authorisation
decisions without an explicit, short TTL and a revocation path (see `secure-service`). Never cache
inside a transaction. And measure the hit rate: a cache below roughly 80% is often adding latency
and a failure mode for very little.

## 7. Zero-downtime migrations

During a rolling deploy, the old and new code run against the same schema. Every migration must be
compatible with both.

**Expand → migrate → contract**, one release per stage:

1. **Expand.** Add the column, table, or index — nullable, defaulted, additive. Old code ignores it.
2. **Migrate.** Deploy code writing both old and new. Backfill existing rows in batches. Reads
   still use the old path.
3. **Switch.** Deploy code reading the new path. Both still written.
4. **Contract.** After the new path has survived a full rollback window, stop writing the old one
   and drop it, in its own release.

Never in a single step: dropping or renaming a column, adding `NOT NULL` without a default,
changing a type in place, or adding a constraint existing rows violate. Each makes the previous
release un-rollbackable — precisely when rollback is what you need.

Also:

- **Run migrations as a separate step**, before the application starts, with a lock so concurrent
  instances cannot race. A migration in application start-up turns a schema failure into a
  crash-looping fleet.
- **Create indexes concurrently** where supported. A blocking index build on a busy table is an
  outage.
- **Backfill in throttled, resumable, idempotent batches**, never one transaction over a large
  table — and never in the same migration as a schema change.
- **Forward-only.** Down-migrations that have never been run are fiction; roll forward.
- **Test against realistic volume.** A migration that takes two seconds on a laptop and forty
  minutes in production is the normal case, not the exception.
