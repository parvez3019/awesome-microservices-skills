# API Contracts — defaults

Loaded by Config Resolution when a project has no override, or as the base layer under an overlay.

---

## 1. Specification first

The specification is authored, reviewed, and agreed before the handler exists. It is the artefact
consumers read, contract tests verify, mocks are generated from, and clients are built against.

| Style | Specification | Registry / catalogue |
|---|---|---|
| REST / HTTP | OpenAPI 3.1 (JSON Schema 2020-12 compatible) | Any spec catalogue; lint with Spectral |
| Async / events | AsyncAPI 3 + the payload schema | Schema registry with a compatibility mode |
| gRPC | Protobuf `.proto` | Buf schema registry; `buf breaking` in CI |
| GraphQL | SDL schema | Schema check in CI against the live schema |

Keep the spec in the producing service's repository, next to the code it constrains, and lint it in
CI. A spec in a separate repository drifts within a quarter.

## 2. Modelling operations

Model what the consumer is trying to *do*, not what the database stores.

- **Resources are nouns; the operation is the verb.** `POST /orders/{id}/cancellation` beats
  `POST /orders/{id}?action=cancel` and beats making the client `PATCH` a status field and hope the
  side effects fire.
- **A state change with business meaning deserves its own operation.** Cancelling, approving, and
  refunding are not three ways of writing to `status`.
- **Prefer explicit sub-resources to overloaded PATCH.** A `PATCH` that triggers workflows is
  indistinguishable from data entry.
- **Bulk operations need a defined partial-failure story.** Either all-or-nothing, or a per-item
  result array. "Some of them worked" with a 200 and no detail is not a contract.
- **Never expose an internal enum.** Map `AWAITING_DOWNSTREAM_ACK_2` to something a consumer can
  reason about.

### Standard shapes

| Concern | Default |
|---|---|
| Identifiers | Opaque strings, typed in code; never leak sequential database keys |
| Timestamps | RFC 3339 UTC with offset (`2026-09-05T11:04:00Z`); name fields `*_at` |
| Money | Minor units as an integer plus an ISO-4217 currency; never a float |
| Enums | Documented closed set; consumers must tolerate unknown values (forward compatibility) |
| Booleans | Avoid for anything with a future third state; prefer a small enum |
| Nullability | Every field explicitly required or optional in the schema |
| Casing | One convention across the estate; state it and never mix |

## 3. Pagination, filtering, sorting

- **Cursor pagination** for anything that changes while being read — it is stable across inserts
  and cheap at depth. Offset pagination is acceptable only for small, static, user-facing lists.
- Always define a **default and a maximum page size**, and enforce the maximum server-side.
- Return the cursor for the next page and nothing else. Total counts are expensive and usually
  unused; add one only when a consumer asks.
- Constrain filtering and sorting to an enumerated set of fields. Free-form query languages become
  an unindexed query surface and, eventually, an incident.

## 4. Errors

Use HTTP status codes for the class of failure, and a stable machine-readable code for the specific
reason. `application/problem+json` (RFC 9457) is the default shape:

```json
{
  "type": "https://errors.example.com/insufficient-inventory",
  "title": "Insufficient inventory",
  "status": 409,
  "detail": "Only 2 units of SKU-1234 remain; 5 were requested.",
  "instance": "/orders/01J8Z",
  "code": "INSUFFICIENT_INVENTORY",
  "traceId": "0af7651916cd43dd8448eb211c80319c"
}
```

| Status | Meaning | Should the caller retry? |
|---|---|---|
| 400 | Malformed or invalid request | No — fix the request |
| 401 / 403 | Not authenticated / not permitted | No |
| 404 | Resource does not exist, or the caller may not know it does | No |
| 409 | Conflicts with current state | Only after re-reading state |
| 422 | Well-formed but violates a business rule | No |
| 429 | Rate limited | Yes, after `Retry-After` |
| 4xx generally | The caller's problem | No |
| 500 | Unexpected server fault | Yes, with backoff, if the operation is idempotent |
| 503 / 504 | Unavailable or timed out | Yes, with backoff and jitter |

Rules: the `code` is part of the contract and never changes meaning. Never return an exception
message, stack trace, or SQL to a caller (see `secure-service`). Always include the trace
identifier — it is what turns a support ticket into a query.

## 5. Idempotency

Any operation a client may retry needs a defined idempotency story, because the client *will* retry
after a timeout without knowing whether the first attempt landed.

- `GET`, `PUT`, `DELETE` are idempotent by definition — make sure the implementation actually is.
- `POST` that creates something needs an **`Idempotency-Key`** header supplied by the client.
- Store the key with the result. A replay within the retention window returns the original
  response, including its status code — not a duplicate resource and not a 409.
- State the retention window in the contract (24 hours is a common default) and what happens after
  it expires.
- The key's scope is the endpoint plus the authenticated caller. The same key with a *different*
  body is a client bug: return 422, not a silent replay.

## 6. Evolution and versioning

**Additive changes are always safe. Everything else is a break.**

| Change | Safe? |
|---|---|
| Add an optional response field | Yes — consumers must ignore unknown fields |
| Add an optional request field with a default | Yes |
| Add a new endpoint or operation | Yes |
| Add an enum value | Only if consumers were told to tolerate unknowns; otherwise breaking |
| Make an optional request field required | Breaking |
| Remove or rename any field | Breaking |
| Narrow a type or tighten validation | Breaking |
| Change a default | Breaking — behaviour changes for existing callers |
| Change an error code's meaning | Breaking |
| Loosen validation | Safe for requests, breaking for responses |

When a break is genuinely necessary:

1. **Add the new shape alongside the old.** Never mutate in place.
2. **Mark the old one deprecated** in the spec, with a sunset date (`Deprecation` and `Sunset`
   headers if the estate uses them).
3. **Measure who still uses it.** Per-consumer metrics on the deprecated path — without them, the
   sunset date is a guess.
4. **Migrate consumers**, then remove. `can-i-deploy` from `contract-testing` tells you when the
   last consumer is gone.

Version only on a real break. Whichever mechanism the estate uses — path, header, or media type —
use it consistently; a mixed strategy is worse than any single one.

## 7. Events

An event is a **fact**: something that happened, named in the past tense, published to whoever
cares. A command is an instruction to one owner. Do not put commands on an event stream.

Envelope every published event with metadata the consumer needs:

```json
{
  "id": "01J8Z...",                       // unique, for consumer-side deduplication
  "type": "orders.order.cancelled",       // namespaced, versioned separately from the payload
  "schemaVersion": 2,
  "occurredAt": "2026-09-05T11:04:00Z",   // when the fact happened, not when it was published
  "correlationId": "...",                 // ties the whole flow together
  "causationId": "...",                   // the message that caused this one
  "producer": "orders-service",
  "data": { }
}
```

- **Include what consumers need to act** without calling back. If you deliberately keep it thin,
  say so in the spec, because every consumer will then need a synchronous dependency on you.
- **Publish through the transactional outbox**, never as a second write beside the database commit
  (see `resilience-patterns`).
- **Consumers must be idempotent** on `id` and tolerate out-of-order and duplicate delivery.
- **Ordering is per partition key at best.** State the key. If a consumer needs global ordering,
  that is a design problem, not a broker setting.

### Registry compatibility modes

| Mode | Allows | Use when |
|---|---|---|
| `BACKWARD` | New schema reads old data — add optional, remove fields | Consumers upgrade first (most common default) |
| `FORWARD` | Old schema reads new data — add fields, remove optional | Producers upgrade first |
| `FULL` | Both | You cannot control upgrade order — the safest default for a wide fan-out |
| `NONE` | Anything | Never, on a topic with consumers you do not own |

A breaking event change means a **new topic or a new `type`**, both running until consumers move.
Mutating a schema in place on a live topic breaks consumers at read time, in production, with no
build-time warning.
