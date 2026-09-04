---
name: contract-testing
description: "Prove that a consumer and a provider still agree, without deploying them together. Covers the consumer-driven flow — consumer expectations, broker publication, provider verification, and a can-i-deploy gate in the pipeline — plus provider-driven and bi-directional variants, message and event contracts for Kafka or queues, contract versioning with branches and environments, pending contracts, and what a contract test must never assert. Use when adding or changing an integration between two services, when a consumer breaks after a provider release, when wiring deployment gates, or when the user says 'contract test', 'Pact', 'consumer-driven', 'can-i-deploy', or 'provider verification'. This skill governs cross-service agreement — contract design belongs to api-contracts, in-service test levels to test-strategy."
license: MIT
---

# Contract Testing

Integration tests that start two services answer a question nobody asked: do *these two versions*
work together, in *this environment*, right now? What teams actually need to know is whether the
version they are about to deploy will break anything already running.

Contract testing answers that. The consumer records what it needs; the provider proves it can
deliver it; the pipeline refuses a deploy that would break someone. No shared environment, no
lockstep releases, and a failure that names the consumer it would have broken.

## Config Resolution

1. Read `.msskills/config.yaml` in the repo root; look up `paths.contracts`.
2. A custom document exists at that path → read its frontmatter `mode`:
   - `override` → use it alone; ignore the defaults below.
   - `overlay` (default, or no `mode` key) → read [defaults](./references/defaults.md) first, then
     apply the custom document's sections on top, matched by exact heading; new sections append.
3. A path is configured but no file exists there → say which path is missing, then use the defaults.
4. No config file or no `paths.contracts` key → use [defaults](./references/defaults.md).
5. `.msskills/stack.md` exists → use its contract tooling and broker, and its language binding. If
   no tool is recorded, describe the flow and say the tool choice is open rather than assuming one.

## Self-Validation Checklist

**STOP after writing or reviewing a contract test, or changing an integration between two services.
Verify every check. Fix failures before presenting.**

1. **CONSUMER DRIVEN**: Does the contract state what the consumer actually needs, derived from real
   consumer code, rather than mirroring the provider's full response? If it was written from the
   provider's schema → rewrite from the consumer's use.
2. **ONLY WHAT IS USED**: Does the expectation include fields the consumer never reads? Every extra
   field is a promise the provider can no longer break → remove them.
3. **TYPES NOT VALUES**: Are matchers used for anything not semantically fixed — IDs, timestamps,
   generated strings? Exact-value matching on incidental data produces false failures.
4. **PROVIDER STATE NAMED**: Does each interaction declare the provider state it needs, in words
   the provider can set up ("an order 123 exists and is cancellable")?
5. **NO BUSINESS LOGIC**: Does the test assert the provider's *behaviour* — a calculation, a rule,
   a workflow? That belongs in the provider's own tests → assert only the shape of the exchange.
6. **BOTH SIDES RUN**: Is the consumer side generating the contract in CI *and* the provider side
   verifying it in CI? A contract nobody verifies is documentation.
7. **VERIFICATION IS REAL**: Does provider verification run against the real handler stack rather
   than a stub? A verification that mocks the provider proves nothing.
8. **STATE HANDLERS COMPLETE**: Does the provider implement every state the consumers name, and do
   those handlers create data through legitimate paths?
9. **DEPLOY GATED**: Does the pipeline block a deploy when the version being deployed is not
   compatible with what is already running in that environment?
10. **MESSAGES COVERED**: Are published events and consumed messages under contract, not just HTTP?
11. **VERSIONED BY COMMIT**: Are contracts published with the commit SHA and the branch, and is the
    deployed version recorded on release, so compatibility can be computed at all?
12. **FAILURE PATHS INCLUDED**: Are the error responses the consumer handles — 404, 409, 422 — part
    of the contract? Consumers depend on those shapes too.

All checks pass → state "Contract holds: <consumer> → <provider>, N interactions, verified."

## Active Anti-Pattern Scan

Any box you can check is a defect. Fix it before presenting.

- [ ] **Provider-Written Consumer Contract**: the provider team authored the consumer's
      expectations → it now tests its own assumptions; let the consumer write them.
- [ ] **Full-Response Contract**: every field of the provider's response asserted → freezes the
      provider's entire schema; assert only what is consumed.
- [ ] **Functional Test in Disguise**: business rules, calculations, or workflow asserted through
      the contract → move to the provider's component tests (see `test-strategy`).
- [ ] **Exact Match on Generated Data**: timestamps, UUIDs, or sequence numbers matched literally →
      type or regex matchers.
- [ ] **Unverified Contract**: published to the broker, never verified by any provider build → wire
      provider verification, or delete the contract.
- [ ] **Stubbed Verification**: the provider verifies against mocked internals → run the real stack
      with only external dependencies stubbed.
- [ ] **Missing Deploy Gate**: contracts verified but the pipeline deploys regardless → add the
      compatibility check before deploy.
- [ ] **Contract as Schema Dump**: generated from OpenAPI with no consumer involvement → that is
      schema validation, useful but different; consumer-driven means driven by a consumer.
- [ ] **Untested Events**: HTTP under contract, published events not → events are contracts too.
- [ ] **Stale Contracts**: contracts from consumer branches deleted long ago still blocking →
      record deployments and let the broker expire unused versions.
- [ ] **Fake Provider States**: state handlers that insert rows directly, bypassing invariants →
      set up through the service's own paths so the state is reachable in reality.
- [ ] **Contract Tests Replacing All Integration Tests**: no test ever exercises the real client
      against a real dependency → keep narrow integration tests for adapter and infrastructure
      behaviour.

## Ambiguity Signals

Route these through `collaborative-judgment`. Each has two defensible answers.

- **Consumer-driven or bi-directional.** Consumer-driven is stronger and requires both teams to
  adopt the tooling. Bi-directional — comparing a consumer's recorded expectations against the
  provider's published spec — is far cheaper to introduce across an estate you do not control, and
  it verifies less.
- **Contracts with an external provider.** You cannot make a third party verify anything. A
  scheduled check of your expectations against their sandbox is the usual compromise, and it is
  weaker.
- **How much of an event to put under contract.** Consumers of a rich event each use a different
  subset; the union quickly approaches the whole schema.
- **Pending contracts.** They let a consumer publish a new expectation without breaking the
  provider's build, which keeps teams unblocked and can let an unimplemented expectation linger.
- **Where the deploy gate blocks.** Before build, before deploy, or as a warning. Stricter is safer
  and stops more releases, including some that would have been fine.
- **Whether a pair needs contracts at all.** Two services owned by one team, always released
  together, may be adequately covered by component tests.
