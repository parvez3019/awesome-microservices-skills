# Awesome Microservices Skills

<p align="left">
  <strong>Composable AI skills that hold an assistant to microservices engineering standards —
  boundary-aware, failure-aware, contract-first.</strong>
</p>

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude_Code-plugin-blue.svg)](https://code.claude.com/docs/en/plugins)
[![Cursor](https://img.shields.io/badge/Cursor-compatible-blue.svg)](https://cursor.com/docs/skills)
[![Agent Skills](https://img.shields.io/badge/Agent_Skills-conformant-8A2BE2.svg)](https://agentskills.io)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

## What is this?

Ask an AI assistant to "add a call to the pricing service" and you get a working call. You usually
do not get a timeout, a circuit breaker, an idempotency key, an authorisation check scoped to the
caller, or a test for the path where pricing times out. Nothing is wrong with the code — it is just
missing everything that separates a demo from a service someone gets paged about.

Awesome Microservices Skills fixes that with **21 composable skills in three tiers** that encode
what "done" means in a distributed system: where boundaries fall, what crosses them, how it fails,
who is allowed to call it, and which test proves it.

Three principles shaped the design:

- **Checks over advice** — "services should be resilient" changes nothing. *"Does this call have an
  explicit timeout shorter than the caller's deadline? If not, set one derived from the latency
  budget"* changes the output.
- **Composability over one big document** — small single-purpose skills that load only when
  relevant, and workflows that compose them, beat one instruction file that tries to cover
  everything.
- **Judgment handed back, not hidden** — sync or async, strong or eventual consistency, split or
  keep together. Every skill lists the calls it must *not* make silently, and routes them back to
  you with options, consequences, and a recommendation.

## The Three Tiers

| Tier | Purpose |
|---|---|
| **Principles** | Single-concern guardrails — boundaries, architecture, domain modelling, data access, contracts, protocols, resilience, security, testing, config. Each has a Config Resolution, a STOP-and-verify checklist, an anti-pattern scan, and its ambiguity signals. They load automatically when the agent touches code they govern |
| **Workflows** | Multi-step procedures that compose principles and pause at human gates — design, implement, refactor, review. You invoke these |
| **Profiles** | Guided interviews that record project-specific reality, so every principle stops speaking in generic pattern names |

## The Pipeline

Skills form a delivery loop: `/design-service` → `/implement-service` → `/review-service`, with
`/refactor-safely` for structural work. `/stack-profile` runs once before all of them and writes
`.msskills/stack.md`, which turns "add a circuit breaker" into *this* project's library, thresholds,
and idiom. Each stage reads and writes `.msskills/` — blueprints, decisions, the context map — so
the second feature starts with everything the first one settled.

```
   /stack-profile ──▶ .msskills/stack.md ──┐
                                           │  read by every principle
   /design-service ──▶ blueprint (approved)│
          │                                │
          ▼                                │
   /implement-service ──▶ code + tests ◀───┤
          │                                │
          ▼                                │
   /review-service ──▶ ranked findings ◀───┘
          │
   /refactor-safely ──▶ structure, no behaviour change
```

See [How It Works](docs/how-it-works.md) for the mechanics and
[the Catalogue](docs/catalogue.md) for every skill and what it checks.

## The Catalogue

### Principles

| Skill | Guards |
|---|---|
| [`service-boundaries`](source/principles/service-boundaries/SKILL.md) | Bounded contexts, context maps, data ownership, the modular-monolith-first bias, strangler-fig extraction |
| [`clean-architecture`](source/principles/clean-architecture/SKILL.md) | Ports and adapters, the dependency rule, SOLID at class *and* service level, patterns only for a named force |
| [`domain-modelling`](source/principles/domain-modelling/SKILL.md) | Entities and value objects, aggregate boundaries justified by an invariant, ubiquitous language, illegal states unrepresentable |
| [`data-access`](source/principles/data-access/SKILL.md) | Repositories, ORM discipline and N+1, transaction boundaries, locking, pooling, keyset pagination, zero-downtime migrations |
| [`cqrs-and-consistency`](source/principles/cqrs-and-consistency/SKILL.md) | The five CQRS levels, projections with a staleness budget, read-your-writes, event sourcing honestly, data ownership |
| [`api-contracts`](source/principles/api-contracts/SKILL.md) | Spec-first OpenAPI/AsyncAPI, additive evolution, RFC 9457 problem details, idempotency keys, event compatibility modes |
| [`api-protocols`](source/principles/api-protocols/SKILL.md) | REST cache semantics, GraphQL depth limits and batching, gRPC deadlines and evolution, WebSocket/SSE reconnection and backpressure |
| [`infrastructure-adapters`](source/principles/infrastructure-adapters/SKILL.md) | Ports owned inward, wrapping SDKs, anti-corruption mapping, tolerant readers, testing at the wire not the library |
| [`resilience-patterns`](source/principles/resilience-patterns/SKILL.md) | Timeouts and deadlines, retry budgets with full jitter, circuit breakers, bulkheads, outbox/inbox, sagas, health probes |
| [`idempotency-and-immutability`](source/principles/idempotency-and-immutability/SKILL.md) | Idempotency keys and dedup stores, conditional updates, exactly-once effect, immutable values and events, safe publication |
| [`secure-service`](source/principles/secure-service/SKILL.md) | OWASP API Top 10 as checks, object-level authorisation, service identity, secrets, PII, supply chain |
| [`test-strategy`](source/principles/test-strategy/SKILL.md) | Choosing the level, component tests with real infrastructure, test doubles, determinism, coverage versus mutation score |
| [`contract-testing`](source/principles/contract-testing/SKILL.md) | Consumer-driven flow, provider verification, `can-i-deploy` gates, message contracts, and what contract tests must never assert |
| [`config-and-dependencies`](source/principles/config-and-dependencies/SKILL.md) | Fail-fast typed config, environment parity, flags with an expiry, lockfiles, shared-library discipline |
| [`design-first`](source/principles/design-first/SKILL.md) | Progressive Design Facilitation — the four-level ladder, depth calibration, approval gates |
| [`collaborative-judgment`](source/principles/collaborative-judgment/SKILL.md) | How every trade-off above is presented, decided, and recorded |

### Workflows

| Skill | Does |
|---|---|
| [`/design-service`](source/workflows/design-service/SKILL.md) | Climbs context → components → interactions → contracts, one level per exchange, leaving an approved blueprint |
| [`/implement-service`](source/workflows/implement-service/SKILL.md) | Builds inside-out from that blueprint, running every checklist before showing you anything |
| [`/review-service`](source/workflows/review-service/SKILL.md) | Severity-ranked findings, each anchored to a file, a line, and the principle it breaks |
| [`/refactor-safely`](source/workflows/refactor-safely/SKILL.md) | Characterisation tests first, then small reversible steps; includes service extraction |

### Profiles

| Skill | Does |
|---|---|
| [`/stack-profile`](source/profiles/stack-profile/SKILL.md) | Detects your language, framework, broker and test tooling, asks about the gaps, writes `.msskills/stack.md` |

Plus a [`microservice-reviewer`](agents/microservice-reviewer.md) subagent that audits with no
memory of having written the code.

## Getting Started

1. **Install** — pick your host. Every option installs the same skills from the same
   [`skills/`](skills/) folder; the manifests are thin pointers, not copies.

   **Option A — Claude Code**

   In the chat:
   ```
   /plugin marketplace add parvez3019/awesome-microservices-skills
   /plugin install microservices-skills@awesome-microservices-skills
   ```

   Or from the terminal, non-interactively:
   ```bash
   claude plugin marketplace add parvez3019/awesome-microservices-skills
   claude plugin install microservices-skills@awesome-microservices-skills --yes
   ```

   Verify with `claude plugin marketplace list`, then type `/` in a session — the skills appear as
   `/microservices-skills:design-service`, and as bare `/design-service` when the name is
   unambiguous. Manifest: [`.claude-plugin/`](.claude-plugin/). Includes the
   [`microservice-reviewer`](agents/microservice-reviewer.md) subagent.

   **Option B — Cursor**

   Cursor supports the vendor-neutral [Agent Plugins](https://agentskills.io) spec, so the root
   [`plugin.json`](plugin.json) is discovered straight from the repository link — add it from
   **Cursor Settings → Customize → Plugins**, or point Cursor at:
   ```
   https://github.com/parvez3019/awesome-microservices-skills
   ```

   To vendor the skills into a project instead — the option most teams want, since the standards
   are then versioned and reviewed with the code:
   ```bash
   git clone https://github.com/parvez3019/awesome-microservices-skills.git
   cd awesome-microservices-skills
   ./tools/install.sh /path/to/your-service/.cursor/skills
   ```

   Cursor also reads `.claude/skills/`, so `./tools/install.sh /path/to/your-service/.claude/skills`
   serves Claude Code and Cursor from one directory. Manifest:
   [`.cursor-plugin/`](.cursor-plugin/). Cursor has no subagent concept, so `/review-service` runs
   as a single pass there — the workflow treats the independent second pass as an addition, not a
   requirement.

   **Option C — Codex**

   ```bash
   codex plugin marketplace add parvez3019/awesome-microservices-skills
   codex plugin add microservices-skills@awesome-microservices-skills
   codex plugin list | grep -i microservices
   ```

   Manifests: [`.codex-plugin/plugin.json`](.codex-plugin/plugin.json), registered by
   [`.agents/plugins/marketplace.json`](.agents/plugins/marketplace.json). Both are thin pointers at
   the shared `skills/` folder. As with Cursor, there is no subagent, so `/review-service` runs as a
   single pass.

   **Option D — any other AI tool**

   The skills are plain [Agent Skills](https://agentskills.io) markdown with the six portable
   frontmatter fields, so any conformant host can read them:
   ```bash
   git clone https://github.com/parvez3019/awesome-microservices-skills.git
   cd awesome-microservices-skills
   ./tools/install.sh ~/.claude/skills                    # Claude Code, all projects
   ./tools/install.sh /absolute/path/to/that/tool/skills  # anything else
   ```

   > **See it before you run it.** [`sample/`](sample/) contains a filled-in stack profile and an
   > approved blueprint for a realistic `orders-service`, so you can read what these skills produce.

2. **Profile the project** — `/stack-profile` reads the repository, asks only about what it could
   not detect, and writes `.msskills/stack.md` plus a starter `.msskills/config.yaml`. All commands
   are typed in the AI chat, not the terminal.

3. **Design** — `/design-service <feature>` climbs the four design levels, stopping for approval at
   each, and leaves an approved blueprint in `.msskills/designs/`.

4. **Implement** — `/implement-service` builds from that blueprint inside-out, layer by layer,
   running every applicable checklist before presenting anything.

5. **Review** — `/review-service` audits the change against every principle and reports
   severity-ranked findings anchored to files and lines.

The principles need no invocation. Writing an HTTP client pulls in `infrastructure-adapters`,
`resilience-patterns` and `secure-service`; writing a migration pulls in `data-access`.

## Make It Yours

The defaults are opinionated, which is the point. When your team disagrees, override rather than
fork. Create `.msskills/config.yaml` pointing at your own standards:

```yaml
paths:
  architecture: docs/standards/architecture.md
  testing: docs/standards/testing.md
```

Your document's frontmatter decides how it combines — `mode: overlay` (default) replaces matching
sections by heading and appends new ones; `mode: override` uses your document alone.
`/stack-profile` writes a starter config for you. See
[Configuration](docs/configuration.md) for every key.

## Learn More

- [How It Works](docs/how-it-works.md) — the tier model, the fixed shape of a principle, Config
  Resolution, and why the checks are written as STOP-and-verify
- [Repository Structure](docs/repository-structure.md) — what every folder is for, which are
  generated, and where things land after each kind of install
- [The Catalogue](docs/catalogue.md) — every skill, what it checks, and which sibling owns the
  adjacent concern
- [Configuration Reference](docs/configuration.md) — every `.msskills/config.yaml` key and every
  file the skills read and write
- [Publishing](docs/publishing.md) — releasing a new version to the Claude Code and Cursor
  marketplaces
- [Authoring Guide](CONTRIBUTING.md) — how to write a skill that actually changes behaviour
- [Worked Example](sample/) — a filled-in stack profile and approved blueprint

## License

MIT — see [LICENSE](LICENSE).
