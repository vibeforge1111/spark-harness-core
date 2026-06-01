# Spark Harness Core

Spark Harness Core is the newborn authority kernel for Spark agent surfaces.

It is designed to govern Telegram, CLI, Builder, Spawner, memory, startup operator, recursive/swarm, voice, domain chips, PR/publish, public/network promotion, and future agentic repos through one contract set:

```text
model proposes -> Governor decides -> lifecycle executes -> ledger records -> evolution improves from evidence
```

## What Lives Here

- JSON Schemas for the authority envelope, capability registry, tool lifecycle, trace ledger, experience index, resources, surface specs, readiness scores, autonomy policy, eval packs, and self-evolution runs.
- A small Python kernel that can create and validate envelopes, authorization decisions, tool ledgers, and change manifests.
- A private Node/TypeScript package face (`@spark/harness-core`) that exports the canonical VNext contract types and helper constructors for Spark adapters.
- Tests proving the contracts load, validate, and reject important authority failures.
- Documentation mapping the research and pasted notes into Spark's implementation plan.

## Core Docs

- [Runtime Charter](docs/RUNTIME_CHARTER.md)
- [Telegram First Integration Plan](docs/TELEGRAM_FIRST_INTEGRATION_PLAN.md)
- [Kernel Schema Design](docs/SPARK_GENESIS_KERNEL_SCHEMA_DESIGN.md)

## First Principle

Words alone never trigger action. Raw language can create evidence and proposals; only a validated `TurnIntentEnvelopeVNext` plus `AuthorizationDecisionV1` can authorize high-agency execution.

## Current Status

This is still an early implementation slice, but the core now owns the Python schema/kernel path and the TypeScript contract surface used by Telegram. Downstream adapters still need deeper migration before this becomes the only runtime authority.

## Quick Check

```bash
npm install
npm run build
PYTHONPATH=src python3 -m unittest discover -s tests
PYTHONPATH=src python3 -m spark_harness_core.cli validate-schemas
```
