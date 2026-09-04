# Design First — defaults

Loaded by Config Resolution when a project has no override, or as the base layer under an overlay.

---

## 1. Depth calibration

Propose a depth in the first message and let the user cut it. Never announce four levels for a
two-line change; never skip to contracts for a new bounded context.

| Change | Levels | Typical shape |
|---|---|---|
| New bounded context or service | L1 → L4 | Several exchanges per level; `service-boundaries` runs at L1 |
| New capability inside an existing service | L2 → L4 | L1 collapses to one paragraph of restated context |
| New endpoint or event on an existing capability | L3 → L4 | Components already exist; the flow and contract are the work |
| Field added, validation changed, error tightened | L4 | Contract change only, with a compatibility check |
| Bug fix | none | Use `refactor-safely` or the bug workflow; design is not the tool |
| Extracting a service from a monolith | L1 → L4 | L1 is the whole argument; most extractions fail at L1, not L4 |

State the proposal explicitly: *"This looks like an L2→L4 change — the context is settled by the
existing `orders` service. Shall we start at components, or do you want to revisit the boundary?"*

## 2. Question banks

Ask the few that matter for this change. Asking all of them is an interrogation, not facilitation.

### L1 — Context

- What problem does this solve, and for whom? What happens today without it?
- Which bounded context does this belong to? Does an existing service already own this language?
- What is explicitly **out** of scope?
- What must remain true — compliance, data residency, latency budget, existing contracts?
- What scale are we designing for: order of magnitude of requests, data volume, growth?
- How will we know it worked? What is the measurable outcome?
- What is the deadline, and what would we cut first if we had to?

### L2 — Components

- What are the nouns of this problem? Which are entities with identity, which are values?
- Which component owns each piece of data? Who else needs to read it, and how do they get it?
- Which of these exist already? What are we reusing rather than building?
- Which layer does each component live in — domain, application, adapter? (see `clean-architecture`)
- What is the aggregate boundary, and what invariant justifies it? (see `domain-modelling`)
- Does anything here cross a bounded context? What is the anti-corruption layer?

### L3 — Interactions

- For each hop: does the caller need the answer to complete its own work, or is it telling
  someone something happened? The first is a call; the second is an event.
- What is the timeout on each outbound call, and what does the caller do when it expires?
- What happens if this step succeeds and the next one fails? Is compensation needed, or is retry
  enough? (see `resilience-patterns`)
- Is the operation idempotent? If the caller retries, what stops a duplicate?
- Where is the consistency boundary? What is allowed to be stale, and for how long?
- What is the ordering guarantee on each event stream, and does the consumer actually need it?
- What does a partial failure look like to the user?

### L4 — Contracts

- What is the request and response shape, field by field, with types and optionality?
- What are the error responses, and what should the caller do with each?
- How is the request authenticated and authorised? Who is allowed to see which fields?
  (see `secure-service`)
- What is the idempotency key, and how long is it honoured?
- How does the consumer paginate, filter, and sort?
- What is the event schema, and what is its compatibility mode? (see `api-contracts`)
- What are the validation rules, and what is the message when each fails?
- Which tests prove this contract — and which of them are contract tests versus component tests?
  (see `test-strategy`, `contract-testing`)

## 3. Gate discipline

At the end of a level, present the artefact, then one closing block:

```markdown
**L2 complete.** Open questions: <list, or "none">.

Next: **L3 Interactions** — we settle sync vs async on the payment hop, the consistency boundary
around inventory, and what checkout does when the payment provider times out.

Proceed to L3, revise L2, or stop here?
```

- **Never descend on an implicit yes.** "Looks good" on a component list is approval of L2, not
  permission to write the contracts.
- **A user who says "just do it" is choosing a depth**, not waiving design. Collapse to the
  minimum level for the change, record that they chose speed, and proceed.
- **Revision does not restart the climb.** Changed components invalidate L3 and L4 for the parts
  they touch — say which parts, and re-derive only those.

## 4. The blueprint document

Write to `.msskills/designs/<feature-slug>.md`, incrementally, as each level completes. The
implementation workflow reads this file and refuses to start without `status: approved`.

```markdown
---
feature: order-cancellation
status: draft          # draft → approved → complete
levels: [L1, L2]       # levels completed so far
updated: 2026-09-05
---

# Order Cancellation

## Design: Level 1 — Context
Problem, actors, bounded context, in/out of scope, constraints, success measure.
**Assumptions:** anything inferred rather than confirmed, listed explicitly.

## Design: Level 2 — Components
| Component | Responsibility | Layer | Owns | New/Existing |

## Design: Level 3 — Interactions
Flow per use case. Per hop: sync or async, timeout, retry, failure behaviour, idempotency.
Consistency boundary and what may be stale.

## Design: Level 4 — Contracts
Request/response schemas, error catalogue, auth, idempotency key, event schemas and
compatibility mode, validation rules, test obligations.

## Decisions Log
Each entry: the question, options considered, the choice, the reason, reversibility.
See `collaborative-judgment` for the format.

## Open Questions
Unresolved items, each with who needs to answer it and what is blocked until they do.
```

Update `status` to `approved` only when the user approves L4 — or approves the final level of a
calibrated shorter climb. Set `complete` when implementation lands.

## 5. What "no code" means

At L4 you may write, because these are the contract:

- OpenAPI / AsyncAPI fragments, JSON Schema, protobuf messages
- Interface and port signatures, type and DTO shapes
- Event payload examples
- Error catalogues and status code tables

You may not write, because these are implementation:

- Method bodies, control flow, queries
- Framework wiring, configuration files, migrations
- Tests — the *obligations* are L4; the tests themselves belong to implementation

The line is simple: if changing it would not change what a consumer sees, it is not design.
