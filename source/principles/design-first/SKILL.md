---
name: design-first
description: "Facilitate design before code through progressive disclosure: climb from context to components to interactions to contracts, asking questions and stopping for approval at each level instead of emitting a finished design. Covers the four-level ladder, depth calibration, approval gates, and how to record the result as a durable blueprint. Use before implementing a new service, endpoint, event, or integration, and when the user says 'design', 'blueprint', 'how should we build', 'spec this out', or 'think before coding'. This skill governs the facilitation process — the design content itself belongs to service-boundaries, api-contracts, domain-modelling, and resilience-patterns."
license: MIT
---

# Design First — Progressive Design Facilitation

The failure mode this prevents is not "no design". It is the agent producing a confident,
complete, plausible design in one shot — which the user skims, approves, and discovers is wrong
after the code exists. A design nobody was forced to think about is worse than no design, because
it carries authority it did not earn.

Progressive facilitation fixes this by climbing one level at a time, asking rather than asserting,
and refusing to descend to the next level until the current one is agreed.

## Config Resolution

1. Read `.msskills/config.yaml` in the repo root; look up `paths.design`.
2. A custom document exists at that path → read its frontmatter `mode`:
   - `override` → use it alone as the design process; ignore the defaults below.
   - `overlay` (default, or no `mode` key) → read [defaults](./references/defaults.md) first, then
     apply the custom document's sections on top, matched by exact heading; new sections append.
3. A path is configured but no file exists there → say which path is missing, then use the
   embedded defaults.
4. No config file or no `paths.design` key → use [defaults](./references/defaults.md).
5. `.msskills/stack.md` exists → phrase every question in that stack's vocabulary. Do not ask a Go
   team about Spring profiles.

## The four levels

Each level answers one question and produces one artefact. See
[defaults](./references/defaults.md) for the question banks and the blueprint template.

| Level | Question | Produces | Gate |
|---|---|---|---|
| **L1 Context** | What problem, for whom, inside which boundary? | Purpose, actors, in/out of scope, the bounded context it belongs to, constraints, how we will know it worked | User confirms the problem is stated correctly |
| **L2 Components** | What parts exist and who owns what data? | Component list with responsibilities, layer placement, data ownership, what is reused versus new | User confirms the shape and the ownership |
| **L3 Interactions** | How do the parts talk, and what happens when that fails? | Call and event flows, sync/async per hop, consistency model, failure behaviour per hop | User confirms the flows and the failure story |
| **L4 Contracts** | What exactly crosses each boundary? | API and event schemas, error responses, idempotency, validation rules, test obligations | User approves — this is the implementation gate |

Climb in order. L3 cannot be answered before the components exist; L4 cannot be answered before the
interactions do. Jumping to L4 because the user asked for "the API" produces a schema for a service
whose boundary nobody agreed on.

## Self-Validation Checklist

**STOP at the end of each level. Verify every check before proposing to descend.**

1. **ONE LEVEL**: Does this message address exactly one level? Content from the next level →
   remove it and hold it for that level.
2. **QUESTIONS OVER ASSERTIONS**: Are the open points asked, or asserted? Anything you inferred
   about the domain, the users, or the constraints → turn it into a question or flag it as an
   explicit assumption.
3. **UNKNOWNS NAMED**: Have you listed what you still do not know at this level? Silence about a
   gap reads as certainty.
4. **GROUNDED**: Does every statement reference something real — an existing service, table,
   endpoint, or a constraint the user gave? Unsourced detail is invention → go read the code or ask.
5. **DECISIONS SURFACED**: Has every genuine trade-off at this level been routed through
   `collaborative-judgment` rather than settled inside the prose?
6. **RECORDED**: Is the level's outcome written into the blueprint document, including the
   rejected options and why?
7. **GATE STATED**: Have you explicitly asked to proceed, and named what the next level will
   decide? "Shall I continue?" is not a gate; "Shall I move to L3, where we settle sync versus
   async for the payment hop?" is.
8. **NO CODE**: Have you written implementation code? Interfaces, schemas, and signatures are L4
   artefacts; bodies are not. Delete them.

All checks pass → present the level, then stop and wait.

## Active Anti-Pattern Scan

Any box you can check is a defect. Fix it before presenting.

- [ ] **Big-Bang Blueprint**: all four levels delivered in one message → split; present L1 and stop.
- [ ] **Confident Invention**: entities, rules, or volumes stated as fact that came from nowhere →
      mark as assumption or ask.
- [ ] **Rhetorical Questions**: questions asked and then answered in the same breath → ask, then stop.
- [ ] **Design as Menu**: a list of every possible approach with no position → recommend one and
      say why, per `collaborative-judgment`.
- [ ] **Premature Contracts**: field-level schemas at L1 or L2 → defer to L4.
- [ ] **Skipped Failure Story**: L3 flows with only the happy path → every hop needs its timeout,
      retry, and failure behaviour, per `resilience-patterns`.
- [ ] **Boundary Assumed**: a new service proposed without asking whether it belongs in an existing
      one → route through `service-boundaries` first.
- [ ] **Ceremony Mismatch**: four full levels for a one-endpoint change → calibrate depth (see below).
- [ ] **Orphan Design**: the blueprint is never written to disk, so implementation cannot reference
      it → write it as you go, not at the end.
- [ ] **Approval Assumed**: descending because the user said "ok" to something else → each gate is
      explicit.

## Ambiguity Signals

Route these through `collaborative-judgment` rather than deciding alone.

- **How deep to climb.** A new bounded context earns all four levels. A field added to an existing
  endpoint earns L4 alone. Most work sits between; propose a depth at the start and let the user
  cut it. Depth is the user's call, not yours.
- **When the design contradicts existing code.** The blueprint says one thing, the repository does
  another. Both "the code is stale" and "the design is wrong" are plausible — present the conflict
  rather than quietly following either.
- **Unknowable answers.** Some questions ("what will peak load be?") cannot be answered before
  launch. The choice between designing for the guess and designing to defer is a real trade-off.
- **Requirements that change mid-climb.** Restarting from L1 is expensive; patching L3 around a
  changed L1 produces incoherence. Say which levels the change invalidates and let the user choose.
