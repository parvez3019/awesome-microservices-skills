---
name: idempotency-and-immutability
description: "Make operations safe to repeat and data safe to share. Covers designing idempotent commands, consumers and jobs, idempotency keys and deduplication stores, conditional updates and natural idempotency, exactly-once effect over at-least-once delivery, plus immutable value objects and events, defensive copying, safe publication across threads, append-only history versus in-place mutation, and where mutability is still the right answer. Use when writing an operation a client or broker may retry, a message handler, a scheduled job, a value type, or shared state, and when the user says 'idempotent', 'duplicate', 'retry safety', 'exactly once', 'immutable', 'defensive copy', or 'thread safe'. This skill governs repeatability and mutability — retry and breaker mechanics belong to resilience-patterns, the idempotency-key header contract to api-contracts."
license: MIT
---

# Idempotency and Immutability

Two properties, one underlying idea: **an operation you can repeat, and a value nobody can change
behind your back, both remove a class of bug rather than mitigating it.**

They matter more in a distributed system than anywhere else. Networks time out without telling the
caller whether the work happened, brokers deliver at least once, jobs get triggered twice by a
scheduler failover, and objects cross thread and module boundaries constantly. Retry logic and
locks manage those risks. Idempotency and immutability remove them.

## Config Resolution

1. Read `.msskills/config.yaml` in the repo root; look up `paths.idempotency`.
2. A custom document exists at that path → read its frontmatter `mode`:
   - `override` → use it alone; ignore the defaults below.
   - `overlay` (default, or no `mode` key) → read [defaults](./references/defaults.md) first, then
     apply the custom document's sections on top, matched by exact heading; new sections append.
3. A path is configured but no file exists there → say which path is missing, then use the defaults.
4. No config file or no `paths.idempotency` key → use [defaults](./references/defaults.md).
5. `.msskills/stack.md` exists → use its type-system idiom. Records, `readonly`, frozen objects,
   persistent collections, and value semantics differ by language; a pattern the language expresses
   natively beats one transliterated from another.

## Self-Validation Checklist

**STOP after writing or reviewing an operation that can be repeated, or a type that will be shared.
Verify every check. Fix failures before presenting.**

1. **REPEAT SAFE**: If this operation runs twice with the same input, is the end state the same as
   running it once? If not → make it idempotent before any retry is added anywhere.
2. **MECHANISM NAMED**: Which mechanism provides that — a client-supplied key, a conditional
   update, a natural upsert, or a state machine that ignores repeated transitions? "It probably
   will not happen twice" is not a mechanism.
3. **KEY SCOPED AND RETAINED**: For a key-based approach, is the key scoped to the operation and
   the caller, stored with the original response, and honoured for a stated window? Is a replay
   with the *same* key and a *different* body rejected rather than silently served?
4. **STORED ATOMICALLY**: Is the deduplication record written in the same transaction as the
   effect? Two separate writes reintroduce exactly the gap you were closing.
5. **CONSUMER IDEMPOTENT**: Does this message handler produce the same result on redelivery, and
   does it tolerate out-of-order arrival? At-least-once is the norm.
6. **SIDE EFFECTS COUNTED**: Are non-transactional effects — emails, payments, third-party calls —
   guarded individually? The database write may be idempotent while the email is sent twice.
7. **JOB SAFE**: For a scheduled or triggered job, what happens on overlapping runs or a
   double-trigger? A lease, a lock, or a naturally idempotent unit of work.
8. **COMPENSATION IDEMPOTENT**: Is every compensating or rollback action itself safe to repeat?
   It runs exactly when the system is already unreliable (see `resilience-patterns`).
9. **VALUES IMMUTABLE**: Are value objects, events, configuration, and anything shared across
   threads or modules immutable, with operations returning new instances?
10. **NO LEAKED MUTABLE STATE**: Does any type hand out its internal collection, array, date, or
    builder, so callers can mutate it from outside? → return copies or read-only views.
11. **COPY AT THE BOUNDARY**: Is mutable input copied on the way in, and mutable output copied on
    the way out, where the type cannot be immutable?
12. **SAFE PUBLICATION**: Is anything shared between threads either immutable, or published through
    a mechanism that guarantees visibility? A partially constructed object seen by another thread
    is a bug that only appears under load.
13. **HISTORY PRESERVED WHERE IT MATTERS**: For anything auditable, financial, or legally
    significant, is history appended rather than overwritten?

All checks pass → state "Repeat-safe via <mechanism>; <types> immutable."

## Active Anti-Pattern Scan

Any box you can check is a defect. Fix it before presenting.

- [ ] **Retry Without Idempotency**: a retry added to a non-idempotent write → duplicate orders,
      double charges, repeated emails.
- [ ] **Check-Then-Act**: `if (!exists) insert` with no unique constraint or conditional update →
      two concurrent callers both pass the check.
- [ ] **Non-Atomic Dedup**: the deduplication record and the effect written separately.
- [ ] **Key Without a Body Check**: the same idempotency key served for a different payload →
      returns the wrong result silently; reject it instead.
- [ ] **Unbounded Dedup Store**: keys retained forever with no eviction, or retained for less time
      than the maximum redelivery window.
- [ ] **Assumed Exactly-Once**: a consumer written as if the broker guarantees single delivery.
- [ ] **Duplicate Side Effect**: the database write is idempotent, the outbound email or payment is
      not.
- [ ] **Overlapping Job Runs**: a scheduled job with no lease, so a slow run overlaps the next.
- [ ] **Mutable Value Object**: a value type with setters, or one whose internal collection is
      reachable and mutable.
- [ ] **Leaked Internal Collection**: a getter returning the live list, so callers add and remove
      behind the owner's back.
- [ ] **Shared Mutable Configuration**: a settings object mutated at runtime and read concurrently.
- [ ] **Mutable Event**: a published or stored event whose fields can be changed after the fact —
      an event is a record of what happened and cannot be edited.
- [ ] **Mutable Map or Date as a Key**: an object mutated after being used as a key or placed in a
      set → it becomes unfindable.
- [ ] **Copy Constructor That Shares**: a "copy" that shallow-copies a mutable field, so both
      instances share it.
- [ ] **Destructive Update on Auditable Data**: overwriting a financial or legal record in place,
      losing the history.

## Ambiguity Signals

Route these through `collaborative-judgment`. Each has two defensible answers.

- **Where idempotency lives.** A client-supplied key is explicit and pushes work onto callers; a
  server-derived natural key needs no cooperation and can be wrong about what "the same request"
  means.
- **Deduplication retention window.** Longer is safer and costs storage and lookup time; shorter
  risks a late retry landing outside the window. Tie it to the maximum redelivery period, which you
  may have to measure.
- **Idempotent by dedup or by design.** A conditional update or upsert needs no extra store and
  constrains the data model; a dedup table is general and is one more thing to operate.
- **How far to take immutability.** Fully persistent structures are safest and allocate; in-place
  mutation behind a boundary is faster and requires discipline. On a genuinely hot path this is a
  real trade-off — measure rather than assume.
- **Defensive copying cost.** Copying every collection at every boundary is safe and can dominate
  a hot loop. An immutable type removes the question entirely, which is usually the better answer.
- **Append-only or update in place.** History is valuable, and it is also unbounded growth plus a
  deletion problem under privacy rules (see `secure-service`, `cqrs-and-consistency`).
