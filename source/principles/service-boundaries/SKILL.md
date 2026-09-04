---
name: service-boundaries
description: "Decide where a service ends and the next one begins, using domain-driven strategic design. Covers bounded contexts, context maps and integration patterns, ubiquitous language, autonomy and coupling tests, the modular-monolith-first bias, and extraction by strangler fig. Use when proposing a new service, splitting or merging existing ones, naming a module, deciding which service owns a piece of data, or when the user says 'should this be its own service', 'boundaries', 'decompose', 'bounded context', or 'microservice or monolith'. This skill governs where boundaries fall — not what crosses them (see api-contracts), not internal layering (see clean-architecture), not aggregate design (see domain-modelling)."
license: MIT
---

# Service Boundaries

Almost every painful microservice system is painful for the same reason: the boundaries were drawn
around technical nouns or team convenience rather than around units of business change. A wrong
boundary is the most expensive mistake in this library — it is not refactorable inside one
repository, and it shows up as chatty calls, shared databases, and lockstep releases.

The default answer to "should this be a new service?" is **no, not yet**. Make the case.

## Config Resolution

1. Read `.msskills/config.yaml` in the repo root; look up `paths.boundaries`.
2. A custom document exists at that path → read its frontmatter `mode`:
   - `override` → use it alone; ignore the defaults below.
   - `overlay` (default, or no `mode` key) → read [defaults](./references/defaults.md) first, then
     apply the custom document's sections on top, matched by exact heading; new sections append.
3. A path is configured but no file exists there → say which path is missing, then use the defaults.
4. No config file or no `paths.boundaries` key → use [defaults](./references/defaults.md).
5. `.msskills/context-map.md` exists → treat it as the current record of contexts and their
   relationships. Any change to a boundary updates that file.

## Self-Validation Checklist

**STOP before proposing any boundary — a new service, a split, a merge, or a module. Verify every
check. Fix failures before presenting.**

1. **BUSINESS CAPABILITY**: Can you name the boundary as a capability the business would recognise
   — *pricing*, *fulfilment*, *identity*? If the name is technical (`api-service`, `db-writer`,
   `orchestrator`) → you have drawn a layer, not a boundary. Redraw around the capability.
2. **UBIQUITOUS LANGUAGE**: Inside this boundary, does each term have exactly one meaning? If
   "order" means two different things in two places → those are two contexts, and the boundary
   runs between them.
3. **DATA OWNERSHIP**: Does exactly one service write each piece of data? Two writers to one table,
   or a shared database → the boundary is wrong or the split is incomplete. Fix before proceeding.
4. **AUTONOMY**: Can this service serve its primary use case when every other service is down? If
   not, list which hops break it and justify each one — every synchronous dependency multiplies
   into the availability budget (see `resilience-patterns`).
5. **CHANGE COUPLING**: Do the last several changes to this area touch this boundary alone? If a
   typical feature edits three services → the boundary cuts through a single unit of change. Merge
   or redraw.
6. **CHATTINESS**: Does one user-facing operation cross this boundary more than once or twice? A
   loop of remote calls, or fetching data only to send it straight back → the data or the logic is
   on the wrong side.
7. **TRANSACTION FIT**: Does any single invariant need to hold across this boundary atomically? If
   yes → either it belongs in one service, or the invariant becomes a saga with compensation, which
   is a decision the user must make (see `cqrs-and-consistency`).
8. **TEAM FIT**: Can one team own this end to end? A boundary that needs two teams to agree on
   every release is a distributed monolith with extra latency.
9. **JUSTIFIED SPLIT**: For a *new* service specifically — which concrete force requires separate
   deployment: independent release cadence, divergent scaling, isolation of failure, regulatory
   separation, or team ownership? "Cleaner" and "more scalable" are not forces. If none applies →
   propose a module inside the existing service instead.

All checks pass → state "Boundary holds: <capability>, owns <data>, autonomous except <hops>."

## Active Anti-Pattern Scan

Any box you can check is a defect. Fix it before presenting.

- [ ] **Distributed Monolith**: services that must deploy together, share a database, or break
      when a sibling is down → merge them, or make the coupling asynchronous.
- [ ] **Entity Service**: a service per database table (`CustomerService`, `AddressService`) with
      no behaviour of its own → collapse into the capability that owns the behaviour.
- [ ] **Nano-Service**: a service whose entire job is two endpoints wrapping one table → the
      operational cost exceeds its value; fold it in.
- [ ] **Shared Database**: two services reading or writing the same schema → publish an API or
      events instead; the schema is an implementation detail, not a contract.
- [ ] **God Service**: one service everything depends on, changed by every feature → split along
      the capabilities that change independently.
- [ ] **Chatty Boundary**: N+1 remote calls, or a call in a loop → move the query, batch it, or
      move the data.
- [ ] **Layer as Boundary**: services named for tiers (`api`, `business-logic`, `data-access`) →
      that is `clean-architecture` inside one service, not a decomposition.
- [ ] **Leaked Language**: another context's terms and identifiers used raw in this one → add an
      anti-corruption layer and translate at the edge.
- [ ] **Conway Mismatch**: a boundary no single team owns → align to team, or accept and document
      the coordination cost.
- [ ] **Premature Extraction**: a service split out of a system whose domain is still moving →
      keep it a module until the seam has stopped shifting.

## Ambiguity Signals

Route these through `collaborative-judgment`. Each has two defensible answers.

- **Module or service.** Both give the same logical boundary; only one gives independent deploy
  and independent failure — at the cost of a network hop, a contract, and an operational surface.
  Present the forces, and lean toward the module until one of them clearly applies.
- **Duplicate the data or call for it.** Owning a replica removes a runtime dependency and adds
  staleness plus a second source of truth. Neither answer is free.
- **Where an ambiguous entity lives.** A concept that appears in two contexts (a "product" in
  catalogue and in fulfilment) may be one shared entity or two models with a translation between
  them. Two models is usually right and always more work.
- **Splitting for scale.** Real when one part's load profile genuinely diverges; a rationalisation
  when the whole system is comfortably within one instance. Ask for the numbers.
- **Extraction order.** Which seam to cut first in a monolith trades risk against value — the
  safest extraction is rarely the one that relieves the most pain.
