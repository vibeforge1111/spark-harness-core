from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from spark_harness_core.schemas import validate_instance


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _id(prefix: str) -> str:
    return f"{prefix}:{uuid4().hex[:24]}"


def trace_ref(kind: str, summary: str, *, redaction_class: str = "metadata_only") -> dict[str, Any]:
    return {
        "id": _id(f"trace.{kind}"),
        "redaction_class": redaction_class,
        "summary": summary,
    }


def artifact_ref(
    kind: str,
    path_or_uri: str,
    summary: str,
    *,
    redaction_class: str = "metadata_only",
) -> dict[str, Any]:
    return {
        "id": _id(f"artifact.{kind}"),
        "kind": kind,
        "path_or_uri": path_or_uri,
        "redaction_class": redaction_class,
        "summary": summary,
    }


def evidence_ref(
    kind: str,
    source: str,
    summary: str,
    *,
    confidence: float = 1.0,
) -> dict[str, Any]:
    return {
        "id": _id(f"evidence.{kind}"),
        "kind": kind,
        "source": source,
        "summary": summary,
        "confidence": confidence,
        "trace_refs": [],
    }


_RISK_ORDER = {
    "none": 0,
    "read": 1,
    "low": 2,
    "medium": 3,
    "high": 4,
    "critical": 5,
}


@dataclass(frozen=True)
class HarnessKernel:
    """Minimal authority kernel for Spark surfaces.

    This class does not attempt to infer rich intent by itself. It enforces the
    contract that any model, surface adapter, or future harness runtime must
    satisfy before action can happen.
    """

    surface: str
    actor_id_ref: str = "human:redacted"

    def create_envelope(
        self,
        *,
        selected_move: str,
        intent_summary: str,
        raw_turn_summary: str,
        evidence: list[dict[str, Any]] | None = None,
        proposed_actions: list[dict[str, Any]] | None = None,
        authority_state: str | None = None,
        risk_tier: str = "none",
        confidence: float = 0.0,
        requires_human_confirmation: bool = False,
    ) -> dict[str, Any]:
        evidence_items = evidence or [
            evidence_ref(
                "fresh_user_intent",
                self.surface,
                "Fresh user turn was observed and summarized for authority evaluation.",
                confidence=confidence or 0.7,
            )
        ]
        actions = proposed_actions or []
        state = authority_state or self._default_authority_state(selected_move, actions)
        envelope = {
            "schema_version": "turn-intent-envelope-vnext",
            "turn_id": _id("turn"),
            "created_at": _now(),
            "surface": self.surface,
            "actor": {
                "kind": "human",
                "id_ref": self.actor_id_ref,
                "redaction_class": "metadata_only",
            },
            "raw_turn_ref": trace_ref("raw_turn", raw_turn_summary, redaction_class="private"),
            "selected_move": selected_move,
            "intent_summary": intent_summary,
            "freshness": {
                "fresh_user_intent_present": True,
                "stale_state_used_as_authority": False,
                "memory_used_as_instruction": False,
                "pending_state_used_as_authority": False,
            },
            "evidence": evidence_items,
            "action_authority": {
                "state": state,
                "risk_tier": risk_tier,
                "confidence": confidence,
                "requires_human_confirmation": requires_human_confirmation,
                "reason": "Authority state was produced by the Governor contract.",
            },
            "proposed_actions": actions,
            "blocked_routes": [],
            "context_policy": {
                "raw_private_text_in_context": False,
                "store_raw_turn": False,
                "summary_required": True,
                "offload_artifacts": [],
            },
            "trace": trace_ref("envelope", "TurnIntent envelope created by Spark Harness Core."),
        }
        return validate_instance("turn-intent-envelope-vnext", envelope)

    def proposed_action(
        self,
        *,
        capability_id: str,
        action_type: str,
        risk_tier: str,
        summary: str,
        args_path: str,
        requires_confirmation: bool,
    ) -> dict[str, Any]:
        return {
            "action_id": _id("action"),
            "capability_id": capability_id,
            "action_type": action_type,
            "risk_tier": risk_tier,
            "summary": summary,
            "args_ref": artifact_ref("tool_args", args_path, "Sanitized tool arguments."),
            "requires_confirmation": requires_confirmation,
        }

    def authorize(
        self,
        envelope: dict[str, Any],
        action: dict[str, Any],
        *,
        approval_ref: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        validate_instance("turn-intent-envelope-vnext", envelope)
        risk = action["risk_tier"]
        executable = envelope["action_authority"]["state"] == "executable"
        if not executable:
            verdict = "deny"
            approval = {"required": False, "status": "not_required"}
            reasons = ["Envelope is not executable; raw words or proposals cannot run tools."]
        elif _RISK_ORDER[risk] >= _RISK_ORDER["high"] and approval_ref is None:
            verdict = "interrupt"
            approval = {"required": True, "status": "requested"}
            reasons = ["High-risk action requires explicit approval before execution."]
        else:
            verdict = "allow"
            approval = (
                {"required": True, "status": "approved", "approval_ref": approval_ref}
                if approval_ref is not None
                else {"required": False, "status": "not_required"}
            )
            reasons = ["Envelope authority and action risk satisfy the kernel policy."]
        decision = {
            "schema_version": "authorization-decision-v1",
            "decision_id": _id("decision"),
            "created_at": _now(),
            "turn_id": envelope["turn_id"],
            "action_id": action["action_id"],
            "capability_id": action["capability_id"],
            "verdict": verdict,
            "risk_tier": risk,
            "reasons": reasons,
            "evidence": envelope["evidence"],
            "approval": approval,
            "restrictions": {
                "network_allowed": False,
                "write_allowed": action["action_type"] in {"edit_file", "write_memory"},
                "publish_allowed": False,
            },
            "trace": trace_ref("authorization", "Authorization decision created by Spark Harness Core."),
        }
        return validate_instance("authorization-decision-v1", decision)

    def record_tool_call(
        self,
        *,
        envelope: dict[str, Any],
        action: dict[str, Any],
        authorization: dict[str, Any],
        tool_name: str,
        status: str,
        output_path: str,
        summary: str,
    ) -> dict[str, Any]:
        ledger = {
            "schema_version": "tool-call-ledger-v1",
            "ledger_id": _id("ledger"),
            "created_at": _now(),
            "turn_id": envelope["turn_id"],
            "action_id": action["action_id"],
            "capability_id": action["capability_id"],
            "tool_name": tool_name,
            "lifecycle": [
                {"stage": "propose", "at": envelope["created_at"], "verdict": "passed"},
                {"stage": "authorize", "at": authorization["created_at"], "verdict": "passed"},
                {"stage": "execute", "at": _now(), "verdict": "passed" if status == "success" else "failed"},
            ],
            "authorization": authorization,
            "arguments": {
                "schema_valid": True,
                "raw_ref": action["args_ref"],
                "sanitized_ref": action["args_ref"],
            },
            "result": {
                "status": status,
                "summary": summary,
                "sanitized_output_ref": artifact_ref("tool_output", output_path, summary),
            },
            "trace": trace_ref("tool_call", f"Ledger for {tool_name}."),
        }
        return validate_instance("tool-call-ledger-v1", ledger)

    @staticmethod
    def _default_authority_state(selected_move: str, actions: list[dict[str, Any]]) -> str:
        if selected_move.startswith("chat_"):
            return "chat_only"
        if selected_move == "read_current_state":
            return "read_only"
        if selected_move == "prepare_action":
            return "prepare_allowed"
        if selected_move == "confirm_action":
            return "confirmation_required"
        if selected_move == "execute_action" and actions:
            return "executable"
        return "none"

