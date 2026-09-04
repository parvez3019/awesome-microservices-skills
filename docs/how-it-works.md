# How It Works

The mechanics behind the 21 skills: what a skill is, the shape every principle shares, how project
overrides are resolved, and why the checks are written the way they are.

---

## 1. What a skill is

A skill is a markdown file with YAML frontmatter that an AI coding agent loads **on demand**. The
frontmatter's `description` is the only thing sitting in context all the time; the body loads when
the agent decides the skill is relevant, and the reference material loads only when the body asks
for it.

That is the whole cost model, and it drives every design choice here:

| Layer | When it loads | Budget |
|---|---|---|
| `description` | Always | 120–1200 characters |
| `SKILL.md` body | When the skill fires | ≤ 12 KB, target ≲ 8 KB |
| `references/*.md` | When Config Resolution asks | Unlimited |
| `assets/*` | When the skill writes a file from a template | Unlimited |

Sixteen principles' descriptions cost a few thousand tokens. The 200 KB of depth behind them costs
nothing until it is needed.

## 2. The three tiers

**Principles** answer *"is this right?"*. One concern each, stated as checks rather than advice.
They fire automatically — writing an outbound HTTP client is enough for `infrastructure-adapters`,
`resilience-patterns` and `secure-service` to become relevant. You rarely invoke one by name.

**Workflows** answer *"what do I do next?"*. They declare which principles they load and when,
sequence the work, and stop at human gates. You invoke these: `/design-service`,
`/implement-service`, `/review-service`, `/refactor-safely`.

**Profiles** answer *"what is true about this project?"*. Guided interviews that write facts into
`.msskills/`, which principles then read.

If a file starts answering two of those questions, it is split.

## 3. The fixed shape of a principle

Every principle has the same four sections, in the same order. Predictability is the point — the
agent knows where to look, and a reviewer can compare two skills.

### Config Resolution

How the skill finds project-specific overrides. Identical logic in every principle:

1. Read `.msskills/config.yaml`; look up this skill's key under `paths:`.
2. A custom document exists → read its frontmatter `mode`:
   - `override` → the custom document is the sole reference.
   - `overlay` (default) → read the embedded defaults first, then apply the custom document's
     sections on top. A section replaces the matching default section **by exact heading**; new
     sections append.
3. A path is configured but the file is missing → say which path, then fall back to the defaults.
4. No config → the embedded defaults.
5. `.msskills/stack.md` exists → translate every generic pattern name into the project's actual
   library and idiom.

Step 5 is what makes stack neutrality work without making the guidance vague. See §5.

### Self-Validation Checklist

Numbered, imperative, STOP-and-verify. Each item states a check **and** the concrete fix when it
fails:

> **TIMEOUT**: Does this call have an explicit timeout, shorter than the caller's own deadline? A
> default of "none" or "60s inherited from the client library" → set one derived from the latency
> budget.

This is the section that actually runs. The phrasing is deliberate: a question the agent can answer
about the code in front of it, and an action when the answer is wrong. Compare with what it
replaces — "consider setting appropriate timeouts" — which is unfalsifiable and therefore inert.

### Active Anti-Pattern Scan

A checkbox list of named failure modes. Any box the agent can check is a defect to fix before
presenting work. Each entry names the anti-pattern, says how to spot it, and gives the remedy:

> - [ ] **Retry Storm**: retries at client, gateway, and service layers compounding → one layer only.

Named failure modes are more findable than described ones. "Retry storm" is a thing an agent can
look for; "be careful with retries" is not.

### Ambiguity Signals

The places where two answers are both defensible. These are routed to `collaborative-judgment`
instead of being silently decided.

A principle with no ambiguity signals is overconfident and will produce bad calls. This is the
section that keeps the library from turning an assistant into a confident source of architectural
decisions nobody made.

Workflows have a freer shape, but must declare a **Required Skills** list up front, marking each
`(always)` or `(conditional: …)`.

## 4. How the pieces compose

A workflow does not restate a principle; it loads it and says when. `/implement-service` maps
component kinds to the principles that govern them:

| Component kind | Apply |
|---|---|
| Domain type or aggregate | `domain-modelling`, `clean-architecture`, `idempotency-and-immutability` |
| Repository, query, or migration | `data-access`, `clean-architecture` |
| Outbound adapter | `infrastructure-adapters`, `resilience-patterns`, `secure-service` |

Then, before showing any code, it runs each applicable principle's checklist and anti-pattern scan,
fixes what fails, and surfaces flagged ambiguity signals through `collaborative-judgment`.

Principles cross-reference each other by **bare name** — "see `clean-architecture`" — which resolves
whether the skills were installed as a plugin (`/microservices-skills:clean-architecture`) or copied
into `.claude/skills/`. The validator checks that every such reference exists, so a rename cannot
leave a dangling pointer.

Descriptions also carry an explicit **negative boundary**: each one ends by naming the sibling that
owns the adjacent concern. Without it, `resilience-patterns` and `test-strategy` both fire on the
word "failure", and the agent loads two skills where one would do.

## 5. Stack neutrality, without vagueness

Skill bodies name **patterns**, never libraries. `resilience-patterns` says "circuit breaker", not
"Resilience4j". That keeps the library usable by a Go team and a .NET team from the same file.

The cost is that generic guidance is less actionable — so `/stack-profile` closes the gap once per
repository. It detects what it can from manifests, lockfiles, deployment files, and existing tests,
asks about the rest, and writes `.msskills/stack.md`. Every principle's Config Resolution step 5
reads it.

With a profile, "add a circuit breaker" becomes the project's own library with the project's own
thresholds. Without one, the advice is still correct — just generic — and the skill says so once
rather than guessing a library name that would then propagate into generated code.

## 6. The `.msskills/` directory

State the skills read and write, in the consumer's repository:

| File | Written by | Read by |
|---|---|---|
| `stack.md` | `/stack-profile` | Every principle, step 5 |
| `config.yaml` | `/stack-profile`, or by hand | Every principle, step 1 |
| `designs/<feature>.md` | `/design-service` | `/implement-service`, `/review-service` |
| `decisions.md` | `collaborative-judgment` | Everything — a recorded decision is settled |
| `context-map.md` | `/design-service`, `service-boundaries` | `service-boundaries`, `cqrs-and-consistency` |

`decisions.md` is what stops the agent re-asking a question the team answered last month. Decisions
are appended, never edited — a superseding entry names the one it replaces and says what changed,
because the history of *why* a system is shaped this way is worth more than a tidy file.

Most teams should commit `.msskills/` alongside the code, so blueprints and decisions are reviewed
in pull requests like anything else.

## 7. Repository mechanics

```
source/{principles,workflows,profiles}/<name>/   →   skills/<name>/
```

Plugin hosts discover skills only **one level deep** under `skills/`, so the tiers cannot survive
into the build output. `source/` is the authoring tree — tiered, navigable — and `skills/` is
generated, committed, and read by all four host manifests.

`tools/validate-skills.sh` is the quality gate: frontmatter within the six portable fields, `name`
matching the directory, description length, required sections present and in order, links resolving,
cross-references existing, size limits, and version agreement across the manifests. CI runs it, then
rebuilds and fails on any diff — so the committed output can never go stale.

## 8. Why the frontmatter is only six fields

`name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools` — the portable subset
shared by Claude Code, Cursor, claude.ai skill uploads, and the Skills API. Claude Code extensions
such as `argument-hint`, `disable-model-invocation`, and `context: fork` are rejected on the
API/upload path, which would make these skills non-portable for the sake of small conveniences.
Staying inside the subset means the same files load everywhere, unchanged.
