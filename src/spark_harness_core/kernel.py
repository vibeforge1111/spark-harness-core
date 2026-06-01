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


READINESS_CATEGORIES = (
    "execution",
    "tools",
    "context",
    "lifecycle",
    "observability",
    "verification",
    "governance",
)

PROTECTED_EVOLUTION_COMPONENTS = frozenset({"verifier", "benchmark", "model_config", "authority_policy"})
NETWORK_ACTION_TYPES = frozenset(
    {
        "run_command",
        "launch_mission",
        "open_pr",
        "publish",
        "deploy",
        "send_message",
        "external_api_call",
        "browser_action",
    }
)
WRITE_ACTION_TYPES = frozenset(
    {
        "write_memory",
        "edit_file",
        "launch_mission",
        "open_pr",
        "publish",
        "deploy",
        "schedule",
        "create_domain_chip",
        "send_message",
        "computer_action",
    }
)


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
        read_only_authorized = envelope["action_authority"]["state"] == "read_only" and action.get("action_type") == "read"
        if not executable and not read_only_authorized:
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
            "restrictions": self._restrictions_for_action(action),
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
        authorization_verdict = str(authorization.get("verdict") or "")
        if authorization_verdict == "allow":
            authorize_stage_verdict = "passed"
        elif authorization_verdict == "interrupt":
            authorize_stage_verdict = "pending"
        else:
            authorize_stage_verdict = "failed"

        if status == "not_started":
            execute_stage_verdict = "skipped"
        elif status in {"success", "partial"}:
            execute_stage_verdict = "passed"
        elif status == "rolled_back":
            execute_stage_verdict = "failed"
        else:
            execute_stage_verdict = "failed"

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
                {"stage": "authorize", "at": authorization["created_at"], "verdict": authorize_stage_verdict},
                {"stage": "execute", "at": _now(), "verdict": execute_stage_verdict},
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

    def component(
        self,
        *,
        component_id: str,
        component_type: str,
        owner_repo: str,
        path: str,
        summary: str,
        tests: list[str],
        editable_by_evolution: bool | None = None,
        authority_scope: list[str] | None = None,
        dependencies: list[str] | None = None,
        rollback_ref: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        component = {
            "schema_version": "harness-component-v1",
            "component_id": component_id,
            "component_type": component_type,
            "owner_repo": owner_repo,
            "path": path,
            "summary": summary,
            "editable_by_evolution": (
                component_type not in PROTECTED_EVOLUTION_COMPONENTS
                if editable_by_evolution is None
                else editable_by_evolution
            ),
            "authority_scope": authority_scope or [self.surface],
            "dependencies": dependencies or [],
            "tests": tests,
        }
        if rollback_ref is not None:
            component["rollback_ref"] = rollback_ref
        return validate_instance("harness-component-v1", component)

    def resource(
        self,
        *,
        resource_id: str,
        resource_type: str,
        owner_repo: str,
        version: str,
        tests: list[str],
        lifecycle_state: str = "active",
        authority_scope: list[str] | None = None,
        created_from: str = "spark-harness-core",
        change_manifest_refs: list[str] | None = None,
        rollback_ref: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return {
            "resource_id": resource_id,
            "resource_type": resource_type,
            "owner_repo": owner_repo,
            "lifecycle_state": lifecycle_state,
            "version": version,
            "authority_scope": authority_scope or [self.surface],
            "tests": tests,
            "lineage": {
                "created_from": created_from,
                "change_manifest_refs": change_manifest_refs or [],
                "rollback_ref": rollback_ref
                or artifact_ref("rollback", f"rollback/{resource_id}.json", "Rollback plan reference."),
            },
        }

    def resource_registry(self, resources: list[dict[str, Any]]) -> dict[str, Any]:
        registry = {
            "schema_version": "resource-registry-v1",
            "registry_id": _id("resource-registry"),
            "created_at": _now(),
            "resources": resources,
        }
        return validate_instance("resource-registry-v1", registry)

    def experience_entry(
        self,
        *,
        entry_type: str,
        summary: str,
        artifact: dict[str, Any],
        tags: list[str] | None = None,
        linked_run_id: str | None = None,
        linked_change_id: str | None = None,
    ) -> dict[str, Any]:
        entry = {
            "entry_id": _id("experience"),
            "entry_type": entry_type,
            "surface": self.surface,
            "summary": summary,
            "artifact": artifact,
            "tags": tags or [],
        }
        if linked_run_id:
            entry["linked_run_id"] = linked_run_id
        if linked_change_id:
            entry["linked_change_id"] = linked_change_id
        return entry

    def experience_index(
        self,
        *,
        entries: list[dict[str, Any]] | None = None,
        query_hints: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        index = {
            "schema_version": "experience-index-v1",
            "index_id": _id("experience-index"),
            "created_at": _now(),
            "entries": entries or [],
            "query_hints": query_hints
            or [
                {
                    "name": "harness evidence",
                    "description": "Search generated harness evidence, traces, scores, and change records.",
                    "glob": "experience/**/*.json",
                }
            ],
        }
        return validate_instance("experience-index-v1", index)

    def readiness_score(
        self,
        *,
        target_kind: str,
        target_id: str,
        owner_repo: str,
        category_scores: dict[str, float] | None = None,
        category_evidence: dict[str, list[dict[str, Any]]] | None = None,
        category_blockers: dict[str, list[str]] | None = None,
        promotion_gates: dict[str, bool] | None = None,
        summary: str | None = None,
    ) -> dict[str, Any]:
        scores = category_scores or {}
        evidence = category_evidence or {}
        blockers = category_blockers or {}
        categories: dict[str, dict[str, Any]] = {}
        for name in READINESS_CATEGORIES:
            score = max(0.0, min(1.0, float(scores.get(name, 0.0))))
            category_blocker_items = list(blockers.get(name, []))
            if score <= 0 and not evidence.get(name):
                category_blocker_items.append(f"missing_{name}_evidence")
            categories[name] = {
                "score": round(score, 4),
                "evidence": evidence.get(name, []),
                "blockers": category_blocker_items,
            }
        gates = {
            "public_ready": False,
            "network_absorbable": False,
            "telegram_live_proven": False,
            "startup_benchmark_proven": False,
            "zero_high_agency_legacy_local_gates": False,
            **(promotion_gates or {}),
        }
        overall_score = round(sum(item["score"] for item in categories.values()) / len(READINESS_CATEGORIES), 4)
        any_blockers = any(item["blockers"] for item in categories.values())
        if gates["public_ready"] and gates["network_absorbable"] and overall_score >= 0.95 and not any_blockers:
            status = "public_ready"
        elif overall_score >= 0.85 and gates["telegram_live_proven"] and gates["startup_benchmark_proven"] and not any_blockers:
            status = "release_candidate"
        elif overall_score >= 0.7 and gates["zero_high_agency_legacy_local_gates"]:
            status = "private_ready"
        else:
            status = "blocked"
        readiness = {
            "schema_version": "readiness-score-v1",
            "score_id": _id("readiness"),
            "created_at": _now(),
            "target": {
                "kind": target_kind,
                "id": target_id,
                "owner_repo": owner_repo,
            },
            "categories": categories,
            "promotion_gates": gates,
            "overall": {
                "score": overall_score,
                "status": status,
                "summary": summary
                or f"{owner_repo} readiness is {status} with score {overall_score:.2f}.",
            },
        }
        return validate_instance("readiness-score-v1", readiness)

    def change_manifest(
        self,
        *,
        target_component: dict[str, Any],
        failure_evidence: list[dict[str, Any]],
        root_cause_hypothesis: str,
        edit_summary: str,
        predicted_fixes: list[str],
        predicted_regression_risks: list[str],
        required_tests: list[str],
        rollback_plan: str,
        live_proof_required: bool = False,
        observed_delta: list[dict[str, Any]] | None = None,
        verdict: str = "draft",
        human_approval_ref: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        manifest = {
            "schema_version": "change-manifest-v1",
            "change_id": _id("change"),
            "created_at": _now(),
            "target_component": target_component,
            "failure_evidence": failure_evidence,
            "root_cause_hypothesis": root_cause_hypothesis,
            "edit_summary": edit_summary,
            "predicted_fixes": predicted_fixes,
            "predicted_regression_risks": predicted_regression_risks,
            "required_tests": required_tests,
            "live_proof_required": live_proof_required,
            "rollback_plan": rollback_plan,
            "observed_delta": observed_delta or [],
            "verdict": verdict,
        }
        if human_approval_ref is not None:
            manifest["human_approval_ref"] = human_approval_ref
        return validate_instance("change-manifest-v1", manifest)

    def self_evolution_run(
        self,
        *,
        mode: str,
        experience_index: dict[str, Any],
        readiness_score: dict[str, Any],
        commands: list[str],
        target_components: list[dict[str, Any]] | None = None,
        change_manifests: list[dict[str, Any]] | None = None,
        evaluation_packs: list[dict[str, Any]] | None = None,
        verdict: str = "not_ready",
        summary: str = "Self-evolution run recorded by Spark Harness Core.",
        roles: dict[str, str] | None = None,
        live_surface_required: bool = False,
    ) -> dict[str, Any]:
        record = {
            "schema_version": "self-evolution-run-v1",
            "evolution_id": _id("evolution"),
            "created_at": _now(),
            "mode": mode,
            "roles": roles
            or {
                "harness_scientist": "spark-harness-core",
                "surface_operator": self.surface,
                "verifier": "spark-harness-core",
            },
            "experience_index": experience_index,
            "target_components": target_components or [],
            "change_manifests": change_manifests or [],
            "test_plan": {
                "evaluation_packs": evaluation_packs or [],
                "live_surface_required": live_surface_required,
                "commands": commands,
            },
            "promotion_decision": {
                "verdict": verdict,
                "summary": summary,
                "readiness_score": readiness_score,
            },
        }
        return validate_instance("self-evolution-run-v1", record)

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

    @staticmethod
    def _restrictions_for_action(action: dict[str, Any]) -> dict[str, bool]:
        action_type = str(action.get("action_type") or "")
        requires_confirmation = bool(action.get("requires_confirmation"))
        return {
            "network_allowed": action_type in NETWORK_ACTION_TYPES,
            "write_allowed": action_type in WRITE_ACTION_TYPES
            or (action_type == "browser_action" and requires_confirmation),
            "publish_allowed": action_type in {"publish", "deploy", "open_pr"},
        }
