---
name: config-and-dependencies
description: "Keep a service's configuration and its dependency graph under control. Covers configuration as environment rather than code, separating config from secrets, fail-fast validation of typed config at startup, feature flags and blast radius, environment parity and drift, plus dependency selection, semantic versioning, lockfiles, transitive bloat, automated updates, and internal shared libraries. Use when adding or changing a setting, wiring an environment, introducing a feature flag, adding or upgrading a library, or when the user says 'config', 'environment variable', 'feature flag', 'dependency', 'upgrade', 'lockfile', or 'shared library'. This skill governs what varies per deployment and what the service is built from — secret storage rules belong to secure-service."
license: MIT
---

# Configuration and Dependencies

Two quiet sources of production incidents share a chapter because they share a cause: things that
differ between environments, and things that change without anyone deciding.

A service that reads a setting halfway through a request and finds it missing has already accepted
traffic it cannot serve. A service that resolves a floating version range at build time is running
code nobody reviewed. Both are preventable at startup, by a build, or by a check — never by
vigilance.

## Config Resolution

1. Read `.msskills/config.yaml` in the repo root; look up `paths.config`.
2. A custom document exists at that path → read its frontmatter `mode`:
   - `override` → use it alone; ignore the defaults below.
   - `overlay` (default, or no `mode` key) → read [defaults](./references/defaults.md) first, then
     apply the custom document's sections on top, matched by exact heading; new sections append.
3. A path is configured but no file exists there → say which path is missing, then use the defaults.
4. No config file or no `paths.config` key → use [defaults](./references/defaults.md).
5. `.msskills/stack.md` exists → use its package manager, lockfile format, configuration mechanism,
   secret manager, and flag system.

## Self-Validation Checklist

**STOP after adding or changing a setting, a flag, or a dependency. Verify every check. Fix
failures before presenting.**

1. **VARIES PER DEPLOYMENT**: Does this value actually differ between environments? If it is the
   same everywhere → it is a constant; put it in code where it can be reviewed and typed.
2. **NOT A SECRET**: Is this a credential, key, or token? → secret manager, never config (see
   `secure-service`).
3. **VALIDATED AT STARTUP**: Is the value parsed, typed, range-checked, and required at boot, so a
   misconfigured instance fails to start rather than failing mid-request?
4. **TYPED AT THE EDGE**: Is it converted into a typed object once at the boundary, or read as a
   raw string deep in business logic? Domain code must never read the environment.
5. **NO ENVIRONMENT BRANCHING**: Does any code test `if (env == "production")`? → express the
   difference as a setting, not as a branch. Branches make production the least-tested path.
6. **DOCUMENTED**: Is every setting listed with its type, whether it is required, its default, and
   what it affects? An undocumented setting is discovered during an incident.
7. **SAFE DEFAULT**: Does the default work for local development and fail closed for anything
   security- or cost-relevant?
8. **FLAG HAS AN END**: Does every new feature flag have an owner and a removal condition? A flag
   with neither becomes permanent branching.
9. **FLAG DEFAULTS OFF**: Does the flag's absence or its lookup failure produce the current
   behaviour, not the new one?
10. **DEPENDENCY JUSTIFIED**: For a new library — does the standard library or an existing
    dependency already do this? What does it pull in transitively? Is it maintained?
11. **PINNED AND LOCKED**: Is the version exact, with a committed lockfile, so the build is
    reproducible?
12. **UPGRADE PATH**: For a major upgrade, are the breaking changes read and the affected code
    identified — not just "tests pass"?
13. **SHARED LIBRARY DISCIPLINE**: For an internal shared library — does it contain only stable,
    genuinely common code, with no business logic that ties services together? (see
    `service-boundaries`)

All checks pass → state "Config holds: validated at startup, no secrets, documented."

## Active Anti-Pattern Scan

Any box you can check is a defect. Fix it before presenting.

- [ ] **Config in the Image**: environment-specific values baked into the artefact, so promoting a
      build means rebuilding it → externalise; one artefact, many environments.
- [ ] **Environment Branching**: `if (isProd)` in application code → make it a setting.
- [ ] **Late Failure**: a missing or malformed setting discovered on first use rather than at
      startup → validate everything at boot.
- [ ] **Stringly-Typed Config**: raw strings read and parsed at each call site → parse once into a
      typed object.
- [ ] **Config Read in the Domain**: business logic reaching for the environment → inject the
      typed value (see `clean-architecture`).
- [ ] **Secret in Config**: credentials in a config file, chart, or environment listing checked into
      the repository → secret manager, and rotate what leaked.
- [ ] **Undocumented Setting**: a value only discoverable by grepping → document it.
- [ ] **Zombie Flag**: a flag on for everyone for months, both branches still present → remove the
      flag and the dead branch.
- [ ] **Flag as Config**: a permanent behaviour switch modelled as a feature flag → make it a
      setting; flags are temporary by definition.
- [ ] **Dynamic Config Without Blast Radius Control**: a value changeable at runtime for the whole
      fleet at once, with no staged rollout or audit trail → stage it and log who changed what.
- [ ] **Floating Version**: a range or `latest` in a manifest, or a missing lockfile → pin and lock.
- [ ] **Mutable Tag**: a container base image referenced by tag rather than digest → pin the digest.
- [ ] **Dependency for a One-Liner**: a package pulling a transitive tree to do what ten lines of
      standard library would → write the ten lines.
- [ ] **Abandoned Dependency**: no release or security fix in years, on a critical path → plan a
      replacement now, not during the advisory.
- [ ] **Shared Business Library**: domain logic in a library several services depend on → they now
      release in lockstep; that is a distributed monolith.

## Ambiguity Signals

Route these through `collaborative-judgment`. Each has two defensible answers.

- **Environment variables or a configuration service.** Variables are simple, auditable, and
  require a restart to change. A config service allows runtime change and adds a runtime dependency
  and a new failure mode.
- **Which settings may change at runtime.** Timeouts and thresholds benefit from being tunable
  during an incident; the ability to change behaviour without a deploy is also the ability to break
  production without a review.
- **Flag granularity.** Per-user targeting enables gradual rollout and makes behaviour hard to
  reproduce; a global boolean is predictable and blunt.
- **How aggressively to auto-merge dependency updates.** Automatic patch updates keep you current
  and occasionally ship someone else's regression; manual review is safer and, in practice, means
  falling behind.
- **Vendoring versus depending.** Copying a small utility removes a supply-chain risk and forfeits
  upstream fixes.
- **Whether a shared library is worth it.** Duplication across services is often cheaper than the
  coupling a shared library creates — but not for cross-cutting concerns like tracing or auth
  clients, where consistency matters more.
