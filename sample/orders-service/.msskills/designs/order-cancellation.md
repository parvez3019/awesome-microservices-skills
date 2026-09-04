---
feature: order-cancellation
status: approved
levels: [L1, L2, L3, L4]
updated: 2026-09-05
---

# Order Cancellation

Worked example of what `design-service` produces. `implement-service` reads this file and refuses
to start unless `status` is `approved`.

## Design: Level 1 — Context

**Problem.** A customer can cancel an order until it has been dispatched. Today they contact
support, who cancel manually in the admin tool — around 400 tickets a week, and a median of six
hours before the warehouse is told, by which time roughly a fifth have already shipped.

**Actors.** The customer (via the storefront); support (via the admin tool, same API); the
warehouse system (consumes the outcome); finance (needs the refund initiated).

**Bounded context.** Order Management. Cancellation is part of an order's lifecycle and uses the
same ubiquitous language, so it belongs in the existing `orders-service`. It is **not** a new
service: no independent release cadence, no divergent scaling, one owning team
(`service-boundaries` checklist item 9 — no force applies).

**In scope.** Customer-initiated and support-initiated cancellation; releasing the inventory
reservation; initiating the refund; notifying the warehouse.

**Out of scope.** Partial cancellation of individual lines (a separate capability, deliberately
deferred); post-dispatch returns (a different process owned by the Returns context); the refund
itself — `payments-service` owns that, and we only initiate it.

**Constraints.** Cancellation must not be possible once dispatch has begun; that check is
authoritative in `warehouse-service`, not here. Refunds must be traceable end to end for audit.
Storefront p99 latency budget for this operation: 800 ms.

**Success measure.** 90% of eligible cancellations self-served within six months; cancelled orders
that ship anyway drop below 0.5%.

**Assumptions** (stated, not confirmed): current cancellation volume is estimated from support
ticket tags rather than measured; peak is assumed to follow the existing checkout profile.

## Design: Level 2 — Components

| Component | Responsibility | Layer | Owns | New/Existing |
|---|---|---|---|---|
| `Order` (aggregate) | The cancellation invariant and the state transition | Domain | `orders`, `order_lines` | Existing — extended |
| `CancellationPolicy` | Whether this order, in this state, may be cancelled | Domain | — | New |
| `CancelOrder` (use case) | Load, transition, persist, record the outbox event | Application | — | New |
| `OrderRepository` | Load and store the aggregate | Application (port) | — | Existing |
| `DispatchStatusPort` | Ask the warehouse whether dispatch has begun | Application (port) | — | New |
| `CancellationController` | `POST /v1/orders/{id}/cancellation` | Adapter | — | New |
| `WarehouseDispatchClient` | HTTP implementation of `DispatchStatusPort` | Adapter | — | New |
| `OutboxRepository` | Append events in the business transaction | Adapter | `outbox` | Existing |

**Invariant** (`data-and-cqrs`): *an order may move to `CANCELLED` only from `PLACED` or
`CONFIRMED`, and only when the warehouse has not begun dispatch.* The `Order` aggregate owns the
state transition; the dispatch fact comes from outside and is passed in as a parameter, so the
aggregate stays free of I/O.

**Data ownership.** `orders-service` owns order state. Inventory reservation is owned by
`inventory-service` and released by it in reaction to our event — we do not write to it. The refund
is owned by `payments-service`.

## Design: Level 3 — Interactions

```
Customer ──POST /v1/orders/{id}/cancellation──▶ orders-service
                                                    │
                        1. authorise: caller owns this order
                        2. load the aggregate
                        3. ── GET dispatch status ──▶ warehouse-service   [sync]
                        4. Order.cancel(dispatchStatus)
                        5. ┌ persist order (CANCELLED) ┐  one transaction
                           └ append OrderCancelled ────┘
                                                    │
                        6. Debezium ──▶ Kafka: orders.order.cancelled     [async]
                                          │
              ┌───────────────────────────┼──────────────────────────┐
              ▼                           ▼                          ▼
      inventory-service           payments-service           notification-service
      releases reservation        initiates refund           emails the customer
```

**Hop 3 — dispatch status (synchronous).** The caller needs the answer to decide, so this is a
call, not an event.

| Property | Value |
|---|---|
| Timeout | 300 ms (within the 800 ms budget, leaving room for the transaction) |
| Retry | 1 retry, exponential backoff with full jitter, only on timeout or 5xx |
| Circuit breaker | 50% failure rate over the last 20 calls; open 30 s; 3 half-open probes |
| Fallback | **Fail closed** — return 503 and do not cancel |
| Idempotent | Yes, it is a read |

**Decision — fail closed rather than degrade.** Cancelling an order that has already shipped costs
a physical return and a support ticket; refusing a cancellation costs the customer a retry. Recorded
below.

**Hops 6 — downstream reactions (asynchronous).** None of them is required for the cancellation to
be valid, so all three are event-driven. Published through the **transactional outbox**; no dual
write. Consumers are idempotent on the event `id` and tolerate redelivery and reordering.

**Consistency boundary.** The order's state is strongly consistent at step 5. Inventory release,
refund initiation, and notification are eventually consistent, budgeted at under 30 seconds and
alerted at 2 minutes.

**Idempotency.** `POST` carries an `Idempotency-Key`. A replay within 24 hours returns the original
response. Cancelling an already-cancelled order returns 200 with the existing state, not a 409 —
the caller's intent is satisfied.

**Trust boundary** (`secure-service`). The caller's JWT is verified in this service. The order is
loaded scoped to the authenticated customer, so an order belonging to someone else returns 404, not
403 — no existence disclosure. Support callers are authorised by a distinct `orders:cancel:any`
scope, and every such cancellation is audit-logged with the acting user.

**No compensation required.** The order transition is the only local write; everything downstream
reacts to a fact that has already happened. There is no saga here — a good outcome, and the reason
the boundary was drawn this way.

## Design: Level 4 — Contracts

### `POST /v1/orders/{orderId}/cancellation`

Headers: `Authorization: Bearer <jwt>` (required), `Idempotency-Key: <uuid>` (required).

```jsonc
// request
{ "reason": "CUSTOMER_CHANGED_MIND" }   // enum, required; consumers must tolerate new values

// 200 OK
{
  "orderId": "01J8ZQ...",
  "status": "CANCELLED",
  "cancelledAt": "2026-09-05T11:04:00Z",
  "refundInitiated": true
}
```

| Status | Code | Meaning | Retry? |
|---|---|---|---|
| 400 | `INVALID_REASON` | Reason not in the enum | No |
| 401 | — | Token missing or invalid | No |
| 404 | `ORDER_NOT_FOUND` | No such order **for this caller** | No |
| 409 | `ORDER_ALREADY_DISPATCHED` | Dispatch has begun | No |
| 422 | `IDEMPOTENCY_KEY_REUSED` | Same key, different body | No |
| 503 | `DISPATCH_STATUS_UNAVAILABLE` | Warehouse unreachable; breaker open | Yes, with backoff |

All errors use `application/problem+json` and carry `traceId`.

### Event `orders.order.cancelled` (Avro, registry compatibility `FULL`)

```jsonc
{
  "id": "01J8ZR...",                       // for consumer-side deduplication
  "type": "orders.order.cancelled",
  "schemaVersion": 1,
  "occurredAt": "2026-09-05T11:04:00Z",
  "correlationId": "...",
  "producer": "orders-service",
  "data": {
    "orderId": "01J8ZQ...",
    "customerId": "cus_...",
    "reason": "CUSTOMER_CHANGED_MIND",
    "lines": [ { "sku": "SKU-1234", "quantity": 2 } ],   // inventory needs these
    "refundAmount": { "minorUnits": 4599, "currency": "GBP" }
  }
}
```

Lines and refund amount are included deliberately so consumers need no callback. Partition key is
`orderId`, giving per-order ordering, which is all any consumer requires.

### Test obligations

| Behaviour | Level |
|---|---|
| The cancellation invariant, including every state transition | Unit (`Order`, `CancellationPolicy`) |
| 409 when dispatched; 404 for another customer's order; audit log on support cancellation | Component |
| Idempotency-Key replay returns the original response | Component |
| Warehouse timeout → 503, breaker opens after the threshold | Component, with a WireMock delay |
| Order row and outbox row committed atomically | Component, Testcontainers PostgreSQL |
| Storefront's expectations of the endpoint | Contract (Pact, consumer: `storefront-bff`) |
| `inventory-service` can consume `orders.order.cancelled` | Contract (message pact) |
| Customer cancels an order end to end | One end-to-end journey, and no more |

## Decisions Log

### 2026-09-05 — Cancellation lives in `orders-service`, not a new service

**Options:** a new `cancellation-service`; a capability inside `orders-service`.
**Decision:** inside `orders-service`.
**Because:** cancellation is a transition of the order aggregate and shares its invariant and
language. None of the four forces for a separate service applies. A separate service would have
needed a distributed transaction over the order's own state.
**Reversibility:** reversible — extraction later would follow the strangler-fig sequence.

### 2026-09-05 — Fail closed when the warehouse is unreachable

**Options:** degrade (cancel optimistically, reconcile later); fail closed (503).
**Decision:** fail closed.
**Because:** the cost of cancelling an order that has already shipped is a physical return and a
support ticket; the cost of a refused cancellation is a retry. Correctness outranks availability
here — a product decision, confirmed with the ops lead.
**Reversibility:** costly — customers would come to rely on optimistic cancellation.
**Consequences:** cancellation availability is now the product of this service's and the
warehouse's. Alert on the breaker opening.

### 2026-09-05 — Downstream effects are events, not synchronous calls

**Options:** call inventory, payments and notification in sequence; publish one event.
**Decision:** publish `orders.order.cancelled` through the transactional outbox.
**Because:** none of the three is required for the cancellation to be valid, and coupling to three
services would make cancellation the least available operation in the system.
**Reversibility:** costly — three consumers will bind to the schema.
**Consequences:** refund and inventory release are eventually consistent; the response reports
`refundInitiated: true` meaning *requested*, not *settled*. The event is a published contract
governed by `api-contracts`.

## Open Questions

- **Cancellation window after dispatch begins but before hand-off to the carrier** — the warehouse
  team believes there is a short reversible period. Needs their input; does not block v1, which
  treats any dispatch as final.
- **Partial cancellation** — explicitly deferred. Would change the aggregate's invariant, so it
  warrants its own design pass rather than an extension of this one.
