---
name: implement-service
description: "Turn an approved design into working code and tests, built inside-out one layer at a time, with every principle's checklist run before anything is presented. Covers implementation ordering, per-component validation against architecture, data, resilience, security and configuration rules, writing tests alongside the code at the right level, and pacing the work so review happens while it is still cheap. Use after design-service has produced an approved blueprint, or when the user says 'implement', 'build it', 'code this up', or 'write the service'. This workflow writes code — for changing existing code safely see refactor-safely, for auditing it see review-service."
license: MIT
---

# Implement a Service

The failure mode this prevents is a large, plausible, unreviewable diff. Code arrives in layers,
each validated against the principles before it is shown, each small enough that a human can
actually read it.

## Required Skills

Read and apply:

1. `clean-architecture` — layer placement and dependency direction for every file. (always)
2. `test-strategy` — every component ships with tests at the right level. (always)
3. `collaborative-judgment` — deviations and trade-offs are surfaced, not absorbed. (always)
4. `domain-modelling` — aggregates, entities, value objects, where behaviour lives. (conditional:
   domain types)
5. `data-access` — repositories, queries, transactions, migrations, caches. (conditional:
   persistence)
6. `cqrs-and-consistency` — read models and projections. (conditional: a separate read path)
7. `infrastructure-adapters` — ports, clients, consumers, publishers, SDK wrappers. (conditional:
   the adapter layer)
8. `resilience-patterns` — timeouts, retries, breakers, outbox. (conditional: any call leaving the
   process, any message handler)
9. `idempotency-and-immutability` — retry safety and shared state. (conditional: retryable
   operations, message handlers, value types)
10. `secure-service` — authorisation, validation, secrets, output hygiene. (conditional: any trust
    boundary — handlers, clients, queries, anything touching credentials or personal data)
11. `api-contracts` — the shape of anything crossing a boundary. (conditional: endpoints, schemas,
    published events)
12. `api-protocols` — protocol-specific craft. (conditional: GraphQL, gRPC, WebSocket or SSE)
13. `config-and-dependencies` — settings, flags, new libraries. (conditional: config or dependency
    changes)
14. `contract-testing` — cross-service agreement. (conditional: an integration with another service)

## Workflow

### Step 1 — Establish the ground

1. Read `.msskills/stack.md`. Absent → say once that `stack-profile` would make the generated code
   match the project's idiom, then infer conventions from the repository and proceed.
2. Read `.msskills/decisions.md` — recorded decisions are binding.
3. Find the blueprint in `.msskills/designs/` for this feature.

**Design gate.** Check the blueprint's frontmatter:

- `status: approved` → proceed **with an approved design**.
- `status: complete` → already implemented. If this is new scope, recommend `design-service` for a
  fresh pass. If the user confirms, continue.
- `status: draft`, or no blueprint → **STOP**: "There is no approved design for this. Run
  `/design-service` first, or shall I proceed from what we have discussed?" On confirmation,
  record it as a decision and continue **without an approved design** — every principle still
  applies; there is simply no agreed contract to build against.

**Level gate.** With a blueprint, check which levels it contains. Missing L3 or L4 means the
failure behaviour or the contracts were never agreed — **STOP**, say which are missing, and ask
whether to proceed and fill them as you go or to design them first.

4. **Read the existing code** before writing any. Find the patterns already in use — error
   handling, naming, test structure, package layout — and match them. Code that is correct but
   foreign is a review burden.

### Step 2 — Plan and agree the order

Derive the component list from the blueprint's L2, or classify it yourself against
`clean-architecture` if there is no blueprint.

Plan **inside-out**: start at the innermost layer with no outward dependencies and work outward, so
each component's dependencies already exist when it is built. Typically: domain types → domain
logic → ports → application use cases → adapters → wiring and configuration.

Present the plan — the ordered component list, each one's layer, and what already exists that you
will reuse. Then ask for a review mode:

> How should we review this?
> 1. **Layer by layer** (recommended) — implement a full layer, pause for review, then the next.
> 2. **All at once** — implement end to end, review the complete result.
> 3. **Component by component** — pause after each one.

Default to layer by layer. **STOP** — do not write code against an unagreed plan. If the user
corrects the plan, revise and re-present it.

### Step 3 — Implement, component by component

For each component, in the planned order, write **code and its tests together**.

Before writing:

- **Prefer what exists.** Does the standard library, an existing dependency, or existing code in
  this repository already do this? Use it. Adding a dependency runs `config-and-dependencies`
  first.
- **Prefer the simpler shape.** No abstraction without a named force (`clean-architecture`).

While writing, apply the principles that govern this component:

| Component kind | Apply |
|---|---|
| Domain type or aggregate | `domain-modelling`, `clean-architecture`, `idempotency-and-immutability` |
| Repository, query, or migration | `data-access`, `clean-architecture` |
| Read model or projection | `cqrs-and-consistency`, `data-access` |
| Use case / handler | `clean-architecture`, `secure-service`, `idempotency-and-immutability` |
| Inbound adapter (HTTP, consumer) | `infrastructure-adapters`, `api-contracts`, `api-protocols`, `secure-service` |
| Outbound adapter (client, publisher) | `infrastructure-adapters`, `resilience-patterns`, `secure-service` |
| Configuration or flag | `config-and-dependencies` |
| Tests | `test-strategy`, plus `contract-testing` at a service boundary |

**Post-generation verification — before showing anything:**

1. Run the **Self-Validation Checklist** of every applicable principle against every function and
   type in the component. The checklists say STOP and verify; do that literally.
2. Run every applicable **Active Anti-Pattern Scan**. Check each box honestly.
3. Fix every violation found. Do not present code you know fails a check.
4. Collect flagged **Ambiguity Signals** and present them through `collaborative-judgment` *before*
   showing the code. Never resolve a real trade-off silently to keep momentum.
5. **Run the tests** you wrote, if the environment allows. Report the result. If you could not run
   them, say so — never imply tests passed when they were only written.
6. Present with a one-line compliance note when clean; be verbose only when reporting a violation
   you fixed or a decision you need.

**Pace by the chosen review mode.** In every mode, one exception overrides it: a component needing
a significant deviation — a new dependency, a changed contract, unexpected complexity, a blueprint
decision that turns out to be unworkable — **STOPS** immediately for discussion, whatever the mode.

### Step 4 — Verify across components

Once the components exist:

1. **Wire it and run it.** Start the service. A set of components that has never been assembled is
   not an implementation.
2. **Run the whole suite**, not just the new tests. Report failures with their output.
3. **Trace one flow end to end** against the blueprint's L3: does the real code follow the agreed
   interactions, with the agreed timeouts and failure behaviour?
4. **Verify the contracts** against L4 — request and response shapes, error catalogue, event
   schemas. Flag every deviation; do not quietly ship a different contract from the approved one.
5. **Check the failure paths actually work**: the timeout fires, the breaker opens, the duplicate
   message is ignored, the compensation runs. These are the paths that only execute on the worst
   day (`test-strategy`).

### Step 5 — Close out

- Update the blueprint: `status: complete`, and record any decision made during implementation in
  its Decisions Log.
- Append cross-cutting decisions to `.msskills/decisions.md`.
- Summarise: what was built, what was reused, which tests cover what, what is deliberately not done.
- Name the follow-ups explicitly rather than leaving them implicit.
- Recommend `review-service` for an independent audit before the change is merged.

## Rules

- **Never present code that fails a checklist.** Fix it first.
- **Tests are part of the component**, not a later step.
- **Never claim a test passed** without running it.
- **A deviation from the approved design stops the work.** Surface it; the design is what was
  agreed, and changing it is the user's call.
- **Match the repository's conventions** over this library's examples.
- **Do not touch unrelated code.** Improvements you notice go in the close-out list, not in the diff.
