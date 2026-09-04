<!-- GENERATED — do not edit. -->

# skills/ (generated)

This directory is built from `source/` by `tools/build-skills.sh` and is what every host
manifest reads. Plugin hosts discover skills only one level deep, so the
`principles/`, `workflows/`, and `profiles/` tiers are flattened here.

Edit `source/`, then run `./tools/build-skills.sh`. CI fails on any drift.
