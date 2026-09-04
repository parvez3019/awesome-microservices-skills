---
name: clean-architecture
description: "Place code in the right layer and keep dependencies pointing inward, inside a single service. Covers ports and adapters (hexagonal) layering, the dependency rule, SOLID applied at class and service level, anti-corruption layers, framework isolation, and choosing a design pattern only when a named force demands it. Use when writing or reviewing any implementation code, deciding where a class belongs, wiring a dependency, adding a framework annotation to domain code, or when the user says 'architecture', 'layering', 'SOLID', 'coupling', 'hexagonal', 'design pattern', or 'where should this go'. This skill governs structure inside one service — not where services divide (see service-boundaries), not aggregate rules (see domain-modelling), not adapter craft (see infrastructure-adapters)."
license: MIT
---

# Clean Architecture

The point of layering is not tidiness. It is that business rules should be readable, testable, and
changeable without starting a database, a broker, or a web server — and that swapping any of those
should not touch a line of business logic.

One rule generates almost everything else: **dependencies point inward, toward the domain.**

## Config Resolution

1. Read `.msskills/config.yaml` in the repo root; look up `paths.architecture`.
2. A custom document exists at that path → read its frontmatter `mode`:
   - `override` → use it alone; ignore the defaults below.
   - `overlay` (default, or no `mode` key) → read [defaults](./references/defaults.md) first, then
     apply the custom document's sections on top, matched by exact heading; new sections append.
3. A path is configured but no file exists there → say which path is missing, then use the defaults.
4. No config file or no `paths.architecture` key → use [defaults](./references/defaults.md).
5. `.msskills/stack.md` exists → express every rule in that stack's idiom: its module system, its
   dependency-injection style, its package conventions, its architecture-test tooling.
6. No project document and no stack profile → use the defaults, and say once that
   `stack-profile` would make the guidance concrete.

## Self-Validation Checklist

**STOP after generating or reviewing each class, module, or file. Verify every check. Fix failures
before presenting.**

1. **LAYER PLACEMENT**: Can you name this file's layer — domain, application, adapter,
   infrastructure — and does its responsibility match? If it does two layers' jobs (a handler that
   contains a business rule, an entity that writes SQL) → split it.
2. **DEPENDENCY DIRECTION**: Does every import point inward or sideways within the layer? An inner
   layer importing an outer one → invert it with an interface owned by the inner layer.
3. **FRAMEWORK ISOLATION**: Is the domain free of framework and library types — annotations, ORM
   base classes, HTTP types, broker clients, serialisation attributes? If not → move them to the
   adapter and map at the edge.
4. **PORTS OWNED INWARD**: Is each outbound interface declared in the layer that *uses* it, not the
   layer that implements it? A repository interface next to its database implementation is not a
   port; it is a package split.
5. **SINGLE RESPONSIBILITY**: Can you describe this class in one sentence without "and"? If not →
   extract. Watch for the common pair: business logic *and* persistence.
6. **OPEN/CLOSED**: Would a new variant of an existing concept require editing a `switch` in
   several files? If yes → introduce polymorphism, but only for a variation that has actually
   happened twice.
7. **LISKOV**: Does every implementation of an interface honour its contract, or do some throw
   `UnsupportedOperation`, tighten preconditions, or return null where others cannot? If so → the
   abstraction is wrong; split it.
8. **INTERFACE SEGREGATION**: Does any caller depend on an interface where it uses one of eight
   methods? Split by consumer need, not by implementation convenience.
9. **DEPENDENCY INVERSION**: Does business logic depend on an abstraction it owns, or on a concrete
   client? Constructor-injected, never resolved from a static locator or `new`ed inline.
10. **TESTABLE WITHOUT I/O**: Can this class's behaviour be tested without a database, network, or
    clock? If not → push the side effect outward and inject time, IDs, and randomness.
11. **PATTERN JUSTIFIED**: If a named design pattern appears, can you state the force that demands
    it in one sentence? "It is more extensible" is not a force → remove the indirection.

All checks pass → state "Passes clean-architecture. [next step]."

## Active Anti-Pattern Scan

Any box you can check is a defect. Fix it before presenting.

- [ ] **Anaemic Domain**: entities are field bags and all rules live in services → move the
      invariants onto the type that owns them.
- [ ] **Framework in the Domain**: ORM, HTTP, or serialisation annotations on domain types → map
      at the adapter boundary instead.
- [ ] **Leaky Repository**: a port that returns the ORM's query builder, a `DataSet`, or a
      framework page type → return domain types.
- [ ] **Fat Controller**: business rules, orchestration, and validation in a handler → the handler
      parses input, calls one application service, and renders output.
- [ ] **Service Locator**: dependencies fetched from a static container or singleton inside a
      method → constructor injection.
- [ ] **Circular Dependency**: two modules importing each other → extract the shared concept, or
      invert one direction with an interface.
- [ ] **Utility Dumping Ground**: a `utils`, `helpers`, or `common` package with unrelated statics →
      move each function next to the concept it belongs to.
- [ ] **Speculative Abstraction**: an interface with exactly one implementation and no second one in
      sight, or a plugin system nobody plugs into → inline it until a real second case appears.
- [ ] **Pattern Theatre**: factories producing factories, a strategy with one strategy, an observer
      with one observer → delete the indirection.
- [ ] **Leaked External Model**: a third-party or upstream DTO used directly as a domain type → add
      an anti-corruption layer and translate at the edge.
- [ ] **Hidden Global State**: static mutable state, ambient singletons, `DateTime.now()` buried in
      logic → inject it.
- [ ] **Transaction in the Domain**: commit or session handling inside domain code → own the
      transaction in the application layer.

## Ambiguity Signals

Route these through `collaborative-judgment`. Each has two defensible answers.

- **How many layers.** Full four-layer separation is right for a service with real domain
  complexity and ceremony for a CRUD adapter over one table. Propose the lighter shape and let the
  user ask for more.
- **Port granularity.** One repository per aggregate is conventional; one narrow port per use case
  is more honest about what each caller needs and produces more interfaces. Both defensible.
- **Mapping cost.** Separate domain, persistence, and API models are the clean answer and triple
  the type count. Sharing one model is pragmatic until the first field that only one of them needs.
- **When an abstraction has earned its place.** The rule of three is a guideline, not a law; a
  second case with the same reason to change can justify it, and three coincidentally similar
  cases do not.
- **Where a rule lives when two aggregates share it.** A domain service, a policy object, or
  duplication in both — the right answer depends on which one owns the invariant.
