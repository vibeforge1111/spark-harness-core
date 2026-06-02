# Spark Genesis Kernel Schema Design

Date: 2026-06-01

## Why This Kernel Exists

The prior Spark intent work hardened several surfaces, but it still left too many local actors capable of turning words into action. The new kernel replaces scattered authority with one portable contract system:

```text
surface evidence -> TurnIntentEnvelopeVNext -> AuthorizationDecisionV1 -> ToolCallLedgerV1 -> HarnessRunV1 -> ExperienceIndexV1 -> ChangeManifestV1
```

## Research And Notes Absorbed

The pasted notes reinforce the same architecture from three directions:

- Agentic Harness Engineering: expose every editable harness component as a file, store raw and distilled trajectories, and make each edit falsifiable through predicted fixes and predicted regression risks.
- Natural-Language Agent Harnesses: keep high-level harness logic as inspectable surface specs with roles, contracts, stages, adapters, state semantics, and failure taxonomy while code enforces tools, sandboxing, and validation.
- Meta-Harness: give the optimizer filesystem access to prior code, scores, traces, and failures instead of compressing experience into one prompt.
- Factory Droid-style harness practice: separate planning, execution, verification, autonomy levels, subagents, hooks, skills, least-privilege tools, readiness, and human approval.
- Safe harness practice: put filtering, verification, privilege, rollback, and adaptive degradation inside the lifecycle.

## Kernel Objects

- `TurnIntentEnvelopeVNext`: the only object allowed to promote raw language into a move such as `chat_explain`, `prepare_action`, `confirm_action`, or `execute_action`.
- `CapabilityModuleV1`: declares every tool, adapter, surface, agent, evaluator, memory store, and domain chip as a capability with owner, risk, inputs, outputs, and authority requirements.
- `AuthorizationDecisionV1`: records allow, deny, interrupt, or degrade verdicts with reasons, approval requirements, restrictions, and trace refs.
- `ToolCallLedgerV1`: tracks propose, validate, authorize, approve, execute, sanitize, store, summarize, continue, rollback, and fail stages.
- `HarnessRunV1`: records complete runs across surfaces, models, tools, metrics, artifacts, and final verdicts.
- `HarnessComponentV1`: makes prompts, tools, middleware, skills, subagents, memory, policies, hooks, evaluators, specs, and code components observable and editable.
- `ChangeManifestV1`: forces every harness improvement to name evidence, root cause, predicted fixes, predicted regressions, tests, rollback, observed delta, and verdict.
- `ResourceRegistryV1`: versions prompts, agents, tools, environments, memory stores, adapters, specs, eval packs, startup policies, and surface rules.
- `ExperienceIndexV1`: keeps raw traces, cleaned traces, screenshots, route decisions, tool ledgers, scores, diffs, and live evidence searchable without flooding context.
- `SurfaceSpecV1`: makes each surface executable as a natural-language harness spec under the shared runtime charter.
- `ReadinessScoreV1`: scores execution, tools, context, lifecycle, observability, verification, and governance before promotion, with explicit gates for live Telegram proof, startup benchmark proof, performance budget proof, governance ruleset proof, and legacy-plane retirement.
- `AutonomyPolicyV1`: defines risk tiers, autonomy levels, allow/deny rules, approvals, hooks, and headless constraints.
- `EvaluationPackV1`: packages route, tool, startup, live Telegram, regression, latency, cost, and blind-jury cases.
- `SelfEvolutionRunV1`: records the observe, distill, diagnose, manifest, patch, test, compare, promote/rollback loop.

## Non-Negotiables

- Normal conversation should not need defensive negation.
- High-agency action requires envelope, authorization, ledger, and verdict.
- Route-specific regex may submit evidence but cannot own authority.
- Memory, pending state, route history, provider names, and stale mission state are evidence only.
- Historical patches and legacy local detectors must be retired or demoted to
  evidence-only adapters; they cannot remain as fallback authority planes.
- Self-evolution cannot alter verifier, benchmark, model config, or authority policy without explicit approval.
- Every accepted improvement must preserve or improve authority correctness.

## First Integration Order

1. Integrate Telegram as a thin evidence adapter.
2. Integrate Spawner as a capability and mission-execution adapter.
3. Integrate Builder as the context and orchestration consumer.
4. Integrate memory as evidence, not instruction.
5. Integrate startup operator benchmarks and blind jury gates.
6. Integrate recursive/swarm experiments through self-evolution runs.
