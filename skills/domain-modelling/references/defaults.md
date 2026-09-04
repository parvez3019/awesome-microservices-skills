# Domain Modelling — defaults

Loaded by Config Resolution when a project has no override, or as the base layer under an overlay.

---

## 1. The building blocks

| Block | Identity | Mutable | Model as this when |
|---|---|---|---|
| **Value object** | None — equal by value | No | The business cares about the value, not which instance it is |
| **Entity** | Yes — equal by ID | Yes, through its own methods | The business tracks this thing as it changes |
| **Aggregate** | The root's ID | Through the root only | A set of objects must change together to keep one invariant true |
| **Domain event** | Yes | Never | A business-meaningful fact has occurred |
| **Domain service** | None | Stateless | A rule genuinely belongs to no single type |
| **Factory** | — | — | Construction is complex and the result must be valid from birth |
| **Policy / specification** | None | No | A rule must be composable, named, and testable on its own |

### Value objects first

Value objects are the highest-return, most-skipped item on the list. A `Money` that refuses to add
two currencies eliminates a class of bug at compile time. A validated `EmailAddress` means nothing
downstream needs to re-check. A `DateRange` that cannot end before it starts removes an entire
category of test.

Make one whenever a value has **rules, units, or a format**: money, quantity, percentage, email,
phone, postcode, identifiers, date ranges, coordinates, SKU, IBAN. Requirements:

- **Immutable.** Operations return new instances (see `idempotency-and-immutability`).
- **Valid on construction.** The constructor rejects; there is no invalid instance to guard against.
- **Equality by value**, with a matching hash.
- **Behaviour included** — `Money.plus`, `DateRange.overlaps`, `Quantity.isZero`. A value object
  with no methods is a struct with a nicer name.
- **Self-describing failure.** `Quantity must be positive, was -3` beats `IllegalArgumentException`.

### Entities

An entity has identity that survives change: this order, this customer, this shipment. Two rules
carry most of the value:

- **No public setters.** Expose intent: `order.cancel(reason)`, not `order.setStatus(CANCELLED)`.
  A setter cannot enforce a rule, cannot record why, and cannot refuse.
- **Guard the transition, not the field.** Cancellation is not "status becomes CANCELLED"; it is
  "an order in PLACED or CONFIRMED, not yet dispatched, becomes CANCELLED and records why". That
  sentence is the method body.

### Aggregates

An aggregate is a **consistency boundary**: the smallest set of objects that must change together
to keep one invariant true. If you cannot state the invariant, you do not have an aggregate.

- *"An order's total equals the sum of its lines"* justifies `Order` owning `OrderLine`.
- *"Orders belong to customers"* does **not** justify `Customer` owning every order. That is a
  foreign key, and modelling it as containment produces an aggregate that grows without limit.

Rules that follow:

- **One aggregate modified per transaction.** Two roots in one commit means the boundary is wrong,
  or the consistency is actually eventual (see `cqrs-and-consistency`). Do not paper over it with a
  wider transaction.
- **Reference other aggregates by ID.** Object references invite lazy loads, unbounded graphs, and
  accidental transaction scope.
- **All changes go through the root**, which enforces the invariant on every one.
- **Keep them small.** A big aggregate is a write-contention hotspot, and contention only appears
  under production load.
- **Optimistic concurrency on the root** — a version checked on write. This is what actually makes
  the invariant hold with concurrent writers.

### Domain events

A domain event is a fact, named in the past tense, recorded by the aggregate that caused it:
`OrderCancelled`, not `CancelOrder`. They are how one aggregate's change triggers another's without
a shared transaction. The aggregate records them; the application layer publishes after commit —
through the outbox if they leave the service (see `resilience-patterns`, `api-contracts`).

Internal domain events and published integration events are **not the same thing**. The internal
one can be refactored freely; the published one is a contract. Translate at the boundary rather
than publishing your domain model.

### Domain services

Legitimate only when a rule genuinely belongs to no single type — a transfer between two accounts,
a pricing calculation across a basket and a promotion set. Tests:

- Would the rule feel arbitrary on any one of its arguments? Then a service is right.
- Does it read and write one entity's fields? It belongs on that entity.
- Is it stateless, and named for the operation rather than as a `*Manager`? Then it is a domain
  service rather than an application service.

## 2. Making illegal states unrepresentable

The strongest form of validation is a type that cannot express the invalid case.

Instead of a nullable field per state:

```
Order { status: Status, cancelledAt: Date?, cancelReason: String?, dispatchedAt: Date?, ... }
// which combinations are valid? A comment, at best.
```

model the states:

```
sealed Order = Placed | Confirmed | Cancelled(at, reason) | Dispatched(at, carrier)
// a Cancelled order has no carrier. It cannot be expressed.
```

Where the language supports sealed hierarchies, sum types, or discriminated unions, this converts
runtime checks into compile-time impossibility, and exhaustive matching means adding a state
produces compiler errors at every place that must handle it. Where it does not, approximate with
distinct types and private constructors, and accept that some invariants stay runtime checks.

Do not over-apply: a state machine with two states and no state-specific data is fine as an enum.

## 3. Ubiquitous language

The model uses the words the business uses, in this bounded context, with one meaning each.

- **Rename in code when the business renames.** A model using last year's vocabulary makes every
  conversation a translation exercise, and translation is where requirements get lost.
- **One word, one meaning, inside the context.** If "order" means two things, that is a context
  boundary, not a naming problem (see `service-boundaries`).
- **Ban technical suffixes on domain types.** `OrderData`, `OrderInfo`, `OrderHelper`,
  `OrderManager` all mean "we did not know what this is".
- **Method names are business verbs.** `approve`, `cancel`, `reserve`, `settle` — not `update`,
  `process`, `handle`.
- **Enum values are the business's words**, not internal codes.

## 4. Structuring the model

- **Package by feature, then layer** — `orders/domain`, not `domain/orders`. It keeps a capability
  together and makes an eventual extraction a directory move.
- **Constructors private, factories named** where construction has meaning: `Order.place(...)`,
  `Money.ofMinorUnits(...)`.
- **Fail loudly at the boundary of the model.** Once an object exists, its invariant holds — every
  method downstream can rely on it rather than re-checking.
- **The model does not know about persistence.** No ORM annotations, no lazy proxies, no
  `@Entity` on a domain type unless the project has deliberately accepted that coupling and
  recorded it (see `clean-architecture`, `data-access`).
- **Test the model directly.** Domain types have no I/O, so their tests are the fastest and most
  valuable in the suite, and the right place for mutation testing (see `test-strategy`).

## 5. When a rich domain model is the wrong answer

Not every service has a domain. A capability that reads a request, validates a few fields, writes a
row, and returns it has no invariants worth protecting, and wrapping it in aggregates and value
objects produces ceremony with no payoff.

Signals that a transaction script is the honest answer: no business rules beyond field validation;
no state machine; no operation that could be refused for a business reason; the language is CRUD
and the business agrees.

Signals that you need the model: the same rule appears in three handlers; a bug report says "it let
someone do X when Y"; the business has words for states and transitions; the answer to "can they do
this?" depends on more than one field.

Choose consciously, and record which one this service is. The expensive mistake is drifting from
one to the other without noticing.
