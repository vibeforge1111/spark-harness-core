from __future__ import annotations

import hashlib
import hmac
import json
from pathlib import Path
from typing import Any

from spark_harness_core import HarnessKernel
from spark_harness_core.governor_signature import canonical_json, sign_governor_decision
from spark_harness_core.legacy_turn_intent import build_vnext_action_intent_envelope


VECTOR_DIR = Path(__file__).resolve().parents[1] / "conformance" / "vectors"
ACTION_CAPABILITY_ID = "capability:spark-harness-core:validate"
ACTION_TYPE = "edit_file"
TOOL_NAME = "spark-harness-core.validate"


def _load_vectors() -> list[dict[str, Any]]:
    return [json.loads(path.read_text(encoding="utf-8")) for path in sorted(VECTOR_DIR.glob("*.json"))]


def _build_governed_action_decision(vector: dict[str, Any]) -> dict[str, Any]:
    params = vector["input"]
    requires_confirmation = bool(params.get("requires_confirmation"))
    kernel = HarnessKernel(surface="telegram")
    action = kernel.proposed_action(
        capability_id=ACTION_CAPABILITY_ID,
        action_type=ACTION_TYPE,
        risk_tier="high" if requires_confirmation else "low",
        summary="Update a local schema validation artifact.",
        args_path="telegram://turns/conformance/actions/validate",
        requires_confirmation=requires_confirmation,
    )
    envelope = kernel.create_envelope(
        selected_move="confirm_action" if requires_confirmation else "execute_action",
        intent_summary="User explicitly asked Spark to update a validation artifact.",
        raw_turn_summary="Update the validation artifact.",
        proposed_actions=[action],
        authority_state="confirmation_required" if requires_confirmation else "executable",
        risk_tier="high" if requires_confirmation else "low",
        confidence=float(params.get("confidence", 0.95)),
    )

    authorizations = []
    if params.get("include_authorization", True):
        authorization = kernel.authorize(envelope, envelope["proposed_actions"][0])
        if params.get("authorization_expires_at"):
            authorization["expires_at"] = params["authorization_expires_at"]
        authorizations.append(authorization)

    ledgers = []
    if params.get("include_ledger", True) and authorizations:
        ledger = kernel.record_tool_call(
            envelope=envelope,
            action=envelope["proposed_actions"][0],
            authorization=authorizations[0],
            tool_name=TOOL_NAME,
            status="not_started",
            output_path="builder://validate/not-started.json",
            summary="Validation is authorized and waiting to execute.",
        )
        if params.get("authorization_expires_at"):
            ledger["authorization"]["expires_at"] = params["authorization_expires_at"]
        ledgers.append(ledger)

    decision = kernel.governor_decision(envelope, authorizations=authorizations, tool_ledgers=ledgers)
    if params.get("sign"):
        signature = params["signature"]
        decision = sign_governor_decision(
            decision,
            key=params["hmac_key"],
            key_id=signature["key_id"],
            nonce=signature["nonce"],
            created_at=signature["created_at"],
        )
    if params.get("tamper_after_sign") and decision["tool_ledgers"]:
        decision["tool_ledgers"][0]["action_id"] = "action-tampered-after-signing"
    return decision


def test_canonical_json_vectors() -> None:
    for vector in _load_vectors():
        if "canonical_value" not in vector["input"]:
            continue
        payload = canonical_json(vector["input"]["canonical_value"])
        assert payload == vector["expected"]["canonical_json"]
        digest = hmac.new(vector["input"]["hmac_key"].encode("utf-8"), payload.encode("utf-8"), hashlib.sha256)
        assert digest.hexdigest() == vector["expected"]["hmac_sha256"]


def test_governor_vectors() -> None:
    kernel = HarnessKernel(surface="telegram")
    for vector in _load_vectors():
        if vector["input"].get("case") != "governed_action":
            continue
        decision = _build_governed_action_decision(vector)
        assert decision["outcome"] == vector["expected"]["governor_outcome"]
        expected_verifier = vector["expected"]["verifier"]
        verification = kernel.verify_governor_execution_authority(
            decision,
            expected_capability_id=ACTION_CAPABILITY_ID,
            expected_action_type=ACTION_TYPE,
            tool_name=TOOL_NAME,
            governor_hmac_key=vector["input"].get("hmac_key"),
            require_signature=bool(vector["input"].get("sign")),
            now=vector["input"].get("now"),
        )
        assert verification["allowed"] is expected_verifier["allowed"]
        for reason_code in expected_verifier["reason_codes"]:
            assert reason_code in verification["reason_codes"]


def test_mutation_mapping_vectors() -> None:
    for vector in _load_vectors():
        if vector["input"].get("case") != "mutation_mapping":
            continue
        params = vector["input"]
        envelope = build_vnext_action_intent_envelope(
            surface="telegram",
            actor_id_ref="human:local-operator",
            request_id=f"req-{vector['name']}",
            source_kind="conformance",
            intent_summary=f"Conformance mapping for {params['mutation_class']}.",
            raw_turn_summary="Conformance mapping vector.",
            actions=[
                {
                    "tool_name": params["tool_name"],
                    "owner_system": params["owner_system"],
                    "mutation_class": params["mutation_class"],
                }
            ],
        )
        action = envelope["proposed_actions"][0]
        assert action["action_type"] == vector["expected"]["action_type"]
        assert action["risk_tier"] == vector["expected"]["risk_tier"]
        assert envelope["action_authority"]["risk_tier"] == vector["expected"]["risk_tier"]
