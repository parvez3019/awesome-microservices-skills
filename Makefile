# Awesome Microservices Skills
#
# Run `make` or `make help` for the target list.
# Everything here wraps tools/ — the scripts remain the source of truth, so CI and
# a contributor's laptop run exactly the same commands.

SHELL := /bin/bash
.DEFAULT_GOAL := help

# The seven host manifests. Their versions must agree; `make check` enforces it.
MANIFESTS := .claude-plugin/plugin.json \
             .claude-plugin/marketplace.json \
             .cursor-plugin/plugin.json \
             .cursor-plugin/marketplace.json \
             .codex-plugin/plugin.json \
             .agents/plugins/marketplace.json \
             plugin.json

# Where `make install` puts the skills. Override on the command line:
#   make install DEST=~/work/orders-service/.cursor/skills
DEST ?= $(HOME)/.claude/skills

SMOKE_DIR := $(shell mktemp -d 2>/dev/null || echo /tmp/ms-skills-smoke)

.PHONY: help build validate check drift manifests shellcheck smoke \
        install install-claude install-cursor plugin-validate \
        version list clean

## help: show this list
help:
	@echo "Awesome Microservices Skills"
	@echo
	@grep -E '^## ' $(MAKEFILE_LIST) | sed 's/^## /  make /' | column -t -s ':'
	@echo
	@echo "Variables:"
	@echo "  DEST=<dir>   target for 'make install'   (default: $(DEST))"
	@echo "  V=<x.y.z>    new version for 'make version'"

## build: regenerate skills/ from source/
build:
	@./tools/build-skills.sh

## validate: run the quality gate over every skill and manifest
validate:
	@./tools/validate-skills.sh

## drift: fail if the committed skills/ is stale
drift: build
	@if ! git diff --quiet -- skills/; then \
		echo "ERROR: skills/ is out of date. Commit the rebuild:"; \
		git diff --stat -- skills/; \
		exit 1; \
	fi
	@echo "skills/ is current."

## manifests: parse every host manifest as JSON
manifests:
	@for f in $(MANIFESTS); do \
		python3 -c "import json,sys; json.load(open(sys.argv[1]))" "$$f" || exit 1; \
		echo "ok   $$f"; \
	done

## shellcheck: syntax-check the shell and python tooling
shellcheck:
	@bash -n tools/*.sh && echo "ok   shell syntax"
	@python3 -m py_compile tools/validate_skills.py && echo "ok   python syntax"

## smoke: install into a temp dir and verify every skill arrived intact
smoke:
	@./tools/install.sh "$(SMOKE_DIR)" >/dev/null
	@missing=0; \
	for d in "$(SMOKE_DIR)"/*/; do \
		[ -f "$$d/SKILL.md" ] || { echo "ERROR: no SKILL.md in $$d"; missing=1; }; \
	done; \
	count=$$(ls -1 "$(SMOKE_DIR)" | wc -l | tr -d ' '); \
	rm -rf "$(SMOKE_DIR)"; \
	[ $$missing -eq 0 ] || exit 1; \
	echo "ok   $$count skills installed, all with SKILL.md"

## check: everything CI runs — do this before every commit
check: shellcheck drift validate manifests smoke
	@echo
	@echo "All checks passed."

## install: copy the skills into DEST (default ~/.claude/skills)
install:
	@./tools/install.sh "$(DEST)"

## install-claude: install into this repo's own .claude/skills, for dogfooding
install-claude:
	@./tools/install.sh .claude/skills

## install-cursor: install into DEST as a Cursor skills folder
install-cursor:
	@if [ "$(DEST)" = "$(HOME)/.claude/skills" ]; then \
		echo "Set DEST to the project's .cursor/skills, e.g."; \
		echo "  make install-cursor DEST=~/work/orders-service/.cursor/skills"; \
		exit 1; \
	fi
	@./tools/install.sh "$(DEST)"

## plugin-validate: ask the real Claude Code loader to validate the manifests
plugin-validate:
	@command -v claude >/dev/null 2>&1 || { \
		echo "claude CLI not found — skipping. Install Claude Code to run this."; exit 1; }
	@claude plugin validate .

## version: bump the version across all seven manifests (make version V=0.2.0)
version:
	@if [ -z "$(V)" ]; then echo "Usage: make version V=0.2.0"; exit 1; fi
	@echo "$(V)" | grep -Eq '^[0-9]+\.[0-9]+\.[0-9]+$$' || { \
		echo "ERROR: '$(V)' is not a semantic version"; exit 1; }
	@for f in $(MANIFESTS); do \
		perl -pi -e 's/"version"(\s*):(\s*)"[^"]*"/"version"$$1:$$2"$(V)"/g' "$$f"; \
		echo "bumped  $$f"; \
	done
	@$(MAKE) --no-print-directory validate
	@echo
	@echo "Now update CHANGELOG.md, then:"
	@echo "  git commit -am 'release: v$(V)' && git tag -a v$(V) -m 'v$(V)' && git push origin main --tags"

## list: show every skill by tier
list:
	@for tier in principles workflows profiles; do \
		echo "$$tier:"; \
		find "source/$$tier" -mindepth 1 -maxdepth 1 -type d 2>/dev/null \
			| sort | sed 's|.*/|  |'; \
	done
	@echo
	@echo "total: $$(find source -name SKILL.md | wc -l | tr -d ' ') skills"

## clean: remove the generated skills/ directory
clean:
	@rm -rf skills
	@echo "Removed skills/. Run 'make build' to regenerate it."
