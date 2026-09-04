# Publishing

How to release this plugin so people can install it, on Claude Code and Cursor. Maintainer-facing.

---

## 0. The one thing to understand first

**A marketplace is just a Git repository with a `marketplace.json` in it.** There is no upload, no
review queue, and no registry account for the basic path. When someone runs
`/plugin marketplace add parvez3019/awesome-microservices-skills`, their client clones this
repository and reads `.claude-plugin/marketplace.json`.

That means **pushing to `main` publishes**. Everything below is about making that safe and
discoverable.

---

## 1. Pre-flight

Run these before every release:

```bash
./tools/build-skills.sh          # regenerate skills/ from source/
./tools/validate-skills.sh       # frontmatter, budgets, cross-refs, manifest versions
git diff --exit-code skills/     # must be clean — CI enforces this too
claude plugin validate .         # the real loader's opinion on your manifests
```

`claude plugin validate .` is the important one. It parses the manifests the way the client will,
and it catches schema mistakes that a JSON linter will not.

Then a real install test, from a **different directory** so you are not testing the working tree:

```bash
cd /tmp && mkdir plugin-test && cd plugin-test
claude plugin marketplace add ~/repos/awesome-microservices-skills
claude plugin install microservices-skills@awesome-microservices-skills --yes
```

Open a session there and check: the skills appear in `/` autocomplete under
`/microservices-skills:…`, `/stack-profile` runs, and a principle fires on relevant work without
being invoked.

---

## 2. Claude Code

### 2.1 What is already in place

| File | Purpose |
|---|---|
| `.claude-plugin/marketplace.json` | The marketplace registry — name, owner, and the plugin list |
| `.claude-plugin/plugin.json` | The plugin manifest — name, version, description, keywords |
| `skills/` | Auto-discovered; no need to list skills in the manifest |
| `agents/` | Auto-discovered |

`source: "./"` in the marketplace entry means "the plugin is this repository's root". That is why
one repository serves as both marketplace and plugin.

### 2.2 Release

```bash
# 1. Bump the version in ALL FIVE manifests — the validator fails if they disagree
#    .claude-plugin/plugin.json, .claude-plugin/marketplace.json,
#    .cursor-plugin/plugin.json, .cursor-plugin/marketplace.json, plugin.json

# 2. Update CHANGELOG.md

./tools/build-skills.sh && ./tools/validate-skills.sh && claude plugin validate .

git commit -am "release: v0.2.0"
git tag -a v0.2.0 -m "v0.2.0"
git push origin main --tags
gh release create v0.2.0 --notes-file <(sed -n '/## 0.2.0/,/## 0.1/p' CHANGELOG.md)
```

Existing installs pick the new version up on `/plugin marketplace update` — or automatically,
depending on the user's settings. Users are **not** pinned to a tag by default; they track the
default branch. So `main` must always be releasable.

### 2.3 Getting listed publicly

Repository-based install works immediately with no listing. To be *discoverable*:

- **[anthropics/claude-plugins-official](https://github.com/anthropics/claude-plugins-official)** —
  Anthropic's curated directory. Open a PR adding an entry. It is curated, so expect a quality bar
  and a wait. Highest-value listing by far.
- **Community aggregators** — sites like claudemarketplaces.com index public marketplace
  repositories. Some crawl GitHub automatically; others take a submission.
- **GitHub discoverability** — add the topics `claude-code`, `claude-plugin`, `agent-skills`,
  `microservices`, `ai-agents` to the repository. This is how most people actually find these.

### 2.4 Things that will bite you

- **Renaming the plugin breaks every existing install.** If you must, add a `renames` map to
  `marketplace.json` so clients auto-migrate on their next sync.
- **`main` is production.** There is no staging. Work on branches; merge only what is releasable.
- **Version drift across the five manifests** is the most common release mistake here — which is
  exactly why `validate-skills.sh` checks it.
- **A skill with malformed frontmatter silently never loads.** No error, it just is not there. Run
  the validator.

---

## 3. Cursor

Cursor supports the vendor-neutral **[Agent Plugins](https://agentskills.io)** specification, so
there are three routes, in increasing order of effort:

**Route 1 — nothing to do.** Cursor reads Claude Code skills from `.claude/skills/`. A user who
runs `./tools/install.sh /path/to/project/.cursor/skills` (or `.claude/skills`) has them.

**Route 2 — the root `plugin.json`.** Already committed, with the
`https://agent-plugins.org/schemas/1.0.0/plugin.schema.json` schema. A conformant client
auto-discovers the skills from a repository link with no extra steps. This is the route to point
Cursor users at.

**Route 3 — the Cursor marketplace.** Submit to
[cursor/plugins](https://github.com/cursor/plugins) — Cursor's plugin specification and official
plugin directory. Check that repository's `CONTRIBUTING` for the current submission process; it
has changed more than once. Listing gets you into Cursor's in-app Customize page.

`.cursor-plugin/` mirrors the Claude manifests for hosts that look there. It points at the same
`skills/` folder — no content is duplicated.

**Verify in Cursor:** install into a test project's `.cursor/skills/`, open the project, and check
the skills appear in the agent's skill list. Cursor does not support subagents, so
`agents/microservice-reviewer.md` is ignored there — `/review-service` degrades to a single-pass
review, which is why that workflow describes the independent pass as an addition rather than a
requirement.

---

## 4. Versioning policy

Semantic versioning, interpreted for a skill library:

| Change | Bump |
|---|---|
| Fixing a typo, sharpening a check, adding an anti-pattern | Patch |
| Adding a skill; adding a section to a reference | Minor |
| Renaming or removing a skill; changing a `config.yaml` key; changing the `.msskills/` layout | **Major** |

The major cases all break someone's existing `config.yaml` or their muscle memory for a slash
command. Treat a skill name as a published contract — which is, pleasingly, exactly what
`api-contracts` says about everything else.

---

## 5. Release checklist

```
[ ] source/ edited (never skills/ directly)
[ ] ./tools/build-skills.sh
[ ] ./tools/validate-skills.sh — 0 errors, 0 warnings
[ ] git diff --exit-code skills/ — clean
[ ] claude plugin validate . — passes
[ ] version identical in all 5 manifests
[ ] CHANGELOG.md updated
[ ] README catalogue matches the actual skill list
[ ] fresh install tested from a clean directory
[ ] at least one skill exercised end to end in that install
[ ] tag pushed, GitHub release created
```
