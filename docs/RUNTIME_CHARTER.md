# Spark Harness Runtime Charter

Date: 2026-06-01

## Purpose

This charter defines the shared runtime semantics for every Spark surface that plugs into Spark Harness Core.

The goal is simple:

```text
surfaces observe -> Governor decides -> lifecycle executes -> ledgers prove -> evolution improves
```

No surface should turn raw language into high-agency action by itself.

## Runtime Authority

- Fresh user intent is the only source that can authorize a new high-agency move.
- Keywords, memory, pending state, prior missions, provider names, route history, and local classifiers are evidence only.
- The Governor is the only runtime component that may promote evidence into `TurnIntentEnvelopeVNext`.
- An action is not executable until it has a valid envelope and an `AuthorizationDecisionV1`.
- A high-agency action is not complete until it has a `ToolCallLedgerV1` and result verdict.

## Legacy Plane Retirement

Prior intent patches, route-specific detectors, helper vetoes, and adapter-local
launch logic must be retired, removed, or demoted to evidence adapters. They
must not remain as fallback authority, shadow routers, hidden launch gates, or
parallel policy systems.

When Spark keeps a historical detector for migration, tests, or diagnostics, it
must satisfy all of these conditions:

- it can only emit evidence into the Governor path
- it cannot execute, save, schedule, publish, mutate memory, start missions, or
  finalize tool ledgers by itself
- its output is traceable as evidence, not as an authority verdict
- it has a named retirement owner or compatibility reason

No surface is release-candidate ready while old patches can still fight the
Governor or bypass Harness Core.

## Move Semantics

`chat_explain`, `chat_plan`, `chat_compare`, `chat_score`, and `chat_draft_text` are conversational moves.

- They must not contain proposed actions.
- They must not write memory, launch missions, publish, deploy, schedule, edit files, or call external tools.
- They may produce useful answers, drafts, comparisons, plans, and reasoning.

`read_current_state` may inspect fresh state through approved read capabilities.

`prepare_action` may shape a possible action but must not execute it.

`confirm_action` may ask for explicit approval when risk or ambiguity requires it.

`execute_action` may run only when the envelope is executable and authorization allows it.

## Tool Lifecycle

Every tool call follows this lifecycle:

```text
propose -> validate -> authorize -> approve/interrupt -> execute -> sanitize -> store -> summarize -> continue
```

Rollback and failure are first-class outcomes, not side notes.

Execution status is authority-bound:

- `not_started` may be recorded for allowed, interrupted, or denied actions so
  blocked work remains inspectable.
- `success`, `failure`, `partial`, and `rolled_back` require an `allow`
  authorization. A blocked or interrupted action cannot be represented as
  executed by changing the ledger result later.
- Tool ledgers are evidence records, not permission grants. The Governor and
  authorization decision remain the execution boundary.

## Authorization Verdicts

- `allow`: the action may proceed inside stated restrictions.
- `deny`: the action cannot proceed and should remain conversational or stop.
- `interrupt`: the action may proceed only after explicit approval or missing evidence is supplied.
- `degrade`: the runtime should narrow scope, reduce privileges, or switch to read/chat behavior.

## Risk Tiers

- `none`: conversational only.
- `read`: fresh state inspection.
- `low`: reversible, local, bounded work.
- `medium`: workspace mutation, installs, builds, or mission execution.
- `high`: publish, deploy, PR, external side effects, or broad write authority.
- `critical`: production, irreversible, secret-bearing, or public/network promotion authority.

High and critical actions require explicit approval unless a future policy grants a narrowly scoped machine-origin exception.

## Surface Responsibilities

Surfaces submit evidence. They do not own authority.

- Telegram owns ingress, concise replies, and delivery.
- CLI owns install, health, provenance, sandbox, registry, and local operator commands.
- Builder owns context orchestration and domain reasoning.
- Spawner owns mission execution once authorized.
- Memory owns recall and durable belief mechanics, but memory is never instruction.
- Startup operator owns startup-quality benchmarks and venture reasoning lanes.
- Recursive/swarm owns experiments, not production mutation authority.
- Domain chips own scoped capability, not global routing.

## Context And Memory

- Raw private turns should be summarized and referenced, not sprayed into long context.
- Large tool outputs should be stored as artifacts and summarized back into the run.
- Memory may influence evidence and personalization, but must not override fresh user intent.
- Pending state expires as context, not authority.

## Observability

Every meaningful step must be inspectable:

- envelope
- candidate evidence
- selected move
- proposed action
- authorization decision
- tool lifecycle stage
- sanitized output
- run verdict
- readiness score
- change manifest

If Spark cannot explain why it acted, the run is not ready for promotion.

Readiness promotion requires performance and governance evidence as first-class
gates. A surface can be private-ready with zero high-agency legacy gates, but it
cannot be release-candidate or public-ready until `performance_budget_proven`
and `governance_rulesets_proven` are true.

## Self-Evolution

Self-evolution may improve prompts, tools, middleware, skills, specs, adapters, policies, and tests only through a `ChangeManifestV1`.

Self-evolution cannot mutate verifier logic, benchmark cases, model config, or authority policy without explicit human approval.

Every improvement must declare:

- failure evidence
- root-cause hypothesis
- target component
- predicted fixes
- predicted regression risks
- required tests
- live proof requirement
- rollback plan
- observed delta
- verdict

## Stop-Ship Gates

Do not ship or promote a surface when:

- high-agency action can run without envelope, authorization, ledger, and verdict
- a route-specific regex owns execution authority
- a legacy patch, fallback router, or adapter-local detector can bypass or fight the Governor
- memory or pending state overrides fresh user intent
- chat-only moves can carry proposed actions
- readiness lacks execution, tools, context, lifecycle, observability, verification, or governance evidence
- release-candidate readiness lacks a proven performance budget
- release-candidate readiness lacks proven repo-local governance rulesets
- self-evolution can alter its verifier, benchmark, model config, or authority policy without approval
