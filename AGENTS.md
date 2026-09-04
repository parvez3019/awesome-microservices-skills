# Awesome Microservices Skills — Cursor / Codex / other agents

**Read and follow [PROJECT.md](PROJECT.md) before changing anything in this repository.**

`PROJECT.md` is the single source of truth for this repo's conventions: the tier model, the fixed
`SKILL.md` shape, the frontmatter budget, the `source/` → `skills/` build rule, and the authoring
anti-patterns. Do not assume conventions from memory if they conflict with that file.

Two rules worth repeating here because getting them wrong breaks the build:

1. **Never hand-edit `skills/`.** It is generated. Edit `source/`, then run `./tools/build-skills.sh`.
2. **Run `./tools/validate-skills.sh` before committing.** CI runs it, and it is the only thing
   standing between a typo in frontmatter and a skill that silently never loads.
