from __future__ import annotations

import argparse
import json
from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from spark_harness_core.governor_signature import sign_governor_decision
from spark_harness_core.kernel import HarnessKernel
from spark_harness_core.sdk import governed_turn


CONFORMANCE_CHECKLIST: tuple[tuple[str, str], ...] = (
    ("propose", "proposes before executing"),
    ("decision_through", "governor decision obtained and passed"),
    ("envelope_bound", "executes only within envelope"),
    ("finalize_all_paths", "records and finalizes on all exits"),
    ("refusal_surfacing", "refusals surfaced as refusals"),
    ("attested_ledger", "ledger written to an attested location"),
    ("expiry", "authorization expiry is set and respected"),
    ("signatures", "governor signatures are verified"),
    ("fail_closed", "harness unavailable fails closed"),
)

ACTION_CAPABILITY_ID = "capability:toy-consumer:artifact.write"
ACTION_TYPE = "edit_file"
TOOL_NAME = "toy_consumer.artifact.write"
SIGNATURE_KEY = "consumer-conformance-test-key"
SIGNATURE_KEY_ID = "consumer-ci"
CONFORMANCE_NOW = "2026-06-10T12:00:00Z"
CONFORMANCE_EXPIRES_AT = "2030-01-01T00:00:00Z"
EXPIRED_AT = "2026-06-10T11:59:59Z"


@dataclass
class ConsumerConformanceArtifacts:
    envelope: dict[str, Any]
    governor_decision: dict[str, Any]
    verification: dict[str, Any]
    success_ledger: dict[str, Any] | None
    failure_ledger: dict[str, Any] | None
    refusal_verification: dict[str, Any]
    refusal_ledger: dict[str, Any] | None
    ledger_location: str
    ledger_location_attested: bool
    expired_verification: dict[str, Any]
    signed_verification: dict[str, Any]
    tampered_signature_verification: dict[str, Any]
    harness_unavailable_result: dict[str, Any]


def build_toy_consumer_artifacts(*, broken: str | None = None) -> ConsumerConformanceArtifacts:
    kernel = HarnessKernel(surface="test_harness", actor_id_ref="human:conformance")
    envelope, action, authorization, ledger = _build_authorized_turn(kernel, expires_at=CONFORMANCE_EXPIRES_AT)
    governor_decision = kernel.governor_decision(envelope, authorizations=[authorization], tool_ledgers=[ledger])
    signed_decision = sign_governor_decision(
        governor_decision,
        key=SIGNATURE_KEY,
        key_id=SIGNATURE_KEY_ID,
        nonce="consumer-conformance-nonce",
        created_at=CONFORMANCE_NOW,
    )
    verification = _verify(kernel, signed_decision)

    success_turn = governed_turn(
        governor_decision=signed_decision,
        tool_name=TOOL_NAME,
        action_type=ACTION_TYPE,
        expected_capability_id=ACTION_CAPABILITY_ID,
        kernel=kernel,
        governor_hmac_key=SIGNATURE_KEY,
        governor_hmac_key_id=SIGNATURE_KEY_ID,
        require_signature=True,
        now=CONFORMANCE_NOW,
        success_output_path="harness-core://consumer-ci/toy-consumer/success.json",
    )
    with success_turn:
        pass

    failure_turn = governed_turn(
        governor_decision=signed_decision,
        tool_name=TOOL_NAME,
        action_type=ACTION_TYPE,
        expected_capability_id=ACTION_CAPABILITY_ID,
        kernel=kernel,
        governor_hmac_key=SIGNATURE_KEY,
        governor_hmac_key_id=SIGNATURE_KEY_ID,
        require_signature=True,
        now=CONFORMANCE_NOW,
        failure_output_path="harness-core://consumer-ci/toy-consumer/failure.json",
        error_path="harness-core://consumer-ci/toy-consumer/error.json",
    )
    try:
        with failure_turn:
            raise RuntimeError("toy consumer failed after authority passed")
    except RuntimeError:
        pass

    refusal_envelope, refusal_action, refusal_authorization = _build_refused_turn(kernel)
    refusal_ledger = kernel.record_refusal(
        envelope=refusal_envelope,
        action=refusal_action,
        authorization=refusal_authorization,
        tool_name=TOOL_NAME,
        output_path="harness-core://consumer-ci/toy-consumer/refusal.json",
    )
    refusal_decision = kernel.governor_decision(
        refusal_envelope,
        authorizations=[refusal_authorization],
        tool_ledgers=[refusal_ledger],
    )
    refusal_verification = kernel.verify_governor_execution_authority(
        refusal_decision,
        expected_capability_id=ACTION_CAPABILITY_ID,
        expected_action_type=ACTION_TYPE,
        tool_name=TOOL_NAME,
        now=CONFORMANCE_NOW,
    )

    expired_envelope, _, expired_authorization, expired_ledger = _build_authorized_turn(kernel, expires_at=EXPIRED_AT)
    expired_decision = kernel.governor_decision(
        expired_envelope,
        authorizations=[expired_authorization],
        tool_ledgers=[expired_ledger],
    )
    expired_verification = kernel.verify_governor_execution_authority(
        expired_decision,
        expected_capability_id=ACTION_CAPABILITY_ID,
        expected_action_type=ACTION_TYPE,
        tool_name=TOOL_NAME,
        now=CONFORMANCE_NOW,
    )

    tampered_decision = deepcopy(signed_decision)
    tampered_decision["tool_ledgers"][0]["action_id"] = "action:tampered-after-signature"
    tampered_signature_verification = _verify(kernel, tampered_decision)

    artifacts = ConsumerConformanceArtifacts(
        envelope=envelope,
        governor_decision=signed_decision,
        verification=verification,
        success_ledger=success_turn.finalized_ledger,
        failure_ledger=failure_turn.finalized_ledger,
        refusal_verification=refusal_verification,
        refusal_ledger=refusal_ledger,
        ledger_location="harness-core://consumer-ci/toy-consumer/tool_call_ledger.jsonl",
        ledger_location_attested=True,
        expired_verification=expired_verification,
        signed_verification=verification,
        tampered_signature_verification=tampered_signature_verification,
        harness_unavailable_result=_simulate_harness_unavailable(),
    )
    return _break_artifacts(artifacts, broken)


def run_consumer_conformance(artifacts: ConsumerConformanceArtifacts) -> dict[str, Any]:
    checks = [
        _check("propose", _check_propose_before_execute(artifacts), "success ledger preserves propose -> authorize -> execute"),
        _check("decision_through", _check_decision_through(artifacts), "consumer verification allowed the Governor decision"),
        _check("envelope_bound", _check_envelope_bound(artifacts), "ledger action is one proposed by the envelope"),
        _check("finalize_all_paths", _check_finalize_all_paths(artifacts), "success and exception paths are terminal"),
        _check("refusal_surfacing", _check_refusal_surfacing(artifacts), "denied action is surfaced as a refusal"),
        _check("attested_ledger", _check_attested_ledger(artifacts), "ledger location is explicitly attested"),
        _check("expiry", _check_expiry(artifacts), "expired authorization is refused"),
        _check("signatures", _check_signatures(artifacts), "valid signature passes and tampering fails"),
        _check("fail_closed", _check_fail_closed(artifacts), "missing harness authority refuses execution"),
    ]
    passed = all(bool(item["passed"]) for item in checks)
    return {
        "suite": "spark-harness-core-consumer-conformance",
        "passed": passed,
        "checks": checks,
    }


def _build_authorized_turn(
    kernel: HarnessKernel,
    *,
    expires_at: str,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    action = kernel.proposed_action(
        capability_id=ACTION_CAPABILITY_ID,
        action_type=ACTION_TYPE,
        risk_tier="low",
        summary="Write a toy consumer artifact.",
        args_path="harness-core://consumer-ci/toy-consumer/args.json",
        requires_confirmation=False,
    )
    envelope = kernel.create_envelope(
        selected_move="execute_action",
        intent_summary="User explicitly asked the toy consumer to write a CI artifact.",
        raw_turn_summary="Write the conformance artifact.",
        proposed_actions=[action],
        authority_state="executable",
        risk_tier="low",
        confidence=0.96,
    )
    authorization = kernel.authorize(envelope, action)
    authorization["expires_at"] = expires_at
    ledger = kernel.record_tool_call(
        envelope=envelope,
        action=action,
        authorization=authorization,
        tool_name=TOOL_NAME,
        status="not_started",
        output_path="harness-core://consumer-ci/toy-consumer/pending.json",
        summary="Toy consumer artifact is authorized and waiting to execute.",
    )
    ledger["authorization"]["expires_at"] = expires_at
    return envelope, action, authorization, ledger


def _build_refused_turn(kernel: HarnessKernel) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    action = kernel.proposed_action(
        capability_id=ACTION_CAPABILITY_ID,
        action_type=ACTION_TYPE,
        risk_tier="high",
        summary="Request a high-risk toy consumer write that requires approval.",
        args_path="harness-core://consumer-ci/toy-consumer/refused-args.json",
        requires_confirmation=True,
    )
    envelope = kernel.create_envelope(
        selected_move="confirm_action",
        intent_summary="User asked for a high-risk write that needs approval before execution.",
        raw_turn_summary="Request confirmation for the high-risk conformance artifact write.",
        proposed_actions=[action],
        authority_state="confirmation_required",
        risk_tier="high",
        confidence=0.7,
        requires_human_confirmation=True,
    )
    return envelope, action, kernel.authorize(envelope, action)


def _verify(kernel: HarnessKernel, decision: dict[str, Any]) -> dict[str, Any]:
    return kernel.verify_governor_execution_authority(
        decision,
        expected_capability_id=ACTION_CAPABILITY_ID,
        expected_action_type=ACTION_TYPE,
        tool_name=TOOL_NAME,
        governor_hmac_key=SIGNATURE_KEY,
        governor_hmac_key_id=SIGNATURE_KEY_ID,
        require_signature=True,
        now=CONFORMANCE_NOW,
    )


def _simulate_harness_unavailable() -> dict[str, Any]:
    return {
        "allowed": False,
        "reason_codes": ["spark_harness_core_unavailable"],
        "surface": "test_harness",
    }


def _break_artifacts(
    artifacts: ConsumerConformanceArtifacts,
    broken: str | None,
) -> ConsumerConformanceArtifacts:
    if broken is None:
        return artifacts
    broken_artifacts = deepcopy(artifacts)
    if broken == "finalize_all_paths":
        broken_artifacts.failure_ledger = None
    elif broken == "attested_ledger":
        broken_artifacts.ledger_location = "tool_call_ledger.jsonl"
        broken_artifacts.ledger_location_attested = False
    else:
        raise ValueError(f"unknown broken fixture: {broken}")
    return broken_artifacts


def _check(check_id: str, passed: bool, detail: str) -> dict[str, Any]:
    name = dict(CONFORMANCE_CHECKLIST)[check_id]
    return {"id": check_id, "name": name, "passed": bool(passed), "detail": detail}


def _check_propose_before_execute(artifacts: ConsumerConformanceArtifacts) -> bool:
    ledger = artifacts.success_ledger or {}
    lifecycle = [str(item.get("stage") or "") for item in ledger.get("lifecycle", []) if isinstance(item, dict)]
    return lifecycle[:3] == ["propose", "authorize", "execute"] and bool(artifacts.envelope.get("proposed_actions"))


def _check_decision_through(artifacts: ConsumerConformanceArtifacts) -> bool:
    verification = artifacts.verification
    return bool(verification.get("allowed")) and verification.get("decision_id") == artifacts.governor_decision.get("decision_id")


def _check_envelope_bound(artifacts: ConsumerConformanceArtifacts) -> bool:
    ledger = artifacts.success_ledger or {}
    proposed = {
        (str(action.get("action_id") or ""), str(action.get("capability_id") or ""))
        for action in artifacts.envelope.get("proposed_actions", [])
        if isinstance(action, dict)
    }
    return (
        (str(ledger.get("action_id") or ""), str(ledger.get("capability_id") or "")) in proposed
        and ledger.get("tool_name") == TOOL_NAME
        and artifacts.verification.get("tool_name") == TOOL_NAME
    )


def _check_finalize_all_paths(artifacts: ConsumerConformanceArtifacts) -> bool:
    success = artifacts.success_ledger or {}
    failure = artifacts.failure_ledger or {}
    return success.get("result", {}).get("status") == "success" and failure.get("result", {}).get("status") == "failure"


def _check_refusal_surfacing(artifacts: ConsumerConformanceArtifacts) -> bool:
    refusal = artifacts.refusal_ledger or {}
    verification = artifacts.refusal_verification
    return (
        verification.get("allowed") is False
        and any(str(reason).startswith("governor_outcome_") for reason in (verification.get("reason_codes") or []))
        and refusal.get("authorization", {}).get("verdict") in {"deny", "interrupt"}
        and "refused" in str(refusal.get("result", {}).get("summary") or "").lower()
    )


def _check_attested_ledger(artifacts: ConsumerConformanceArtifacts) -> bool:
    location = str(artifacts.ledger_location or "")
    return bool(artifacts.ledger_location_attested) and (
        location.startswith("harness-core://") or "/.spark/" in location.replace("\\", "/")
    )


def _check_expiry(artifacts: ConsumerConformanceArtifacts) -> bool:
    return (
        artifacts.expired_verification.get("allowed") is False
        and "authorization_expired" in (artifacts.expired_verification.get("reason_codes") or [])
    )


def _check_signatures(artifacts: ConsumerConformanceArtifacts) -> bool:
    return (
        artifacts.signed_verification.get("allowed") is True
        and artifacts.tampered_signature_verification.get("allowed") is False
        and "governor_signature_invalid" in (artifacts.tampered_signature_verification.get("reason_codes") or [])
    )


def _check_fail_closed(artifacts: ConsumerConformanceArtifacts) -> bool:
    return (
        artifacts.harness_unavailable_result.get("allowed") is False
        and "spark_harness_core_unavailable" in (artifacts.harness_unavailable_result.get("reason_codes") or [])
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m spark_harness_core.consumer_conformance")
    parser.add_argument("--fixture", choices=["good", "broken"], default="good")
    parser.add_argument("--broken-check", choices=["finalize_all_paths", "attested_ledger"], default="finalize_all_paths")
    args = parser.parse_args(argv)

    artifacts = build_toy_consumer_artifacts(broken=args.broken_check if args.fixture == "broken" else None)
    report = run_consumer_conformance(artifacts)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
