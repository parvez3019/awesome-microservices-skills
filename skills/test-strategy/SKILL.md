---
name: test-strategy
description: "Choose the right test level for each behaviour and write tests that fail only for real reasons. Covers the microservice test portfolio — unit, component (service in isolation with real infrastructure and stubbed collaborators), integration, and narrow end-to-end — plus what each level must not own, test doubles discipline, determinism and flakiness, arrange-act-assert structure, assertion quality, coverage versus value, mutation testing, and test data management. Use when writing or reviewing any test, deciding what level to test at, diagnosing a flaky or slow suite, or when the user says 'tests', 'unit test', 'component test', 'test pyramid', 'mocking', 'flaky', or 'coverage'. This skill governs test design inside a service — cross-service contract verification belongs to contract-testing."
license: MIT
---

# Test Strategy

A test suite has one job: tell you, quickly and truthfully, whether a change is safe to ship. Most
suites fail at this in one of two ways — they are so slow and flaky that people stop believing
them, or they are so tightly bound to implementation that every refactor breaks a hundred tests
while real defects walk through.

Both come from testing at the wrong level. The level is the decision that matters; everything else
is craft.

## Config Resolution

1. Read `.msskills/config.yaml` in the repo root; look up `paths.testing`.
2. A custom document exists at that path → read its frontmatter `mode`:
   - `override` → use it alone as the testing standard; ignore the defaults below.
   - `overlay` (default, or no `mode` key) → read [defaults](./references/defaults.md) first, then
     apply the custom document's sections on top, matched by exact heading; new sections append.
3. A path is configured but no file exists there → say which path is missing, then use the defaults.
4. No config file or no `paths.testing` key → use [defaults](./references/defaults.md).
5. `.msskills/stack.md` exists → use its test framework, assertion style, container/stub tooling,
   and naming convention. Match the conventions of the tests already in the repository over these
   defaults.

## Choosing the level

Test each behaviour once, at the cheapest level that can genuinely prove it.

| Level | Boundary | Real | Stubbed | Owns |
|---|---|---|---|---|
| **Unit** | A class or function | The code under test and its value objects | Everything with I/O | Business rules, calculations, state machines, edge cases |
| **Component** | One whole service | The service, its database, its HTTP and message entry points | Every other service | Wiring, serialisation, persistence, validation, error mapping, auth |
| **Contract** | One consumer–provider pair | The message shape | Both sides' internals | That two services agree — see `contract-testing` |
| **Integration** | One adapter and one real dependency | That adapter and that dependency | Everything else | Queries, migrations, client configuration, broker semantics |
| **End-to-end** | The deployed system | Everything | Nothing | A handful of critical user journeys, and nothing more |

**Component tests are the highest-value level in a microservice** and the most often missing. One
service, real database in a container, real HTTP in and out, collaborators stubbed at the network
boundary: fast enough to run on every commit, and it proves the thing actually starts and works.

## Self-Validation Checklist

**STOP after writing or reviewing each test. Verify every check. Fix failures before presenting.**

1. **RIGHT LEVEL**: Is this the cheapest level that can prove this behaviour? A rule covered by a
   unit test does not also need an end-to-end test.
2. **BEHAVIOUR NOT IMPLEMENTATION**: Would this test survive a refactor that preserves behaviour?
   If it asserts on internal calls, private state, or field order → rewrite against observable
   outcomes.
3. **ONE REASON TO FAIL**: Does the test have a single clear subject? Multiple unrelated assertions
   → split, so a failure names the defect.
4. **NAMED BY BEHAVIOUR**: Does the name state the scenario and the expected outcome, so a failure
   in CI is self-explanatory without opening the file?
5. **AAA VISIBLE**: Are arrange, act, and assert distinguishable? Assertions interleaved with
   actions → restructure.
6. **DETERMINISTIC**: Does it depend on wall-clock time, real randomness, timezone, locale,
   ordering, network, or another test's state? → inject the clock and the ID source; sort before
   comparing; seed randomness.
7. **ISOLATED**: Does it pass when run alone, in a different order, and in parallel? Shared mutable
   fixtures → give each test its own data.
8. **NO SLEEP**: Does it wait on a fixed sleep? → poll with a bounded timeout on the actual
   condition.
9. **DOUBLES JUSTIFIED**: Is each test double replacing something slow, non-deterministic, or
   external? Mocking a pure value object or the type under test → use the real thing.
10. **ASSERTS THE POINT**: Does the assertion check what the test claims to prove — including
    values, not just that a call happened? `verify(save called)` does not prove the right thing was
    saved.
11. **FAILURE PATHS COVERED**: Are timeouts, rejections, and compensation paths tested, not just
    the happy path? Untested error handling is the code that runs during an incident.
12. **FAILS FIRST**: Would this test fail if the behaviour were removed? A test that passes against
    a broken implementation proves nothing — check it.

All checks pass → state "Test holds: <level>, <behaviour>, deterministic."

## Active Anti-Pattern Scan

Any box you can check is a defect. Fix it before presenting.

- [ ] **Ice Cream Cone**: mostly end-to-end tests, few unit tests → slow, flaky feedback; push
      coverage down to the cheapest level that proves each behaviour.
- [ ] **Mockery**: everything mocked including the subject's own collaborators, so the test asserts
      the implementation back to itself → use real objects for anything without I/O.
- [ ] **Assertion-Free Test**: exercises code and asserts nothing, or only that no exception was
      thrown → assert the outcome.
- [ ] **Sleep-Based Waiting**: `sleep(2000)` for async work → poll the condition with a timeout.
- [ ] **Shared Mutable Fixture**: tests that pass only in a particular order, or fail in parallel →
      per-test data with unique keys.
- [ ] **Snapshot Everything**: large auto-generated snapshots accepted without reading → assert the
      fields that matter.
- [ ] **Coverage Theatre**: tests written to raise a percentage, exercising getters → delete them;
      cover behaviour instead.
- [ ] **Test Logic**: conditionals and loops in tests, so the test itself needs testing → use
      parameterised cases.
- [ ] **Retried Flake**: a failing test wrapped in a retry annotation → find the non-determinism;
      a retried test is a test nobody trusts.
- [ ] **Mocked Third Party at the Wrong Layer**: mocking the vendor SDK rather than stubbing its
      HTTP → stub at the network boundary so serialisation is exercised.
- [ ] **Happy Path Only**: no test for timeout, rejection, duplicate delivery, or compensation.
- [ ] **Slow Unit Suite**: unit tests that start a container or a framework context → that is a
      component test; move it.
- [ ] **Disabled Test**: `@Ignore`/`skip` with no linked issue → fix or delete; a skipped test is
      false comfort.

## Ambiguity Signals

Route these through `collaborative-judgment`. Each has two defensible answers.

- **Unit or component.** A rule reachable only through the HTTP layer can be unit tested by
  extracting it, or component tested where it lives. Extraction is cleaner and is also a design
  change.
- **How many end-to-end tests.** They catch integration and environment faults nothing else does,
  and they are the slowest and flakiest thing you own. The right number is small and non-zero.
- **Test doubles for another service.** A stub is fast and can drift from reality; a real instance
  in a container is faithful and slow. Contract tests are how you get both, at the cost of a broker
  (see `contract-testing`).
- **Coverage targets.** A number drives behaviour, and not always the behaviour you wanted. Mutation
  score measures the same thing more honestly and costs more to run.
- **Fixtures versus builders.** Shared fixtures are concise and couple tests together; per-test
  builders are explicit and verbose.
- **Whether to test a thin adapter.** Some layers are pure delegation, and a test for them asserts
  the framework works.
