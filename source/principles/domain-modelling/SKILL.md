---
name: domain-modelling
description: "Design the classes that carry business meaning, using tactical domain-driven design. Covers entities versus value objects, aggregate boundaries justified by a named invariant, domain services, domain events, factories, the ubiquitous language, making illegal states unrepresentable, and keeping behaviour on the type that owns the rule rather than in a service. Use when creating or changing a domain class, choosing an aggregate boundary, deciding whether something is an entity or a value, naming a domain concept, or when the user says 'domain model', 'DDD', 'aggregate', 'entity', 'value object', 'domain class', or 'business rules'. This skill governs the shape of domain types — persistence craft belongs to data-access, read models and consistency to cqrs-and-consistency, service-level boundaries to service-boundaries."
license: MIT
---

# Domain Modelling

The domain model is where the business rules live, or it is a set of data holders with the rules
scattered through service classes. There is no third option, and which one you have is decided by
a hundred small choices about where to put behaviour.

One question settles most of them: **what invariant does this type protect?** A type with no
invariant is a data structure — fine, but do not call it a domain model. A rule with no type that
owns it will be duplicated in three services within a year.

## Config Resolution

1. Read `.msskills/config.yaml` in the repo root; look up `paths.domain`.
2. A custom document exists at that path → read its frontmatter `mode`:
   - `override` → use it alone; ignore the defaults below.
   - `overlay` (default, or no `mode` key) → read [defaults](./references/defaults.md) first, then
     apply the custom document's sections on top, matched by exact heading; new sections append.
3. A path is configured but no file exists there → say which path is missing, then use the defaults.
4. No config file or no `paths.domain` key → use [defaults](./references/defaults.md).
5. `.msskills/stack.md` exists → use its type-system idiom. Records, sealed hierarchies, structs,
   traits, discriminated unions, and their absence change how these rules are expressed. A pattern
   the language expresses natively beats a transliterated one from another language.
6. `.msskills/context-map.md` exists → use the ubiquitous language recorded for this context. A term
   that means something else in another context must not be borrowed.

## Self-Validation Checklist

**STOP after creating or changing any domain type. Verify every check. Fix failures first.**

1. **INVARIANT NAMED**: For an aggregate, can you state in one sentence the rule that must hold at
   every commit? If not → it is not an aggregate. Model it as an entity, a value, or a plain record.
2. **VALID ON CONSTRUCTION**: Can this type be constructed in an invalid state? Every path in —
   constructor, factory, deserialisation, ORM materialisation — must enforce the invariant, or
   reject.
3. **BEHAVIOUR WITH THE DATA**: Does the rule about this data live on this type? A rule enforced in
   a service while the type exposes setters → move it in.
4. **ENTITY OR VALUE**: Does the business track this thing through change, or care only about its
   value? Identity it does not need → make it a value object.
5. **VALUE OBJECTS IMMUTABLE**: Are value objects immutable, with operations returning new
   instances, and equality by value? A mutable value object shared between two aggregates is a
   defect waiting to be found (see `idempotency-and-immutability`).
6. **NO PRIMITIVE OBSESSION**: Is any concept with rules, units, or a format passed as a bare
   string, number, or boolean across a boundary? → give it a type.
7. **SMALLEST AGGREGATE**: Does the aggregate contain only what its invariant requires? Collections
   loaded only for reading → they belong in a query, not the write model.
8. **REFERENCE BY IDENTITY**: Do aggregates reference other aggregates by ID, not by object
   reference?
9. **ENCAPSULATED**: Does the root hand out mutable internals — a live collection, a mutable child?
   → return copies or read-only views, and expose intent-revealing methods instead of setters.
10. **UBIQUITOUS LANGUAGE**: Does every type, method, and enum value use the word the business uses?
    A `StatusManager` or a `flag2` means the language was never agreed.
11. **DOMAIN SERVICE JUSTIFIED**: For each domain service — is this rule genuinely owned by no
    single type? If it belongs to one of its arguments → move it there. A `*Service` holding logic
    that operates on one entity's fields is an anaemic model with extra steps.
12. **NO INFRASTRUCTURE**: Is the type free of persistence, framework, serialisation, HTTP, clock,
    and randomness? (see `clean-architecture`)
13. **ILLEGAL STATES UNREPRESENTABLE**: Where the language allows, is an invalid combination
    impossible to express rather than merely rejected? Prefer a sealed hierarchy or a sum type to a
    nullable field plus a status enum.

All checks pass → state "Model holds: <type> protects <invariant>."

## Active Anti-Pattern Scan

Any box you can check is a defect. Fix it before presenting.

- [ ] **Anaemic Model**: fields plus getters and setters, all rules in `*Service` classes → move
      behaviour onto the types that own it.
- [ ] **God Aggregate**: an aggregate spanning many concepts, loading hundreds of children, touched
      by every write → split by invariant.
- [ ] **Aggregate Without an Invariant**: a class called an aggregate that only groups rows → it is
      a table; stop pretending otherwise.
- [ ] **Primitive Obsession**: `String customerId`, `double amount`, `int days` crossing boundaries
      → typed values.
- [ ] **Mutable Value Object**: a value type with setters, or one whose internal collection can be
      changed by a caller → make it immutable.
- [ ] **Public Setters on an Entity**: state changed field by field from outside, so no rule can be
      enforced → intent-revealing methods (`cancel(reason)`, not `setStatus(CANCELLED)`).
- [ ] **Leaked Collection**: the root returns its internal list, so callers add and remove behind
      its back → return an unmodifiable view.
- [ ] **Cross-Aggregate Object Reference**: one root holding another root as a field → reference
      by ID.
- [ ] **Service Envy**: a domain service whose every operation reads and writes one entity's fields
      → the behaviour belongs on the entity.
- [ ] **Technical Naming**: `OrderData`, `OrderHelper`, `OrderManager`, `processData` → name it in
      the business's words.
- [ ] **Nullable Soup**: many nullable fields whose valid combinations are documented in a comment
      → sum types or separate types per state.
- [ ] **Anaemic Enum**: an enum plus a `switch` in five places → put the behaviour on the enum or
      use polymorphism.
- [ ] **Shared Domain Across Contexts**: one model reused in two bounded contexts → two models with
      translation between them (see `service-boundaries`).

## Ambiguity Signals

Route these through `collaborative-judgment`. Each has two defensible answers.

- **Aggregate granularity.** A larger aggregate makes the invariant trivial to enforce and creates
  write contention; a smaller one scales and pushes the rule into a process. Without write-volume
  numbers this is a genuine guess — say so.
- **Where a rule lives when it spans two aggregates.** A domain service, a policy object invoked by
  both, or eventual enforcement through events.
- **Which primitives earn a type.** Wrapping everything is noise; wrapping nothing is how a
  currency mismatch reaches production. The line is usually "does it have rules, units, or a
  format".
- **Rich model or transaction script.** For a genuinely CRUD capability with no invariants, a rich
  model is ceremony. Not every service needs one — but the decision should be conscious.
- **Modelling state as fields or as types.** A sealed hierarchy per state makes illegal states
  impossible and multiplies the type count.
- **Whether a concept is one thing or two.** The same word used by two parts of the business often
  means two models, and merging them is the most common modelling mistake there is.
