# Worked example — `orders-service`

Not a runnable service. This is the **state the skills read and write**, shown filled in, so you can
see what to expect before running anything against your own repository.

```
sample/orders-service/.msskills/
├── stack.md                          # written by /stack-profile
└── designs/order-cancellation.md     # written by /design-service, status: approved
```

## What each file is for

**[`stack.md`](orders-service/.msskills/stack.md)** — the project's actual technology choices. Every
principle reads this in step 5 of its Config Resolution and translates its generic pattern names
into the team's libraries. With it, "add a circuit breaker" becomes Resilience4j with the project's
own thresholds; "write a component test" becomes JUnit 5 with Testcontainers and WireMock. Without
it, the guidance stays correct but generic.

Note the **Known gaps** section at the end. Recording that there is no load-test suite is what makes
`resilience-patterns` flag its timeout values as guesses rather than presenting them as derived.

**[`designs/order-cancellation.md`](orders-service/.msskills/designs/order-cancellation.md)** — an
approved blueprint. It shows all four design levels, and three things worth looking at specifically:

- **L1 declines to create a new service.** `service-boundaries` asks which of four forces requires
  separate deployment; none applies, so cancellation stays in `orders-service`. This is the single
  most valuable question in the library, and it is asked before any code exists.
- **L3 gives every hop a failure story** — timeout, retry, breaker, fallback — and states the
  consistency boundary. The synchronous hop fails closed; the three downstream effects are events
  through the outbox, so there is no dual write and no saga.
- **The Decisions Log records the rejected options**, not just the choice. That is what makes the
  design reviewable six months later, when someone asks why cancellation is not its own service.

## Reading it as a test of the skills

Two useful exercises once the plugin is installed:

```
/review-service on the L4 contracts in the sample blueprint
```

Findings should cite the principle each violates. The blueprint is deliberately not perfect — the
open questions at the end are real.

```
/design-service partial cancellation of individual order lines
```

It should notice the existing blueprint, see that partial cancellation was explicitly deferred, and
start a fresh climb rather than extending an approved design.

## Trying it on your own repository

```
/stack-profile          # detects what it can, asks about the rest
/design-service <feature>
/implement-service
/review-service
```

`stack-profile` writes `.msskills/stack.md` and a starter `.msskills/config.yaml` in your repository
root. Add `.msskills/designs/` to version control if you want blueprints reviewed alongside code —
most teams should.
