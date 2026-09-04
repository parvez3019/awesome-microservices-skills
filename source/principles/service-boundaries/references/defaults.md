# Service Boundaries — defaults

Loaded by Config Resolution when a project has no override, or as the base layer under an overlay.

---

## 1. Finding a boundary

Boundaries are discovered from language and change, not drawn from an architecture diagram.

**Start from language.** Where a word changes meaning, a context boundary runs. "Order" in
checkout is a basket being confirmed; in fulfilment it is a set of packages with addresses; in
finance it is a revenue event. Those are three models, not one shared `Order` class with thirty
nullable fields.

**Confirm with change.** Look at the last twenty commits or tickets. Group them by what they
touched. Work that repeatedly changes the same set of files belongs on the same side of a boundary;
work that never touches a group belongs on the other side. This is the single most reliable signal
available, and it costs one `git log`.

**Check with a heuristic sweep:**

| Signal | Where the boundary probably is |
|---|---|
| A term means two things | Between the two meanings |
| Two areas always change together | Nowhere — they are one context |
| Two areas never change together | Between them |
| An invariant must hold atomically | Inside — never across |
| Different actors with different vocabulary | Between the actors' concerns |
| Wildly different load or availability needs | Possibly between, if the numbers are real |
| A regulatory or data-residency line | Always between; this one is not negotiable |

**Event storming** is the fastest workshop form: list domain events in past tense on a timeline,
cluster them by the language and the actor, and the clusters are candidate contexts. The pivotal
events — where the process visibly hands off to different people — are the strongest boundaries.

## 2. The modular-monolith-first bias

A module boundary inside one deployable gives most of what a service boundary gives — separate
model, separate ubiquitous language, explicit interface, independent tests, clear ownership — for
none of the operational cost. It also stays *refactorable*, which is the property that matters most
while a domain is still being understood.

A service adds exactly four things, and each has a price:

| What a separate service buys | What it costs |
|---|---|
| Independent deployment | A versioned contract, backward compatibility, and a deploy pipeline |
| Independent scaling | Duplicated infrastructure and a capacity story per service |
| Failure isolation | Every synchronous caller now needs timeouts, retries, and fallbacks |
| Hard ownership boundary | Cross-team coordination for anything that spans it |

Extract when one of those four is *required*, not when it would be nice. Until then, enforce the
boundary in the module — package-private types, an explicit facade, an architecture test that fails
the build on a cross-module import of an internal type. A boundary the compiler enforces is a real
boundary.

## 3. Context mapping

Once boundaries exist, the relationships between them are design decisions in their own right.
Record them in `.msskills/context-map.md`.

| Relationship | What it means | When it is right |
|---|---|---|
| **Partnership** | Two contexts succeed or fail together; teams coordinate releases | Rare, and a warning sign — usually the boundary is wrong |
| **Shared Kernel** | A small model deliberately shared | Only for genuinely stable concepts; every shared type is a deploy dependency |
| **Customer/Supplier** | Downstream's needs are on the upstream's backlog | Same organisation, aligned incentives |
| **Conformist** | Downstream accepts the upstream model as-is | The upstream will not change and the model is tolerable |
| **Anti-Corruption Layer** | Downstream translates the upstream model into its own | The default for anything external, legacy, or third-party |
| **Open Host Service** | Upstream publishes a general protocol for many consumers | The upstream has several consumers with similar needs |
| **Published Language** | A shared, versioned schema everyone speaks | Event-driven integration; pairs with a schema registry |
| **Separate Ways** | No integration at all; duplicate instead | The integration cost exceeds the duplication cost — a legitimate answer |

The one to reach for by default is the **anti-corruption layer**. It is the cheapest insurance
against another team's model leaking into yours, and it localises the damage when they change it.

## 4. Data ownership

One writer per piece of data. This is the rule that makes everything else possible.

Readers get data one of three ways, in increasing order of coupling and decreasing order of
freshness cost:

1. **Ask the owner** — a synchronous query. Simple, always fresh, and it puts the owner's
   availability inside your own.
2. **Subscribe to the owner's events** — build a local read model. No runtime dependency, but the
   data is stale by some bounded amount, and you now maintain a projection (see `cqrs-and-consistency`).
3. **Accept a copy at write time** — the caller sends what you need. Zero dependency, and the copy
   is a snapshot that never updates, which is exactly right for things like the price at time of
   order.

Choose per field, not per service. An order needs the *price at purchase* as a copy and the
*customer's current address* as a query — the same integration answered two different ways.

**Never** reach into another service's database, even read-only. A schema is not a contract, and
the first migration will prove it.

## 5. Extraction by strangler fig

Extracting a service from a monolith, in order. Each step is independently releasable and
reversible — that is the point.

1. **Find the seam.** Pick a capability with few inbound dependencies and clear data ownership.
   Verify with change coupling, not with intuition.
2. **Make it a module first.** Move the code inside the monolith behind an explicit interface.
   Enforce the boundary with an architecture test. Ship this. Most of the risk is here, and it is
   still cheap to undo.
3. **Separate the data.** Stop other modules touching those tables; route everything through the
   interface. Ship this. Now you know whether the boundary is real.
4. **Add the remote implementation.** Stand the new service up alongside, implementing the same
   interface over HTTP or messaging. Nothing calls it yet.
5. **Shift traffic behind a flag.** Route a percentage through the remote implementation, compare
   results, roll back instantly on divergence (see `config-and-dependencies` for flag hygiene).
6. **Remove the local implementation.** Only after the remote one has run at full traffic long
   enough to trust.

If step 2 or 3 proves impossible, the boundary was wrong. That is the cheapest possible way to
learn it — far cheaper than discovering it after step 6.

## 6. Sizing

There is no correct number of lines, endpoints, or tables. The useful tests are:

- **One team can own it.** If two teams must agree on every release, it is too big or misplaced.
- **It fits in one person's head.** A new engineer should understand what it does in a day.
- **It has one reason to change.** Two independent release drivers means two services.
- **It can be rewritten in a quarter.** Not that you will — but a service you cannot replace has
  become a monolith with a network boundary.

"Micro" is not a size target. A service that correctly owns a large capability is healthier than
six services that must be deployed as a set.
