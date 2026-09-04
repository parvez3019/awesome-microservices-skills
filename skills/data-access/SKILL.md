---
name: data-access
description: "Write the persistence layer so it is correct under concurrency and fast under load. Covers repository implementations that return domain types, ORM discipline and the N+1 problem, explicit transaction boundaries and isolation levels, optimistic and pessimistic locking, connection pool sizing, keyset pagination, indexing and query plans, batching, caching with a defined invalidation story, and zero-downtime schema migrations. Use when writing a repository, a query, a migration, or a caching layer, when diagnosing a slow or deadlocking query, or when the user says 'repository', 'ORM', 'query', 'N+1', 'transaction', 'migration', 'index', 'connection pool', or 'lock'. This skill governs how data is stored and fetched — the shape of domain types belongs to domain-modelling, read models and consistency to cqrs-and-consistency."
license: MIT
---

# Data Access

The persistence layer is where clean models meet a database that does not care about them. Most of
what goes wrong here is invisible in development — an N+1 that is imperceptible over ten rows, a
transaction held open across a network call, a pool sized for a laptop, a migration that only fails
when there is data.

All of it surfaces at the same moment: production, under load.

## Config Resolution

1. Read `.msskills/config.yaml` in the repo root; look up `paths.persistence`.
2. A custom document exists at that path → read its frontmatter `mode`:
   - `override` → use it alone; ignore the defaults below.
   - `overlay` (default, or no `mode` key) → read [defaults](./references/defaults.md) first, then
     apply the custom document's sections on top, matched by exact heading; new sections append.
3. A path is configured but no file exists there → say which path is missing, then use the defaults.
4. No config file or no `paths.persistence` key → use [defaults](./references/defaults.md).
5. `.msskills/stack.md` exists → use its datastore, access style, and migration tool. Transactional
   guarantees, locking, and isolation differ enormously between a relational store, a document
   store, and a key-value store — name which assumptions the code relies on.

## Self-Validation Checklist

**STOP after writing or reviewing a repository, a query, a migration, or a cache. Verify every
check. Fix failures before presenting.**

1. **RETURNS DOMAIN TYPES**: Does the repository return domain objects rather than ORM entities,
   result sets, query builders, or framework page types? A leaked persistence type couples every
   caller to the database (see `clean-architecture`).
2. **WHOLE AGGREGATE**: Does a repository load and store a complete aggregate, with one repository
   per root and none for internal entities? (see `domain-modelling`)
3. **TRANSACTION BOUNDARY EXPLICIT**: Is the transaction opened and committed in the application
   layer, around one use case, and is its extent obvious from reading the code?
4. **NO I/O IN A TRANSACTION**: Does any transaction stay open across an HTTP call, a broker
   publish, or a long computation? → do the remote work outside it; a transaction holding locks
   while waiting on a network is how a database stalls.
5. **NO N+1**: Does any code path issue a query per element of a collection? → fetch in one query,
   or batch. Check loops, lazy-loaded associations, and mappers that resolve references.
6. **BOUNDED RESULT SET**: Does every query have a limit? An unbounded `SELECT` is a future
   out-of-memory error with a table that grew.
7. **INDEXED PREDICATE**: Is every filter, join, and sort column covered by an index? For a new
   query on a large table, has the plan been checked rather than assumed?
8. **CONCURRENCY HANDLED**: For a read-modify-write, what stops a lost update? Optimistic version
   check, a conditional update, or an explicit lock — one of them must be present and deliberate.
9. **LOCK ORDER CONSISTENT**: Where multiple rows are locked, are they always acquired in the same
   order? Inconsistent ordering is a deadlock waiting for concurrency.
10. **PARAMETERISED**: Is every query parameterised, with no string concatenation of input,
    including dynamic filters and sort columns? (see `secure-service`)
11. **KEYSET PAGINATION**: Does deep pagination use a cursor rather than a growing offset?
    `OFFSET 100000` scans and discards a hundred thousand rows.
12. **MIGRATION IS COMPATIBLE**: Is the schema change compatible with both the currently deployed
    code and the new code, so rollout *and* rollback are safe?
13. **BACKFILL IS SAFE**: Is any data backfill batched, throttled, resumable, and idempotent —
    never one transaction over a large table?
14. **CACHE HAS AN INVALIDATION STORY**: For anything cached, what invalidates it, what is the
    maximum staleness, and what happens on a miss storm? A cache without an answer to all three is
    a bug with better latency.
15. **POOL SIZED**: Is the connection pool sized deliberately against the database's limits and the
    number of instances, rather than left at a default?

All checks pass → state "Data access holds: <query bounded/indexed>, transaction <scope>,
concurrency <mechanism>."

## Active Anti-Pattern Scan

Any box you can check is a defect. Fix it before presenting.

- [ ] **N+1 Query**: a query inside a loop, or lazy loading triggered per element → single query
      or batch fetch.
- [ ] **Leaked ORM Entity**: a managed entity, lazy proxy, or query builder returned past the
      repository → map to a domain type at the boundary.
- [ ] **Repository per Entity**: repositories for objects inside an aggregate → roots only.
- [ ] **Fat Repository**: a repository with dozens of bespoke finders serving screens → those are
      queries, not aggregate loading (see `cqrs-and-consistency`).
- [ ] **Unbounded Query**: `SELECT` with no limit, or a `findAll` on a growing table.
- [ ] **Offset Pagination at Depth**: `OFFSET` growing with page number on a large table → keyset.
- [ ] **Transaction Around a Network Call**: an HTTP request, broker publish, or external API call
      inside an open transaction.
- [ ] **Transaction per Repository Call**: each save its own transaction, so a use case cannot be
      atomic → own the boundary in the application layer.
- [ ] **Lost Update**: read, modify in memory, write back, with no version check or conditional
      update.
- [ ] **Nested Transaction Confusion**: relying on framework propagation nobody can explain →
      make the boundary explicit.
- [ ] **String-Built Query**: any concatenation of input into SQL, a query document, or a sort
      clause.
- [ ] **Destructive Migration**: a column or table dropped, renamed, or narrowed in the same
      release that stops using it → expand, migrate, contract.
- [ ] **Blocking Index Build**: an index created without the concurrent option on a busy table.
- [ ] **Migration at Startup**: schema changes run by the application on boot, so a failed
      migration crash-loops the fleet and concurrent instances race.
- [ ] **Cache Without Invalidation**: cached values with no TTL and no invalidation path → stale
      forever, and impossible to reason about.
- [ ] **Default Pool Size**: a connection pool left at the library default while running many
      instances → the database hits its connection limit before the service saturates.
- [ ] **`SELECT *`**: fetching every column, including large ones nobody reads.

## Ambiguity Signals

Route these through `collaborative-judgment`. Each has two defensible answers.

- **ORM or hand-written SQL.** An ORM is productive for aggregate loading and obstructive for
  reporting queries. Using both — ORM for writes, SQL for reads — is a legitimate and common answer.
- **Optimistic or pessimistic locking.** Optimistic is cheaper and pushes retry onto the caller;
  pessimistic serialises and risks deadlocks and timeouts. Depends on contention you may not have
  measured.
- **Isolation level.** A stronger level removes anomalies and costs throughput. Read committed plus
  explicit version checks is usually right, and "usually" is doing real work in that sentence.
- **Where to cache.** In-process is fastest and inconsistent across instances; a shared cache is
  consistent and adds a dependency and a failure mode.
- **Denormalising for read performance.** Buys query speed, costs a synchronisation obligation
  forever.
- **Whether to add an index.** Every index speeds reads and slows writes, and consumes storage. On
  a hot write path this is a genuine trade-off.
- **Soft delete or real delete.** Soft delete preserves history and quietly poisons every
  subsequent query that forgets the predicate.
