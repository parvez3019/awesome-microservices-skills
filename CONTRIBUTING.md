# Contributing

New skills, sharper checks, and better anti-pattern descriptions are all welcome. This guide is
about writing a skill that actually changes an agent's behaviour — the mechanical conventions the
validator enforces are in [PROJECT.md](PROJECT.md).

---

## Before you start

```bash
git clone https://github.com/parvez3019/awesome-microservices-skills.git
cd awesome-microservices-skills
make check     # should pass on a fresh clone
make help      # every available target
```

Two rules that will otherwise cost you a review round:

1. **Never edit `skills/`.** It is generated. Edit `source/`, then `make build`.
2. **Run `make check` before pushing.** It is exactly what CI runs, and it catches the frontmatter
   mistakes that make a skill silently never load.

---

## The one thing that separates a useful skill from a useless one

**Write checks, not advice.**

An agent already knows what good practice is in the abstract. Telling it again changes nothing.
What changes the output is a question it can ask about the code in front of it, with an action
attached when the answer is wrong.

| Inert | Effective |
|---|---|
| "Services should be resilient to downstream failures." | "**TIMEOUT**: Does this call have an explicit timeout, shorter than the caller's own deadline? A default of 'none' or '60s inherited from the client library' → set one derived from the latency budget." |
| "Follow the single responsibility principle." | "**SINGLE RESPONSIBILITY**: Can you describe this class in one sentence without 'and'? If not → extract. Watch for the common pair: business logic *and* persistence." |
| "Be careful with retries." | "- [ ] **Retry Storm**: retries at client, gateway, and service layers compounding → one layer only." |

The test: **could this check fail?** If there is no state of the code that makes it fail, it is
prose. Delete it.

---

## Writing a new principle

### 1. Check nothing already owns it

Read [the catalogue](docs/catalogue.md), particularly *Frequently confused pairs*. Two skills that
fire on the same words means the agent loads both and trusts neither. If your idea overlaps an
existing skill, the contribution is probably a *section* in that skill, not a new one.

### 2. Write the description last, and carefully

The description is the only routing signal, and it sits in context for the entire session. Four
parts, in order:

1. **What it does** — imperative, leading with the trigger condition.
2. **What it covers** — the concrete concepts, because those words are what the agent matches on.
3. **When to use it** — literal phrases a user would type, in quotes.
4. **What it is *not*** — one clause naming the sibling skills that own the adjacent concerns.

Part 4 is not optional. Without it, your skill collides with an existing one.

120–1200 characters. The validator enforces the range and warns if there is no "Use when…" clause.

### 3. Use the four sections

`## Config Resolution`, `## Self-Validation Checklist`, `## Active Anti-Pattern Scan`,
`## Ambiguity Signals` — in that order, no others at `##` level. The validator enforces this.

Copy the Config Resolution block from an existing principle and change only the config key and the
step-5 stack note. Identical logic everywhere is the point.

**The checklist** is the part that runs. Numbered, imperative, one check per item, each with the
concrete fix. Order by consequence — the most expensive mistake first.

**The anti-pattern scan** names failure modes. A named anti-pattern is findable; a described one is
not. Name it, say how to spot it, give the remedy.

**The ambiguity signals** are where you say what the skill must *not* decide alone. A principle with
none is overconfident. If you cannot think of any, you have not thought hard enough about the
trade-offs — every real engineering rule has a case where it is wrong.

### 4. Put the depth in `references/defaults.md`

`SKILL.md` stays ≤ 12 KB, ideally ≲ 8 KB, because it loads in full whenever the skill fires.
Tables, worked examples, per-stack equivalents, and long explanations go in the reference file,
which loads only when Config Resolution asks for it.

### 5. Stay stack-neutral

Name **patterns**, never libraries, in the checklist. `.msskills/stack.md` is what turns "circuit
breaker" into the project's actual library. A reference file may carry a per-stack translation
table; the checks the agent runs must not.

### 6. Cross-reference by bare name

"see `clean-architecture`" — never the plugin prefix, which differs between a plugin install and a
manual one. The validator checks that every `see \`name\`` resolves.

---

## Writing a new workflow

- Declare `## Required Skills` up front, each marked `(always)` or `(conditional: …)`. The
  validator requires this section.
- **Every workflow needs STOP gates.** A workflow that never pauses produces a large diff nobody
  can review, which is the failure mode this library exists to prevent.
- Do not restate a principle's content. Load it and say *when*.
- Say what the workflow writes to `.msskills/`, and what it refuses to start without.

---

## Style

Match what is there. Specifically:

- **British spelling** — behaviour, initialise, modelling.
- **Second person for the agent**, imperative for checks.
- **Concrete over abstract.** "One slow dependency exhausts the shared connection pool" beats
  "resource contention may occur".
- **No hedging in a check.** "Consider whether you might want to" is not a check.
- **Tables for anything with more than three parallel cases.**
- Say *why* a rule exists when the reason is not obvious. A rule an agent understands is applied
  better than one it merely follows — and a reviewer can tell whether it is still true.

## Authoring anti-patterns

- **Prose describing good practice.** See above.
- **Advice with no failure mode.** Every rule needs its anti-pattern.
- **Overlapping descriptions.** Two skills firing on the same words.
- **Silent judgment calls.** If the trade-off is real, it goes in Ambiguity Signals.
- **Library lock-in in the body.**
- **A workflow with no STOP gate.**
- **Restating another skill.** Point at it instead.

---

## Pull requests

1. Branch from `main`.
2. Edit `source/`.
3. `make check`.
4. Commit both `source/` and the regenerated `skills/`.
5. In the PR description, say **what behaviour changes**. "Adds a check for X" is a description;
   "an agent writing a Kafka consumer will now be told to deduplicate on message ID before
   acknowledging" is a claim someone can evaluate.

### Reviewing your own work first

Ask of every check you added:

- Could it fail? On what code?
- Does it say what to do when it fails?
- Would a competent engineer disagree with it? If so, it belongs in Ambiguity Signals instead.
- Does it duplicate something another skill already checks?

## Reporting a problem

- **The agent ignored a skill** → most likely a description that does not match the trigger. Include
  what you typed and what you expected. This is the most valuable bug report there is.
- **A check is wrong** → say which check, and the case where it gives bad advice.
- **A gap** → open a skill request; [the catalogue](docs/catalogue.md) lists the known gaps and
  whether they are deliberate.

## Licence

Contributions are MIT, matching the repository.
