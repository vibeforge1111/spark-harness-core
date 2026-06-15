# Harness Core Consumer Integration Guide

This guide is the blessed path for adding Spark Harness Core to a consumer.
Use the SDK helpers. Do not hand-roll the primitive sequence in application
code.

The reference pattern is the Telegram to Spawner PRD write chain:

1. A surface turns fresh user intent into a `TurnIntentEnvelopeVNext`.
2. The producer creates a Governor decision with a pre-execution ledger.
3. The consumer verifies that decision against the exact tool, action type, and
   capability it is about to run.
4. The consumer executes only inside the governed SDK wrapper.
5. The SDK finalizes the ledger on success and on exception.
6. Refusals surface as refusals with reason codes, not generic errors.

## Install And Build

From this repository:

```bash
npm install
npm run build
python -m pytest tests/test_kernel_contracts.py tests/test_typescript_contracts.py -q
```

For a Spark repo, consume the pinned mirror or the vendored package already
checked into that repo. Do not copy individual helper functions into the
consumer.

## TypeScript Consumer

This is the worked Spawner-style pattern. It creates one governed dispatch,
verifies the decision, executes inside `withGovernedTurn`, and finalizes the
ledger even if the body throws.

```ts
import {
  createHarnessCoreActionEnvelopeVNext,
  createHarnessCoreAuthorizedGovernorDecision,
  withGovernedTurn
} from '@spark/harness-core';

const envelope = createHarnessCoreActionEnvelopeVNext({
  surface: 'spawner',
  ownerSystem: 'spawner-ui',
  toolName: 'spawner.dispatch',
  mutationClass: 'launches_mission',
  source: 'telegram',
  reason: 'User asked Spark to dispatch a mission.',
  requestId: 'dispatch-request-123'
});

const governorDecision = createHarnessCoreAuthorizedGovernorDecision({
  envelope,
  tool_name: 'spawner.dispatch',
  restrictions: {
    network_allowed: false,
    write_allowed: true,
    publish_allowed: false
  }
});

await withGovernedTurn(
  {
    governor_decision: governorDecision,
    tool_name: 'spawner.dispatch',
    owner_system: 'spawner-ui',
    action_type: 'launch_mission',
    success_summary: 'Spawner dispatch completed.',
    failure_summary: 'Spawner dispatch failed.'
  },
  async (turn) => {
    const mission = await dispatchMission();
    turn.finalize({
      status: 'success',
      summary: 'Spawner dispatch completed.',
      output_path_or_uri: `spawner://missions/${mission.id}/result`
    });
    return mission;
  }
);
```

Dry-run uses the same path and skips the execution callback:

```ts
await withGovernedTurn(
  {
    governor_decision: governorDecision,
    tool_name: 'spawner.dispatch',
    owner_system: 'spawner-ui',
    action_type: 'launch_mission',
    dry_run: true,
    dry_run_summary: 'Dry-run dispatch skipped the spawner call.'
  },
  async () => {
    throw new Error('This callback is not called in dry-run mode.');
  }
);
```

## Python Consumer

Use the high-level context manager once you have a Governor decision. The body
must still respect `turn.should_execute`; Python context managers cannot skip a
caller body for you.

```py
from spark_harness_core import HarnessKernel, evidence_ref, governed_turn

kernel = HarnessKernel(surface="spawner", actor_id_ref="human:test")
action = kernel.proposed_action(
    capability_id="capability:spawner-ui:spawner.dispatch",
    action_type="launch_mission",
    risk_tier="low",
    summary="Dispatch a prepared mission.",
    args_path="spawner://missions/dispatch-request-123/args",
    requires_confirmation=False,
)
envelope = kernel.create_envelope(
    selected_move="execute_action",
    intent_summary="User asked Spark to dispatch a mission.",
    raw_turn_summary="Telegram dispatch request summarized without raw text.",
    proposed_actions=[action],
    authority_state="executable",
    risk_tier="low",
    confidence=0.95,
    evidence=[
        evidence_ref(
            "fresh_user_intent",
            "telegram",
            "User explicitly asked Spark to dispatch this mission.",
        )
    ],
)
authorization = kernel.authorize(envelope, action)
ledger = kernel.record_tool_call(
    envelope=envelope,
    action=action,
    authorization=authorization,
    tool_name="spawner.dispatch",
    status="not_started",
    output_path="spawner://missions/dispatch-request-123/pending",
    summary="Spawner dispatch is authorized and waiting to execute.",
)
governor_decision = kernel.governor_decision(
    envelope,
    authorizations=[authorization],
    tool_ledgers=[ledger],
)

with governed_turn(
    governor_decision=governor_decision,
    kernel=kernel,
    tool_name="spawner.dispatch",
    owner_system="spawner-ui",
    action_type="launch_mission",
    success_summary="Spawner dispatch completed.",
    failure_summary="Spawner dispatch failed.",
) as turn:
    if turn.should_execute:
        mission_id = "mission:dispatch-request-123"
        turn.finalize(
            status="success",
            summary="Spawner dispatch completed.",
            output_path=f"spawner://missions/{mission_id}/result",
        )
```

Dry-run:

```py
with governed_turn(
    governor_decision=governor_decision,
    kernel=kernel,
    tool_name="spawner.dispatch",
    owner_system="spawner-ui",
    action_type="launch_mission",
    dry_run=True,
    dry_run_summary="Dry-run dispatch skipped the spawner call.",
) as turn:
    assert not turn.should_execute
    assert turn.finalized_ledger["simulation"]["dry_run"] is True
```

## Refusal Handling

Every consumer must render Harness refusals as refusals. A refused PRD write
should not become "spawner error" or "bridge error". Preserve the reason codes
from the verification result or authority exception and show a compact refusal
message at the operator surface.

Recommended HTTP shape:

```json
{
  "code": "harness_authority_blocked",
  "reason_codes": ["governor_missing_matching_tool_ledger"],
  "message": "Harness authority refused this action before execution."
}
```

## Warning Boxes

> Warning: Do not call low-level `authorize` plus `record_tool_call` directly in
> consumer code. Use the SDK wrapper or the authorized Governor helper. The old
> primitive path is where non-proposed actions and instant-success ledgers came
> from.

> Warning: Do not execute when `governor_decision` is missing. The correct SDK
> wrappers refuse construction without one. Treat a missing decision as a
> refusal, not as a degraded local permission check.

> Warning: Do not persist only the pre-execution row. Finalize the ledger on
> every success and every exception. A permanent `not_started` row is stranded
> evidence, not proof of execution.

> Warning: Do not swallow ledger ingest failures in a live mutation path. If the
> action executed but the attested ledger did not persist, the run is not fully
> governed.

> Warning: Do not strip reason codes at the user boundary. Operators need to see
> whether the refusal was missing authority, expired authority, signature
> failure, or a ledger mismatch.

> Warning: Do not depend on unsigned decisions once a stack key is configured.
> Pass the Governor HMAC key and require signatures in armed environments.

> Warning: Do not copy vendored Harness Core artifacts by hand without a checksum
> or manifest update. Silent stale vendors are worse than an import failure.

## One-Hour Checklist

Use this checklist for a new consumer. A cold reader should be able to complete
it without reading Harness Core source.

1. Import the SDK from the pinned mirror or vendored package.
2. Build the envelope with fresh user intent evidence.
3. Create the Governor decision with the SDK helper.
4. Verify and execute only through `governed_turn` or `withGovernedTurn`.
5. Finalize success and exception paths.
6. Persist the final ledger to the consumer's attested location.
7. Render refusal reason codes at the user or operator surface.
8. Add the consumer conformance kit to CI.
9. Add one dry-run test that proves the action body does not execute.

## Verification

A minimal integration is acceptable only when the good fixture exits 0, the
broken fixture exits 1 with at least one failed check, and the dry-run tests
pass:

```bash
python -m spark_harness_core.consumer_conformance --fixture good
python -m spark_harness_core.consumer_conformance --fixture broken  # expected exit 1
python -m pytest tests/test_kernel_contracts.py::KernelContractTests::test_governed_turn_dry_run_marks_artifacts_and_skips_execution -q
python -m pytest tests/test_typescript_contracts.py::TypeScriptContractTests::test_with_governed_turn_dry_run_skips_callback_and_marks_artifacts -q
```

The `good` fixture must pass. The `broken` fixture must fail at least one check,
proving the kit catches integration drift.
