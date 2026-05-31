# Spark Harness Core Agent Rules

This repo owns the newborn Spark harness kernel: authority envelopes, tool lifecycle contracts, resource/version registries, experience ledgers, readiness scoring, and the self-evolution protocol.

## Authority

- The Governor is the only component that converts raw language into high-agency authority.
- Surface adapters, route matchers, memory, pending state, provider names, domain chips, and local classifiers may submit evidence; they must not execute from words alone.
- High-agency actions require a validated envelope, an authorization decision, a ledger entry, and a result verdict.
- Normal conversation must remain useful without requiring defensive phrasing from the user.

## Design

- Schemas are the public contract; code is the enforcement kernel.
- Every schema must be language-neutral and usable by Telegram, CLI, Builder, Spawner, memory, startup operator, recursive/swarm, voice, domain chips, and future Spark repos.
- Keep deterministic mechanics explicit: validation, authorization, risk tiering, hooks, state, traces, resource versions, rollback, and verification.
- Keep model judgment inside bounded decisions with observable evidence and confidence.
- Do not put secrets, raw private prompts, raw account ids, provider payloads, or unredacted transcripts in fixtures, docs, traces, or schemas.

## Evolution

- Self-evolution can propose harness edits only through a change manifest.
- Self-evolution cannot mutate verifier logic, benchmark cases, model config, or authority policy without explicit human approval.
- Every improvement must declare predicted fixes, predicted regression risks, required tests, rollback plan, observed delta, and verdict.
- Failed or regressive edits must be reversible at file/component level.

## Testing

- Run schema validation and kernel tests before claiming this repo is ready for integration.
- Add negative tests for authority escalation, word hijack, missing approval, missing trace, invalid resources, and unscored readiness categories.
- Treat test fixtures as contracts that downstream Spark repos can implement against.

