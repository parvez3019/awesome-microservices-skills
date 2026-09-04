---
name: collaborative-judgment
description: "Surface genuine architectural trade-offs as structured options with consequences instead of silently picking one. Governs how every other skill in this library reports its Ambiguity Signals — synchronous vs asynchronous, strong vs eventual consistency, orchestration vs choreography, split vs keep together. Use when a decision has two defensible answers, when the user says 'what do you think', 'which approach', 'trade-offs', or 'options', or when another skill routes an ambiguity here. This skill governs how a decision is presented and recorded — not what the right answer is (that belongs to the domain skill that raised it)."
license: MIT
---

# Collaborative Judgment

Microservice decisions are rarely wrong at the moment they are made. They are wrong six months
later, in a direction nobody wrote down. An agent that quietly picks "eventual consistency" and
moves on has not saved the team a decision — it has hidden one.

This skill defines the protocol for handing a real decision back to the human, and for recording
the answer so it is not re-litigated every session.

## Config Resolution

1. Read `.msskills/config.yaml` in the repo root; look up `paths.judgment`.
2. A custom document exists at that path → read its frontmatter `mode`:
   - `override` → use it alone as the presentation protocol; ignore the defaults below.
   - `overlay` (default, or no `mode` key) → read [defaults](./references/defaults.md) first,
     then apply the custom document's sections on top. A section replaces the matching default
     section by exact heading; new sections append.
3. A path is configured but no file exists there → say which path is missing, then use the
   embedded defaults.
4. No config file or no `paths.judgment` key → use [defaults](./references/defaults.md).
5. `.msskills/decisions.md` exists → read it before presenting any option set. A decision already
   recorded there is **settled**: apply it, cite it in one line, and do not re-ask.

## Self-Validation Checklist

**STOP before presenting a decision. Verify every check. Fix failures before showing anything.**

1. **GENUINE**: Do at least two options survive the project's stated constraints? If only one
   does → this is not a judgment call. Decide it, state the reason in one line, move on.
2. **BOUNDED**: Are there two or three options? More than three is a research dump, not a
   decision → merge the near-duplicates and drop the ones you would never recommend.
3. **CONCRETE**: Does each option name what actually changes in *this* codebase — the component,
   the contract, the failure mode? If an option could be pasted into any project → it is a
   textbook summary, not an option. Rewrite it against the real code.
4. **CONSEQUENCED**: Does each option state what it costs, not just what it gives? An option
   with no downside is a recommendation in disguise → find the cost or delete the option.
5. **REVERSIBILITY**: Is each option marked as reversible or one-way? A cheap-to-undo choice does
   not deserve the same ceremony as a data model you will live with for years.
6. **RECOMMENDED**: Have you named which option you would take, and why? Presenting three options
   with no lean is abdication → recommend one and stay open to being overruled.
7. **ANSWERABLE**: Can the user answer with a single word or number, without opening a file to
   check something you could have checked yourself? If not → go read that file first.
8. **RECORDED**: Once answered, will the decision and its reason land in `.msskills/decisions.md`
   (or the feature's design doc when one is open)? An unrecorded decision will be asked again.

All checks pass → present using the format in [defaults](./references/defaults.md).

## Active Anti-Pattern Scan

Any box you can check is a defect. Fix it before presenting.

- [ ] **Silent Resolution**: a real trade-off was decided inside the work and mentioned only in
      passing, or not at all → surface it as an option set before continuing.
- [ ] **False Choice**: options that differ only in wording, or where two are obviously wrong →
      collapse them; if one option remains, just decide.
- [ ] **Unbounded Menu**: five or more options, or nested sub-options → cut to the two or three
      the project would actually adopt.
- [ ] **Consequence-Free Pitch**: benefits listed for every option, costs for none → every option
      pays for itself somehow; say how.
- [ ] **Textbook Options**: generic definitions of the patterns instead of what each does to this
      service's boundaries, contracts, and failure modes → rewrite against the code in front of you.
- [ ] **Decision Amnesia**: re-asking something already settled in `.msskills/decisions.md` or the
      open design doc → read it first and apply the recorded answer.
- [ ] **Blocking on Trivia**: pausing for naming, formatting, or a choice with no downstream
      consequence → decide it and keep going; note it in one line.
- [ ] **Question Without Position**: "how would you like to handle this?" with no analysis →
      always bring a recommendation and the reasoning behind it.
- [ ] **Buried Reversibility**: presenting a one-way door (public API shape, event schema, data
      ownership) with the same weight as an easily changed detail → mark it explicitly.
- [ ] **Answer Ignored**: the user picked option B and the work proceeded down A → the choice is
      binding; if it turns out to be unworkable, say so and re-open it explicitly.

## Ambiguity Signals

These are the meta-calls this skill itself faces. Resolve them with judgment, not ceremony.

- **Is this genuinely ambiguous, or am I avoiding a decision?** If the project's recorded stack,
  constraints, and prior decisions already imply one answer, you are stalling. Decide.
- **When to batch versus ask immediately.** A decision that blocks the next line of code is asked
  now. Three independent decisions discovered while reading are batched into one message —
  interrupting eight times to write one component is worse than a single well-framed set.
- **How much analysis before asking.** Enough that each option is concrete about this codebase;
  not so much that you have effectively implemented two of them. If you cannot make an option
  concrete without prototyping it, say that is what the option would cost.
- **When to re-open a recorded decision.** New evidence that the recorded reasoning was wrong, or
  a constraint that has since changed — never merely because the decision is now inconvenient.
  Re-open explicitly, cite what changed, and record the supersession.
