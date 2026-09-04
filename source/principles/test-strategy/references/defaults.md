# Test Strategy — defaults

Loaded by Config Resolution when a project has no override, or as the base layer under an overlay.

---

## 1. The portfolio

For a microservice, the useful shape is not a strict pyramid. It is wide in the middle: many fast
unit tests for logic, a solid band of component tests that prove the service works as a service,
contract tests instead of cross-service integration tests, and a thin cap of end-to-end journeys.

Some teams call this the honeycomb or the testing trophy. The name matters less than the rule
behind it: **push each behaviour to the cheapest level that can genuinely prove it, and never test
the same behaviour twice at two levels.** Duplicated coverage is where suites go to become slow.

Rough targets for a typical service — adjust to the domain, do not treat as law:

| Level | Share | Runtime budget | Runs |
|---|---|---|---|
| Unit | ~60% | Whole suite in seconds | Every save |
| Component | ~25% | Whole suite in a few minutes | Every commit |
| Contract | ~10% | Seconds per pair | Every commit; provider verification on every provider build |
| Integration | ~5% | Minutes | Every commit |
| End-to-end | a handful | Minutes | Before release |

### What each level must **not** own

- **Unit** must not own wiring, serialisation, or SQL. If it needs a framework context, it is a
  component test wearing the wrong label.
- **Component** must not own another service's behaviour. Stub collaborators at the network
  boundary and let contract tests prove the stub is honest.
- **Integration** must not own business rules. It proves the adapter and the dependency work
  together — the query returns what the mapping expects, the migration applies, the consumer group
  rebalances.
- **End-to-end** must not own edge cases, validation, or error mapping. It owns "a user can
  complete this journey", and nothing more. Every edge case added here costs the whole team time on
  every run, forever.

## 2. Component tests, in detail

This is the level that pays for itself in a microservice, so it is worth being precise.

**In scope — real:**

- The service, started the way production starts it, through its real entry points.
- Its own datastore, in a container, with real migrations applied.
- Real serialisation, real routing, real validation, real error mapping, real auth filters.
- Its own broker, in a container, when messaging behaviour is part of the service's job.

**Out of scope — stubbed at the network boundary:**

- Every other service. Stub the HTTP or the messages, not the client class — stubbing the client
  skips serialisation, timeouts, and error mapping, which is where the bugs are.
- Third-party APIs.

Practices:

- **One container set per suite**, reused across tests. Starting a database per test is what makes
  people abandon this level.
- **Isolate by data, not by restart.** Unique identifiers per test; never truncate shared tables in
  a parallel suite.
- **Stub at the network boundary** — an in-process HTTP stub server, or the platform's equivalent.
- **Assert through the front door.** Drive with an HTTP request or a message; assert on the
  response, the emitted messages, and the stored state. Reaching into internals turns a component
  test into a coupled unit test.
- **Include the failure cases**: the stub returns 500, the stub times out, the message is
  redelivered. These are the paths `resilience-patterns` cares about, and this is the only level
  where they are cheap to exercise.

## 3. Test doubles

| Double | What it does | Use for |
|---|---|---|
| **Stub** | Returns canned answers | Supplying input to the subject |
| **Fake** | A working lightweight implementation (in-memory repository) | Replacing infrastructure while keeping real behaviour |
| **Mock** | Asserts on the interaction | Verifying an outbound effect that has no other observable trace |
| **Spy** | Records calls for later inspection | Same, when the assertion should not drive the setup |
| **Dummy** | Fills a parameter, never used | Satisfying a signature |

Discipline:

- **Double at the architectural boundary**, not inside. Ports get doubles; domain objects do not.
- **Prefer fakes to mocks** for repositories. An in-memory implementation keeps tests readable and
  survives refactors that a chain of `when(...).thenReturn(...)` will not.
- **Never mock a type you do not own.** Wrap it in your own port and fake that; otherwise your test
  encodes your *belief* about the library's behaviour, which is exactly what is likely to be wrong.
- **Mock only for outbound effects with no other trace** — "an email was requested", "the event was
  published". If you can assert on state or on a returned value instead, do that.
- **A test with more setup than assertion** is testing the mock framework. Reconsider the level.

## 4. Determinism

Flakiness is not a fact of life; it is a set of specific, fixable causes.

| Cause | Fix |
|---|---|
| Wall-clock time | Inject a clock; freeze it in tests |
| `now()` in comparisons | Assert a range, or control the clock |
| Random values, UUIDs | Inject the generator; seed it |
| Timezone or locale | Pin both in the test configuration |
| Unordered collections | Sort before comparing, or use order-insensitive assertions |
| Async completion | Poll the condition with a bounded timeout — never `sleep` |
| Shared state between tests | Fresh data per test, unique keys |
| Test order dependence | Randomise order in CI so the dependency surfaces |
| Real network | Stub it; a test that reaches the internet is not a test |
| Port collisions | Bind port 0 and read the assigned port |

**Never retry a flaky test.** A retry converts a real intermittent bug — a race, an unhandled
redelivery — into a green build. Quarantine it, fix the cause, and restore it. If nobody will fix
it, delete it: an untrusted test costs more than no test.

## 5. Structure and naming

```
Arrange — the world in a known state, only what this test needs
Act     — one call, the behaviour under test
Assert  — the observable outcome
```

Name by behaviour, so a CI failure is diagnosable without opening the file:

```
cancelling_a_dispatched_order_is_rejected
returns_409_when_the_idempotency_key_was_used_with_a_different_body
publishes_OrderCancelled_once_when_the_message_is_redelivered
```

Not `testCancel1`, `testOrderService`, `shouldWork`.

Further rules: assert one behaviour per test, but a behaviour may need several assertions —
splitting `status`, `body`, and `emitted event` into three tests that share setup is noise. Prefer
a domain-specific assertion helper to a wall of field comparisons. Keep the arrange section
readable with builders that default everything and take only what the test cares about.

## 6. Test data

- **Builders with sane defaults.** `anOrder().withTotal(500).build()` — the test states only what
  matters, so a new required field does not touch a hundred tests.
- **Unique per test.** Generate identifiers per test so parallel runs cannot collide.
- **No shared golden dataset.** A fixture file everybody depends on becomes untouchable within a
  year.
- **Never production data.** Even "anonymised" — re-identification is easier than it looks, and it
  puts personal data in a place with no access controls (see `secure-service`).

## 7. Coverage, honestly

Line coverage measures which lines ran, not which behaviours are protected. A suite with 95%
coverage and no assertions has 95% coverage.

- Use coverage to **find untested areas**, not as a target. A ratchet that forbids decreases is
  more useful than an absolute number.
- **Mutation testing** answers the real question: if the code were subtly wrong, would a test
  fail? Run it on the domain layer, where it is affordable and where the value is highest. A low
  mutation score on well-covered code means the assertions are weak.
- **Weight by risk.** Money, authorisation, and state machines deserve near-total coverage. A
  generated DTO does not.
- **Untested error handling is the real gap** in most services, and it is invisible in a coverage
  number because the happy path already touched those lines.
