#!/usr/bin/env python3
"""Quality gate for the skill library.

Checks every skill under source/ for the conventions in PROJECT.md, then checks that the
committed build output and the five host manifests agree. Exits non-zero on any error.

No third-party dependencies: the frontmatter this repo allows is a small, fixed subset of
YAML, so it is parsed here directly rather than pulling in PyYAML.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SOURCE = REPO / "source"
BUILD = REPO / "skills"

TIERS = ("principles", "workflows", "profiles")

# The portable subset shared by Claude Code, Cursor, claude.ai uploads and the Skills API.
ALLOWED_KEYS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
REQUIRED_KEYS = {"name", "description", "license"}

DESCRIPTION_MIN = 120
DESCRIPTION_MAX = 1200
SKILL_MAX_BYTES = 12 * 1024

PRINCIPLE_SECTIONS = [
    "## Config Resolution",
    "## Self-Validation Checklist",
    "## Active Anti-Pattern Scan",
    "## Ambiguity Signals",
]

NAME_RE = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")
SEE_REF_RE = re.compile(r"see ((?:`[a-z][a-z0-9-]*`(?:,\s*(?:and\s*)?)?)+)")
BACKTICKED_RE = re.compile(r"`([a-z][a-z0-9-]*)`")
USE_WHEN_RE = re.compile(r"\bUse (when|before|after|during|while|on|for)\b", re.I)
REQUIRED_SKILL_RE = re.compile(r"^\s*(?:[-*]|\d+\.)\s+`([a-z][a-z0-9-]*)`")
LINK_RE = re.compile(r"]\((\./[^)#\s]+)\)")

MANIFESTS = (
    ".claude-plugin/plugin.json",
    ".claude-plugin/marketplace.json",
    ".cursor-plugin/plugin.json",
    ".cursor-plugin/marketplace.json",
    ".codex-plugin/plugin.json",
    ".agents/plugins/marketplace.json",
    "plugin.json",
)

errors: list[str] = []
warnings: list[str] = []


def error(where: str, msg: str) -> None:
    errors.append(f"{where}: {msg}")


def warn(where: str, msg: str) -> None:
    warnings.append(f"{where}: {msg}")


def parse_frontmatter(text: str, where: str) -> dict[str, str] | None:
    """Parse the leading YAML frontmatter block.

    Supports the shapes this repo allows: `key: value`, a quoted scalar that may wrap across
    several indented lines, and a block scalar introduced with `>` or `|`.
    """
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        error(where, "frontmatter must open with `---` on line 1")
        return None

    try:
        close = next(i for i, line in enumerate(lines[1:], start=1) if line.strip() == "---")
    except StopIteration:
        error(where, "frontmatter is never closed by a second `---`")
        return None

    body = lines[1:close]
    fields: dict[str, str] = {}
    key: str | None = None
    buf: list[str] = []

    def flush() -> None:
        if key is not None:
            fields[key] = " ".join(part.strip() for part in buf if part.strip())

    for line in body:
        if not line.strip():
            continue
        match = re.match(r"^([A-Za-z][A-Za-z0-9_-]*):\s*(.*)$", line)
        if match and not line.startswith((" ", "\t")):
            flush()
            key, first = match.group(1), match.group(2)
            buf = [] if first in (">", "|", ">-", "|-", "") else [first]
        elif key is not None:
            buf.append(line)
        else:
            error(where, f"cannot parse frontmatter line: {line!r}")
            return None
    flush()

    return {k: v.strip().strip('"').strip("'").strip() for k, v in fields.items()}


def collect_skills() -> dict[str, tuple[str, Path]]:
    """Map skill name -> (tier, directory). Reports duplicates across tiers."""
    found: dict[str, tuple[str, Path]] = {}
    for tier in TIERS:
        tier_dir = SOURCE / tier
        if not tier_dir.is_dir():
            continue
        for skill_dir in sorted(p for p in tier_dir.iterdir() if p.is_dir()):
            name = skill_dir.name
            if name in found:
                other_tier = found[name][0]
                error(f"source/{tier}/{name}", f"duplicate skill name, already defined in {other_tier}/")
                continue
            found[name] = (tier, skill_dir)
    return found


def check_skill(name: str, tier: str, skill_dir: Path, known: set[str]) -> None:
    where = f"source/{tier}/{name}"
    skill_md = skill_dir / "SKILL.md"

    if not skill_md.is_file():
        error(where, "missing SKILL.md")
        return

    raw = skill_md.read_bytes()
    if len(raw) > SKILL_MAX_BYTES:
        error(where, f"SKILL.md is {len(raw)} bytes, over the {SKILL_MAX_BYTES}-byte limit — move depth into references/")

    text = raw.decode("utf-8")
    fm = parse_frontmatter(text, where)
    if fm is None:
        return

    unexpected = set(fm) - ALLOWED_KEYS
    if unexpected:
        error(where, f"frontmatter keys outside the portable subset: {', '.join(sorted(unexpected))}")

    missing = REQUIRED_KEYS - set(fm)
    if missing:
        error(where, f"frontmatter missing required key(s): {', '.join(sorted(missing))}")

    if fm.get("name") and fm["name"] != name:
        error(where, f"frontmatter name {fm['name']!r} does not match directory name {name!r}")
    if not NAME_RE.match(name):
        error(where, f"skill directory name {name!r} is not kebab-case")

    desc = fm.get("description", "")
    if desc:
        if len(desc) < DESCRIPTION_MIN:
            error(where, f"description is {len(desc)} chars, under the {DESCRIPTION_MIN}-char minimum — say what it covers and when to use it")
        if len(desc) > DESCRIPTION_MAX:
            error(where, f"description is {len(desc)} chars, over the {DESCRIPTION_MAX}-char maximum")
        if not USE_WHEN_RE.search(desc):
            warn(where, "description has no 'Use when/before/after ...' clause; the agent needs trigger phrases to route on")

    if fm.get("license") and fm["license"] != "MIT":
        error(where, f"license is {fm['license']!r}, expected 'MIT' to match the repository")

    body = text.split("\n---", 1)[-1]

    if tier == "principles":
        present = [s for s in PRINCIPLE_SECTIONS if re.search(rf"^{re.escape(s)}\s*$", body, re.M)]
        if present != PRINCIPLE_SECTIONS:
            missing_sections = [s for s in PRINCIPLE_SECTIONS if s not in present]
            if missing_sections:
                error(where, f"principle is missing required section(s): {', '.join(missing_sections)}")
            else:
                error(where, "principle sections are present but out of order; see PROJECT.md §5")
        else:
            positions = [body.index(s) for s in PRINCIPLE_SECTIONS]
            if positions != sorted(positions):
                error(where, "principle sections are out of order; see PROJECT.md §5")

    if tier == "workflows" and not re.search(r"^## Required Skills\s*$", body, re.M):
        error(where, "workflow is missing its `## Required Skills` section")

    # Cross-references are checked in SKILL.md and in every bundled reference/asset document,
    # so renaming a skill cannot leave a dangling pointer in the depth material either.
    referenced: set[str] = set()
    for doc in sorted(skill_dir.rglob("*.md")):
        doc_text = doc.read_text()
        for group in SEE_REF_RE.findall(doc_text):
            referenced |= set(BACKTICKED_RE.findall(group))
        for target in LINK_RE.findall(doc_text):
            if not (doc.parent / target).exists():
                rel = doc.relative_to(skill_dir)
                error(where, f"{rel} links to a file that does not exist: {target}")

    if tier == "workflows":
        section = re.split(r"^## Required Skills\s*$", body, maxsplit=1, flags=re.M)
        if len(section) > 1:
            listing = re.split(r"^## ", section[1], maxsplit=1, flags=re.M)[0]
            referenced |= {m.group(1) for line in listing.split("\n") if (m := REQUIRED_SKILL_RE.match(line))}

    for ref in sorted(referenced - known - {name}):
        error(where, f"references skill `{ref}`, which does not exist")


def check_build(known: set[str]) -> None:
    if not BUILD.is_dir():
        error("skills/", "build output is missing — run ./tools/build-skills.sh")
        return
    built = {p.name for p in BUILD.iterdir() if p.is_dir()}
    for stale in sorted(built - known):
        error("skills/", f"contains {stale!r}, which no longer exists in source/ — rerun ./tools/build-skills.sh")
    for absent in sorted(known - built):
        error("skills/", f"missing {absent!r} — rerun ./tools/build-skills.sh")


def check_manifest_versions() -> None:
    versions: dict[str, str] = {}
    for rel in MANIFESTS:
        path = REPO / rel
        if not path.is_file():
            error(rel, "manifest is missing")
            continue
        try:
            data = json.loads(path.read_text())
        except json.JSONDecodeError as exc:
            error(rel, f"invalid JSON: {exc}")
            continue
        if "version" in data:
            versions[rel] = data["version"]
        for plugin in data.get("plugins", []):
            if "version" in plugin:
                versions[f"{rel} → plugins[{plugin.get('name', '?')}]"] = plugin["version"]

    distinct = set(versions.values())
    if len(distinct) > 1:
        detail = ", ".join(f"{k}={v}" for k, v in sorted(versions.items()))
        error("manifests", f"version mismatch across manifests: {detail}")


def main() -> int:
    if not SOURCE.is_dir():
        print(f"error: {SOURCE} does not exist", file=sys.stderr)
        return 1

    skills = collect_skills()
    known = set(skills)

    for name, (tier, skill_dir) in sorted(skills.items()):
        check_skill(name, tier, skill_dir, known)

    check_build(known)
    check_manifest_versions()

    for w in warnings:
        print(f"warn:  {w}")
    for e in errors:
        print(f"ERROR: {e}", file=sys.stderr)

    counts = {tier: sum(1 for t, _ in skills.values() if t == tier) for tier in TIERS}
    summary = ", ".join(f"{counts[t]} {t}" for t in TIERS)
    print(f"\nvalidated {len(skills)} skills ({summary}); {len(errors)} error(s), {len(warnings)} warning(s)")

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
