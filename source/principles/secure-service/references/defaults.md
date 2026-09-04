# Secure Service — defaults

Loaded by Config Resolution when a project has no override, or as the base layer under an overlay.

Anchors: the OWASP API Security Top 10 (2023) for the risk list, and the OWASP Application Security
Verification Standard for the verification depth. The Top 10 is an awareness floor, not a
compliance target — ASVS is where a team goes when it wants a real bar.

---

## 1. The API Security Top 10, as checks

| Risk | The check that prevents it |
|---|---|
| **API1 — Broken object-level authorisation** | Every query filtered by the caller's identity. Never `findById(requestId)` without an ownership predicate |
| **API2 — Broken authentication** | Verify signature, issuer, audience, expiry, algorithm. No `alg: none`. Short-lived tokens |
| **API3 — Broken object property-level authorisation** | Explicit response field allowlists; explicit request binding allowlists |
| **API4 — Unrestricted resource consumption** | Page-size caps, payload-size limits, query depth and complexity limits, timeouts, rate limits |
| **API5 — Broken function-level authorisation** | Server-side permission check per operation; deny by default; admin routes never distinguished only by path |
| **API6 — Unrestricted access to sensitive business flows** | Identify the flows worth automating and add friction: per-identity limits, device signals, anomaly detection |
| **API7 — Server-side request forgery** | Allowlist outbound destinations; never fetch a user-supplied URL; block link-local and private ranges |
| **API8 — Security misconfiguration** | Secure defaults, TLS everywhere, no debug endpoints in production, restrictive CORS, security headers |
| **API9 — Improper inventory management** | Every endpoint and every environment catalogued; old versions retired, not merely undocumented |
| **API10 — Unsafe consumption of third-party APIs** | Validate and bound what upstreams return; do not trust a partner's response more than a user's input |

**API1 and API5 deserve disproportionate attention.** They cannot be found by a scanner and are the
most common cause of real breaches. The structural fix is to make the safe path the only convenient
path: a repository whose methods *require* a caller identity, so an unscoped query does not compile.

## 2. Authentication and authorisation

**End-user identity** arrives as a token, verified on every request. Verify: signature against the
current key set (rotated, fetched from JWKS, cached with a bounded TTL), `iss`, `aud`, `exp`,
`nbf`, and the algorithm against an allowlist.

**Service identity** is separate and must not be borrowed from the end user's token.

| Mechanism | Gains | Costs |
|---|---|---|
| **mTLS** (mesh or manual) | Strong, automatic, rotated by the platform | Certificate infrastructure |
| **Workload identity** (SPIFFE/SVID, cloud IAM) | Short-lived, attested, no shared secret | Platform dependency |
| **Signed service tokens** | Simple, portable | Key distribution and rotation are yours |
| **Static shared API keys** | Trivial | Never rotated, widely copied, found in logs — avoid |

**Propagating the user through a call chain:** either pass the original token (simple, but every
hop gets full user authority) or exchange it for a narrowed, audience-scoped token per hop (least
privilege, more machinery). Pick deliberately — and never let a downstream service infer the user
from an unauthenticated header.

**Authorise in the service that owns the data.** A gateway can authenticate and do coarse routing
checks; it cannot know whether this user owns that order. Assume every service is directly
reachable, because eventually one will be.

## 3. Input, injection, and output

**Validate at the boundary, on an allowlist**: type, format, length, range, enum membership,
required fields. Reject rather than sanitise — sanitising guesses at intent.

- **Parameterised queries always.** Includes NoSQL: a query document built from user input can
  smuggle operators just as SQL can.
- **Never concatenate into a shell.** Use argument arrays; avoid the shell entirely where possible.
- **Deserialisation is code execution** unless the type is constrained. Never deserialise
  polymorphic types from untrusted input.
- **Path traversal:** canonicalise, then verify the result is inside the permitted root. Never
  concatenate a user string into a path.
- **Templates:** auto-escaping on, contextual by output type.
- **Bind with an allowlist.** Mass assignment is how `role: "admin"` gets set.

**Output** is the mirror of input:

- Return only fields this caller may see. Filter server-side, per caller, not in the client.
- Errors: a generic message plus a stable code plus a trace ID (see `api-contracts`). Never a stack
  trace, SQL, internal hostname, or library version.
- Set `Content-Type` explicitly; never let it be sniffed.

## 4. Secrets

- **Never in the repository.** Not in code, config, tests, fixtures, Dockerfiles, or CI YAML. Run
  a secret scanner in CI and as a pre-commit hook.
- **A committed secret is a compromised secret.** Rotate it; removing the commit does not help,
  because clones, forks, and mirrors exist.
- **Inject at runtime** from a secret manager or the platform's secret mechanism. Prefer a
  short-lived credential brokered by workload identity to any stored secret at all.
- **Rotate on a schedule and on departure.** Rotation that has never been exercised does not work;
  test it.
- **Keep them out of process listings, crash dumps, and error reports.** Wrap secrets in a type
  whose `toString` redacts.
- **Scope narrowly.** One credential per service per purpose, with least privilege. A shared
  "application" database user with full rights makes every incident total.

## 5. Personal data

Classify first — you cannot protect what nobody has labelled. Record categories in
`.msskills/data-classification.md`:

| Class | Examples | Handling |
|---|---|---|
| **Public** | Product catalogue | No restriction |
| **Internal** | Aggregate metrics | Authenticated access |
| **Personal** | Name, email, address, IP | Encrypt in transit and at rest; never in logs; retention limit; erasable |
| **Sensitive personal** | Health, biometric, financial, government ID | Field-level encryption; strict access control; audit every access |
| **Secret** | Credentials, keys | Secret manager only; never logged; rotate |

Practices: collect only what is used; set a retention period per category and enforce it with a job,
not a policy document; redact at the logging and tracing boundary so nothing depends on every call
site remembering; make deletion actually reach backups, caches, search indexes, and analytics —
design the erasure path when the data is introduced, not when the first request arrives.

## 6. Supply chain

Most code in a service was written by strangers. Treat the dependency graph as an attack surface.

- **Pin and lock.** Committed lockfiles, exact versions. Floating ranges mean the build is not
  reproducible and a compromised release lands automatically.
- **Verify integrity.** Hash checks from the lockfile; signature or provenance verification where
  the ecosystem supports it.
- **Scan continuously**, not once. A dependency safe today gets an advisory tomorrow; the value is
  in the ongoing signal.
- **Generate an SBOM per build** and store it with the artefact. When an advisory lands, the
  question "which of our services ship this?" must be answerable in minutes.
- **Build provenance.** Signed attestations tying an artefact to the source commit and the builder
  (SLSA-style) let you verify that what is deployed is what was reviewed.
- **Lock down the build.** CI has credentials and produces artefacts everyone trusts — it is a
  high-value target. Least-privilege tokens, no secrets in pull-request builds from forks, pinned
  action and image digests rather than mutable tags.
- **Review what you add.** A transitive graph of hundreds for one utility function is a cost.
  Prefer the standard library; prefer fewer, well-maintained dependencies (see
  `config-and-dependencies`).

## 7. Threat modelling, cheaply

At design time (see `design-first` L3), ask four questions per trust boundary. This takes fifteen
minutes and catches more than a scanner will:

1. **What crosses this boundary, and who controls it?**
2. **What is the worst thing an attacker could do with that input?**
3. **What is the most sensitive data reachable from here, and what stops this caller reaching it?**
4. **How would we know if this were being abused right now?**

Record the answers in the design document. Question 4 is the one most often skipped, and it is the
one that determines whether an incident lasts an hour or a quarter.
