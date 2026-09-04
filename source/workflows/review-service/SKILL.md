---
name: review-service
description: "Audit service code against every microservices principle and report severity-ranked findings, each anchored to a file, a line, and the rule it breaks. Covers scoping a review to a diff, branch, pull request or whole service, running the applicable principle checklists and anti-pattern scans, verifying each candidate finding against a concrete failure scenario, and separating genuine defects from deliberate trade-offs. Use before merging, when reviewing a pull request or a diff, when auditing an existing service, or when the user says 'review', 'code review', 'audit this', or 'is this ready to ship'. Reports findings and does not change code — to apply fixes, follow up with implement-service or refactor-safely."
license: MIT
---

# Review a Service

A review is worth having only if it finds what the author could not see. That means running the
checklists mechanically rather than reading for a general impression, verifying each finding
against a concrete failure, and being ruthless about what does not make the bar.

Padding a review with style opinions is not neutral — it buries the two findings that mattered.

## Required Skills

Read and apply every principle that the code under review touches:

1. `clean-architecture` — layering, dependency direction, SOLID, pattern justification. (always)
2. `test-strategy` — test level, determinism, assertion quality, coverage of failure paths. (always
   when tests are present or absent)
3. `collaborative-judgment` — deliberate trade-offs are reported as questions, not defects. (always)
4. `service-boundaries` — ownership, coupling, new modules or services. (conditional)
5. `domain-modelling` — domain types, aggregates, value objects. (conditional)
6. `data-access` — repositories, queries, transactions, migrations, caches. (conditional)
7. `cqrs-and-consistency` — read models, projections, ownership. (conditional)
8. `infrastructure-adapters` — clients, consumers, publishers, SDK wrappers. (conditional)
9. `resilience-patterns` — any call leaving the process, any message handler. (conditional)
10. `idempotency-and-immutability` — retryable operations, shared or mutable state. (conditional)
11. `secure-service` — handlers, clients, queries, credentials, personal data. (conditional)
12. `api-contracts` — endpoint, schema, or published event changes. (conditional)
13. `api-protocols` — GraphQL, gRPC, WebSocket or SSE surfaces. (conditional)
14. `config-and-dependencies` — settings, flags, dependency manifests. (conditional)
15. `contract-testing` — integrations between services. (conditional)

## Workflow

### Step 1 — Scope

Establish exactly what is under review, and say so before starting.

| Ask | Scope |
|---|---|
| "review my changes" | Uncommitted working tree plus staged changes |
| "review this branch" / a PR number | The diff against the merge base |
| "review the orders service" | The whole service — announce a sampling strategy, since a full audit of a large codebase in one pass is not credible |
| A file or directory | That path |

For a diff, a finding must be **in the changed code or activated by it**. Pre-existing issues in a
file the diff happens to touch go in a separate "out of scope" list — never mixed into the findings.

### Step 2 — Load the project's standards

1. Read `.msskills/stack.md` — idiom-appropriate expectations, and which libraries exist.
2. Read `.msskills/config.yaml` and follow each principle's Config Resolution. **Project overrides
   outrank this library's defaults.** Reporting a deliberate house standard as a violation destroys
   the review's credibility.
3. Read the blueprint in `.msskills/designs/` if one covers this change. Deviation from an approved
   design is itself a finding.
4. Read `.msskills/decisions.md`. A recorded decision is settled — do not re-litigate it as a
   finding. If you believe it is now wrong, say so under judgment calls with what changed.

### Step 3 — Run the checklists

For each file in scope, apply the Self-Validation Checklist and Active Anti-Pattern Scan of every
principle from Required Skills that governs that file. Work through them item by item — the value
of this workflow is that it is mechanical where a human reviewer is impressionistic.

Give disproportionate attention to the defects that are cheap to miss and expensive to ship:

- **Missing ownership check** — an ID from the request used to load a record with no scoping to the
  caller (`secure-service`, API1). Look for it on every single read and write path.
- **Missing timeout** on any outbound call (`resilience-patterns`).
- **Dual write** — a database commit and a broker publish as separate steps (`resilience-patterns`).
- **Non-idempotent consumer** under at-least-once delivery
  (`idempotency-and-immutability`).
- **N+1 query** on any path that handles a collection (`data-access`).
- **Breaking contract change** — a field removed, renamed, narrowed, or made required
  (`api-contracts`).
- **Destructive migration** that makes the previous release un-rollbackable (`data-access`).
- **Secret in the repository** (`secure-service`).
- **Untested failure path** — error handling with no test (`test-strategy`).

For a large scope, sample deliberately and say how: every trust boundary and every outbound call
first, then the domain, then the rest. State what you did not examine.

### Step 4 — Verify each candidate

For every candidate finding, before it goes in the report:

1. **Construct the failure.** Name the input, state, or sequence that makes it go wrong, and the
   observable consequence. If you cannot, it is a preference — drop it.
2. **Look for the central mechanism.** Timeouts, authorisation, validation, and error mapping are
   often applied by a filter, a client factory, an interceptor, or a base class. A reviewer who has
   not gone looking will report a wall of false positives.
3. **Check it is not deliberate.** A comment, a decision record, or a project override may explain
   it. If it looks deliberate but undocumented, that is a judgment call, not a defect.
4. **Assign severity by consequence**, not by effort to fix:

   | Severity | Meaning |
   |---|---|
   | **Critical** | Data loss, data exposure, unauthorised access, or breaks a deployed consumer |
   | **High** | Will cause an incident under load or failure |
   | **Medium** | Correctness or maintainability defect with bounded blast radius |
   | **Low** | Real but minor |

Anything below Low is not reported.

**Independent pass.** For a substantial change, also run the `microservice-reviewer` agent over the
same scope and merge its findings with yours, keeping the more specific version of any duplicate.
A second pass with no memory of the reasoning catches what a single reading rationalises.

### Step 5 — Report

Lead with a two-line verdict: what the change does, and whether it is safe to ship. Then findings,
most severe first:

```markdown
**High — Outbound call to the pricing service has no timeout**
`src/adapter/PricingClient.java:34` · violates `resilience-patterns`

The client is constructed without a request timeout, so a hung dependency holds the calling
thread indefinitely.

**Fails when:** pricing stops responding without closing connections. Checkout threads accumulate
until the pool is exhausted; every checkout then fails, including those not needing pricing.
**Fix:** set an explicit request timeout below checkout's own budget, and wrap the call in the
circuit breaker already configured for `inventory` in `ResilienceConfig`.
```

Close with:

- **Judgment calls** — real trade-offs the author may have decided deliberately, in the
  `collaborative-judgment` format. Never as findings.
- **Out of scope** — pre-existing issues worth their own change, one line each.
- **What was checked** — the principles applied and, for a sampled review, what was not examined.

If nothing meets the bar, say so and list what you checked. A clean review is a real result.

## Rules

- **Report; do not fix.** This workflow ends with findings. Applying them is a separate,
  explicitly requested step.
- **No praise section.** The author wants the defects.
- **No padding.** Two real findings beat two real findings and eight style notes.
- **Cite a file and a line** for every finding.
- **Never restate the principle** — cite it and go straight to the specific violation.
- **Say when you are unsure.** A flagged uncertainty is useful; a confident claim that turns out to
  be wrong costs the reader trust in the whole list.
