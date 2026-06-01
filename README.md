# Spark Harness Core

Spark Harness Core is the newborn authority kernel for Spark agent surfaces.

It is designed to govern Telegram, CLI, Builder, Spawner, memory, startup operator, recursive/swarm, voice, domain chips, PR/publish, public/network promotion, and future agentic repos through one contract set:

```text
model proposes -> Governor decides -> lifecycle executes -> ledger records -> evolution improves from evidence
```

## What Lives Here

- JSON Schemas for the authority envelope, Governor decision, capability registry, tool lifecycle, trace ledger, experience index, resources, surface specs, readiness scores, autonomy policy, eval packs, and self-evolution runs.
- A small Python kernel that can create and validate envelopes, authorization decisions, Governor decisions, tool ledgers, resource registries, experience indexes, readiness scores, change manifests, and self-evolution run records.
- A private Node/TypeScript package face (`@spark/harness-core`) that exports the canonical VNext contract types and helper constructors for Spark adapters.
- Tests proving the contracts load, validate, and reject important authority failures.
- Documentation mapping the research and pasted notes into Spark's implementation plan.

## Core Docs

- [Runtime Charter](docs/RUNTIME_CHARTER.md)
- [Telegram First Integration Plan](docs/TELEGRAM_FIRST_INTEGRATION_PLAN.md)
- [Kernel Schema Design](docs/SPARK_GENESIS_KERNEL_SCHEMA_DESIGN.md)

## First Principle

Words alone never trigger action. Raw language can create evidence and proposals; only a validated `TurnIntentEnvelopeVNext`, `AuthorizationDecisionV1`, and `GovernorDecisionV1` can authorize high-agency execution.

## Current Status

This is still an early implementation slice, but the core now owns the Python schema/kernel path, the TypeScript contract surface used by Telegram, and the first operating-record CLI for harness promotion evidence. Downstream adapters still need deeper migration before this becomes the only runtime authority.

## Operating Records

The kernel can now emit and validate the records Spark needs before promoting a harness change:

- `resource-registry-v1`: declares prompts, tools, agents, specs, adapters, policies, memory stores, eval packs, and surface rules as versioned resources.
- `governor-decision-v1`: binds one envelope, authorization set, optional ledgers, execution boundary, and reply contract into the canonical route outcome every Spark surface must consume.
- `experience-index-v1`: points to traces, screenshots, tool ledgers, scorecards, diffs, and live proof without flooding the live model context.
- `readiness-score-v1`: scores execution, tools, context, lifecycle, observability, verification, and governance, then derives blocked, private-ready, release-candidate, or public-ready status from evidence and gates.
- `change-manifest-v1`: records evidence, root cause, predicted fixes, regression risks, required tests, rollback, observed delta, and verdict. Protected components such as verifiers, benchmarks, model config, and authority policy require explicit human approval evidence.
- `self-evolution-run-v1`: ties experience, target components, manifests, eval packs, commands, readiness, and promotion verdict into one auditable run.
- `spark.telegram_live_qa_evidence_packet.v1`: records the 100-prompt Telegram live QA container with observed replies, side-effect checks, ledger/trace/screenshot refs, session evidence, verdicts, and release claim boundary.

## Quick Check

```bash
npm install
npm run build
PYTHONPATH=src python3 -m unittest discover -s tests
PYTHONPATH=src python3 -m spark_harness_core.cli validate-schemas
PYTHONPATH=src python3 -m spark_harness_core.cli resource-registry
PYTHONPATH=src python3 -m spark_harness_core.cli governor-decision
PYTHONPATH=src python3 -m spark_harness_core.cli experience-index
PYTHONPATH=src python3 -m spark_harness_core.cli telegram-live-qa-packet --include-risky
PYTHONPATH=src python3 -m spark_harness_core.cli readiness-score --category execution=1 --category tools=1 --category context=1 --category lifecycle=1 --category observability=1 --category verification=1 --category governance=1 --gate zero_high_agency_legacy_local_gates=true
PYTHONPATH=src python3 -m spark_harness_core.cli self-evolution-run
```
