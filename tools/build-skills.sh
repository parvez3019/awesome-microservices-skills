#!/usr/bin/env bash
# Regenerate skills/ from source/. Plugin hosts only discover skills one level deep, so the
# principles/workflows/profiles tiers are flattened here. Never hand-edit skills/.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SOURCE_DIR="$ROOT/source"
BUILD_DIR="$ROOT/skills"

[ -d "$SOURCE_DIR" ] || { echo "error: $SOURCE_DIR does not exist" >&2; exit 1; }

# Fail loudly on a name collision rather than letting one tier silently overwrite another.
duplicates="$(
  for tier in principles workflows profiles; do
    [ -d "$SOURCE_DIR/$tier" ] || continue
    find "$SOURCE_DIR/$tier" -mindepth 1 -maxdepth 1 -type d -exec basename {} \;
  done | sort | uniq -d
)"

if [ -n "$duplicates" ]; then
  echo "error: skill name(s) defined in more than one tier:" >&2
  echo "$duplicates" | sed 's/^/  /' >&2
  exit 1
fi

rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

count=0
for tier in principles workflows profiles; do
  [ -d "$SOURCE_DIR/$tier" ] || continue
  for skill_dir in "$SOURCE_DIR/$tier"/*/; do
    [ -d "$skill_dir" ] || continue
    cp -R "$skill_dir" "$BUILD_DIR/$(basename "$skill_dir")"
    count=$((count + 1))
  done
done

cat > "$BUILD_DIR/README.md" <<'EOF'
<!-- GENERATED — do not edit. -->

# skills/ (generated)

This directory is built from `source/` by `tools/build-skills.sh` and is what every host
manifest reads. Plugin hosts discover skills only one level deep, so the
`principles/`, `workflows/`, and `profiles/` tiers are flattened here.

Edit `source/`, then run `./tools/build-skills.sh`. CI fails on any drift.
EOF

echo "Built $count skills into $BUILD_DIR from $SOURCE_DIR."
echo "Shared by every host manifest: .claude-plugin/, .cursor-plugin/, and the root plugin.json."
