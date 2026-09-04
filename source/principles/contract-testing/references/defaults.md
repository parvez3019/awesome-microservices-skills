# Contract Testing — defaults

Loaded by Config Resolution when a project has no override, or as the base layer under an overlay.

Tool names appear only as illustration. Follow `.msskills/stack.md`; the flow is the same whichever
tool implements it.

---

## 1. The flow

```
  CONSUMER CI                      BROKER                     PROVIDER CI
  ───────────                      ──────                     ───────────
  1. Unit-test the client
     against a mock provider
     configured from the
     expectations
            │
  2. Contract generated ──────────▶ published
     (tagged with branch + SHA)     │
                                    │
                                    ├──────────────▶ 3. Provider build fetches
                                    │                   every relevant contract
                                    │                and replays each interaction
                                    │                against the real handler stack,
                                    │                setting up provider states
                                    │
                                    ◀────────────── 4. Verification result published
                                    │
  5. can-i-deploy ◀─────────────────┤              5. can-i-deploy
     "is my version compatible                        "is my version compatible
      with what is deployed?"                          with every deployed consumer?"
            │                                                    │
         deploy                                               deploy
            │                                                    │
  6. record-deployment ────────────▶ environment state ◀──────── 6. record-deployment
```

Steps 5 and 6 are what turn contract tests from a checkbox into a safety net. Without recorded
deployments the broker cannot know what is running, and `can-i-deploy` has nothing to answer with.

## 2. Writing the consumer side

The contract is a by-product of testing the consumer's own client code. That is the point: it
records what the consumer *actually* uses, because the consumer's real code is what exercised it.

```
given   "an order 123 exists and is cancellable"     // provider state
upon    POST /orders/123/cancellation
        with  { reason: <string> }
expect  200
        { id: <string>, status: "CANCELLED", cancelledAt: <iso8601> }
```

Rules:

- **Drive it through the real client.** If the test calls the mock directly instead of going
  through the service's own HTTP client, it verifies nothing about the consumer.
- **Assert only the fields the consumer reads.** A field in the contract is a field the provider
  can never remove. Contracts that mirror the full response make the provider's schema immovable
  and produce failures for changes that harm nobody.
- **Match on type, not value**, for anything generated: IDs, timestamps, sequence numbers. Use
  exact values only where the value carries meaning — `status: "CANCELLED"` is the assertion; the
  timestamp is not.
- **Include the failures you handle.** If the consumer has a branch for 409, the 409 shape is part
  of the contract.
- **Name provider states in domain language** the provider team can set up without reading your
  code.
- **One state per interaction**, and keep the number of distinct states small — every one is a
  fixture the provider must maintain.

## 3. Provider verification

The provider fetches the contracts, replays each interaction, and compares the response.

- **Run against the real stack**: real routing, real serialisation, real handlers, real
  authorisation. Stub only what leaves the provider — its own downstream services.
- **Provider state handlers** put the service into the named state. Set data up through legitimate
  paths where practical; a handler that inserts a row violating an invariant verifies a state that
  cannot occur.
- **Verify every relevant consumer version**: what is deployed in each environment, plus the head
  of the main branch. Not just the latest contract.
- **Verification runs on every provider build**, not nightly. Its whole value is telling you before
  merge.
- **A verification failure names the consumer** it would break — that is the diagnostic teams
  actually want, and it is why this beats a shared integration environment.

## 4. Messages and events

Async integrations need contracts more than HTTP does, because there is no request to fail
visibly — a mismatched event is silently unprocessable at 3 a.m.

- The contract is the **message payload and its metadata**, not the transport. It applies equally
  to Kafka, RabbitMQ, SNS/SQS, or a pub/sub service.
- **Consumer side:** the test hands the expected message to the real message handler and asserts it
  processes correctly. This proves the handler can consume what it claims to need.
- **Provider side:** verification asks the provider to produce the message for a given state — by
  invoking the real code path that emits it — and compares it against the expectation.
- **Cover the envelope too**: `type`, `schemaVersion`, `id`, `correlationId`, and any header a
  consumer routes on (see `api-contracts`).
- **Contract tests and a schema registry are complementary.** The registry enforces structural
  compatibility on the topic; the contract proves a specific consumer's needs are still met. The
  registry cannot know that one consumer parses a field the schema calls optional.

## 5. Versioning, branches, environments

- **Version contracts by commit SHA**, tagged with the branch name. Semantic versions of a service
  are too coarse — the question is always about a specific build.
- **Tag with environments on deployment** (`record-deployment`), so the broker knows what is
  actually running where.
- **`can-i-deploy` before every deploy**, in both directions:
  - Consumer: "is my version compatible with the providers deployed in this environment?"
  - Provider: "is my version compatible with every consumer version deployed in this environment?"
- **Pending contracts** let a consumer publish a new expectation without breaking the provider's
  build until the provider has implemented it. They keep teams unblocked; watch that pending items
  do not accumulate quietly.
- **Work in progress** on a consumer branch should not gate anyone. Branch tagging is what makes
  that distinction possible.

## 6. Variants, and when each fits

| Variant | How it works | Fits when | Weaker because |
|---|---|---|---|
| **Consumer-driven** | Consumer writes expectations; provider verifies | Both teams inside the organisation | Requires provider adoption |
| **Provider-driven** | Provider publishes a spec; consumers verify against it | Many unknown consumers, public API | Nobody proves consumers' real needs are met |
| **Bi-directional** | Consumer expectations compared against the provider's published OpenAPI | Rolling out across an estate, or the provider will not adopt tooling | Compares to a spec, not to running code — the spec can be wrong |
| **Schema compatibility** | Registry enforces evolution rules on a topic | Event-driven estates | Structural only; no consumer-specific knowledge |

Starting from nothing, bi-directional plus registry compatibility is a realistic first step, moving
the highest-risk pairs to full consumer-driven contracts over time.

## 7. What contract tests are not

They prove that two services **agree on the shape of an exchange**. They do not prove:

- that the provider's logic is correct — that is the provider's component tests;
- that the consumer handles the response sensibly — that is the consumer's own tests;
- that the deployment, network, and configuration work — that is the thin end-to-end layer;
- anything about performance, security, or resilience.

Keeping the scope narrow is what keeps contract tests fast, stable, and worth having. A contract
suite that has grown into a functional test suite will be slow, will fail for the wrong reasons,
and will be switched off.
