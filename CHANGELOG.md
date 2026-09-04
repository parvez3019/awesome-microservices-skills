# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project uses
[semantic versioning](docs/publishing.md#4-versioning-policy) as interpreted for a skill library:
renaming or removing a skill, or changing a `config.yaml` key, is a **major** change.

## [Unreleased]

## [0.1.0] — 2026-09-05

First release. 21 skills across three tiers, with build tooling, a validator, CI, and manifests for
Claude Code, Cursor, Codex, and any Agent-Plugins-conformant host.

### Principles (16)

- `service-boundaries` — bounded contexts, context maps, data ownership, modular-monolith-first
  bias, strangler-fig extraction
- `clean-architecture` — ports and adapters, the dependency rule, SOLID at class and service level,
  patterns only for a named force
- `domain-modelling` — entities and value objects, aggregates justified by an invariant, ubiquitous
  language, illegal states unrepresentable
- `data-access` — repositories, N+1, transaction boundaries, locking, pooling, keyset pagination,
  zero-downtime migrations
- `cqrs-and-consistency` — the five CQRS levels, projections with a staleness budget,
  read-your-writes, event sourcing honestly
- `api-contracts` — spec-first OpenAPI/AsyncAPI, additive evolution, RFC 9457 problem details,
  idempotency keys, event compatibility modes
- `api-protocols` — REST, GraphQL, gRPC, WebSocket and SSE selection and per-protocol craft
- `infrastructure-adapters` — ports owned inward, SDK wrapping, anti-corruption mapping, testing at
  the wire
- `resilience-patterns` — timeouts, retry budgets with full jitter, circuit breakers, bulkheads,
  outbox/inbox, sagas, health probes
- `idempotency-and-immutability` — idempotency keys, conditional updates, exactly-once effect,
  immutable values and events, safe publication
- `secure-service` — OWASP API Top 10 as checks, object-level authorisation, service identity,
  secrets, PII, supply chain
- `test-strategy` — the test portfolio, component tests with real infrastructure, doubles,
  determinism, coverage versus mutation score
- `contract-testing` — consumer-driven flow, provider verification, `can-i-deploy` gates, message
  contracts
- `config-and-dependencies` — fail-fast typed config, environment parity, flags with an expiry,
  lockfiles, shared-library discipline
- `design-first` — Progressive Design Facilitation: the four-level ladder, depth calibration,
  approval gates
- `collaborative-judgment` — how trade-offs are presented, decided, and recorded

### Workflows (4)

- `/design-service`, `/implement-service`, `/review-service`, `/refactor-safely`

### Profiles (1)

- `/stack-profile` — writes `.msskills/stack.md` and a starter `.msskills/config.yaml`

### Agents

- `microservice-reviewer` — read-only independent auditor used by `/review-service`

### Tooling

- `tools/build-skills.sh` — compiles the tiered `source/` tree into the flat `skills/` folder
- `tools/install.sh` — installs into any agent's skills directory
- `tools/validate-skills.sh` — frontmatter, description budgets, required sections, link and
  cross-reference resolution, size limits, and manifest version agreement
- CI validates, rebuilds, and fails on any drift in `skills/`

[Unreleased]: https://github.com/parvez3019/awesome-microservices-skills/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/parvez3019/awesome-microservices-skills/releases/tag/v0.1.0
