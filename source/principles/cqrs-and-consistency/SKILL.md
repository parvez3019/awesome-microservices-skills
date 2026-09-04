---
name: cqrs-and-consistency
description: "Decide how reads are served, how far they may lag behind writes, and who owns each piece of data. Covers the five levels of command-query separation and when each is earned, read models and projections with a stated staleness budget, rebuildability, event sourcing and its permanent costs, read-your-writes, and data ownership between services. Use when adding a read model or projection, choosing between one model and separate read and write paths, evaluating event sourcing, deciding whether a service may hold a copy of another's data, or when the user says 'CQRS', 'read model', 'projection', 'event sourcing', 'eventual consistency', or 'stale data'. This skill governs the read path and the consistency model — domain types belong to domain-modelling, query and transaction craft to data-access."
license: MIT
---

# CQRS and Consistency

Separating reads from writes is a spectrum with five steps, and almost every service that gets
hurt by it jumped to step four without needing steps one to three. Full asynchronous projections
solve real problems; they also introduce eventual consistency into the user's own session, which
is where the surprises are.

Two questions settle most decisions here: **what force requires the read path to differ from the
write path?** and **how stale may this data be, in seconds, for this specific use case?** A read
model with no answer to the second is not designed — it is just late.

## Config Resolution

1. Read `.msskills/config.yaml` in the repo root; look up `paths.consistency`.
2. A custom document exists at that path → read its frontmatter `mode`:
   - `override` → use it alone; ignore the defaults below.
   - `overlay` (default, or no `mode` key) → read [defaults](./references/defaults.md) first, then
     apply the custom document's sections on top, matched by exact heading; new sections append.
3. A path is configured but no file exists there → say which path is missing, then use the defaults.
4. No config file or no `paths.consistency` key → use [defaults](./references/defaults.md).
5. `.msskills/stack.md` exists → read its recorded CQRS level and datastore. Do not propose a step
   up the ladder without saying it is a step up, and why.
6. `.msskills/context-map.md` exists → respect the recorded data ownership. A read model built from
   another context's data must follow the integration pattern the map records
   (see `service-boundaries`).

## Self-Validation Checklist

**STOP after designing or changing a read path, a projection, or anything that holds a copy of
another service's data. Verify every check. Fix failures before presenting.**

1. **LEVEL JUSTIFIED**: Can you name the force that requires this level of separation — a read
   shape the write model cannot serve, or genuinely divergent read and write load? "Cleaner" or
   "more scalable" are not forces → collapse to one model.
2. **SMALLEST STEP**: Is this the lowest level on the ladder that solves the problem? Jumping
   straight to asynchronous projections when a purpose-built query would do → step down.
3. **STALENESS BUDGET**: For an asynchronous read model, is the acceptable lag stated as a number,
   monitored, and alerted on? An unstated budget means nobody can tell degradation from normal.
4. **READ-YOUR-WRITES**: What does a user see immediately after their own write? If the answer is
   "the old value" → handle it explicitly: return the result from the command, read from the write
   model for that user, or wait on a version token.
5. **REBUILDABLE**: Can this projection be rebuilt from its source, in a documented and exercised
   way? If not → it is a second source of truth and it will diverge.
6. **PROJECTION IDEMPOTENT**: Does replaying the same event twice leave the same result? Projections
   see duplicates and replays (see `idempotency-and-immutability`).
7. **POISON EVENT HANDLED**: Does one unprocessable event stop the projection for everyone? →
   dead-letter it and continue, loudly.
8. **VERSIONED**: Does changing the projection's logic rebuild into a new version and switch reads
   over, rather than mutating in place while consumers read?
9. **OWNERSHIP SINGLE**: Does exactly one service write this data, and does nothing else touch its
   store directly? (see `service-boundaries`)
10. **COPY JUSTIFIED**: For a local copy of another service's data — is it a snapshot that must not
    change (price at time of order), or a replica that must stay fresh? These need different
    designs; conflating them is how stale prices get charged.
11. **CONSISTENCY STATED**: Does the design say which operations are strongly consistent and which
    are eventual, and is that visible to the caller where it matters?
12. **EVENT SOURCING EARNED**: If events are the source of truth — is there an actual audit,
    temporal, or replay requirement, and has the permanent cost of schema evolution, deletion, and
    snapshots been accepted?

All checks pass → state "Read path holds: level <n>, staleness <budget>, rebuildable."

## Active Anti-Pattern Scan

Any box you can check is a defect. Fix it before presenting.

- [ ] **CQRS Cargo Cult**: separate command and query stacks over one table with one shape →
      collapse to one model.
- [ ] **Event Sourcing by Default**: an event store adopted with no audit, temporal, or replay
      requirement → state-based persistence plus domain events through the outbox gives you
      publication without the permanent cost.
- [ ] **Unbounded Projection Lag**: an asynchronous read model with no stated budget, no metric,
      and no alert.
- [ ] **Read-Your-Writes Broken**: a user updates something and immediately sees the old value.
- [ ] **Unrebuildable Projection**: a read store that has drifted and can only be fixed by hand →
      make the rebuild a first-class, exercised operation.
- [ ] **In-Place Projection Change**: projection logic altered while it serves reads, leaving a
      mix of old and new rows.
- [ ] **Silent Divergence**: no reconciliation or comparison between a projection and its source,
      so drift is discovered by a customer.
- [ ] **Stale Snapshot Treated as Live**: a cached copy of another service's data used as if it
      were current → decide whether it is a snapshot or a replica and design accordingly.
- [ ] **Shared Database**: another service reading these tables directly → publish an API or events.
- [ ] **Projection With Business Logic**: rules applied while projecting that the write side does
      not enforce → the read model has become a second, unauditable implementation of the domain.
- [ ] **Eventual Consistency Undisclosed**: an API that returns success while the effect is still
      pending, with nothing in the contract saying so (see `api-contracts`).

## Ambiguity Signals

Route these through `collaborative-judgment`. Each has two defensible answers.

- **How far up the ladder to go.** Each level buys capability and costs a consistency problem. The
  right level depends on load asymmetry you may not have measured yet — say when it is a guess.
- **How stale a read model may be.** Seconds are fine for a dashboard and unacceptable for a
  balance check. This is a product decision, not a technical one.
- **Event sourcing.** Genuinely right for audit-heavy, temporal, and replay-driven domains; a large
  and permanent cost everywhere else. The decision is effectively irreversible.
- **Own a replica or call for the data.** A replica removes a runtime dependency and adds staleness
  plus a second source of truth to reconcile (see `service-boundaries`).
- **Where the read model lives.** The same database is simple and couples the two paths' capacity;
  a separate store scales independently and adds infrastructure.
- **Synchronous or asynchronous projection.** Updating in the write transaction keeps reads
  consistent and slows writes; asynchronous is the reverse.
