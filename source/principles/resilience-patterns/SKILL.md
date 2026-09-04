---
name: resilience-patterns
description: "Make a service behave predictably when its dependencies are slow, failing, or duplicating work. Covers timeouts and deadline propagation, retry with exponential backoff, jitter and retry budgets, circuit breakers, bulkheads, rate limiting and load shedding, fallbacks and graceful degradation, idempotent consumers, the transactional outbox and inbox, saga compensation, and health probes. Use when writing or reviewing any call that leaves the process, when handling a message, or when the user says 'resilience', 'circuit breaker', 'retry', 'timeout', 'cascading failure', 'outbox', 'saga', or 'graceful degradation'. This skill governs runtime failure behaviour — not layering (see clean-architecture), not test design (see test-strategy)."
license: MIT
---

# Resilience Patterns

In a single process, a slow function is a performance problem. Across a network, a slow dependency
is an outage: threads pile up on the caller, its own callers time out, and the failure walks
upstream faster than anyone can page. Most microservice incidents are this, not a crash.

Two rules carry most of the weight: **every remote call has a timeout**, and **every retry has a
budget**. Retries without a budget are a self-inflicted denial of service on a service that was
already struggling.

## Config Resolution

1. Read `.msskills/config.yaml` in the repo root; look up `paths.resilience`.
2. A custom document exists at that path → read its frontmatter `mode`:
   - `override` → use it alone; ignore the defaults below.
   - `overlay` (default, or no `mode` key) → read [defaults](./references/defaults.md) first, then
     apply the custom document's sections on top, matched by exact heading; new sections append.
3. A path is configured but no file exists there → say which path is missing, then use the defaults.
4. No config file or no `paths.resilience` key → use [defaults](./references/defaults.md).
5. `.msskills/stack.md` exists → name that stack's actual library and idiom rather than the generic
   pattern: the platform's circuit breaker, its retry policy type, its client deadline mechanism, its
   outbox tooling. Never invent a library; if the profile does not name one, describe the behaviour
   and say the library choice is open.

## Self-Validation Checklist

**STOP after writing or reviewing any code that crosses a process boundary — HTTP, gRPC, database,
cache, broker, filesystem. Verify every check. Fix failures before presenting.**

1. **TIMEOUT**: Does this call have an explicit timeout, shorter than the caller's own deadline? A
   default of "none" or "60s inherited from the client library" → set one derived from the latency
   budget.
2. **DEADLINE PROPAGATION**: Is the remaining time budget passed downstream, so work nobody is
   waiting for is abandoned? If the framework supports it and it is unused → use it.
3. **RETRY SAFETY**: Is the operation idempotent before it is retried? Retrying a non-idempotent
   write → add an idempotency key first, or do not retry.
4. **RETRY SHAPE**: Does every retry use exponential backoff *with jitter*, a bounded attempt
   count, and a budget capping retries as a fraction of total traffic? Fixed-interval or unbounded
   retries → fix; synchronised retries → add jitter.
5. **RETRY CLASSIFICATION**: Are only retryable failures retried — timeouts, connection errors,
   429, 502/503/504? Retrying a 400 or 422 wastes the budget and never succeeds.
6. **NO NESTED RETRIES**: Does more than one layer retry the same logical call? Retries multiply;
   pick exactly one layer, usually the outermost that still knows the operation is idempotent.
7. **CIRCUIT BREAKER**: Does a call to a dependency that can fail persistently sit behind a breaker
   with a defined failure threshold, open duration, and half-open probe? If not → add one, or
   record why this dependency does not need it.
8. **ISOLATION**: Can one slow dependency exhaust the resource pool the whole service shares? If
   yes → bulkhead it with a separate pool or concurrency limit.
9. **FALLBACK DEFINED**: When this fails after all protection, what does the caller see — cached
   data, a partial response, a degraded feature, or a clean error? "It throws" is only acceptable
   if that is the deliberate choice.
10. **IDEMPOTENT CONSUMER**: For a message handler, does redelivery of the same message produce the
    same result? At-least-once delivery is the norm → deduplicate on message ID or make the effect
    naturally idempotent.
11. **NO DUAL WRITE**: Does anything write to the database and publish to a broker as two separate
    operations? → transactional outbox.
12. **COMPENSATION**: For a multi-service workflow, is every step's compensating action defined,
    and is it itself idempotent and retryable?
13. **PROBES CORRECT**: Does readiness reflect the ability to serve traffic, and liveness only
    unrecoverable state? A readiness probe that checks a downstream dependency will take the whole
    fleet out when that dependency blips.

All checks pass → state "Passes resilience: timeout <x>, retry <policy>, breaker <yes/no>,
fallback <behaviour>."

## Active Anti-Pattern Scan

Any box you can check is a defect. Fix it before presenting.

- [ ] **Infinite Timeout**: any remote call using the library default → set an explicit one.
- [ ] **Retry Storm**: retries at client, gateway, and service layers compounding → one layer only.
- [ ] **Synchronised Retry**: fixed backoff with no jitter, so every caller returns together →
      full jitter.
- [ ] **Unbounded Retry Budget**: retries allowed regardless of overall failure rate → cap them as
      a fraction of traffic and shed when exceeded.
- [ ] **Retrying the Unretryable**: 4xx responses, validation failures, or non-idempotent writes
      retried → classify before retrying.
- [ ] **Dual Write**: database commit and event publish as separate steps → outbox.
- [ ] **Fire and Forget**: an async publish whose failure is logged and dropped → outbox, or an
      explicit dead-letter path.
- [ ] **Missing Dead Letter**: a consumer that retries forever on a poison message, blocking the
      partition → bounded retries, then dead-letter with enough context to replay.
- [ ] **Cascading Readiness**: readiness checking downstream dependencies, so one outage empties
      every load balancer → readiness reflects *this* instance only.
- [ ] **Shared Pool Exhaustion**: one connection or thread pool for every dependency → bulkhead the
      risky ones.
- [ ] **Silent Fallback**: degraded data served as if it were fresh, with no signal to the caller
      or the dashboards → make degradation visible.
- [ ] **Compensation Assumed**: a saga whose rollback path was never written or never tested → it
      does not exist.
- [ ] **Unbounded Queue or Buffer**: in-memory work queues with no limit → bound them and shed;
      an unbounded queue converts a latency problem into an out-of-memory crash.

## Ambiguity Signals

Route these through `collaborative-judgment`. Each has two defensible answers.

- **Fail closed or degrade.** Serving stale or partial data protects availability; refusing
  protects correctness. Which one is right is a product decision — ask, do not assume.
- **Timeout values.** Too short sheds load that would have succeeded; too long ties up resources.
  Without latency percentiles this is a guess; say so, propose a starting point, and make it
  configurable.
- **Circuit breaker thresholds.** Sensitive breakers trip on noise; tolerant ones let cascades
  build. Depends on traffic volume and the cost of a false trip.
- **Orchestration or choreography** for a multi-step workflow. An orchestrator makes the flow
  visible and debuggable in one place; choreography avoids the central component and scatters the
  flow across services (see `service-boundaries`).
- **Where the outbox relay lives.** Change-data-capture is robust and adds infrastructure; a polling
  publisher is simple and adds latency and load.
- **Whether this dependency needs a breaker at all.** For a rarely used, non-critical call, the
  breaker may be more machinery than the risk justifies.
