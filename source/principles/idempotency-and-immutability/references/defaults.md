# Idempotency and Immutability — defaults

Loaded by Config Resolution when a project has no override, or as the base layer under an overlay.

---

## 1. Why repeatability is not optional

A caller whose request times out does not know whether the work happened. It has exactly two
options: retry, or give up on work that may already have succeeded. Every real client retries.

So the question is never *"will this be called twice?"* — it is *"what happens when it is?"* The
same applies to brokers (at-least-once delivery is the norm), schedulers (failover double-triggers),
service meshes (edge retries), and users (double-clicks).

**Exactly-once delivery does not exist across a network. Exactly-once *effect* does**, and it is
built from at-least-once delivery plus an idempotent receiver.

## 2. Four ways to be idempotent

In rough order of preference — the earlier ones need no extra machinery.

**1. Naturally idempotent operations.** Setting a value, an upsert on a natural key, adding to a
set. `PUT` semantics. Nothing to do.

**2. Conditional update.** Make the transition itself atomic and self-guarding:

```sql
UPDATE orders SET status = 'CANCELLED', cancelled_at = ?
WHERE id = ? AND status IN ('PLACED', 'CONFIRMED')
-- 0 rows: already cancelled, or not cancellable. Distinguish by reading.
```

The second execution changes nothing. No dedup store, no key. This is the cheapest correct answer
and it is under-used.

**3. State machine that ignores repeats.** Model the transition, not the assignment. Cancelling an
already-cancelled order returns success with the existing state — the caller's intent is satisfied.
Returning a conflict for a repeated request punishes correct retry behaviour.

**4. Deduplication with a key.** The general answer when the others do not apply, and the only one
for "create a new thing".

## 3. Idempotency keys

For any operation that creates something, the client supplies a key (see `api-contracts` for the
header contract).

Requirements, all of them:

- **Scope** = operation + authenticated caller. The same key from a different caller is a different
  request.
- **Store the key with the outcome** — status, body, and enough to reproduce the original response
  exactly, including its status code.
- **Write the key record and the effect in one transaction.** If they are separate writes, a crash
  between them recreates the very gap you are closing.
- **A replay returns the original response**, unchanged. Not a duplicate resource, and not a 409.
- **Same key, different body → reject** (422). Serving the first result for a different request is
  silent, and it is the worst possible outcome.
- **Retention window**, stated in the contract, longer than any realistic client retry — 24 hours
  is a common default. Evict beyond it, or the store grows without bound.
- **Concurrent requests with the same key**: the second must not proceed in parallel. A unique
  constraint on the key gives you this for free — let the insert fail and treat the failure as
  "already in flight or done".

The last point is worth stating plainly: **let the database enforce uniqueness.** `if (!exists)
insert` is a check-then-act race that two concurrent callers both pass. A unique constraint is the
only version that holds under concurrency.

## 4. Idempotent consumers

At-least-once delivery means every handler will see duplicates, and rebalances mean it will see
messages out of order.

**Inbox pattern** — record the processed message ID in the same transaction as the effect:

```
BEGIN
  INSERT INTO inbox (message_id) VALUES (?)   -- unique constraint; conflict = already processed
  ... apply the effect ...
COMMIT
```

A duplicate hits the constraint, the transaction rolls back, the message is acknowledged. Simple,
durable, and the table is trivially prunable — prune beyond the broker's maximum redelivery window,
not before.

Alternatives: make the effect naturally idempotent (§2), or track a per-key version and ignore
events at or below the version already applied — which also handles out-of-order delivery.

**Tolerate reordering.** Ordering holds per partition key at best, and a rebalance breaks even
that. If a handler only works when events arrive in order, that assumption belongs in the design
document, not in the code by accident (see `api-contracts`).

## 5. Side effects that are not database writes

The database write can be perfectly idempotent while the email goes out twice. Every non-
transactional effect needs its own guard:

| Effect | Guard |
|---|---|
| Email, SMS, push | Deduplicate on a derived key before sending; most providers accept one |
| Payment or refund | The provider's own idempotency key — never invent your own scheme |
| Third-party create | Their idempotency mechanism, or a local record written atomically first |
| File or object write | Deterministic key, write-if-absent |
| Outbound event | The outbox makes publication at-least-once; consumers deduplicate on event ID |

The general pattern: **record the intent transactionally, perform the effect afterwards, and record
completion.** A crash between intent and effect means a retry; a crash between effect and
completion means a duplicate — which is why the receiver must deduplicate too.

## 6. Jobs and schedulers

Scheduled work is triggered twice more often than teams expect — failover, a manual re-run, an
overlapping slow execution.

- **Take a lease** with a TTL, not an unbounded lock. A lock held by a crashed instance blocks
  forever; a lease expires.
- **Make the unit of work idempotent** so an overlap is harmless rather than merely unlikely.
- **Bound the run.** A job with no timeout eventually overlaps itself.
- **Checkpoint long jobs** so a resumed run does not redo completed work.
- **Never assume single execution** because "the scheduler guarantees it". None of them do, across
  a failover.

## 7. Immutability

An immutable value cannot be changed after construction. That single property gives you: thread
safety with no synchronisation, safe sharing with no defensive copying, valid-forever invariants
checked once, and safe use as a map key.

**Make immutable by default:**

- Value objects — money, quantities, ranges, identifiers (see `domain-modelling`).
- Domain and integration events. An event records what happened; editing it is meaningless.
- Configuration, once loaded (see `config-and-dependencies`).
- DTOs crossing a boundary.
- Anything shared between threads.

**How, in practice:**

- Use the language's native construct — records, `readonly`/`val`, frozen objects, data classes.
- **Operations return new instances**: `money.plus(other)` returns a new `Money`.
- **Copy collections on the way in and out**, or store an immutable collection type. A constructor
  that stores the caller's list keeps a reference the caller can still mutate.
- **Deep, not shallow.** A "copy" that shares a mutable field is not a copy. Watch dates, arrays,
  nested objects, and builders.
- **Read-only views are not immutability.** An unmodifiable wrapper over a list the owner still
  mutates changes under the reader. It is still better than handing out the live list.
- **`with`-style copies** for a changed field: `order.withStatus(CANCELLED)`. Where a language has
  no built-in support and the object is large, a builder that produces immutable instances is the
  usual compromise.

**Safe publication.** In a language with a memory model, an object shared between threads must be
either immutable or published through a mechanism that guarantees visibility — a final field, a
volatile write, a concurrent collection, a lock. A partially constructed object seen by another
thread is a real bug, it does not reproduce locally, and it appears under production load.

## 8. Where mutability is right

Immutability is a default, not a rule.

- **Entities have identity and change over time** — that is what makes them entities. Their state
  changes through methods that enforce invariants, not through setters (see `domain-modelling`).
- **Local, unshared state** inside a method: a builder, an accumulator, a buffer. Never escapes,
  never shared, no benefit to making it immutable.
- **Genuinely hot paths** where allocation dominates. Measure first — this is asserted far more
  often than it is true, and the safe version is fast enough almost always.
- **Large structures with small deltas**, where copying is prohibitive and a persistent data
  structure is unavailable.

The rule that survives all four: **contain the mutation.** Mutable state that never escapes its
owner is manageable. Mutable state shared across a boundary is where the bug lives.

## 9. Append-only history

For anything auditable — money, permissions, legal records, order lifecycles — record what happened
rather than overwriting what is:

```
-- instead of: UPDATE accounts SET balance = ?
INSERT INTO ledger_entries (account_id, amount, reason, occurred_at) VALUES (...)
-- balance is derived, and every change has a reason and a time
```

You gain a complete audit trail, the ability to answer "what did this look like then", and
debuggability that no log gives you. You pay in unbounded growth, a snapshot or projection for
current state (see `cqrs-and-consistency`), and a real deletion problem under privacy rules — plan
crypto-shredding or field-level erasure up front, not after the first request (see
`secure-service`).

This is not event sourcing. It is one table modelled as facts rather than as state, which is a much
smaller commitment and available to any service.
