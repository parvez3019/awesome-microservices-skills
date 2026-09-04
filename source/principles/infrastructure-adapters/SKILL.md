---
name: infrastructure-adapters
description: "Write the adapter layer that connects a service to everything outside it. Covers designing ports at the right granularity and owning them inward, wrapping third-party SDKs so their types never reach the domain, mapping and anti-corruption at the edge, where resilience and observability belong, adapters for HTTP clients, brokers, caches, blob storage and the clock, and how to test an adapter without testing the vendor. Use when writing or reviewing a client, a consumer, a publisher, a repository implementation, a mapper, or any wrapper around an external system, or when the user says 'adapter', 'port', 'client', 'SDK', 'wrapper', 'anti-corruption layer', or 'infrastructure'. This skill governs the outer layer's craft — the layering rules themselves belong to clean-architecture, persistence specifics to data-access."
license: MIT
---

# Infrastructure Adapters

The adapter layer is where a clean design usually leaks. A vendor SDK's exception type propagates
into a use case; a port is defined next to its implementation and named after the technology; a
retry appears in three layers because nobody agreed where it lives.

An adapter has exactly one job: **translate between the outside world and this service's own
vocabulary, and absorb everything about the outside world that the inside should not know.** If
the domain can tell which HTTP library you use, the adapter has failed.

## Config Resolution

1. Read `.msskills/config.yaml` in the repo root; look up `paths.adapters`.
2. A custom document exists at that path → read its frontmatter `mode`:
   - `override` → use it alone; ignore the defaults below.
   - `overlay` (default, or no `mode` key) → read [defaults](./references/defaults.md) first, then
     apply the custom document's sections on top, matched by exact heading; new sections append.
3. A path is configured but no file exists there → say which path is missing, then use the defaults.
4. No config file or no `paths.adapters` key → use [defaults](./references/defaults.md).
5. `.msskills/stack.md` exists → use its HTTP client, broker client, serialisation library, and
   resilience library, and note where a service mesh already provides retries or timeouts so they
   are not applied twice.

## Self-Validation Checklist

**STOP after writing or reviewing any adapter — a client, consumer, publisher, repository
implementation, mapper, or SDK wrapper. Verify every check. Fix failures before presenting.**

1. **PORT OWNED INWARD**: Is the interface declared in the layer that *uses* it, named for what the
   caller needs, not for the technology? `PaymentGateway`, not `StripeClient`; `OrderRepository`,
   not `JpaOrderRepository`.
2. **PORT IS DOMAIN-SHAPED**: Does the port's signature use domain types only — no `HttpResponse`,
   no `ConsumerRecord`, no vendor DTO, no `JsonNode`? If a caller must inspect a status code, the
   abstraction has leaked.
3. **VENDOR TYPES STOP HERE**: Does any type from the SDK, driver, or wire format escape this
   class? → map at the boundary; the adapter is the only place that knows the vendor exists.
4. **FAILURES TRANSLATED**: Are vendor exceptions caught and converted into the port's own failure
   vocabulary — not found, rejected, unavailable, timed out? A leaked `SdkException` forces every
   caller to depend on the vendor.
5. **NO BUSINESS RULES**: Does the adapter make any decision the domain should own — defaulting a
   value, deciding eligibility, choosing between outcomes? → move it inward.
6. **RESILIENCE LIVES HERE**: Are timeout, retry, and circuit breaker applied at this adapter and
   nowhere else in the call path? Exactly one layer retries (see `resilience-patterns`).
7. **MAPPING IS EXPLICIT AND TESTED**: Is the translation a named, tested function rather than
   reflection-based auto-mapping? An auto-mapper silently drops a field when the shape changes.
8. **TOLERANT READER**: Does the adapter ignore unknown fields from upstream rather than failing on
   them, and validate only the fields it actually uses? A strict parser breaks on every additive
   change upstream (see `api-contracts`).
9. **UNTRUSTED INPUT**: Is data from an external system validated and bounded before use — sizes,
   counts, enum values, nested depth? An upstream response deserves the same suspicion as user
   input (see `secure-service`).
10. **AMBIENT DEPENDENCIES INJECTED**: Are the clock, ID generation, and randomness injected rather
    than called statically, so the adapter is testable? (see `test-strategy`)
11. **CONFIGURED, NOT HARD-CODED**: Are endpoints, timeouts, and pool sizes typed configuration
    validated at startup? (see `config-and-dependencies`)
12. **OBSERVABLE**: Does the adapter record the outcome and duration of the external call, and
    propagate the trace and correlation context outward?
13. **TESTED AT THE WIRE**: Is the adapter tested against a stubbed protocol — an HTTP stub server,
    an embedded broker, a container — rather than by mocking the SDK? Mocking the SDK tests your
    belief about the SDK, which is the thing most likely to be wrong.

All checks pass → state "Adapter holds: port <name>, vendor types contained, failures translated."

## Active Anti-Pattern Scan

Any box you can check is a defect. Fix it before presenting.

- [ ] **Port Named After Technology**: `KafkaPublisher`, `RedisCache`, `RestClient` as the interface
      the domain depends on → name it for the capability.
- [ ] **Port Defined Beside Its Implementation**: the interface living in the adapter package → it
      belongs to the layer that uses it.
- [ ] **Leaked Vendor Type**: an SDK model, `HttpResponse`, `ResultSet`, `ConsumerRecord`, or raw
      JSON crossing the port.
- [ ] **Leaked Vendor Exception**: the caller catching a library-specific exception → translate.
- [ ] **Anaemic Wrapper**: a class that forwards every SDK method one-to-one with no translation →
      that is not an adapter; it is an alias with a maintenance cost.
- [ ] **Business Logic in the Adapter**: eligibility, defaulting, or branching on domain meaning →
      move it into the domain.
- [ ] **Strict Reader**: deserialisation that fails on an unknown field from upstream → tolerate
      additions.
- [ ] **Blind Trust**: an upstream response used without bounds or validation → treat it as
      untrusted input.
- [ ] **Retry in Two Places**: adapter, client library, gateway, and mesh all retrying → pick one.
- [ ] **Missing Timeout**: any outbound call using the library default.
- [ ] **Reflection Mapping**: an auto-mapper between models, so a renamed field silently becomes
      null → explicit, tested mapping.
- [ ] **Static Clock or Random**: `now()` or a random source called directly inside the adapter.
- [ ] **Shared Mutable Client State**: a client configured per call, or one mutated between calls →
      configure once, use immutably.
- [ ] **SDK Mocked in Tests**: the adapter's tests assert on mocked SDK calls → stub the protocol.
- [ ] **Adapter With No Test**: "it is just a wrapper" — the wrapper is exactly where serialisation
      and error mapping bugs live.

## Ambiguity Signals

Route these through `collaborative-judgment`. Each has two defensible answers.

- **Port granularity.** One port per external system is simple; one narrow port per use case is
  honest about what each caller needs and multiplies interfaces. The interface-segregation reading
  favours narrow ports; the maintenance reading favours fewer.
- **Whether to wrap an SDK at all.** A wrapper buys testability, replaceability, and containment,
  and costs a layer of indirection. For a small, stable, ubiquitous library it can be ceremony.
- **Where resilience is applied** when a service mesh already provides retries and timeouts.
  Duplicating them multiplies; relying on the mesh alone means the behaviour is invisible in the
  code and absent in tests.
- **Mapping cost.** Separate wire, persistence, and domain models are correct and triple the types.
  Sharing one is pragmatic until the first field only one of them needs.
- **How much to validate from a trusted internal upstream.** Full validation is safest and
  duplicates the provider's contract; none makes you dependent on their correctness.
- **Generated clients or hand-written ones.** Generated stays in step with the spec and imports its
  shape wholesale; hand-written is an anti-corruption layer by construction and drifts.
