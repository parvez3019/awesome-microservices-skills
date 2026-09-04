#!/usr/bin/env bash
# Copy the flat skill set into any agent's skills directory.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SOURCE_DIR="$ROOT/source"

usage() {
  cat <<'EOF'
Usage: ./tools/install.sh <target-skills-dir>

Copies every skill into <target-skills-dir>, flattening the principles/workflows/profiles
structure so your AI tool can discover them. Existing skills of the same name are replaced.

Common targets:
  Claude Code (all projects)  ~/.claude/skills
  Claude Code (one project)   /path/to/your-service/.claude/skills
  Cursor (one project)        /path/to/your-service/.cursor/skills
  Anything else               /absolute/path/to/that/tool/skills

Examples:
  ./tools/install.sh ~/.claude/skills
  ./tools/install.sh ~/work/orders-service/.cursor/skills
EOF
  exit 1
}

[ $# -ge 1 ] || usage

DEST="$1"
mkdir -p "$DEST"
DEST="$(cd "$DEST" && pwd)"

if [ "$DEST" = "$ROOT" ] || [ "$DEST" = "$SOURCE_DIR" ]; then
  echo "error: refusing to install into the repository's own source tree" >&2
  exit 1
fi

added=0
updated=0

for tier in principles workflows profiles; do
  tier_dir="$SOURCE_DIR/$tier"
  [ -d "$tier_dir" ] || continue

  for skill_dir in "$tier_dir"/*/; do
    [ -d "$skill_dir" ] || continue
    name="$(basename "$skill_dir")"

    if [ -e "$DEST/$name" ]; then
      echo "  update  $name"
      rm -rf "${DEST:?}/$name"
      updated=$((updated + 1))
    else
      echo "  add     $name"
      added=$((added + 1))
    fi

    cp -R "$skill_dir" "$DEST/$name"
  done
done

echo
echo "Installed $((added + updated)) skills into $DEST ($added added, $updated updated)."
