# Configuration Reference

Everything the skills read and write in your repository, and how to override the defaults.

---

## `.msskills/` — the state directory

Created in your repository root by `/stack-profile`. Most teams should commit it: blueprints and
decisions then get reviewed in pull requests like any other artefact.

| File | Written by | Read by |
|---|---|---|
| `config.yaml` | `/stack-profile`, or by hand | Every principle, Config Resolution step 1 |
| `stack.md` | `/stack-profile` | Every principle, Config Resolution step 5 |
| `designs/<feature>.md` | `/design-service` | `/implement-service`, `/review-service` |
| `decisions.md` | `collaborative-judgment` | Everything — a recorded decision is settled |
| `context-map.md` | `/design-service`, `service-boundaries` | `service-boundaries`, `cqrs-and-consistency` |
| `data-classification.md` | By hand | `secure-service` |

## `config.yaml`

One job: point each skill at your team's own standard, if you have one.

```yaml
paths:
  architecture: docs/standards/architecture.md
  testing: docs/standards/testing.md
  security: docs/standards/security.md
```

**Only include a key when the document exists.** A configured path with no file produces a warning
every time that skill runs.

### Every key

| Key | Skill | Governs |
|---|---|---|
| `boundaries` | `service-boundaries` | Where services divide, context mapping, data ownership |
| `architecture` | `clean-architecture` | Layering, dependency rules, SOLID, pattern selection |
| `domain` | `domain-modelling` | Entities, value objects, aggregates, ubiquitous language |
| `persistence` | `data-access` | Repositories, queries, transactions, migrations, caching |
| `consistency` | `cqrs-and-consistency` | CQRS level, projections, staleness, event sourcing |
| `api` | `api-contracts` | Specification format, evolution rules, error contract, events |
| `protocols` | `api-protocols` | REST, GraphQL, gRPC, WebSocket and SSE conventions |
| `adapters` | `infrastructure-adapters` | Port design, SDK wrapping, mapping, adapter testing |
| `resilience` | `resilience-patterns` | Timeouts, retries, breakers, outbox, sagas, probes |
| `idempotency` | `idempotency-and-immutability` | Retry safety, dedup, immutability rules |
| `security` | `secure-service` | Authorisation model, secrets, PII, supply chain |
| `testing` | `test-strategy` | Test levels, doubles, determinism, coverage policy |
| `contracts` | `contract-testing` | Contract tooling, verification, deploy gates |
| `config` | `config-and-dependencies` | Config mechanism, flags, dependency policy |
| `design` | `design-first` | Design levels, depth calibration, gate discipline |
| `judgment` | `collaborative-judgment` | How decisions are presented and recorded |

## Overriding a default

Your document's frontmatter decides how it combines with the skill's built-in defaults:

```markdown
---
mode: overlay
---

## Timeouts

Every outbound call uses a 250 ms timeout unless the design records otherwise.
Payment provider calls are the exception at 3 s, agreed with the payments team.
```

**`mode: overlay`** (the default, and what you want most of the time)

The skill reads its embedded defaults first, then applies your document on top. A section replaces
the matching default section **by exact heading**; sections you do not mention keep the defaults;
new sections append. Use this to adjust a handful of rules without restating everything.

Match the heading text exactly — `## Timeouts` replaces the defaults' `## Timeouts`. A near-miss
appends a second section instead of replacing.

**`mode: override`**

Your document is used alone; the embedded defaults are ignored entirely. Use this only when you
have a complete house standard, because anything you omit is simply not covered.

**No `mode` key** is treated as `overlay`.

## `stack.md`

Written by `/stack-profile`. Records what the project actually uses, so principles translate
generic pattern names into your libraries and idiom. See
[the template](../source/profiles/stack-profile/assets/stack-template.md) for the full shape and
[the worked example](../sample/orders-service/.msskills/stack.md) for a filled-in one.

Two things worth knowing:

- **Confidence markers matter.** `confirmed` (you said so), `detected` (read from a file),
  `inferred` (deduced — treat as a question). An inferred value is not a fact.
- **The Known gaps section is load-bearing.** Recording "no load-test suite" is what makes
  `resilience-patterns` present its timeout values as guesses rather than as derived numbers.

Re-run `/stack-profile` after adopting a new framework, broker, or test tool. It reads the existing
profile, shows what changed, and preserves anything you typed by hand.

## `decisions.md`

Appended to by `collaborative-judgment` whenever a genuine trade-off is settled. Format:

```markdown
## 2026-09-05 — Order confirmation is published as an event, not a synchronous call

**Context:** Checkout must not fail when the notification service is down.
**Options considered:** Synchronous call with circuit breaker; domain event via the outbox.
**Decision:** Domain event via the transactional outbox.
**Because:** Confirmation is not required for the order to be valid; availability of checkout
outranks immediacy of the email.
**Reversibility:** Costly — consumers will bind to the event schema.
**Consequences:** Adds an outbox table and a relay; `OrderConfirmed` is now a published contract.
```

A recorded decision is **settled** — skills apply it and do not re-ask. Never edit an entry;
append a new one naming the entry it supersedes and what changed.

## `data-classification.md`

Written by hand, read by `secure-service`. Categorises the data this service handles so the agent
knows what may be logged, cached, exported, or returned.

```markdown
| Field | Class | Handling |
|---|---|---|
| `customer.email` | Personal | Never logged; encrypted at rest; erasable |
| `payment.pan` | Sensitive personal | Field-level encryption; access audited |
| `product.name` | Public | No restriction |
```

Without it, `secure-service` applies its default categories, which are conservative but generic.

## Version control

Commit `.msskills/`. The exceptions are anything containing secrets — which nothing here should —
and, if your team prefers, in-progress `designs/*.md` with `status: draft`.

Add to `.gitignore` only if you have a specific reason:

```gitignore
.msskills/designs/*.draft.md
```
