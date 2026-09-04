---
updated: 2026-09-05
confidence: mixed
---

# Stack Profile — orders-service

Worked example. This is what `stack-profile` writes after reading a repository and filling the gaps
by interview. Every principle reads it in step 5 of Config Resolution and translates its generic
pattern names into these libraries.

## Platform

| Aspect | Value | Confidence |
|---|---|---|
| Language | Java 21 | detected |
| Framework | Spring Boot 3.4 | detected |
| Build tool | Gradle 8, Kotlin DSL | detected |
| Package manager / lockfile | Gradle with dependency locking enabled | detected |
| Runtime target | Kubernetes, distroless container images | detected |
| CI platform | GitHub Actions | detected |

## Architecture

| Aspect | Value | Confidence |
|---|---|---|
| Layering style | Ports and adapters, four source sets | confirmed |
| Module layout | Feature-first: `orders/{domain,application,adapter}` | detected |
| Dependency injection | Constructor injection; no field injection | confirmed |
| Architecture tests | ArchUnit — no `adapter` import from `domain`, no cycles | detected |

## Data

| Aspect | Value | Confidence |
|---|---|---|
| Primary datastore | PostgreSQL 16 | detected |
| Access style | Spring Data JPA for aggregates; native SQL for read queries | detected |
| Migration tool | Flyway, forward-only, expand/migrate/contract | confirmed |
| Cache | Redis, for the pricing read model only | detected |
| CQRS level | 1 — one write model, purpose-built read queries | confirmed |

## Messaging

| Aspect | Value | Confidence |
|---|---|---|
| Broker | Kafka | detected |
| Schema registry | Confluent Schema Registry | confirmed |
| Compatibility mode | FULL | confirmed |
| Serialisation | Avro | detected |
| Outbox mechanism | Debezium change data capture on the `outbox` table | confirmed |

## API

| Aspect | Value | Confidence |
|---|---|---|
| Style | REST over HTTP/JSON | detected |
| Specification | OpenAPI 3.1 at `api/openapi.yaml`, authored before handlers | confirmed |
| Spec linter | Spectral in CI | detected |
| Error format | RFC 9457 `application/problem+json` | confirmed |
| Versioning | Path-based (`/v1`), minted only on a genuine break | confirmed |

## Resilience

| Aspect | Value | Confidence |
|---|---|---|
| Library | Resilience4j — circuit breaker, retry, time limiter, bulkhead | detected |
| Applied at | Application code. The mesh handles edge retries only | confirmed |
| Service mesh | Istio | detected |

## Testing

| Aspect | Value | Confidence |
|---|---|---|
| Framework | JUnit 5 | detected |
| Assertions | AssertJ | detected |
| Mocking | Mockito — ports only, never domain types | confirmed |
| Component tests | Testcontainers (PostgreSQL, Kafka) + WireMock for collaborators | detected |
| Contract testing | Pact JVM against a self-hosted Pact Broker; `can-i-deploy` gates deploys | confirmed |
| Mutation testing | PIT on the `domain` source set only | detected |
| Naming convention | `behaviour_scenario_expectedOutcome`, snake case | detected |

## Configuration and security

| Aspect | Value | Confidence |
|---|---|---|
| Config mechanism | Environment variables bound to typed `@ConfigurationProperties`, validated at startup | detected |
| Secret manager | HashiCorp Vault via the CSI driver | confirmed |
| Feature flags | Unleash | confirmed |
| Service-to-service auth | mTLS provided by Istio; no application-level service tokens | confirmed |
| End-user auth | OIDC JWT, verified in each service — never trusted from the gateway alone | confirmed |
| Dependency scanning | Dependabot for updates, Trivy for images, both in CI | detected |

## Conventions worth knowing

- Domain types are Java records where immutable; no Lombok anywhere.
- No checked exceptions across a layer boundary. Domain failures are sealed result types; adapters
  map them to problem details.
- Structured JSON logging via SLF4J. `orderId` and `correlationId` on every log line in a request
  scope. Never log a customer email or address.
- All money is `Money(long minorUnits, Currency currency)`. `BigDecimal` never crosses a boundary.
- Formatting by Spotless with `palantir-java-format`; the build fails on a formatting diff.

## Known gaps

- **No load or performance test suite.** Timeout values in `resilience-patterns` are therefore
  educated guesses rather than derived from measured percentiles — flag this whenever a timeout is
  chosen.
- **No architecture test on the `application` source set** — only `domain` is guarded. Adding one
  is on the backlog.
