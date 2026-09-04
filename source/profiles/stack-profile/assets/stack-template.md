# Stack Profile — template

Copy this to `.msskills/stack.md`. Fill what is known; write `unknown` or `none` rather than
guessing. Mark each row's confidence: **confirmed** (the user said so), **detected** (read from a
file), **inferred** (deduced — treat as a question, not a fact).

```markdown
---
updated: YYYY-MM-DD
confidence: detected | confirmed | mixed
---

# Stack Profile — <service or repository name>

## Platform

| Aspect | Value | Confidence |
|---|---|---|
| Language | e.g. Java 21 | detected |
| Framework | e.g. Spring Boot 3.4 | detected |
| Build tool | e.g. Maven | detected |
| Package manager / lockfile | e.g. Maven, `pom.xml` + dependency lock | detected |
| Runtime target | e.g. Kubernetes, Linux containers | detected |
| CI platform | e.g. GitHub Actions | detected |

## Architecture

| Aspect | Value | Confidence |
|---|---|---|
| Layering style | e.g. ports and adapters, four modules | detected |
| Module layout | e.g. feature-first: `orders/{domain,application,adapter}` | detected |
| Dependency injection | e.g. constructor injection via Spring | detected |
| Architecture tests | e.g. ArchUnit, or none | detected |

## Data

| Aspect | Value | Confidence |
|---|---|---|
| Primary datastore | e.g. PostgreSQL 16 | detected |
| Access style | e.g. Spring Data JPA; native SQL for queries | detected |
| Migration tool | e.g. Flyway, forward-only | detected |
| Cache | e.g. Redis, or none | detected |
| Read models / CQRS level | e.g. level 1 — queries only | confirmed |

## Messaging

| Aspect | Value | Confidence |
|---|---|---|
| Broker | e.g. Kafka, or none | detected |
| Schema registry | e.g. Confluent Schema Registry | confirmed |
| Compatibility mode | e.g. FULL | confirmed |
| Serialisation | e.g. Avro / JSON / protobuf | detected |
| Outbox mechanism | e.g. Debezium CDC, polling relay, or none | confirmed |

## API

| Aspect | Value | Confidence |
|---|---|---|
| Style | e.g. REST over HTTP/JSON | detected |
| Specification | e.g. OpenAPI 3.1 at `api/openapi.yaml`, spec-first | detected |
| Spec linter | e.g. Spectral in CI | detected |
| Error format | e.g. RFC 9457 problem+json | confirmed |
| Versioning | e.g. path-based, only on a break | confirmed |

## Resilience

| Aspect | Value | Confidence |
|---|---|---|
| Library | e.g. Resilience4j | detected |
| Applied at | e.g. application code; mesh handles retries at the edge | confirmed |
| Service mesh | e.g. Istio, or none | detected |

## Testing

| Aspect | Value | Confidence |
|---|---|---|
| Framework | e.g. JUnit 5 | detected |
| Assertions | e.g. AssertJ | detected |
| Mocking | e.g. Mockito | detected |
| Component tests | e.g. Testcontainers + WireMock | detected |
| Contract testing | e.g. Pact + Pact Broker, or none | confirmed |
| Mutation testing | e.g. PIT on the domain module, or none | detected |
| Naming convention | e.g. `method_scenario_expectedOutcome` | detected |

## Configuration and security

| Aspect | Value | Confidence |
|---|---|---|
| Config mechanism | e.g. environment variables via typed `@ConfigurationProperties` | detected |
| Secret manager | e.g. Vault via CSI driver | confirmed |
| Feature flags | e.g. LaunchDarkly, or none | confirmed |
| Service-to-service auth | e.g. mTLS via the mesh | confirmed |
| End-user auth | e.g. OIDC JWT, verified per service | confirmed |
| Dependency scanning | e.g. Dependabot + Trivy in CI | detected |

## Conventions worth knowing

Anything a generated change must match that the tables above do not capture — naming, error
handling idiom, logging style, package boundaries, formatting tool, review expectations.

## Known gaps

Aspects that are absent, and whether that is deliberate. Absence recorded here stops other skills
from assuming a tool exists.
```
