---
name: refactor-safely
description: "Change the structure of existing code without changing its behaviour, in verified steps small enough to abandon. Covers pinning current behaviour with characterisation tests before touching anything, sequencing small reversible transformations, keeping the build green throughout, separating refactoring from behaviour change, and extracting a service from a monolith by strangler fig. Use when improving structure, paying down design debt, preparing code for a feature, splitting a module or service, or when the user says 'refactor', 'clean this up', 'restructure', 'extract', 'strangle', or 'reduce coupling'. This workflow preserves behaviour — to add or change behaviour use implement-service, to audit without changing use review-service."
license: MIT
---

# Refactor Safely

Refactoring is behaviour-preserving by definition. The moment behaviour changes, this stops being a
refactor and becomes a change that needs a design and a review.

Two rules make the difference between a refactor and an outage: **pin the behaviour before you
touch it**, and **keep every step small enough to throw away**. A large refactor that "works" but
cannot be reverted is a rewrite wearing a safer name.

## Required Skills

Read and apply:

1. `test-strategy` — characterisation tests, and the right level to pin behaviour at. (always)
2. `clean-architecture` — the target structure and why it is better. (always)
3. `collaborative-judgment` — the scope, the target, and anything that turns out to be a behaviour
   change. (always)
4. `service-boundaries` — module or service extraction. (conditional: moving code across a boundary)
5. `domain-modelling` — restructuring domain types and aggregate boundaries. (conditional)
6. `data-access` — schema changes, migrations, query restructuring. (conditional)
7. `infrastructure-adapters` — introducing or reshaping a port to create a seam. (conditional)
8. `api-contracts` — anything a consumer can observe. (conditional: a public surface is involved)
9. `resilience-patterns` — moving code across a process boundary turns a call into a network hop.
   (conditional: extraction)

## Workflow

### Step 1 — Name the target and the reason

Before any change, state three things and get agreement:

1. **What is wrong now** — the concrete pain, not an aesthetic judgment. "Adding a payment method
   requires edits in six files" is a reason. "This does not follow SOLID" is not.
2. **What it should look like** — the target structure, in terms of `clean-architecture`.
3. **What will be measurably better** — fewer files touched per change, a testable unit, a boundary
   the compiler enforces.

If you cannot fill all three, **STOP**. Refactoring without a named force is churn: it produces a
large diff, a review burden, and a merge conflict for everyone else, in exchange for nothing.

Agree the **scope boundary** explicitly — which files may change, and which are out of bounds. A
refactor that spreads is one nobody can review.

### Step 2 — Pin the current behaviour

You cannot preserve behaviour you have not captured.

1. **Run the existing tests.** They must be green before you start. Failing tests → fix or
   quarantine them first; you cannot tell your breakage from theirs otherwise.
2. **Assess the coverage of the code you are about to move.** Read the tests; do not trust a
   percentage (`test-strategy`).
3. **Write characterisation tests for what is not covered.** These pin what the code *does*, not
   what it should do:
   - Drive from the outside — the level where behaviour is observable without knowing the
     structure you are about to change. Usually a component test.
   - Include the ugly cases: nulls, empty collections, boundary values, error paths.
   - **If a characterisation test reveals a bug, do not fix it now.** Pin the current behaviour,
     note the bug, and raise it separately. Fixing behaviour during a refactor makes the diff
     impossible to reason about.
4. **STOP** if the code cannot be characterised at any level. That is itself the finding — say so,
   and propose either adding a seam first or leaving it alone.

### Step 3 — Transform in small steps

Each step is one transformation, verified, and independently revertible.

For every step:

1. Make **one** change — rename, extract, inline, move, introduce a parameter object, replace a
   conditional with polymorphism.
2. **Run the tests.** Green → continue. Red → revert the step; do not debug forward. A revert costs
   seconds; debugging a half-applied refactor costs an afternoon.
3. **Commit** at each green point, so any step can be abandoned without losing the rest.

Rules that hold throughout:

- **Never mix behaviour change with structure change.** If a fix or improvement is needed, finish
  the refactor, then make it as a separate change. If it cannot wait, stop the refactor, make the
  behaviour change with its own tests, then resume.
- **Keep the build green between steps.** Long-lived broken states are how refactors get abandoned
  half-done, leaving the codebase worse than before.
- **Prefer parallel-change (expand → migrate → contract)** for anything with callers: add the new
  shape, move callers over one at a time, remove the old one. Each stage ships independently.
- **Use the tooling.** IDE and language-server refactorings are safer than hand editing for renames
  and moves — but re-read the diff; automated moves miss reflection, strings, configuration, and
  documentation.
- **Update tests only for structure.** A test whose *assertions* must change means behaviour
  changed — stop and reconsider.

Apply the `clean-architecture` checklist after each significant step, and surface any
`Ambiguity Signals` through `collaborative-judgment` rather than deciding the target unilaterally.

### Step 4 — Extraction (module or service)

Moving code across a process boundary is not a refactor of one codebase; it is a change to the
system's failure model. Follow the strangler-fig sequence in `service-boundaries`, and stop at each
stage:

1. **Module first.** Move the code inside the existing deployable, behind an explicit interface.
   Add an architecture test that fails the build on a boundary violation. **Ship this.** Most of
   the risk lives here, and it is still cheap to undo.
2. **Separate the data.** Route every access through the interface; nothing else touches those
   tables. **Ship this.** If this proves impossible, the boundary was wrong — that is the cheapest
   possible moment to learn it.
3. **Add the remote implementation** of the same interface, called by nothing yet.
4. **Shift traffic behind a flag** (`config-and-dependencies`), comparing results, with an instant
   rollback.
5. **Remove the local implementation** only after the remote one has carried full traffic long
   enough to trust.

At step 3, every call that was a method call becomes a network call. Apply `resilience-patterns` in
full — timeout, retry policy, breaker, fallback — and `api-contracts` to the interface, which is
now a published contract. A "pure refactor" that turns an in-process call into an unguarded remote
one has introduced a new outage mode.

### Step 5 — Verify and close

1. **Run the whole suite**, not only the tests near the change.
2. **Confirm the characterisation tests still pass unchanged.** If any needed editing, behaviour
   changed — say so explicitly rather than quietly adjusting the test.
3. **Re-read the diff as a reviewer.** Anything outside the agreed scope → revert it.
4. **Check the target was actually reached.** If the structure is only partly improved, say which
   part remains and why, rather than implying it is done.
5. **Summarise:** what moved, what did not change, which steps were taken, what is deliberately
   left, and any bug found and deferred during characterisation.

## Rules

- **Behaviour is preserved, always.** A behaviour change makes this a different workflow.
- **Never refactor on red.** Green before, green between, green after.
- **Revert, do not debug forward** when a step breaks tests.
- **A bug found is a bug reported**, not a bug fixed mid-refactor.
- **Stay inside the agreed scope.** Improvements you notice elsewhere go in the close-out list.
- **No named force, no refactor.** Say so plainly rather than producing churn.
