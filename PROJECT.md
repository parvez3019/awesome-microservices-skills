# PROJECT.md — how this repository works

This is the single source of truth for contributors and for AI agents working on this repo.
`CLAUDE.md` and `AGENTS.md` both point here.

---

## 1. What this repository is

A library of **skills** — markdown instruction files that an AI coding agent loads on demand — that
install microservices engineering discipline into Claude Code, Cursor, and any other host that
speaks the [Agent Skills](https://agentskills.io) standard.

It is not a linter and not a framework. It changes what the agent *does* when it designs, writes,
refactors, or reviews service code.

---

## 2. Tiers

| Tier | Directory | What it is | Loaded |
|---|---|---|---|
| **Principle** | `source/principles/` | One concern, stated as enforceable checks. Never a workflow. | Automatically, when the work touches its concern; also by workflows |
| **Workflow** | `source/workflows/` | A multi-step procedure that composes principles and pauses at human gates | Usually invoked by the user (`/design-service`) |
| **Profile** | `source/profiles/` | A guided interview that writes project-specific standards into `.msskills/` | Invoked once per project |

A principle answers *"is this right?"*. A workflow answers *"what do I do next?"*. If a file starts
answering both, split it.

---

## 3. The build rule

```
source/{principles,workflows,profiles}/<name>/   →   skills/<name>/
```

Plugin hosts only discover skills **one level deep** under `skills/`, so the tiers cannot survive
into the build output. `skills/` is generated, committed, and read by every host manifest.

- **Never hand-edit `skills/`.** Edit `source/`, then `./tools/build-skills.sh`.
- CI runs the build and fails on any diff, so the committed output can never go stale.
- Skill names must be unique across all three tiers — the build fails on a collision.

---

## 4. Frontmatter budget

Use **only these six fields**. They are the portable subset shared by Claude Code, Cursor, claude.ai
skill uploads, and the Skills API. Claude Code extensions such as `argument-hint`,
`disable-model-invocation`, and `context: fork` are *rejected* on the API/upload path, which would
make these skills non-portable.

```yaml
---
name: resilience-patterns          # must equal the directory name
description: "..."                 # 120–1200 chars; see below
license: MIT
---
```

`compatibility`, `metadata`, and `allowed-tools` are also permitted but currently unused.

### Writing the `description`

The description is the **only** signal the agent uses to decide whether to load the skill. It is
truncated at 1,536 characters in the listing, and every skill's description sits in context for the
whole session — so it must be dense, and it must earn its space. Four parts, in this order:

1. **What it does**, imperative, leading with the trigger condition.
2. **What it covers** — the concrete concepts, because those words are what the agent matches on.
3. **When to use it** — literal phrases a user would type, in quotes.
4. **What it is *not*** — one clause pointing at the sibling skills that own the adjacent concerns.

Part 4 is not optional. Without it, `resilience-patterns` and `test-strategy` both fire on the word
"failure" and the agent loads two skills where one would do.

---

## 5. The fixed shape of a principle

Every principle uses these four sections, in this order, with no others at `##` level:

```markdown
## Config Resolution
## Self-Validation Checklist
## Active Anti-Pattern Scan
## Ambiguity Signals
```

**Config Resolution** — how the skill finds project-specific overrides. Identical logic everywhere:

1. Read `.msskills/config.yaml`; look up this skill's key under `paths:`.
2. A custom doc exists → read its frontmatter `mode`:
   - `override` → the custom doc is the sole reference; ignore the embedded defaults.
   - `overlay` (default) → read `./references/defaults.md` first, then apply the custom doc's
     sections on top. A section replaces the matching default section by exact heading; new
     sections append.
3. A path is configured but the file is missing → say which path is missing, then fall back.
4. No config → `./references/defaults.md`.
5. `.msskills/stack.md` exists → translate every generic pattern name into that stack's actual
   library and idiom before presenting anything.

**Self-Validation Checklist** — numbered, imperative, STOP-and-verify. Each item states a check
*and* the concrete fix when it fails. This is the section the agent actually runs.

**Active Anti-Pattern Scan** — a checkbox list of named failure modes. Any box the agent can check
is a defect to fix before presenting work. Name the anti-pattern, describe how to spot it, give the
remedy.

**Ambiguity Signals** — the places where two answers are both defensible. These route to
`collaborative-judgment` instead of being silently decided. Every principle has some; a principle
with none is overconfident and will produce bad calls.

Workflows have a freer shape but must declare a **Required Skills** list up front, marking each
`(always)` or `(conditional: …)`.

---

## 6. Size and progressive disclosure

- `SKILL.md` ≤ 12 KB, and aim for ≲ 8 KB. It is loaded in full whenever the skill fires.
- Depth goes in `references/defaults.md`, loaded only when Config Resolution asks for it. Reference
  files have no size limit.
- Templates the agent writes into a user's repo go in `assets/`.

---

## 7. Stack neutrality

Skill bodies name **patterns**, never libraries. `resilience-patterns` says "circuit breaker", not
"Resilience4j". The `stack-profile` skill records the project's language, framework, broker, and
test tooling into `.msskills/stack.md`; every other skill's Config Resolution step 5 reads it and
translates. A reference file may list per-stack equivalents in a table, but the checklist the agent
runs stays neutral.

---

## 8. Cross-references

Refer to another skill by its **bare name**: "see `clean-architecture`". This resolves whether the
skills were installed as a plugin (`/microservices-skills:clean-architecture`) or copied into
`.claude/skills/` by `tools/install.sh`. Never hard-code the plugin prefix.

`validate-skills.sh` checks that every backticked name matching a known skill actually exists, so a
renamed skill cannot leave dangling references.

---

## 9. Authoring anti-patterns

- **Prose that describes good practice.** "Services should be resilient" changes nothing. Write a
  check the agent can fail.
- **Advice with no failure mode.** Every rule needs its anti-pattern in the scan list.
- **Overlapping descriptions.** Two skills that fire on the same words means neither is trusted.
- **Silent judgment calls.** If the trade-off is real, it belongs in Ambiguity Signals.
- **Library lock-in in the body.** See §7.
- **A workflow with no STOP gate.** Workflows that never pause produce large unreviewable diffs.
- **Restating another skill.** Point at it instead.

---

## 10. Before you commit

```bash
./tools/build-skills.sh      # regenerate skills/ from source/
./tools/validate-skills.sh   # frontmatter, budgets, cross-references, links
git diff --stat skills/      # confirm the build output changed as you expect
```

Keep `version` identical across all seven manifests — `.claude-plugin/plugin.json`,
`.claude-plugin/marketplace.json`, `.cursor-plugin/plugin.json`,
`.cursor-plugin/marketplace.json`, `.codex-plugin/plugin.json`,
`.agents/plugins/marketplace.json`, and the root `plugin.json`. The validator enforces it, because
version drift across manifests is the most common release mistake here.

See [docs/repository-structure.md](docs/repository-structure.md) for what every folder is for, and
[docs/publishing.md](docs/publishing.md) for the release process.
