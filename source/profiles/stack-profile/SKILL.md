---
name: stack-profile
description: "Record this project's technology choices once, so every other skill speaks the team's actual language instead of generic pattern names. Detects the language, framework, datastore, broker, test tooling, contract tooling, secret manager, and deployment platform from the repository, confirms the gaps by interview, and writes .msskills/stack.md plus a starter .msskills/config.yaml. Use on first setup in a repository, after adopting a new framework or broker, when guidance from other skills feels generic, or when the user says 'set up', 'stack profile', 'configure the skills', or 'onboard this repo'. Run this before the workflows — it is what turns 'add a circuit breaker' into the project's own library and idiom."
license: MIT
---

# Stack Profile

Every other skill in this library deliberately names patterns rather than libraries: "circuit
breaker", not a specific implementation. That keeps the guidance portable, and it makes the advice
vague until someone says what this project actually uses.

This skill closes that gap once. It writes `.msskills/stack.md`, which every principle reads in
step 5 of its Config Resolution, and a starter `.msskills/config.yaml` pointing at any house
standards the team already has.

## Workflow

### Step 1 — Detect what you can

Read the repository before asking anything. A question whose answer is sitting in a manifest file
wastes the user's time and signals you did not look.

Look for, in this order:

1. **Build and dependency manifests** — `pom.xml`, `build.gradle*`, `package.json`, `go.mod`,
   `*.csproj`, `Cargo.toml`, `pyproject.toml`, `requirements.txt`, `Gemfile`. These give the
   language, the framework, and most libraries.
2. **Lockfiles** — confirm actual versions rather than declared ranges.
3. **Container and deployment files** — `Dockerfile`, `docker-compose*`, `*.yaml` under `k8s/`,
   `helm/`, `.github/workflows/`, Terraform. These give the platform, the datastore, and the broker.
4. **Configuration** — `application*.yml`, `appsettings*.json`, `.env.example`, config packages.
   These give the config mechanism and often the secret manager.
5. **Existing tests** — the framework, the assertion style, whether containers or contract tooling
   are already in use, and the naming convention.
6. **Existing architecture** — the package or module layout, any architecture tests, any
   specification files (`openapi.*`, `asyncapi.*`, `*.proto`).
7. **Existing standards** — a `CONTRIBUTING.md`, `ARCHITECTURE.md`, `docs/`, or an ADR directory.
   If the team already has written standards, they outrank this library's defaults, and
   `config.yaml` should point at them.

An empty or greenfield repository is a valid answer. Say so and move to the interview.

### Step 2 — Present what you found, then ask only for the gaps

Show the detected profile as a compact table with a confidence marker, then ask about what is
genuinely missing or ambiguous. Batch the questions into one message — see
`collaborative-judgment` on batching.

```markdown
Detected from the repository:

| Aspect | Value | Source |
|---|---|---|
| Language | Java 21 | pom.xml |
| Framework | Spring Boot 3.4 | pom.xml |
| Datastore | PostgreSQL 16 | docker-compose.yml, Flyway migrations |
| Test framework | JUnit 5 + AssertJ + Testcontainers | pom.xml, src/test |
| Resilience | Resilience4j | pom.xml |

Not found — could you confirm?
1. Message broker: none detected. Is this service synchronous only, or is a broker planned?
2. Contract testing: nothing detected. Is there a broker for contracts, or is this the first?
3. Secret management: where do credentials come from in production?
4. Do you already have written architecture or testing standards I should point the skills at?
```

Ask no more than six questions. If the user does not know an answer, record it as `unknown` and
move on — an incomplete profile is far better than an interview nobody finishes.

### Step 3 — Cover the aspects that matter

The profile is only useful for what other skills actually consult. Aim to fill these; leave the
rest blank rather than padding.

| Aspect | Read by |
|---|---|
| Language, version, idiom notes | every skill |
| Framework and DI style | `clean-architecture` |
| Module and package layout, architecture-test tool | `clean-architecture`, `service-boundaries` |
| Datastore, ORM/query style, migration tool | `data-access` |
| CQRS level, read models, consistency | `cqrs-and-consistency` |
| Type-system idiom for domain types | `domain-modelling`, `idempotency-and-immutability` |
| API style: REST, GraphQL, gRPC, push | `api-protocols` |
| Broker, schema registry and compatibility mode | `api-contracts`, `resilience-patterns` |
| Specification format, error contract, event schemas | `api-contracts` |
| Port and adapter conventions, service mesh | `infrastructure-adapters` |
| Resilience library | `resilience-patterns` |
| Test framework, assertions, container and stub tooling | `test-strategy` |
| Contract tooling and broker | `contract-testing` |
| Config mechanism, secret manager, flag system | `config-and-dependencies`, `secure-service` |
| Auth model between services | `secure-service` |
| Package manager, lockfile, update automation | `config-and-dependencies` |
| CI platform, deployment target | workflows |

### Step 4 — Write the files

Write `.msskills/stack.md` using [the template](./assets/stack-template.md). Keep it factual: what
is used, not what is recommended. Mark anything inferred rather than confirmed.

Then write `.msskills/config.yaml` if it does not exist:

```yaml
# Points skills at this project's own standards. Delete any key you have no document for —
# a key with no file produces a warning on every run.
paths:
  architecture: docs/standards/architecture.md   # clean-architecture
  testing: docs/standards/testing.md             # test-strategy
  # api:          # api-contracts
  # protocols:    # api-protocols
  # security:     # secure-service
  # boundaries:   # service-boundaries
  # domain:       # domain-modelling
  # persistence:  # data-access
  # consistency:  # cqrs-and-consistency
  # adapters:     # infrastructure-adapters
  # resilience:   # resilience-patterns
  # idempotency:  # idempotency-and-immutability
  # contracts:    # contract-testing
  # config:       # config-and-dependencies
  # judgment:     # collaborative-judgment
  # design:       # design-first
```

Only include keys for documents that exist. A custom document needs `mode: overlay` (add to the
defaults) or `mode: override` (replace them) in its own frontmatter.

### Step 5 — Confirm and hand off

Show the written profile, say which skills it will change the behaviour of, and name the concrete
difference:

> Written `.msskills/stack.md`. `resilience-patterns` will now say Resilience4j rather than
> "a circuit breaker library", and `test-strategy` will assume Testcontainers for component tests.
> Contract testing is recorded as `none` — when you adopt a tool, rerun this skill.

## Rules

- **Detect before asking.** Anything discoverable from the repository must not be a question.
- **Record, do not recommend.** This skill captures what the project uses. If something is missing
  — no contract testing, no secret manager — note it as absent. Suggesting a tool here would put a
  recommendation into a file that ten other skills treat as fact.
- **Mark confidence.** Distinguish confirmed by the user, read from a file, and inferred.
- **Never invent.** If a library was not found and the user did not name one, write `unknown`. A
  guessed library name propagates into generated code.
- **Re-running is normal.** Read the existing profile, show what changed, and preserve anything the
  user typed by hand.
- **Keep it short.** This file is read by every skill. Facts and versions, not prose.
