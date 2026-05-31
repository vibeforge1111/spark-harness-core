# Spark Harness Core

Spark Harness Core is the newborn authority kernel for Spark agent surfaces.

It is designed to govern Telegram, CLI, Builder, Spawner, memory, startup operator, recursive/swarm, voice, domain chips, PR/publish, public/network promotion, and future agentic repos through one contract set:

```text
model proposes -> Governor decides -> lifecycle executes -> ledger records -> evolution improves from evidence
```

## What Lives Here

- JSON Schemas for the authority envelope, capability registry, tool lifecycle, trace ledger, experience index, resources, surface specs, readiness scores, autonomy policy, eval packs, and self-evolution runs.
- A small Python kernel that can create and validate envelopes, authorization decisions, tool ledgers, and change manifests.
- Tests proving the contracts load, validate, and reject important authority failures.
- Documentation mapping the research and pasted notes into Spark's implementation plan.

## First Principle

Words alone never trigger action. Raw language can create evidence and proposals; only a validated `TurnIntentEnvelopeVNext` plus `AuthorizationDecisionV1` can authorize high-agency execution.

## Current Status

This is the first implementation slice: schemas plus a minimal kernel. Downstream adapters still need to consume these contracts before this becomes runtime authority.

## Quick Check

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
PYTHONPATH=src python3 -m spark_harness_core.cli validate-schemas
```
