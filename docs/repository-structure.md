# Repository Structure

What every folder is for, which ones are generated, and which ones you edit.

---

## The map

```
awesome-microservices-skills/
│
├── source/                     ✏️  EDIT HERE — the authoring tree
│   ├── principles/<name>/
│   │   ├── SKILL.md                the guardrail: checklist, anti-patterns, ambiguity signals
│   │   └── references/
│   │       └── defaults.md         the depth, loaded only when Config Resolution asks
│   ├── workflows/<name>/
│   │   └── SKILL.md                a multi-step procedure that composes principles
│   └── profiles/<name>/
│       ├── SKILL.md                a guided interview
│       └── assets/                 templates the skill writes into a user's repo
│
├── skills/                     🤖  GENERATED — never edit by hand
│                                   Flat copy of every skill above. This is what all host
│                                   manifests read.
│
├── agents/                     ✏️  Subagent definitions (Claude Code only)
│   └── microservice-reviewer.md    read-only auditor used by /review-service
│
├── tools/                      ✏️  Build and quality tooling
│   ├── build-skills.sh             source/ → skills/ (flattens the tiers)
│   ├── install.sh <dir>            copies skills into any agent's skills folder
│   ├── validate-skills.sh          the quality gate (wrapper)
│   └── validate_skills.py          the actual checks
│
├── docs/                       ✏️  Documentation for humans
│   ├── how-it-works.md             the tier model and the mechanics
│   ├── catalogue.md                every skill, and which sibling owns the adjacent concern
│   ├── configuration.md            every .msskills/ file and config.yaml key
│   ├── repository-structure.md     this file
│   └── publishing.md               releasing to the Claude Code and Cursor marketplaces
│
├── sample/                     ✏️  Worked example — the state the skills read and write
│   ├── README.md
│   └── orders-service/.msskills/
│       ├── stack.md                a filled-in stack profile
│       └── designs/…               an approved blueprint
│
├── .claude-plugin/             ✏️  HOST MANIFEST — Claude Code
│   ├── plugin.json                 the plugin: name, version, keywords
│   └── marketplace.json            the marketplace registry that lists it
├── .cursor-plugin/             ✏️  HOST MANIFEST — Cursor
│   ├── plugin.json
│   └── marketplace.json
├── .codex-plugin/              ✏️  HOST MANIFEST — Codex
│   └── plugin.json
├── .agents/plugins/            ✏️  HOST MANIFEST — the Codex/agents plugin registry
│   └── marketplace.json
├── plugin.json                 ✏️  HOST MANIFEST — vendor-neutral Agent Plugins 1.0
│
├── .github/
│   ├── workflows/ci.yml            validate + build-drift check on every PR
│   └── ISSUE_TEMPLATE/
│
├── PROJECT.md                  ✏️  Repo conventions — the source of truth for contributors
├── CLAUDE.md · AGENTS.md       ✏️  Thin pointers at PROJECT.md, for the agents working here
├── CONTRIBUTING.md             ✏️  How to write a skill that changes behaviour
├── README.md · LICENSE · CHANGELOG.md
└── .gitignore
```

---

## The two rules that follow from this layout

**1. `skills/` is generated. Never edit it.**

Edit `source/`, then run `./tools/build-skills.sh`. CI rebuilds and fails on any diff, so a
hand-edited `skills/` will be caught — but only after you have wasted the round trip.

**2. Every host manifest points at the same `skills/` folder.**

There is exactly one copy of every skill. The five manifest locations are thin pointers, not
duplicates. Adding a new host means adding a manifest, not copying content.

---

## Why `source/` and `skills/` both exist

Plugin hosts discover skills **one level deep** under `skills/` — `skills/<name>/SKILL.md` becomes
`/<plugin>:<name>`. Nesting deeper is not supported, so the `principles/`, `workflows/`, and
`profiles/` tiers cannot survive into the build output.

But the tiers are genuinely useful to contributors: they say what kind of thing each skill is, and
they make 21 skills navigable. So they live in `source/`, and `build-skills.sh` flattens them.

The obvious risk is drift between the two. CI closes it:

```yaml
- run: ./tools/build-skills.sh
- run: git diff --exit-code -- skills/     # fails if the committed output is stale
```

---

## Anatomy of a skill folder

```
source/principles/resilience-patterns/
├── SKILL.md                   ≤ 12 KB — loads in full whenever the skill fires
└── references/
    └── defaults.md            unlimited — loads only when Config Resolution asks
```

`SKILL.md` carries the frontmatter (six portable fields only) and the four fixed sections. Depth,
tables, worked examples, and per-stack translations go in `references/`. Profiles also have
`assets/` for templates they write into a user's repository.

This split is the whole cost model: the description is always in context, the body loads when
relevant, the references load when needed. See [How It Works](how-it-works.md).

---

## Where things land after install

Two different shapes, depending on how a user installed.

**As a plugin** — the client clones this repository and reads the host manifest. Skills are
namespaced:

```
/microservices-skills:design-service      (and bare /design-service when unambiguous)
```

**Manually**, via `./tools/install.sh ~/.claude/skills` — the flat skill folders are copied into
the target directory. No namespace:

```
~/.claude/skills/
├── api-contracts/SKILL.md
├── clean-architecture/SKILL.md
└── …                                     → /design-service
```

This is why every cross-reference inside a skill uses the **bare name** — "see
`clean-architecture`" — and never a plugin prefix. The validator enforces that those names resolve.

---

## What the skills create in *your* repository

Nothing from this repository is copied into a consumer's project except the skills themselves. The
skills then read and write one directory:

```
your-service/
└── .msskills/
    ├── config.yaml             points skills at your own standards
    ├── stack.md                your language, framework, broker, test tooling
    ├── decisions.md            trade-offs, why they were decided, and by whom
    ├── context-map.md          bounded contexts and their relationships
    └── designs/<feature>.md    blueprints, gated by status: approved
```

Commit it. Blueprints and decisions are then reviewed in pull requests like any other artefact. See
[Configuration](configuration.md) for every file and key.
