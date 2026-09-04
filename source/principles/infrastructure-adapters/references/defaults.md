# Infrastructure Adapters — defaults

Loaded by Config Resolution when a project has no override, or as the base layer under an overlay.

---

## 1. Ports

A port is an interface **owned by the layer that uses it**, expressed entirely in that layer's
vocabulary. The adapter implements it. This is what makes the dependency arrow point inward
(see `clean-architecture`).

```
application/
  PaymentGateway            <- the port: domain types in, domain results out
  OrderRepository
adapter/
  StripePaymentGateway      <- implements PaymentGateway, knows about Stripe
  PostgresOrderRepository
```

Design rules:

- **Name for the capability, never the technology.** `PaymentGateway`, `EventPublisher`,
  `DispatchStatusPort` — not `StripeClient`, `KafkaProducer`, `WarehouseRestClient`. The name is
  the test: if it mentions a vendor, the abstraction has already leaked.
- **Domain types only in the signature.** No `HttpResponse`, `ConsumerRecord`, `ResultSet`,
  `JsonNode`, or vendor model. If a caller must read a status code to know what happened, the port
  is a thin alias for the protocol.
- **Model outcomes, not mechanisms.** `PaymentResult = Authorised | Declined(reason) | Unavailable`
  says what the domain cares about. `int statusCode` does not.
- **Size by consumer need.** Interface segregation says a caller should not depend on a port with
  eight methods when it uses one. In practice: one port per external system is a reasonable start;
  split when a second consumer needs a different slice.
- **Keep ports small enough to fake.** If writing an in-memory implementation for tests is painful,
  the port is too wide.

## 2. What belongs in the adapter

Everything about the outside world that the inside must not know:

| Concern | Belongs in the adapter because |
|---|---|
| Protocol and serialisation | The domain has no wire format |
| Authentication to the external system | It is a property of that integration |
| Timeouts, retries, circuit breaker | Failure is a property of the network, not the rule (see `resilience-patterns`) |
| Mapping between wire and domain models | This is the anti-corruption layer |
| Failure translation | Callers depend on the port's vocabulary, not the vendor's |
| Pagination and cursor handling | Mechanism, not meaning |
| Rate-limit handling and `Retry-After` | Protocol detail |
| Observability of the external call | Only here is there something to observe |

And what does **not** belong: any decision with business meaning. If the adapter chooses a default
because "that is what the business wants when the field is missing", that rule has escaped the
domain and nobody will find it there.

## 3. Wrapping a third-party SDK

The value of the wrapper is containment: exactly one class in the codebase knows this vendor
exists. That makes the vendor replaceable, the code testable, and the blast radius of their next
breaking change one file.

- **Do not mirror the SDK.** A wrapper exposing the same twenty methods with the same types is an
  alias. Expose the two operations you actually use, in your vocabulary.
- **Catch the vendor's exceptions at the boundary** and translate. Nothing outside should reference
  a vendor type in a `catch`.
- **Configure the client once**, immutably, at composition. A client rebuilt per call loses
  connection pooling and warm TLS sessions — a common and invisible latency problem.
- **Own the failure taxonomy.** Translate into: not found, rejected (business), invalid (ours),
  unavailable (theirs), timed out. Callers branch on those, not on codes.
- **Be a tolerant reader.** Ignore unknown fields; validate only what you use. Strict parsing turns
  every additive upstream change into an outage (see `api-contracts`).
- **Treat responses as untrusted.** Bound collection sizes, validate enums, check nesting depth. A
  trusted internal upstream can still be compromised or buggy (see `secure-service`).

## 4. Mapping

Mapping is where fields go missing, and it is almost always under-tested because it looks trivial.

- **Explicit functions, not reflection.** An auto-mapper silently produces `null` when a field is
  renamed on either side, and the failure appears far away.
- **One direction per function**, named `toDomain` / `toWire`. Bidirectional mappers hide asymmetry.
- **Test the mapping directly**, including absent optional fields, empty collections, and values at
  the edge of each range. Round-trip properties are a cheap way to get real coverage.
- **Map failures too.** The error response is part of the contract and needs the same treatment.
- **Do not share one model across the wire, the database, and the domain.** It is pragmatic exactly
  until the first field that only one of them needs — and then the coupling is everywhere.

## 5. Adapter shapes

**Outbound HTTP client.** Explicit connect and read timeouts; a bounded connection pool; retry with
backoff and jitter only on retryable failures; a circuit breaker; deadline propagation; trace
context outward. Never log a response body containing personal data.

**Message consumer.** Deserialise, validate, translate, delegate to one application use case — no
business logic here. Idempotent on the message ID (see `idempotency-and-immutability`). Bounded
retries, then dead-letter with enough context to replay. Acknowledge only after the effect is
durable, and handle redelivery and out-of-order arrival by design.

**Message publisher.** Publish from the outbox, not directly from a use case — a direct publish
beside a database commit is a dual write (see `resilience-patterns`). Populate the envelope:
`id`, `type`, `schemaVersion`, `occurredAt`, `correlationId`, `causationId`.

**Repository implementation.** Return domain aggregates; map at the boundary; never leak managed
entities or query builders. Details in `data-access`.

**Cache adapter.** Behind a port expressed in domain terms, not `get(String)`. A cache failure must
degrade to a miss, never to an error — a cache outage should be slow, not fatal.

**Blob or file storage.** Stream rather than buffering whole objects; bound sizes; validate content
type; generate keys that cannot be influenced into path traversal.

**Clock, IDs, randomness.** These are dependencies. Inject `Clock`, `IdGenerator`,
`RandomSource` — a static `now()` inside an adapter makes the behaviour untestable and the tests
flaky (see `test-strategy`).

## 6. Testing adapters

The rule: **stub the protocol, not the library.**

Mocking the SDK asserts that your code calls the SDK the way you believe it should be called — the
belief most likely to be wrong. Stubbing the wire exercises the real serialisation, the real error
mapping, the real timeout behaviour.

| Adapter | Test against |
|---|---|
| HTTP client | An in-process HTTP stub server |
| Message consumer/publisher | An embedded or containerised broker |
| Repository | A containerised database with real migrations applied |
| Cache | A containerised cache, or a fake behind the port |
| Blob storage | A local emulator, or a fake behind the port |
| Third-party SDK over HTTP | The stub server, pointed at by the SDK's base URL |

Always test the failure paths — the timeout, the 500, the malformed body, the redelivery — because
that is the code that only runs when something is already wrong. And keep an in-memory fake of each
port for use by tests of the layers above; that is what keeps their tests fast.

## 7. Adapters and a service mesh

Where a mesh provides timeouts, retries, and outlier detection, decide explicitly which layer owns
what and record it in `.msskills/stack.md`. Applying both multiplies retries
(see `resilience-patterns`).

A workable split: the mesh handles connection-level concerns and coarse retries at the edge; the
application handles anything requiring knowledge of the operation — whether it is idempotent, what
the fallback is, what a business failure means. The mesh cannot know that a `POST` without an
idempotency key must not be retried, and it can never supply a fallback, an outbox, or a
compensating action. Those stay in the adapter.
