# Configuration and Dependencies — defaults

Loaded by Config Resolution when a project has no override, or as the base layer under an overlay.

---

## 1. What is configuration

Configuration is **everything that varies between deployments of the same artefact**. Nothing else.

| Kind | Example | Where it belongs |
|---|---|---|
| Environment config | Database URL, broker address, downstream base URLs, log level | Environment / config store |
| Tunable | Timeouts, pool sizes, retry limits, page-size caps | Config, with safe defaults |
| Credential | Passwords, API keys, signing keys | Secret manager only (see `secure-service`) |
| Feature flag | Temporary rollout switch | Flag system, with an owner and an expiry |
| Business constant | VAT rate, approval threshold | Config *if* it changes per market; otherwise code |
| Structural constant | Enum values, state machine transitions | Code — reviewed, typed, tested |

The test that settles most arguments: **would you deploy the same artefact to staging and
production?** If yes, everything that differs is configuration. If no, something environment-shaped
has been baked into the build.

## 2. Rules

**One artefact, many environments.** The container that passed testing is the container that runs
in production. Rebuilding per environment means the thing you tested is not the thing you shipped.

**Validate at startup, and fail.** Read and parse everything at boot: required values present,
types correct, ranges sane, URLs parseable, enums recognised. A misconfigured instance must fail to
start — a service that starts and then fails on the first request has already taken traffic and, if
the readiness probe passed, taken it from a healthy instance.

Report **all** validation failures at once, not the first:

```
Configuration errors:
  DATABASE_URL       required, not set
  HTTP_TIMEOUT_MS    expected integer, got "3s"
  MAX_PAGE_SIZE      1000 exceeds the maximum of 500
```

**Type it once at the edge.** Parse into a typed configuration object in the composition root, then
inject typed values. `Duration httpTimeout`, not `System.getenv("HTTP_TIMEOUT_MS")` in a handler.
Domain code should have no idea an environment exists.

**No environment branching.** `if (env == "production")` means the production path is the one your
tests never take. Express the difference as a value.

**Document every setting** in one place, generated from the typed config object where the language
allows:

| Name | Type | Required | Default | Effect |
|---|---|---|---|---|
| `HTTP_TIMEOUT_MS` | integer | no | 2000 | Per-request timeout for outbound calls |

**Safe defaults.** A default should let a developer run the service locally and should fail closed
for anything touching money, permissions, or data retention. `DEBUG_ENDPOINTS_ENABLED` defaults to
false; nobody should have to remember to turn it off.

## 3. Environment parity and drift

Drift is what makes "it works in staging" a useless statement.

- **Same shape everywhere**: the same settings exist in every environment, differing only in value.
  A setting that exists only in production is untested by definition.
- **Declare environments as code**, reviewed like any other change.
- **Detect drift**: compare the running configuration against the declared one and alert on
  difference. Manual changes made during an incident are the most common source, and the least
  likely to be reverted.
- **Expose the effective configuration** (with secrets redacted) on an authenticated endpoint, so
  "what is this instance actually running with?" is answerable in seconds.
- **Log the resolved configuration once at startup**, redacted. It is the cheapest incident
  artefact there is.

## 4. Feature flags

Flags are branches in production. They are worth it for release control, and they cost complexity
every day they exist.

- **Every flag has an owner and a removal condition** recorded when it is created. Without both,
  it is permanent.
- **Default off.** Absence of the flag, or a failure to reach the flag service, must yield the
  current behaviour. A flag system outage should be invisible.
- **Flags are temporary; settings are permanent.** A switch you intend to keep is configuration —
  model it as such and stop calling it a flag.
- **One flag, one decision.** Flags that combine into a state space nobody has tested are how
  unreproducible bugs happen.
- **Test both branches.** A flag whose "on" path never runs in CI will fail the day you enable it.
- **Remove flag and dead branch together**, promptly. The clean-up is part of the feature, not a
  follow-up ticket.
- **Audit changes**: who flipped what, when. During an incident, that is the first question.

Runtime-changeable configuration follows the same discipline: stage the rollout, keep the blast
radius small, log every change, and make reverting instant.

## 5. Choosing a dependency

Before adding one, answer four questions:

1. **Is it in the standard library or something already present?** A date library on top of a
   perfectly good built-in one is pure cost.
2. **What does it pull in?** Check the transitive tree. One convenience function that adds forty
   packages adds forty packages' worth of advisories and updates.
3. **Is it alive?** Recent releases, responsive maintainers, security fixes shipped. An abandoned
   dependency on a critical path is a future migration under time pressure.
4. **How hard is it to remove?** A library used in three places behind a port is replaceable. One
   whose types are woven through the domain is not (see `clean-architecture`).

Prefer: the standard library; one well-maintained dependency over three small ones; libraries with
narrow, stable APIs. Avoid: a package for a single one-line function; anything requiring a
post-install script; frameworks that want to own the application's structure when a library would do.

## 6. Versions, locks, and updates

- **Pin exact versions and commit the lockfile.** A range means the build is not reproducible and a
  compromised or broken release lands automatically. This applies to base images too — reference by
  digest, not by a mutable tag.
- **Semantic versioning is a promise, not a guarantee.** A patch release can and does break things.
  Pinning is what makes that a decision rather than an event.
- **Automate the update *proposals*, not the merges** for anything but patches: grouped pull
  requests, one per ecosystem, with the changelog attached. Small, frequent updates are far cheaper
  than an annual catch-up.
- **Security advisories jump the queue** and are evaluated on reachability — an advisory in a code
  path you never execute is not the same emergency as one in your request handler.
- **Major upgrades get a real read** of the migration notes. "Tests pass" only proves the tested
  behaviour still works.
- **Deduplicate.** Three HTTP clients, two JSON libraries, and two date libraries in one service is
  a maintenance surface nobody chose.
- **Prune.** Remove unused dependencies as deliberately as you add them.

## 7. Internal shared libraries

The most common way a microservice estate becomes a distributed monolith.

**Reasonable to share:** tracing and logging setup, the auth client, the resilience configuration
defaults, generated API and event clients, build tooling.

**Not reasonable to share:** domain models, business rules, database entities, anything encoding a
process. When ten services depend on `common-domain`, changing a rule means eleven coordinated
releases — the deployment coupling microservices were adopted to escape.

Where sharing is right:

- **Version it independently** and let consumers upgrade on their own schedule. A shared library
  every service must be on the latest version of is not a library; it is a deployment dependency.
- **Keep it backward compatible** for a full deprecation cycle (see `api-contracts`).
- **Keep it small and stable.** A shared library that changes weekly is a coordination tax.
- **Prefer generated clients from a contract** to a hand-written shared client — the contract stays
  the source of truth, and each consumer generates what it needs.
- **Duplication is often the cheaper answer.** Two services with a similar fifty-line mapper are
  fine. Two services that must release together are not.
