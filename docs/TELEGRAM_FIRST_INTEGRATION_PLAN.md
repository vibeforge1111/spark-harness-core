# Telegram First Integration Plan

Date: 2026-06-01

## Purpose

Telegram is the first live surface to integrate with Spark Harness Core because it has shown the hardest real-world failure class: ordinary conversation containing action words can be mistaken for execution intent.

The integration target:

```text
Telegram message -> evidence refs -> TurnIntentEnvelopeVNext -> AuthorizationDecisionV1 -> human reply or authorized action
```

## Owner Repos

- Kernel owner: `spark-harness-core`
- First adapter owner: `spark-telegram-bot`
- Spawner consumer: `spawner-ui`
- Context/orchestration consumer: `spark-intelligence-builder`
- Private doctrine mirror: `spark-intelligence-systems`

## Architecture Decision

Telegram should remain thin.

It should:

- summarize the fresh turn
- emit evidence refs
- ask the Governor for the selected move and authority state
- render human replies
- pass authorized execution to owner capabilities

It should not:

- launch missions from local keyword checks
- write memory from local message parsing
- publish, deploy, schedule, or open PRs from route text
- let pending state or stale route history seize the turn
- fork a separate authority model

## First Code Slice

1. Add a Telegram-side harness adapter that creates `TurnIntentEnvelopeVNext` shaped objects.
2. Keep existing Telegram intent detectors as evidence producers only.
3. Add a compatibility layer that maps current route outcomes into envelope moves.
4. Gate Spawner, memory write, PR/publish, schedule, and domain-chip actions behind authorization.
5. Preserve existing positive explicit commands by allowing `prepare_action`, `confirm_action`, and `execute_action` when evidence is strong.
6. Keep normal chat useful without requiring the user to say defensive phrases.

## Contract Tests

Add tests for:

- action words inside bug reports stay `chat_explain`
- quoted commands stay conversational
- startup planning without execution stays `chat_plan`
- no-edit Spawner probe can become `execute_action`
- explicit build/run mission can become `prepare_action` or `execute_action`
- memory recall cannot become instruction
- pending mission state cannot hijack a fresh unrelated turn
- high-risk publish/PR/deploy returns `interrupt` without approval
- chat-only moves reject proposed actions
- every executed action writes a tool ledger

## Live Telegram Proof

Before calling this integrated:

1. Send 20 negative/meta prompts containing action words.
2. Send 10 positive explicit action prompts.
3. Send 5 stale/pending-state prompts.
4. Send 5 startup-operator prompts.
5. Confirm no unexpected mission, memory write, PR, publish, deploy, schedule, or chip action fires.
6. Confirm explicit authorized probes still work.

This is the small live proof. The larger 100-message and 350-case QA packs should run after the first integration is locally clean.

## Stop Conditions

Stop and fix before continuing if:

- Telegram can execute from words without a valid envelope
- an existing local detector bypasses authorization
- user-facing replies become rigid or defensive
- positive explicit actions stop working
- the adapter requires private raw chat text to leave Telegram when metadata would do
- tests pass only at helper level while the top-level message path fails

