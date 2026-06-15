# Spark Harness Core

Spark Harness Core is the newborn authority kernel for Spark agent surfaces.

It is designed to govern Telegram, CLI, Builder, Spawner, memory, startup operator, recursive/swarm, voice, domain chips, PR/publish, public/network promotion, and future agentic repos through one contract set:

```text
model proposes -> Governor decides -> lifecycle executes -> ledger records -> evolution improves from evidence
```

## What Lives Here

- JSON Schemas for the authority envelope, signed Governor decision, consumer verification, capability registry, tool lifecycle, trace ledger, experience index, resources, surface specs, readiness scores, autonomy policy, eval packs, and self-evolution runs.
- A small Python kernel that can create and validate envelopes, authorization decisions, Governor decisions, signed decision payloads, consumer-verification verdicts, tool ledgers, bound ledger rows, resource registries, experience indexes, readiness scores, change manifests, change-manifest runner decisions, and self-evolution run records.
- A private Node/TypeScript package face (`@spark/harness-core`) that exports the canonical VNext contract types, signing helpers, verification helpers, and bound-ledger-row constructors for Spark adapters.
- Tests proving the contracts load, validate, and reject important authority failures.
- Documentation mapping the research and pasted notes into Spark's implementation plan.

## Core Docs

- [Runtime Charter](docs/RUNTIME_CHARTER.md)
- [Consumer Integration Guide](docs/CONSUMER_INTEGRATION_GUIDE.md)
- [Telegram First Integration Plan](docs/TELEGRAM_FIRST_INTEGRATION_PLAN.md)
- [Kernel Schema Design](docs/SPARK_GENESIS_KERNEL_SCHEMA_DESIGN.md)

## First Principle

Words alone never trigger action. Raw language can create evidence and proposals; only a validated `TurnIntentEnvelopeVNext`, `AuthorizationDecisionV1`, and `GovernorDecisionV1` can authorize high-agency execution.

## Current Status

The core now owns the Python schema/kernel path, the TypeScript contract surface used by Spark adapters, signed Governor decision contracts, consumer-verification records, and the bound ledger-row helper used by Builder's canonical observability table. Downstream adapters still need full publish-path migration before this becomes the only runtime authority everywhere.

## Operating Records

The kernel can now emit and validate the records Spark needs before promoting a harness change:

- `common-v1`: shared definitions used by the other schemas; not a standalone proof object.
- `turn-intent-envelope-vnext`: records fresh-turn evidence, selected move, proposed actions, blocked routes, and freshness policy.
- `authorization-decision-v1`: records allow, deny, interrupt, or degrade verdicts for a proposed action.
- `tool-call-ledger-v1`: records the tool lifecycle and result proof; it is evidence, not permission.
- `governor-consumer-verification-v1`: proves a consuming owner route verified the Governor decision, authorization, action, capability, tool, and ledger it expected.
- `capability-module-v1`: declares tools, adapters, surfaces, and domain capabilities with owner, risk, inputs, outputs, and authority requirements.
- `surface-spec-v1`: records surface-specific harness behavior and evidence requirements.
- `autonomy-policy-v1`: records autonomy/risk policy as policy evidence; it is not a parallel router.
- `harness-component-v1`: records editable harness components, owners, surfaces, risks, and rollback refs.
- `resource-registry-v1`: declares prompts, tools, agents, specs, adapters, policies, memory stores, eval packs, and surface rules as versioned resources.
- `governor-decision-v1`: binds one envelope, authorization set, optional ledgers, execution boundary, and reply contract into the canonical route outcome every Spark surface must consume. Decisions may carry a nonce-backed HMAC signature envelope when a surface has a shared governor key.
- `governor-consumer-verification-v1`: records the consuming surface's fail-closed verification of the Governor decision against expected action, capability, tool, authorization, and ledger ids.
- `bound_ledger_row` / `boundLedgerRow`: flattens a validated tool ledger plus consumer-verification verdict into the shared `tool_call_ledger` row shape.
- `consumer_conformance`: runnable doc 30 consumer checklist for CI. Green means propose, decision-through, envelope-bound execution, all-exit finalization, refusal surfacing, attested ledger location, expiry, signatures, and fail-closed behavior are all present.
- `experience-index-v1`: points to traces, screenshots, tool ledgers, scorecards, diffs, and live proof without flooding the live model context.
- `readiness-score-v1`: scores execution, tools, context, lifecycle, observability, verification, and governance, then derives blocked, private-ready, release-candidate, or public-ready status from evidence and gates.
- `change-manifest-v1`: records evidence, root cause, predicted fixes, regression risks, required tests, rollback, observed delta, and verdict. Protected components such as verifiers, benchmarks, model config, and authority policy require explicit human approval evidence for mutation.
- `change-manifest-runner`: evaluates accepted manifests, readiness, live-proof requirements, rollback state, and protected-component approval before emitting a `self-evolution-run-v1` promotion decision. It records `not_ready` instead of mutating when evidence is missing.
- `self-evolution-run-v1`: ties experience, target components, manifests, eval packs, commands, readiness, and promotion verdict into one auditable run.
- `harness-run-v1`: records a complete run across surfaces, models, tools, metrics, artifacts, and verdicts.
- `evaluation-pack-v1`: packages route, tool, startup, live, regression, latency, cost, and blind-jury cases.
- `legacy-authority-plane-v1`: records one old authority plane and its disposition.
- `legacy-authority-inventory-v1`: records the repo-wide inventory of old authority planes and release blockers.
- `spark.telegram_live_qa_evidence_packet.v1`: records the 100-prompt Telegram live QA container with observed replies, side-effect checks, ledger/trace/screenshot refs, session evidence, verdicts, and release claim boundary.

## Quick Check

```bash
npm install
npm run build
PYTHONPATH=src python3 -m pytest tests/test_kernel_contracts.py tests/test_typescript_contracts.py -q
PYTHONPATH=src python3 -m spark_harness_core.cli validate-schemas
PYTHONPATH=src python3 -m spark_harness_core.cli resource-registry
PYTHONPATH=src python3 -m spark_harness_core.cli governor-decision
PYTHONPATH=src python3 -m spark_harness_core.consumer_conformance --fixture good
PYTHONPATH=src python3 -m spark_harness_core.cli experience-index
PYTHONPATH=src python3 -m spark_harness_core.cli telegram-live-qa-packet --include-risky
PYTHONPATH=src python3 -m spark_harness_core.cli readiness-score --category execution=1 --category tools=1 --category context=1 --category lifecycle=1 --category observability=1 --category verification=1 --category governance=1 --gate zero_high_agency_legacy_local_gates=true
PYTHONPATH=src python3 -m spark_harness_core.cli change-manifest-runner
PYTHONPATH=src python3 -m spark_harness_core.cli self-evolution-run
```
