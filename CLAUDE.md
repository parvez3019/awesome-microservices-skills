# Awesome Microservices Skills — Claude Code

**Read and follow [PROJECT.md](PROJECT.md) before changing anything in this repository.**

Every convention that governs this repo — the tier model, the fixed `SKILL.md` shape, the
frontmatter budget, the `source/` → `skills/` build rule, and the anti-patterns to avoid when
authoring a skill — lives in `PROJECT.md`. This file exists only so Claude Code loads that context
from the repo root.

Two rules worth repeating here because getting them wrong breaks the build:

1. **Never hand-edit `skills/`.** It is generated. Edit `source/`, then run `./tools/build-skills.sh`.
2. **Run `./tools/validate-skills.sh` before committing.** CI runs it, and it is the only thing
   standing between a typo in frontmatter and a skill that silently never loads.
