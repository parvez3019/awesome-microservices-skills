# Clean Architecture — defaults

Loaded by Config Resolution when a project has no override, or as the base layer under an overlay.

---

## 1. The layers

Names differ across teams — onion, hexagonal, clean, ports and adapters. The rule is the same:
**dependencies point inward.** Adapt the vocabulary to whatever the project already uses.

| Layer | Contains | May depend on | Must never contain |
|---|---|---|---|
| **Domain** | Entities, value objects, aggregates, domain events, domain services, invariants | Nothing outside itself (language stdlib only) | Frameworks, I/O, SQL, HTTP, annotations, `now()`, randomness |
| **Application** | Use cases / command and query handlers, orchestration, transaction boundaries, outbound port interfaces | Domain | Framework annotations beyond DI, direct SQL, HTTP or broker clients |
| **Adapter** | Controllers, consumers, repository implementations, HTTP and broker clients, mappers | Application, domain | Business rules of any kind |
| **Infrastructure** | Wiring, configuration, migrations, serialisation setup, observability plumbing | Everything | Business rules |

**Ports are owned inward.** The application layer declares `interface OrderRepository`; the adapter
layer implements `PostgresOrderRepository`. The arrow points from adapter to application, which is
what makes the domain testable and the database replaceable.

A useful check: delete every adapter. The domain and application layers must still compile.

### Where a given thing goes

| Thing | Layer | Note |
|---|---|---|
| "An order over £500 needs approval" | Domain | It is a rule about an order, so it lives on the order |
| "Load the order, approve it, save it, publish the event" | Application | Orchestration, no rules |
| "POST /orders/{id}/approve" | Adapter | Parse, delegate, render |
| "Approval emails go through SendGrid" | Adapter | Behind a port the application owns |
| "Retry the SendGrid call three times" | Adapter | Resilience lives with the I/O (see `resilience-patterns`) |
| "The approval threshold is £500" | Config → Domain | Read as config, injected as a typed value (see `config-and-dependencies`) |
| Transaction begin/commit | Application | One use case, one transaction |
| Input validation (well-formedness) | Adapter | Malformed JSON is not a domain concept |
| Input validation (business rules) | Domain | An invalid quantity is |

## 2. SOLID, at two scales

These are the same five ideas applied to classes and to services. In a distributed system, the
service-level reading is usually the one that saves money.

**Single Responsibility — one reason to change.**
*Class:* describe it without "and". *Service:* if two unrelated business drivers force releases of
the same service, it holds two responsibilities (see `service-boundaries`).

**Open/Closed — extend without editing.**
*Class:* a new payment method adds a class rather than a case to five switches. *Service:* a new
consumer of your events should not require you to change anything — which is what additive-only
schema evolution buys (see `api-contracts`).

**Liskov — substitutes must honour the contract.**
*Class:* no implementation may throw where the interface promises a value, tighten a precondition,
or weaken a postcondition. *Service:* a v2 provider must satisfy every promise v1 made, or it is a
new contract, not a new version.

**Interface Segregation — no forced dependencies on unused methods.**
*Class:* split interfaces by consumer. *Service:* a single endpoint returning everything forces
every consumer to couple to fields it does not use; give the consumer the shape it needs.

**Dependency Inversion — depend on abstractions you own.**
*Class:* constructor-inject a port defined by the caller. *Service:* depend on a published contract
and your own translation of it, never on another team's internal model — that is the anti-corruption
layer.

## 3. Choosing a design pattern

A pattern is a solution to a *named force*. Without the force, it is indirection with a famous name.

| Force actually present | Pattern that answers it |
|---|---|
| One concept has several behaviours chosen at runtime, and the set grows | Strategy |
| Construction is complex, conditional, or needs invariants enforced | Factory / factory method |
| An object needs many optional fields and must be valid when built | Builder |
| An external model must not leak into the domain | Adapter / anti-corruption layer |
| Cross-cutting behaviour must wrap an existing contract without changing it | Decorator |
| A multi-step process varies only at fixed points | Template method |
| Something must react to a domain fact without the source knowing who | Domain event / observer |
| A complex subsystem needs one coherent entry point | Facade |
| A domain rule must be composable and testable on its own | Specification / policy |
| An expensive or remote resource needs lazy or guarded access | Proxy |

Rules of use:

- **Name the force before the pattern.** If you cannot write the force in one sentence, do not
  apply the pattern.
- **The rule of three.** Two similar things may be coincidence. The third with the *same reason to
  change* justifies the abstraction. Similarity alone never does.
- **Prefer the language's built-in answer.** A first-class function beats a strategy interface; a
  record beats a builder for four fields; an enum with behaviour beats a class hierarchy of one
  method each.
- **Patterns are refactoring destinations, not starting points.** Write the direct version, let the
  duplication appear, then extract.

## 4. Dependency injection

- **Constructor injection** for everything a class needs to function. Required dependencies are not
  optional and should not be settable.
- **Explicit over ambient.** Inject the clock, the ID generator, the random source. Anything that
  makes a test non-deterministic is a dependency (see `test-strategy`).
- **Composition root at the edge.** All wiring happens in one place in infrastructure. Nothing else
  knows the container exists.
- **No service locator.** Fetching dependencies from a static container hides the real dependency
  graph and makes construction untestable.
- **Depend on interfaces you own.** Wrapping a third-party client in your own port is not
  ceremony — it is what lets you replace it, fake it, and add resilience around it.

Where a language's idiom differs — Go's implicit interfaces, Rust's traits, TypeScript's structural
typing — follow the idiom. The requirement is that business logic never names a concrete external
type, not that a particular DI container is used.

## 5. Enforcing it

Reviews do not hold a boundary; the build does.

- **Architecture tests.** ArchUnit (JVM), NetArchTest (.NET), `import-linter` (Python),
  `dependency-cruiser` or ESLint boundary rules (JS/TS), `go-arch-lint` or an internal package
  (Go). One test per rule: "nothing in `domain` imports `adapter`"; "no framework annotation in
  `domain`"; "no cycles between modules".
- **Package structure by feature, then layer.** `orders/domain`, `orders/application`,
  `orders/adapter` beats `domain/orders`, `application/orders` — it keeps a feature's code together
  and makes the eventual extraction (see `service-boundaries`) a directory move.
- **Language-level visibility.** Package-private, internal, or unexported types are the cheapest
  enforcement available. Use them before writing a test.

Add the architecture test in the same change that introduces the rule. A rule with no test is a
comment.
