---
name: design-service
description: "Run a design session before code exists, producing an approved blueprint the implementation workflow can build from. Climbs the four design levels — context, components, interactions, contracts — pausing for approval at each, and pulls in boundary, data, API, resilience, and security thinking at the level where each belongs. Use before building a new service, capability, endpoint, or integration, when a change needs agreement before code, or when the user says 'design this', 'blueprint', 'spec this out', 'how should we build', or 'plan the service'. Produces .msskills/designs/<feature>.md; implement-service refuses to start without it."
license: MIT
---

# Design a Service

Facilitates a design conversation and leaves behind a document that outlives it. The output is not
a diagram — it is a set of decisions with their reasons, which is what makes the implementation
reviewable six months later.

## Required Skills

Read and apply, in this order:

1. `design-first` — the four-level ladder, gate discipline, and the blueprint format. (always)
2. `collaborative-judgment` — every trade-off is presented as options and recorded. (always)
3. `service-boundaries` — which context this belongs to, whether it needs a new service, who owns
   the data. (always at L1; the whole of L1 for a new service)
4. `domain-modelling` — aggregates, invariants, value objects, ubiquitous language. (at L2)
5. `cqrs-and-consistency` — the read path, data ownership, staleness budgets. (at L2 and L3)
6. `api-protocols` — which protocol fits the interaction shape. (at L2, before contracts exist)
7. `resilience-patterns` — the failure behaviour of every hop. (at L3)
8. `idempotency-and-immutability` — what happens when a hop is retried. (at L3)
9. `api-contracts` — the shape of everything crossing a boundary. (at L4)
10. `secure-service` — trust boundaries and authorisation. (at L3 and L4)
11. `test-strategy` — which level proves each behaviour. (at L4, as obligations only)

## Workflow

### Step 0 — Orient

1. Read `.msskills/stack.md`. Absent → say once that running `stack-profile` first will make the
   design concrete, then continue in neutral terms.
2. Read `.msskills/decisions.md` and `.msskills/context-map.md` if present. Recorded decisions are
   settled; apply them rather than re-asking.
3. Scan `.msskills/designs/` for an existing blueprint covering this feature.
   - **Found, `status: draft`** → resume at the first incomplete level. Show what is already
     decided before continuing.
   - **Found, `status: approved`** → this design is done. Ask whether the request is new scope (a
     fresh design) or a revision (which levels it invalidates).
   - **Found, `status: complete`** → it is already built. Treat the request as a change: say which
     levels it reopens.
   - **Not found** → new design.

### Step 1 — Calibrate the depth

Propose a depth from the change's shape, using the table in `design-first`. Say which levels you
propose to climb and why, and let the user cut it.

> This adds one endpoint to the existing `orders` service, so the context and components are
> settled — I would start at **L3 Interactions** and finish at **L4 Contracts**. Start at L3, or do
> you want to revisit the boundary first?

**STOP.** Do not begin until the depth is agreed. A user who says "just design it" has chosen the
minimum depth for the change — record that they chose speed and proceed.

### Step 2 — Climb, one level per exchange

For each level in the agreed range:

1. **Read before asking.** Ground the level in the repository: existing services, tables,
   endpoints, events. A question whose answer is in the code is a wasted turn.
2. **Apply the level's skills** from Required Skills. Their Self-Validation Checklists apply to
   design decisions, not only to code — an aggregate proposed at L2 must still name its invariant.
3. **Ask what you cannot know.** Domain rules, volumes, priorities, and what the business would
   accept when things fail are not in the repository.
4. **Present the level's artefact** in the format from `design-first`, with assumptions marked and
   unknowns listed.
5. **Route every trade-off** through `collaborative-judgment`. Do not settle a real decision inside
   the prose.
6. **Write the level into the blueprint** at `.msskills/designs/<feature-slug>.md` before moving
   on, including the options rejected and why.
7. **Close the gate** explicitly: what this level settled, what remains open, what the next level
   will decide. **STOP** and wait.

Level-specific obligations beyond `design-first`:

- **L1** — run `service-boundaries` properly. For anything proposed as a new service, its checklist
  item 9 must be answered with a named force, not "cleaner". Most bad architectures are approved at
  L1 by a question nobody asked.
- **L2** — every aggregate names its invariant (`domain-modelling`); every component names its
  layer (`clean-architecture`); data ownership is explicit and single-writer, and each piece of
  borrowed data is classified as query, replica, or snapshot (`cqrs-and-consistency`). Where an
  interface is exposed, the protocol is chosen from the interaction shape (`api-protocols`).
- **L3** — every hop states sync or async, its timeout, its retry policy, its failure behaviour,
  and whether it is idempotent (`resilience-patterns`, `idempotency-and-immutability`). Every trust
  boundary states who is authorised and how (`secure-service`). The consistency boundary is named,
  along with what may be stale and for how long (`cqrs-and-consistency`).
- **L4** — full contracts (`api-contracts`), including the error catalogue, idempotency keys, and
  event compatibility mode. List **test obligations** per contract — which behaviour is proven at
  which level (`test-strategy`), and which cross-service promises need contract tests
  (`contract-testing`). Write obligations, not tests.

### Step 3 — Approve

At the final agreed level, present a summary: the components, the flows, the contracts, every
decision with its reason, and the open questions that remain.

Ask for approval explicitly. On approval:

- Set `status: approved` and the completed `levels` in the blueprint frontmatter.
- Append any decision not already recorded to `.msskills/decisions.md`, or leave the pointer to the
  blueprint's own Decisions Log.
- Update `.msskills/context-map.md` if a boundary or an integration relationship changed.

Then say what comes next: `implement-service` reads this blueprint and will refuse to start without
`status: approved`.

## Rules

- **One level per message.** The whole method is the pause.
- **Never write implementation code.** Contracts, schemas, and interface signatures are L4
  artefacts. Bodies, queries, and wiring are not.
- **Write the blueprint as you go**, not at the end. A session that ends early must still leave
  something usable.
- **Assumptions are marked, always.** Anything you inferred about the domain is labelled as an
  assumption, not stated as fact.
- **Do not descend on an implicit yes.** "Looks good" on components approves L2 and nothing else.
- **If the design contradicts the code**, present the conflict rather than quietly following either.
