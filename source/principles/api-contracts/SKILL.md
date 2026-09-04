---
name: api-contracts
description: "Design and evolve the contracts that cross a service boundary — synchronous APIs and published events — specification first. Covers resource and operation modelling, OpenAPI and AsyncAPI as source of truth, backward-compatible evolution and versioning, RFC 9457 problem details, idempotency keys, pagination and filtering, and event schema compatibility modes. Use when adding or changing an endpoint, message, or published event, when reviewing a schema, or when the user says 'API design', 'contract', 'OpenAPI', 'AsyncAPI', 'versioning', 'breaking change', 'REST', or 'event schema'. This skill governs what crosses a boundary — not where boundaries fall (see service-boundaries), not how contracts are verified (see contract-testing)."
license: MIT
---

# API Contracts

A contract is the only part of a service that is genuinely hard to change, because you do not
control who depends on it or when they will redeploy. Everything behind it is refactorable;
everything in it is a promise. Design it deliberately, and evolve it additively.

The contract is written **before** the implementation, and the specification is the source of
truth — not a document generated afterwards from whatever the code happened to return.

## Config Resolution

1. Read `.msskills/config.yaml` in the repo root; look up `paths.api`.
2. A custom document exists at that path → read its frontmatter `mode`:
   - `override` → use it alone as the API standard; ignore the defaults below.
   - `overlay` (default, or no `mode` key) → read [defaults](./references/defaults.md) first, then
     apply the custom document's sections on top, matched by exact heading; new sections append.
3. A path is configured but no file exists there → say which path is missing, then use the defaults.
4. No config file or no `paths.api` key → use [defaults](./references/defaults.md).
5. `.msskills/stack.md` exists → use its protocol and tooling: REST, gRPC, or GraphQL; its
   serialisation format; its schema registry and compatibility mode; its spec linter.
6. An existing specification is in the repository → its conventions outrank these defaults. Match
   the API that exists rather than introducing a second style beside it.

## Self-Validation Checklist

**STOP before presenting any new or changed contract. Verify every check. Fix failures first.**

1. **SPEC FIRST**: Does a specification fragment exist — OpenAPI, AsyncAPI, protobuf, JSON Schema —
   before the implementation? If the code came first → write the spec now and reconcile.
2. **CONSUMER-SHAPED**: Does each operation serve a real consumer use case, or does it expose the
   internal model? An endpoint that mirrors a table row by row → reshape it around what the caller
   is trying to do.
3. **BACKWARD COMPATIBLE**: For a change to an existing contract, is it purely additive — new
   optional field, new endpoint, new enum value the consumer may ignore? If it removes, renames,
   narrows a type, tightens validation, or changes a default → it is breaking. **STOP** and route
   through `collaborative-judgment`.
4. **ERRORS SPECIFIED**: Is every failure enumerated with a status code, a stable machine-readable
   code, and guidance on whether retrying helps? A contract with only the success case is half
   written.
5. **IDEMPOTENCY**: Can every non-`GET` operation be safely retried? If not → define the
   idempotency key, its scope, and how long it is honoured (see `resilience-patterns`).
6. **NO UNBOUNDED COLLECTION**: Does any response return a list with no limit? Every collection is
   paginated with an explicit default and maximum page size.
7. **TYPES EXPLICIT**: Are money, time, and identifiers unambiguous — currency alongside amount,
   timestamps in UTC with offset, IDs typed rather than bare strings? Ambiguity here becomes a
   production incident.
8. **NO INTERNAL LEAKAGE**: Does the payload expose database identifiers, internal enum names,
   stack traces, or fields no consumer needs? Strip them (see `secure-service`).
9. **EVENTS ARE FACTS**: Is each published event named in the past tense, describing something that
   happened, and does it carry what consumers need without requiring a call back? Events named as
   commands (`SendEmail`) belong on a queue, not an event stream.
10. **COMPATIBILITY MODE**: For an event schema, is the registry's compatibility mode stated, and
    does the change satisfy it?
11. **VERIFIABLE**: Is it clear which contract test will hold this promise (see
    `contract-testing`)?

All checks pass → state "Contract holds: <operation>, <compat status>, errors specified."

## Active Anti-Pattern Scan

Any box you can check is a defect. Fix it before presenting.

- [ ] **Code-First Spec**: the specification is generated from handlers after the fact, so the
      contract is whatever the code does → author the spec deliberately.
- [ ] **CRUD Leakage**: endpoints that mirror tables, forcing consumers to orchestrate business
      operations → model the operation the consumer actually performs.
- [ ] **Chatty Contract**: the consumer must call three endpoints to render one screen → give it
      one purpose-built representation.
- [ ] **Silent Breaking Change**: a field removed, renamed, or narrowed without a version or a
      migration window → additive change, or an explicit deprecation cycle.
- [ ] **Envelope Errors**: HTTP 200 with `{"success": false}` → use the status code; it is the part
      every proxy, client, and dashboard already understands.
- [ ] **Stringly-Typed Payload**: dates, money, enums, and booleans passed as free text → use typed
      fields with stated formats.
- [ ] **Unbounded List**: a collection endpoint with no pagination → it will time out the day the
      data grows.
- [ ] **Chatty Event**: an event carrying only an ID, forcing every consumer to call back → include
      the facts consumers need, and say why anything is deliberately omitted.
- [ ] **Command as Event**: `SendConfirmationEmail` published to a topic → that is a command with
      one owner, not a fact.
- [ ] **Version in Every Path**: `/v2/` minted for an additive change → version only on a genuine
      break.
- [ ] **Undocumented Nullability**: optional and required unstated, so consumers guess → mark every
      field.
- [ ] **Leaked Internals**: database IDs, internal status names, or exception text in responses →
      map to the public vocabulary.

## Ambiguity Signals

Route these through `collaborative-judgment`. Each has two defensible answers.

- **Break now or carry the field forever.** A clean break costs a coordinated migration; carrying a
  deprecated field costs permanent complexity. Which is cheaper depends on how many consumers exist
  and whether you can see their traffic.
- **Versioning strategy.** URL path, header, or media type — each trades discoverability against
  cache and routing behaviour, and the right answer is usually "whatever the rest of the estate
  already does".
- **Event granularity.** Fine-grained facts are flexible and chatty; coarse aggregate events are
  efficient and couple consumers to a bigger shape.
- **Thin versus fat events.** Carrying state removes callbacks and duplicates data that can go
  stale; carrying only an ID keeps one source of truth and adds a synchronous dependency.
- **Whether a change is really breaking.** Tightening validation, changing a default, or adding a
  required field to a request breaks *some* consumers. Deciding whether those consumers exist is a
  judgment call, not a lookup.
