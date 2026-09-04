#!/usr/bin/env bash
# Quality gate for the skill library. See tools/validate_skills.py for the checks.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

if ! command -v python3 >/dev/null 2>&1; then
  echo "error: python3 is required to run the skill validator" >&2
  exit 1
fi

exec python3 "$ROOT/tools/validate_skills.py" "$@"
