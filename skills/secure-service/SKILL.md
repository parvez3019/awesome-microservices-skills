---
name: secure-service
description: "Apply security controls at every trust boundary of a service. Covers the OWASP API Security Top 10 with object- and function-level authorisation first, service-to-service authentication with mTLS or signed tokens, input validation and injection prevention, secrets handling, output and error hygiene, PII classification and data protection, rate limiting of sensitive business flows, and supply-chain integrity through pinning, SBOMs and provenance. Use when writing or reviewing a handler, a client call, a query, an authorisation check, a dependency change, or anything touching credentials, tokens, or personal data; also when the user says 'security', 'auth', 'vulnerability', 'secrets', 'OWASP', or 'threat model'. This skill governs trust boundaries — not contract shape (see api-contracts), not failure behaviour (see resilience-patterns)."
license: MIT
---

# Secure Service

In a distributed system the perimeter is gone. Every service is reachable by something, and the
network is not a trust boundary. Authorisation happens in the service that owns the data, on every
request, for every object — not once at the gateway.

Broken authorisation is the top category in the OWASP API Security Top 10 and, in practice, the one
that leaks the most data. It is also the one that no scanner finds, because a request that returns
someone else's record looks exactly like a request that returns your own.

## Config Resolution

1. Read `.msskills/config.yaml` in the repo root; look up `paths.security`.
2. A custom document exists at that path → read its frontmatter `mode`:
   - `override` → use it alone as the security standard; ignore the defaults below.
   - `overlay` (default, or no `mode` key) → read [defaults](./references/defaults.md) first, then
     apply the custom document's sections on top, matched by exact heading; new sections append.
3. A path is configured but no file exists there → say which path is missing, then use the defaults.
4. No config file or no `paths.security` key → use [defaults](./references/defaults.md).
5. `.msskills/stack.md` exists → name that stack's actual mechanisms: its auth libraries, its
   secret manager, its dependency scanner, its parameterised-query idiom.
6. `.msskills/data-classification.md` exists → apply its categories when deciding what may be
   logged, cached, exported, or returned.

## Self-Validation Checklist

**STOP after writing or reviewing anything at a trust boundary — a request handler, a message
consumer, a query, an outbound call, a log statement, a dependency change. Verify every check.**

1. **AUTHENTICATED**: Is the caller's identity established and verified — signature, issuer,
   audience, expiry — not merely parsed? A decoded token is not a verified one.
2. **OBJECT AUTHORISATION**: Does the code check that *this* caller may access *this specific
   record*, on every access including nested and batch ones? An ID taken from the request and used
   to fetch without an ownership check is the single most common API vulnerability.
3. **FUNCTION AUTHORISATION**: Is the caller's permission to perform this *operation* checked
   server-side? Hiding a button is not authorisation.
4. **DENY BY DEFAULT**: Does a new endpoint or consumer require an explicit grant, or does it
   inherit access? New surfaces must start closed.
5. **INPUT VALIDATED**: Is every input validated against an allowlist of shape, type, range, and
   length at the boundary, before use? Rejecting known-bad patterns is not validation.
6. **INJECTION SAFE**: Are all queries parameterised, all commands built without string
   concatenation, all templates auto-escaped, and all deserialisation type-constrained? Includes
   SQL, NoSQL query documents, shell, LDAP, XPath, and template engines.
7. **MASS ASSIGNMENT BLOCKED**: Does binding use an explicit allowlist of fields, so a request
   cannot set `role`, `isAdmin`, `price`, or `ownerId`?
8. **SSRF GUARDED**: Does any outbound request use a URL derived from user input? → allowlist the
   destination; never fetch an arbitrary address from inside the network.
9. **SECRETS EXTERNAL**: Are all credentials, keys, and tokens from a secret manager or injected
   environment — never in code, config files, container images, or version control?
10. **OUTPUT CLEAN**: Do responses and errors avoid stack traces, SQL, internal hostnames, and
    fields the caller is not entitled to? Filter server-side; never rely on the client to hide.
11. **LOGS CLEAN**: Are credentials, tokens, full card or account numbers, and personal data kept
    out of logs, traces, and error reports?
12. **TRANSPORT SECURE**: Is every hop encrypted, including service-to-service inside the cluster,
    with certificates actually verified?
13. **SENSITIVE FLOW LIMITED**: Are business flows worth automating — signup, login, password
    reset, checkout, coupon redemption — rate limited and abuse-monitored per identity, not just
    per IP?
14. **DEPENDENCY INTEGRITY**: Are new dependencies pinned with a lockfile, from a trusted registry,
    scanned for known vulnerabilities, and actually necessary?

All checks pass → state "Passes secure-service: authz at <layer>, inputs validated, no secrets in
code."

## Active Anti-Pattern Scan

Any box you can check is a defect. Fix it before presenting.

- [ ] **Broken Object-Level Authorisation**: an ID from the request used to load a record with no
      ownership check → scope every query by the caller's identity.
- [ ] **Gateway-Only Authorisation**: the service trusts that something upstream already checked →
      each service authorises for itself.
- [ ] **Unverified Token**: a JWT decoded but not verified, or verified without checking issuer,
      audience, expiry, and algorithm → verify all of them; reject `alg: none`.
- [ ] **Internal Means Trusted**: an endpoint or consumer with no authentication because it is "on
      the internal network" → authenticate every caller.
- [ ] **String-Built Query**: any query, command, or path assembled by concatenation → parameterise.
- [ ] **Blocklist Validation**: filtering known-bad input instead of allowing known-good → allowlist.
- [ ] **Mass Assignment**: request body bound straight onto a domain or persistence object →
      explicit field allowlist.
- [ ] **Secret in Repository**: a key, password, or token in code, config, a test fixture, a
      Dockerfile, or CI YAML → move to the secret manager and **rotate it**; git history is public.
- [ ] **Verbose Error**: exception text, stack trace, or SQL returned to the caller → generic
      message plus a trace ID.
- [ ] **PII in Logs**: emails, phone numbers, addresses, tokens, or full identifiers in log lines
      or span attributes → redact at the logging boundary.
- [ ] **Over-Fetching Response**: the full record serialised and the client expected to display a
      subset → return only what the caller may see.
- [ ] **Unbounded Sensitive Flow**: signup, login, or reset with no per-identity limit → rate limit
      and monitor.
- [ ] **Unpinned Dependency**: a floating version range, no lockfile, or an unverified install
      script → pin and lock.
- [ ] **Long-Lived Static Credential**: a permanent shared API key between services → short-lived
      workload identity.

## Ambiguity Signals

Route these through `collaborative-judgment`. Each has two defensible answers.

- **Where authorisation lives.** In the handler it is visible and repetitive; in the domain it is
  central and easy to bypass from a new entry point; in a policy layer it is testable and indirect.
- **Token model.** Opaque tokens with introspection are revocable and add a network hop on every
  request; self-contained JWTs are fast and effectively un-revocable until they expire.
- **Encryption at the field level.** Protects the data at rest from the database itself and breaks
  querying, sorting, and indexing on those fields.
- **How much to reveal in an error.** Detailed errors help legitimate callers and help attackers
  enumerate. The right level differs between a public API and an internal one.
- **Tenant isolation depth.** A discriminator column, a schema per tenant, or a database per tenant
  trade blast radius against operational cost.
- **Blocking a build on vulnerability severity.** Failing on every advisory produces alert fatigue
  and bypasses; failing on none means nobody looks. Pick the line deliberately.
