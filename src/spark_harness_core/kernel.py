from __future__ import annotations

from copy import deepcopy
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
MUTATING_EVOLUTION_MODES = frozenset({"sandbox", "promote", "rollback"})
PROMOTION_VERDICTS = frozenset({"promote_private", "promote_release_candidate"})
READINESS_STATUS_RANK = {
    "blocked": 0,
    "private_ready": 1,
    "release_candidate": 2,
    "public_ready": 3,
}
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
LIVE_QA_RISKS = ("safe", "mission", "writes_files", "external")
LIVE_QA_VERDICTS = ("pass", "fail", "blocked", "needs-retest", "untested")
EXECUTED_TOOL_STATUSES = frozenset({"success", "failure", "partial", "rolled_back"})
LEGACY_PLANE_DISPOSITIONS = (
    "removed",
    "quarantined",
    "evidence_adapter",
    "canonical_consumer",
    "release_blocker",
)
LEGACY_PLANE_HIGH_AGENCY_RISK_KEYS = (
    "can_execute",
    "can_mutate_state",
    "can_route_turns",
    "can_write_memory",
    "can_launch_mission",
    "can_call_network",
    "can_publish",
    "can_schedule",
)
FRESH_USER_INTENT_REQUIRED_MOVES = frozenset({"read_current_state", "confirm_action", "execute_action"})


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
        fresh_user_intent_ref = self._fresh_user_intent_ref_from_evidence(evidence_items)
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
                "fresh_user_intent_present": fresh_user_intent_ref is not None,
                "fresh_user_intent_ref": fresh_user_intent_ref,
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
        authority_state = envelope["action_authority"]["state"]
        executable = authority_state == "executable"
        read_only_authorized = authority_state == "read_only" and action.get("action_type") == "read"
        freshness_reasons = self._fresh_user_intent_authority_reason_codes(envelope)
        if freshness_reasons and (executable or read_only_authorized or authority_state == "confirmation_required"):
            verdict = "deny"
            approval = {"required": False, "status": "not_required"}
            reasons = freshness_reasons
        elif authority_state == "confirmation_required":
            verdict = "interrupt"
            approval = {"required": True, "status": "requested"}
            reasons = ["Envelope requires explicit confirmation before execution."]
        elif not executable and not read_only_authorized:
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
            "restrictions": self._restrictions_for_decision(verdict, action),
            "trace": trace_ref("authorization", "Authorization decision created by Spark Harness Core."),
        }
        return validate_instance("authorization-decision-v1", decision)

    def governor_decision(
        self,
        envelope: dict[str, Any],
        *,
        authorizations: list[dict[str, Any]] | None = None,
        tool_ledgers: list[dict[str, Any]] | None = None,
        reply_style: str | None = None,
        reply_instruction: str | None = None,
    ) -> dict[str, Any]:
        validate_instance("turn-intent-envelope-vnext", envelope)
        authorization_items = list(authorizations or [])
        ledger_items = list(tool_ledgers or [])
        for authorization in authorization_items:
            validate_instance("authorization-decision-v1", authorization)
        for ledger in ledger_items:
            validate_instance("tool-call-ledger-v1", ledger)

        outcome = self._governor_outcome(envelope, authorization_items, ledger_items)
        authorized_action_count = sum(1 for item in authorization_items if item.get("verdict") == "allow")
        requires_confirmation = bool(envelope["action_authority"].get("requires_human_confirmation")) or any(
            item.get("approval", {}).get("required") for item in authorization_items
        )
        decision = {
            "schema_version": "governor-decision-v1",
            "decision_id": _id("governor-decision"),
            "created_at": _now(),
            "surface": envelope["surface"],
            "turn_id": envelope["turn_id"],
            "selected_move": envelope["selected_move"],
            "authority_state": envelope["action_authority"]["state"],
            "risk_tier": envelope["action_authority"]["risk_tier"],
            "outcome": outcome,
            "envelope": envelope,
            "authorizations": authorization_items,
            "tool_ledgers": ledger_items,
            "execution_boundary": {
                "action_authorized": outcome == "execute",
                "action_count": len(envelope.get("proposed_actions", [])),
                "authorized_action_count": authorized_action_count,
                "requires_human_confirmation": requires_confirmation,
                "legacy_authority_demoted": True,
                "reasons": self._governor_reasons(outcome, envelope, authorization_items),
            },
            "reply_contract": {
                "style": reply_style or self._default_reply_style(outcome),
                "instruction": reply_instruction or self._default_reply_instruction(outcome),
                "inspect_link_allowed": outcome in {"read_only", "execute", "interrupt", "degrade"},
                "should_interrupt": outcome == "interrupt",
            },
            "evidence": envelope["evidence"],
            "trace": trace_ref("governor", "Governor decision created by Spark Harness Core."),
        }
        return validate_instance("governor-decision-v1", decision)

    def verify_governor_execution_authority(
        self,
        governor_decision: dict[str, Any] | None,
        *,
        expected_capability_id: str,
        expected_action_type: str | None = None,
        tool_name: str | None = None,
        action_id: str | None = None,
        allow_read_only: bool = False,
        require_pre_execution_ledger: bool = True,
    ) -> dict[str, Any]:
        if not isinstance(governor_decision, dict):
            return self._governor_consumer_verification(
                allowed=False,
                reason_codes=["missing_governor_decision"],
                governor_decision=None,
            )
        try:
            decision = validate_instance("governor-decision-v1", governor_decision)
        except Exception:
            return self._governor_consumer_verification(
                allowed=False,
                reason_codes=["invalid_governor_decision"],
                governor_decision=governor_decision,
            )

        reason_codes: list[str] = []
        outcome = str(decision.get("outcome") or "")
        allowed_outcomes = {"execute"}
        if allow_read_only:
            allowed_outcomes.add("read_only")
        if outcome not in allowed_outcomes:
            reason_codes.append(f"governor_outcome_{outcome or 'missing'}")

        boundary = decision.get("execution_boundary") if isinstance(decision.get("execution_boundary"), dict) else {}
        if outcome == "execute" and not bool(boundary.get("action_authorized")):
            reason_codes.append("governor_action_not_authorized")
        reason_codes.extend(self._fresh_user_intent_authority_reason_codes(decision.get("envelope", {})))

        turn_id = str(decision.get("turn_id") or "")
        matching_authorization = self._matching_governor_authorization(
            decision,
            turn_id=turn_id,
            expected_capability_id=expected_capability_id,
            action_id=action_id,
        )
        if matching_authorization is None:
            reason_codes.append("governor_missing_matching_authorization")
        elif not self._has_matching_governor_proposed_action(
            decision,
            authorization=matching_authorization,
            expected_action_type=expected_action_type,
        ):
            reason_codes.append("governor_missing_matching_proposed_action")

        matching_ledger = None
        if matching_authorization is not None:
            matching_ledger = self._matching_governor_tool_ledger(
                decision,
                authorization=matching_authorization,
                turn_id=turn_id,
                expected_capability_id=expected_capability_id,
                tool_name=tool_name,
                require_pre_execution_ledger=require_pre_execution_ledger,
            )
        if outcome == "execute" and matching_ledger is None:
            reason_codes.append("governor_missing_matching_tool_ledger")

        return self._governor_consumer_verification(
            allowed=not reason_codes,
            reason_codes=reason_codes,
            governor_decision=decision,
            authorization=matching_authorization,
            ledger=matching_ledger,
            expected_capability_id=expected_capability_id,
            expected_action_type=expected_action_type,
            tool_name=tool_name,
        )

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
        self._assert_authorization_matches_action(envelope, action, authorization)
        self._assert_execution_status_authorized(authorization_verdict, status)
        if authorization_verdict == "allow":
            authorize_stage_verdict = "passed"
        elif authorization_verdict == "interrupt":
            authorize_stage_verdict = "pending"
        else:
            authorize_stage_verdict = "failed"

        execute_stage_verdict = self._execute_verdict_for_status(status)

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

    def finalize_tool_call_ledger(
        self,
        ledger: dict[str, Any],
        *,
        status: str,
        output_path: str,
        summary: str,
        error_path: str | None = None,
        rollback_path: str | None = None,
    ) -> dict[str, Any]:
        validate_instance("tool-call-ledger-v1", ledger)
        self._assert_ledger_authorization_binding(ledger)
        self._assert_execution_status_authorized(str(ledger["authorization"].get("verdict") or ""), status)
        updated = deepcopy(ledger)
        execute_stage = {"stage": "execute", "at": _now(), "verdict": self._execute_verdict_for_status(status)}
        lifecycle = [dict(item) for item in updated.get("lifecycle", [])]
        if lifecycle and lifecycle[-1].get("stage") == "execute":
            lifecycle[-1] = execute_stage
        else:
            lifecycle.append(execute_stage)
        result = {
            "status": status,
            "summary": summary,
            "sanitized_output_ref": artifact_ref("tool_output", output_path, summary),
        }
        if error_path:
            result["error_ref"] = artifact_ref("tool_error", error_path, "Sanitized tool error reference.")
        if rollback_path:
            result["rollback_ref"] = artifact_ref("rollback", rollback_path, "Tool rollback reference.")
        updated["lifecycle"] = lifecycle
        updated["result"] = result
        updated["trace"] = trace_ref("tool_call", f"Final ledger for {updated['tool_name']}.")
        return validate_instance("tool-call-ledger-v1", updated)

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

    def metric(
        self,
        *,
        name: str,
        value: int | float | bool | str,
        unit: str | None = None,
        higher_is_better: bool | None = None,
    ) -> dict[str, Any]:
        metric = {"name": name, "value": value}
        if unit is not None:
            metric["unit"] = unit
        if higher_is_better is not None:
            metric["higher_is_better"] = higher_is_better
        return metric

    def evaluation_case(
        self,
        *,
        case_id: str,
        case_type: str,
        prompt_ref: dict[str, Any],
        expected_move: str,
        expected_authority_state: str,
    ) -> dict[str, Any]:
        return {
            "case_id": case_id,
            "case_type": case_type,
            "prompt_ref": prompt_ref,
            "expected_move": expected_move,
            "expected_authority_state": expected_authority_state,
        }

    def evaluation_pack(
        self,
        *,
        scope: list[str],
        cases: list[dict[str, Any]],
        metrics: list[dict[str, Any]],
        promotion_rules: list[str],
        blind: bool = True,
        judge_count: int = 3,
        rubric_ref: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        pack = {
            "schema_version": "evaluation-pack-v1",
            "pack_id": _id("evaluation-pack"),
            "created_at": _now(),
            "scope": scope,
            "cases": cases,
            "metrics": metrics,
            "jury": {
                "blind": blind,
                "judge_count": judge_count,
                "rubric_ref": rubric_ref
                or artifact_ref("rubric", "eval/rubric.md", "Evaluation rubric reference."),
            },
            "promotion_rules": promotion_rules,
        }
        return validate_instance("evaluation-pack-v1", pack)

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
            "performance_budget_proven": False,
            "governance_rulesets_proven": False,
            "zero_high_agency_legacy_local_gates": False,
            **(promotion_gates or {}),
        }
        overall_score = round(sum(item["score"] for item in categories.values()) / len(READINESS_CATEGORIES), 4)
        any_blockers = any(item["blockers"] for item in categories.values())
        if (
            gates["public_ready"]
            and gates["network_absorbable"]
            and gates["performance_budget_proven"]
            and gates["governance_rulesets_proven"]
            and gates["zero_high_agency_legacy_local_gates"]
            and overall_score >= 0.95
            and not any_blockers
        ):
            status = "public_ready"
        elif (
            overall_score >= 0.85
            and gates["telegram_live_proven"]
            and gates["startup_benchmark_proven"]
            and gates["performance_budget_proven"]
            and gates["governance_rulesets_proven"]
            and gates["zero_high_agency_legacy_local_gates"]
            and not any_blockers
        ):
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

    def harness_run(
        self,
        *,
        run_type: str,
        model_refs: list[str],
        status: str,
        summary: str,
        envelopes: list[dict[str, Any]] | None = None,
        tool_ledgers: list[dict[str, Any]] | None = None,
        artifacts: list[dict[str, Any]] | None = None,
        metrics: list[dict[str, Any]] | None = None,
        remaining_risks: list[str] | None = None,
    ) -> dict[str, Any]:
        run = {
            "schema_version": "harness-run-v1",
            "run_id": _id("harness-run"),
            "created_at": _now(),
            "run_type": run_type,
            "surface": self.surface,
            "model_refs": model_refs,
            "envelopes": envelopes or [],
            "tool_ledgers": tool_ledgers or [],
            "artifacts": artifacts or [],
            "metrics": metrics or [],
            "verdict": {
                "status": status,
                "summary": summary,
                "remaining_risks": remaining_risks or [],
            },
        }
        return validate_instance("harness-run-v1", run)

    def legacy_authority_plane(
        self,
        *,
        plane_id: str,
        owner_repo: str,
        surface: str,
        plane_type: str,
        source_path: str,
        summary: str,
        authority_risk: dict[str, bool],
        disposition: str,
        evidence: list[dict[str, Any]],
        governor_required: bool = False,
        evidence_only: bool = False,
        consumer_of_governor: bool = False,
        ledger_required: bool = False,
        blockers: list[str] | None = None,
    ) -> dict[str, Any]:
        if disposition not in LEGACY_PLANE_DISPOSITIONS:
            raise ValueError(f"unsupported legacy authority plane disposition: {disposition}")
        normalized_risk = {key: bool(authority_risk.get(key)) for key in LEGACY_PLANE_HIGH_AGENCY_RISK_KEYS}
        blocker_items = list(blockers or [])
        self._validate_legacy_plane_disposition(
            authority_risk=normalized_risk,
            disposition=disposition,
            governor_required=governor_required,
            evidence_only=evidence_only,
            consumer_of_governor=consumer_of_governor,
            ledger_required=ledger_required,
            blockers=blocker_items,
        )
        plane = {
            "schema_version": "legacy-authority-plane-v1",
            "plane_id": plane_id,
            "created_at": _now(),
            "owner_repo": owner_repo,
            "surface": surface,
            "plane_type": plane_type,
            "source_ref": artifact_ref("legacy_authority_source", source_path, summary, redaction_class="metadata_only"),
            "authority_risk": normalized_risk,
            "disposition": disposition,
            "harness_binding": {
                "governor_required": governor_required,
                "evidence_only": evidence_only,
                "consumer_of_governor": consumer_of_governor,
                "ledger_required": ledger_required,
                "notes": summary,
            },
            "evidence": evidence,
            "blockers": blocker_items,
            "trace": trace_ref("legacy_authority_plane", summary),
        }
        return validate_instance("legacy-authority-plane-v1", plane)

    def legacy_authority_inventory(
        self,
        *,
        inventory_id: str,
        owner_repo: str,
        surfaces: list[str],
        planes: list[dict[str, Any]],
    ) -> dict[str, Any]:
        for plane in planes:
            validate_instance("legacy-authority-plane-v1", plane)
        disposition_counts = {disposition: 0 for disposition in LEGACY_PLANE_DISPOSITIONS}
        high_agency_count = 0
        blockers: list[str] = []
        for plane in planes:
            disposition = str(plane.get("disposition") or "")
            if disposition in disposition_counts:
                disposition_counts[disposition] += 1
            if self._legacy_plane_has_high_agency_risk(dict(plane.get("authority_risk") or {})):
                high_agency_count += 1
            for blocker in plane.get("blockers", []):
                blockers.append(str(blocker))
            if disposition == "release_blocker":
                blockers.append(f"{plane.get('plane_id', 'legacy-plane:unknown')} is a release blocker")
        release_blocker_count = disposition_counts["release_blocker"]
        ready = release_blocker_count == 0 and not blockers
        inventory = {
            "schema_version": "legacy-authority-inventory-v1",
            "inventory_id": inventory_id,
            "created_at": _now(),
            "scope": {
                "owner_repo": owner_repo,
                "surfaces": surfaces,
            },
            "planes": planes,
            "summary": {
                "plane_count": len(planes),
                "removed_count": disposition_counts["removed"],
                "quarantined_count": disposition_counts["quarantined"],
                "evidence_adapter_count": disposition_counts["evidence_adapter"],
                "canonical_consumer_count": disposition_counts["canonical_consumer"],
                "release_blocker_count": release_blocker_count,
                "high_agency_risk_count": high_agency_count,
            },
            "release_gate": {
                "zero_high_agency_legacy_local_gates": ready,
                "ready_for_readiness_promotion": ready,
                "blockers": blockers,
            },
        }
        return validate_instance("legacy-authority-inventory-v1", inventory)

    def telegram_live_qa_case(
        self,
        *,
        ordinal: int,
        case_id: str,
        suite: str,
        risk: str,
        expected_route: str,
        expected_outcome: str,
        prompts: list[str],
    ) -> dict[str, Any]:
        turns = [prompt.strip() for prompt in prompts if prompt.strip()]
        if not turns:
            raise ValueError("telegram live QA case requires at least one prompt.")
        if risk not in LIVE_QA_RISKS:
            raise ValueError(f"unsupported Telegram live QA risk: {risk}")
        return {
            "ordinal": ordinal,
            "id": case_id,
            "suite": suite,
            "risk": risk,
            "expected_route": expected_route,
            "expected_outcome": expected_outcome,
            "verdict": "untested",
            "actual_route": None,
            "actual_outcome": None,
            "observed_turns": [
                {
                    "turn_index": index + 1,
                    "prompt": prompt,
                    "reply": None,
                    "reply_timestamp": None,
                }
                for index, prompt in enumerate(turns)
            ],
            "side_effects": {
                "files_changed": None,
                "memory_written": None,
                "mission_started": None,
                "external_network_called": None,
                "pr_opened": None,
                "publish_or_deploy_started": None,
                "schedule_changed": None,
                "tool_or_browser_used": None,
            },
            "evidence_refs": {
                "authorization_ledgers": [],
                "tool_ledgers": [],
                "traces": [],
                "runtime_status": [],
                "screenshots": [],
                "commits": [],
                "prs": [],
            },
            "issue": None,
            "fix_commit": None,
            "retest_required": False,
        }

    def telegram_live_qa_evidence_packet(
        self,
        *,
        cases: list[dict[str, Any]],
        catalog: str,
        title: str = "Spark Telegram Live QA Evidence Packet",
        suite: str | None = None,
        include_risky: bool = False,
        required_session_evidence: dict[str, Any] | None = None,
        run_id: str | None = None,
        generated_at: str | None = None,
    ) -> dict[str, Any]:
        created_at = generated_at or _now()
        risk_counts = {risk: 0 for risk in LIVE_QA_RISKS}
        summary_counts = {verdict.replace("-", "_"): 0 for verdict in LIVE_QA_VERDICTS}
        for case in cases:
            risk = str(case.get("risk") or "")
            verdict = str(case.get("verdict") or "untested")
            if risk not in risk_counts:
                raise ValueError(f"unsupported Telegram live QA risk: {risk}")
            if verdict not in LIVE_QA_VERDICTS:
                raise ValueError(f"unsupported Telegram live QA verdict: {verdict}")
            risk_counts[risk] += 1
            summary_counts[verdict.replace("-", "_")] += 1
        session_evidence = {
            "profile": None,
            "tester": None,
            "bot_runtime_commit": None,
            "harness_core_commit": None,
            "spark_os_compile_ref": None,
            "spark_live_status_ref": None,
            "spark_verify_provenance_ref": None,
            "telegram_chat_evidence_ref": None,
            "overall_verdict": "untested",
            "follow_up_commits": [],
            "pr_links": [],
            "remaining_risks": [],
        }
        if required_session_evidence:
            session_evidence.update(required_session_evidence)
            session_evidence["follow_up_commits"] = list(required_session_evidence.get("follow_up_commits") or [])
            session_evidence["pr_links"] = list(required_session_evidence.get("pr_links") or [])
            session_evidence["remaining_risks"] = list(required_session_evidence.get("remaining_risks") or [])
        packet = {
            "schema_version": "spark.telegram_live_qa_evidence_packet.v1",
            "generated_at": created_at,
            "run_id": run_id or f"telegram-live-qa-{created_at.replace(':', '-').replace('.', '-')}",
            "title": title,
            "catalog": catalog,
            "selection": {
                "suite": suite,
                "include_risky": include_risky,
                "case_count": len(cases),
                "risk_counts": risk_counts,
            },
            "authority_claim_boundary": (
                "This packet is a live QA evidence container. It does not prove release readiness until "
                "each case has observed replies, side-effect checks, ledger or trace evidence where required, "
                "and a human verdict. It must not be treated as authority to execute high-agency actions."
            ),
            "required_session_evidence": session_evidence,
            "verdict_values": list(LIVE_QA_VERDICTS),
            "cases": cases,
            "summary": summary_counts,
        }
        return validate_instance("telegram-live-qa-evidence-packet-v1", packet)

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
        manifests = change_manifests or []
        components = target_components or []
        packs = evaluation_packs or []
        self._validate_self_evolution_policy(
            mode=mode,
            verdict=verdict,
            readiness_score=readiness_score,
            target_components=components,
            change_manifests=manifests,
            live_surface_required=live_surface_required,
        )
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
            "target_components": components,
            "change_manifests": manifests,
            "test_plan": {
                "evaluation_packs": packs,
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
    def _fresh_user_intent_ref_from_evidence(evidence_items: list[dict[str, Any]]) -> dict[str, Any] | None:
        for item in evidence_items:
            if isinstance(item, dict) and item.get("kind") == "fresh_user_intent":
                return item
        return None

    @staticmethod
    def _fresh_user_intent_authority_reason_codes(envelope: dict[str, Any]) -> list[str]:
        if str(envelope.get("selected_move") or "") not in FRESH_USER_INTENT_REQUIRED_MOVES:
            return []

        reasons: list[str] = []
        actor = envelope.get("actor") if isinstance(envelope.get("actor"), dict) else {}
        if actor.get("kind") != "human":
            reasons.append("fresh_user_intent_actor_not_human")

        freshness = envelope.get("freshness") if isinstance(envelope.get("freshness"), dict) else {}
        if not freshness.get("fresh_user_intent_present"):
            reasons.append("fresh_user_intent_missing")
        if freshness.get("stale_state_used_as_authority"):
            reasons.append("stale_state_used_as_authority")
        if freshness.get("memory_used_as_instruction"):
            reasons.append("memory_used_as_instruction")
        if freshness.get("pending_state_used_as_authority"):
            reasons.append("pending_state_used_as_authority")

        fresh_ref = freshness.get("fresh_user_intent_ref") if isinstance(freshness, dict) else None
        if not isinstance(fresh_ref, dict):
            reasons.append("fresh_user_intent_ref_missing")
            return reasons
        if fresh_ref.get("kind") != "fresh_user_intent":
            reasons.append("fresh_user_intent_ref_not_fresh_user_intent")

        evidence_items = envelope.get("evidence") if isinstance(envelope.get("evidence"), list) else []
        bound = any(
            isinstance(item, dict)
            and item.get("id") == fresh_ref.get("id")
            and item.get("kind") == "fresh_user_intent"
            and item.get("source") == fresh_ref.get("source")
            for item in evidence_items
        )
        if not bound:
            reasons.append("fresh_user_intent_evidence_unbound")
        return list(dict.fromkeys(reasons))

    def change_manifest_runner(
        self,
        *,
        mode: str,
        experience_index: dict[str, Any],
        readiness_score: dict[str, Any],
        commands: list[str],
        target_components: list[dict[str, Any]] | None = None,
        change_manifests: list[dict[str, Any]] | None = None,
        evaluation_packs: list[dict[str, Any]] | None = None,
        requested_verdict: str | None = None,
        roles: dict[str, str] | None = None,
        live_surface_required: bool = False,
    ) -> dict[str, Any]:
        manifests = list(change_manifests or [])
        components = list(target_components or [])
        known_component_ids = {str(component.get("component_id") or "") for component in components}
        for manifest in manifests:
            validate_instance("change-manifest-v1", manifest)
            component = manifest.get("target_component")
            if isinstance(component, dict):
                component_id = str(component.get("component_id") or "")
                if component_id and component_id not in known_component_ids:
                    components.append(component)
                    known_component_ids.add(component_id)

        decision = self._change_manifest_runner_decision(
            mode=mode,
            readiness_score=readiness_score,
            target_components=components,
            change_manifests=manifests,
            live_surface_required=live_surface_required,
            requested_verdict=requested_verdict,
        )
        return self.self_evolution_run(
            mode=mode,
            experience_index=experience_index,
            readiness_score=readiness_score,
            commands=commands,
            target_components=components,
            change_manifests=manifests,
            evaluation_packs=evaluation_packs,
            verdict=decision["verdict"],
            summary=decision["summary"],
            roles=roles,
            live_surface_required=live_surface_required,
        )

    def _governor_outcome(
        self,
        envelope: dict[str, Any],
        authorizations: list[dict[str, Any]],
        tool_ledgers: list[dict[str, Any]],
    ) -> str:
        state = str(envelope["action_authority"]["state"])
        selected_move = str(envelope["selected_move"])
        action_count = len(envelope.get("proposed_actions", []))
        verdicts = [str(item.get("verdict") or "") for item in authorizations]
        if self._fresh_user_intent_authority_reason_codes(envelope):
            return "deny"
        if state == "executable" and "allow" in verdicts:
            if self._has_matching_execution_ledger(envelope, authorizations, tool_ledgers):
                return "execute"
            return "degrade"
        if state == "confirmation_required" or "interrupt" in verdicts:
            return "interrupt"
        if state == "read_only":
            return "read_only"
        if state == "prepare_allowed":
            return "prepare"
        if "deny" in verdicts or state == "blocked":
            return "deny"
        if selected_move.startswith("chat_") and action_count == 0:
            return "chat_only"
        return "degrade"

    @staticmethod
    def _has_matching_execution_ledger(
        envelope: dict[str, Any],
        authorizations: list[dict[str, Any]],
        tool_ledgers: list[dict[str, Any]],
    ) -> bool:
        allowed_actions = {
            (
                str(authorization.get("action_id") or ""),
                str(authorization.get("capability_id") or ""),
            )
            for authorization in authorizations
            if authorization.get("verdict") == "allow"
        }
        if not allowed_actions:
            return False
        turn_id = str(envelope.get("turn_id") or "")
        proposed_action_ids = {str(action.get("action_id") or "") for action in envelope.get("proposed_actions", [])}
        for ledger in tool_ledgers:
            action_key = (
                str(ledger.get("action_id") or ""),
                str(ledger.get("capability_id") or ""),
            )
            authorization = ledger.get("authorization") if isinstance(ledger.get("authorization"), dict) else {}
            if (
                str(ledger.get("turn_id") or "") == turn_id
                and str(ledger.get("action_id") or "") in proposed_action_ids
                and action_key in allowed_actions
                and authorization.get("verdict") == "allow"
                and str(authorization.get("turn_id") or "") == turn_id
                and str(authorization.get("action_id") or "") == str(ledger.get("action_id") or "")
                and str(authorization.get("capability_id") or "") == str(ledger.get("capability_id") or "")
                and str(authorization.get("decision_id") or "")
            ):
                return True
        return False

    @staticmethod
    def _matching_governor_authorization(
        governor_decision: dict[str, Any],
        *,
        turn_id: str,
        expected_capability_id: str,
        action_id: str | None,
    ) -> dict[str, Any] | None:
        authorizations = governor_decision.get("authorizations")
        if not isinstance(authorizations, list):
            return None
        for authorization in authorizations:
            if not isinstance(authorization, dict):
                continue
            if str(authorization.get("verdict") or "") != "allow":
                continue
            if str(authorization.get("turn_id") or "") != turn_id:
                continue
            if str(authorization.get("capability_id") or "") != expected_capability_id:
                continue
            if action_id is not None and str(authorization.get("action_id") or "") != str(action_id):
                continue
            if not str(authorization.get("decision_id") or ""):
                continue
            return authorization
        return None

    @staticmethod
    def _has_matching_governor_proposed_action(
        governor_decision: dict[str, Any],
        *,
        authorization: dict[str, Any],
        expected_action_type: str | None,
    ) -> bool:
        envelope = governor_decision.get("envelope") if isinstance(governor_decision.get("envelope"), dict) else {}
        proposed_actions = envelope.get("proposed_actions") if isinstance(envelope.get("proposed_actions"), list) else []
        for action in proposed_actions:
            if not isinstance(action, dict):
                continue
            if str(action.get("action_id") or "") != str(authorization.get("action_id") or ""):
                continue
            if str(action.get("capability_id") or "") != str(authorization.get("capability_id") or ""):
                continue
            if expected_action_type is not None and str(action.get("action_type") or "") != expected_action_type:
                continue
            return True
        return False

    @staticmethod
    def _matching_governor_tool_ledger(
        governor_decision: dict[str, Any],
        *,
        authorization: dict[str, Any],
        turn_id: str,
        expected_capability_id: str,
        tool_name: str | None,
        require_pre_execution_ledger: bool,
    ) -> dict[str, Any] | None:
        ledgers = governor_decision.get("tool_ledgers")
        if not isinstance(ledgers, list):
            return None
        for ledger in ledgers:
            if not isinstance(ledger, dict):
                continue
            ledger_authorization = ledger.get("authorization") if isinstance(ledger.get("authorization"), dict) else {}
            result = ledger.get("result") if isinstance(ledger.get("result"), dict) else {}
            if str(ledger.get("turn_id") or "") != turn_id:
                continue
            if str(ledger.get("action_id") or "") != str(authorization.get("action_id") or ""):
                continue
            if str(ledger.get("capability_id") or "") != expected_capability_id:
                continue
            if tool_name is not None and str(ledger.get("tool_name") or "") != str(tool_name):
                continue
            if require_pre_execution_ledger and str(result.get("status") or "") != "not_started":
                continue
            if str(ledger_authorization.get("verdict") or "") != "allow":
                continue
            if str(ledger_authorization.get("turn_id") or "") != turn_id:
                continue
            if str(ledger_authorization.get("action_id") or "") != str(authorization.get("action_id") or ""):
                continue
            if str(ledger_authorization.get("capability_id") or "") != expected_capability_id:
                continue
            if str(ledger_authorization.get("decision_id") or "") != str(authorization.get("decision_id") or ""):
                continue
            return ledger
        return None

    @staticmethod
    def _governor_consumer_verification(
        *,
        allowed: bool,
        reason_codes: list[str],
        governor_decision: dict[str, Any] | None,
        authorization: dict[str, Any] | None = None,
        ledger: dict[str, Any] | None = None,
        expected_capability_id: str | None = None,
        expected_action_type: str | None = None,
        tool_name: str | None = None,
    ) -> dict[str, Any]:
        return {
            "schema_version": "governor-consumer-verification-v1",
            "allowed": allowed,
            "reason_codes": reason_codes,
            "source_kind": "governor_decision" if isinstance(governor_decision, dict) else "missing_governor_decision",
            "decision_id": str((governor_decision or {}).get("decision_id") or "") or None,
            "turn_id": str((governor_decision or {}).get("turn_id") or "") or None,
            "outcome": str((governor_decision or {}).get("outcome") or "") or None,
            "expected_capability_id": expected_capability_id,
            "expected_action_type": expected_action_type,
            "tool_name": tool_name,
            "action_id": str((authorization or {}).get("action_id") or "") or None,
            "capability_id": str((authorization or {}).get("capability_id") or "") or None,
            "authorization_decision_id": str((authorization or {}).get("decision_id") or "") or None,
            "ledger_id": str((ledger or {}).get("ledger_id") or "") or None,
        }

    @staticmethod
    def _assert_authorization_matches_action(
        envelope: dict[str, Any],
        action: dict[str, Any],
        authorization: dict[str, Any],
    ) -> None:
        mismatches: list[str] = []
        if str(authorization.get("turn_id") or "") != str(envelope.get("turn_id") or ""):
            mismatches.append("turn_id")
        if str(authorization.get("action_id") or "") != str(action.get("action_id") or ""):
            mismatches.append("action_id")
        if str(authorization.get("capability_id") or "") != str(action.get("capability_id") or ""):
            mismatches.append("capability_id")
        if mismatches:
            raise ValueError(f"authorization does not match proposed action: {', '.join(mismatches)}")

    @staticmethod
    def _assert_ledger_authorization_binding(ledger: dict[str, Any]) -> None:
        authorization = ledger.get("authorization") if isinstance(ledger.get("authorization"), dict) else {}
        mismatches: list[str] = []
        if str(authorization.get("turn_id") or "") != str(ledger.get("turn_id") or ""):
            mismatches.append("turn_id")
        if str(authorization.get("action_id") or "") != str(ledger.get("action_id") or ""):
            mismatches.append("action_id")
        if str(authorization.get("capability_id") or "") != str(ledger.get("capability_id") or ""):
            mismatches.append("capability_id")
        if not str(authorization.get("decision_id") or ""):
            mismatches.append("decision_id")
        if mismatches:
            raise ValueError(f"tool ledger authorization binding mismatch: {', '.join(mismatches)}")

    def _governor_reasons(
        self,
        outcome: str,
        envelope: dict[str, Any],
        authorizations: list[dict[str, Any]],
    ) -> list[str]:
        reasons = [
            "fresh_user_intent_is_authority",
            "legacy_detectors_are_evidence_only",
        ]
        if outcome == "execute":
            reasons.append("governor_authorized_execution")
        elif (
            envelope["action_authority"].get("state") == "executable"
            and any(authorization.get("verdict") == "allow" for authorization in authorizations)
        ):
            reasons.append("governor_missing_tool_ledger_for_authorized_execution")
        elif outcome == "interrupt":
            reasons.append("governor_requires_explicit_confirmation")
        elif outcome == "read_only":
            reasons.append("governor_allows_read_only_state_access")
        elif outcome == "chat_only":
            reasons.append("governor_keeps_turn_conversational")
        elif outcome == "prepare":
            reasons.append("governor_allows_preparation_without_execution")
        elif outcome == "deny":
            reasons.append("governor_denies_action_boundary")
        else:
            reasons.append("governor_degrades_to_safe_surface_behavior")
        for authorization in authorizations:
            for reason in authorization.get("reasons", []):
                if reason not in reasons:
                    reasons.append(str(reason))
        if envelope["action_authority"].get("requires_human_confirmation"):
            reasons.append("human_confirmation_required_by_envelope")
        for reason in self._fresh_user_intent_authority_reason_codes(envelope):
            if reason not in reasons:
                reasons.append(reason)
        return reasons

    def _default_reply_style(self, outcome: str) -> str:
        if outcome == "degrade":
            return "compact_status"
        return "human_conversational"

    def _default_reply_instruction(self, outcome: str) -> str:
        if outcome == "execute":
            return "Proceed only with the authorized action and record the result ledger."
        if outcome == "interrupt":
            return "Ask for explicit approval before any high-agency action executes."
        if outcome == "read_only":
            return "Answer from fresh read-only state; do not mutate state."
        if outcome == "prepare":
            return "Prepare the action plan without executing tools or mutating state."
        if outcome == "deny":
            return "Briefly explain why the action boundary was denied and stay conversational."
        if outcome == "degrade":
            return "Use the safest non-executing surface behavior and preserve evidence for review."
        return "Answer conversationally; do not launch, write, schedule, publish, or run tools."

    def _validate_self_evolution_policy(
        self,
        *,
        mode: str,
        verdict: str,
        readiness_score: dict[str, Any],
        target_components: list[dict[str, Any]],
        change_manifests: list[dict[str, Any]],
        live_surface_required: bool,
    ) -> None:
        if mode == "observe" and verdict != "not_ready":
            raise ValueError("observe mode cannot promote or roll back changes.")
        if verdict in PROMOTION_VERDICTS:
            if not change_manifests:
                raise ValueError("self-evolution promotion requires at least one accepted change manifest.")
            non_accepted = [
                str(manifest.get("change_id") or "change:unknown")
                for manifest in change_manifests
                if manifest.get("verdict") != "accepted"
            ]
            if non_accepted:
                raise ValueError(
                    "self-evolution promotion requires accepted change manifests; "
                    f"not accepted: {', '.join(non_accepted)}"
                )
            if live_surface_required or any(bool(manifest.get("live_proof_required")) for manifest in change_manifests):
                raise ValueError("self-evolution promotion cannot proceed while live proof is still required.")
            required_status = "private_ready" if verdict == "promote_private" else "release_candidate"
            readiness_status = str(readiness_score.get("overall", {}).get("status") or "blocked")
            if READINESS_STATUS_RANK.get(readiness_status, 0) < READINESS_STATUS_RANK[required_status]:
                raise ValueError(
                    f"self-evolution {verdict} requires readiness status {required_status} or better; "
                    f"got {readiness_status}."
                )
        if verdict == "rollback":
            if mode != "rollback":
                raise ValueError("rollback verdict requires rollback mode.")
            if not any(manifest.get("verdict") == "rolled_back" for manifest in change_manifests):
                raise ValueError("rollback verdict requires at least one rolled_back change manifest.")

        if self._self_evolution_requires_protected_approval(mode=mode, verdict=verdict):
            missing_approval = self._protected_components_missing_approval(
                target_components=target_components,
                change_manifests=change_manifests,
            )
            if missing_approval:
                raise ValueError(
                    "protected self-evolution components require approval evidence: "
                    f"{', '.join(missing_approval)}"
                )

    def _change_manifest_runner_decision(
        self,
        *,
        mode: str,
        readiness_score: dict[str, Any],
        target_components: list[dict[str, Any]],
        change_manifests: list[dict[str, Any]],
        live_surface_required: bool,
        requested_verdict: str | None,
    ) -> dict[str, str | list[str]]:
        reasons: list[str] = []
        if mode == "observe":
            reasons.append("observe_mode_records_evidence_only")
            return self._runner_decision("not_ready", reasons)
        if requested_verdict == "rollback" or mode == "rollback":
            if mode != "rollback":
                reasons.append("rollback_requires_rollback_mode")
            if not any(manifest.get("verdict") == "rolled_back" for manifest in change_manifests):
                reasons.append("rollback_requires_rolled_back_manifest")
            return self._runner_decision("rollback" if not reasons else "not_ready", reasons or ["rollback_manifest_present"])
        if mode != "promote":
            reasons.append(f"{mode}_mode_cannot_promote")
        if not change_manifests:
            reasons.append("no_change_manifests")
        non_accepted = [
            str(manifest.get("change_id") or "change:unknown")
            for manifest in change_manifests
            if manifest.get("verdict") != "accepted"
        ]
        if non_accepted:
            reasons.append(f"non_accepted_change_manifests:{','.join(non_accepted)}")
        if live_surface_required or any(bool(manifest.get("live_proof_required")) for manifest in change_manifests):
            reasons.append("live_proof_still_required")
        missing_approval = self._protected_components_missing_approval(
            target_components=target_components,
            change_manifests=change_manifests,
        )
        if missing_approval:
            reasons.append(f"protected_component_requires_approval:{','.join(missing_approval)}")

        requested = requested_verdict if requested_verdict in PROMOTION_VERDICTS else None
        readiness_status = str(readiness_score.get("overall", {}).get("status") or "blocked")
        if requested is None:
            requested = (
                "promote_release_candidate"
                if READINESS_STATUS_RANK.get(readiness_status, 0) >= READINESS_STATUS_RANK["release_candidate"]
                else "promote_private"
            )
        required_status = "private_ready" if requested == "promote_private" else "release_candidate"
        if READINESS_STATUS_RANK.get(readiness_status, 0) < READINESS_STATUS_RANK[required_status]:
            reasons.append(f"readiness_below_{required_status}:{readiness_status}")
        if reasons:
            return self._runner_decision("not_ready", reasons)
        return self._runner_decision(requested, ["accepted_change_manifests_ready"])

    @staticmethod
    def _runner_decision(verdict: str, reasons: list[str]) -> dict[str, str | list[str]]:
        reason_text = ", ".join(reasons) if reasons else "no_blockers"
        if verdict == "not_ready":
            summary = f"Change manifest runner is not ready to promote: {reason_text}."
        elif verdict == "rollback":
            summary = f"Change manifest runner selected rollback: {reason_text}."
        else:
            summary = f"Change manifest runner selected {verdict}: {reason_text}."
        return {"verdict": verdict, "summary": summary, "reasons": reasons}

    @staticmethod
    def _self_evolution_requires_protected_approval(*, mode: str, verdict: str) -> bool:
        return verdict != "not_ready" and (
            mode in MUTATING_EVOLUTION_MODES or verdict in PROMOTION_VERDICTS or verdict == "rollback"
        )

    @staticmethod
    def _protected_components_missing_approval(
        *,
        target_components: list[dict[str, Any]],
        change_manifests: list[dict[str, Any]],
    ) -> list[str]:
        approved_component_ids = {
            str(manifest.get("target_component", {}).get("component_id"))
            for manifest in change_manifests
            if manifest.get("human_approval_ref") is not None
        }
        missing: list[str] = []
        for component in target_components:
            component_type = str(component.get("component_type") or "")
            component_id = str(component.get("component_id") or "")
            if component_type in PROTECTED_EVOLUTION_COMPONENTS and component_id not in approved_component_ids:
                missing.append(component_id or component_type)
        return missing

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
    def _execute_verdict_for_status(status: str) -> str:
        if status == "not_started":
            return "skipped"
        if status in {"success", "partial"}:
            return "passed"
        return "failed"

    @staticmethod
    def _assert_execution_status_authorized(authorization_verdict: str, status: str) -> None:
        if status in EXECUTED_TOOL_STATUSES and authorization_verdict != "allow":
            raise ValueError(
                "Tool execution status requires allow authorization; blocked or interrupted actions may only "
                "record a not_started ledger."
            )

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

    def _restrictions_for_decision(self, verdict: str, action: dict[str, Any]) -> dict[str, bool]:
        restrictions = self._restrictions_for_action(action)
        if verdict == "deny":
            return {
                **restrictions,
                "network_allowed": False,
                "write_allowed": False,
                "publish_allowed": False,
            }
        return restrictions

    @staticmethod
    def _legacy_plane_has_high_agency_risk(authority_risk: dict[str, Any]) -> bool:
        return any(bool(authority_risk.get(key)) for key in LEGACY_PLANE_HIGH_AGENCY_RISK_KEYS)

    def _validate_legacy_plane_disposition(
        self,
        *,
        authority_risk: dict[str, bool],
        disposition: str,
        governor_required: bool,
        evidence_only: bool,
        consumer_of_governor: bool,
        ledger_required: bool,
        blockers: list[str],
    ) -> None:
        high_agency_risk = self._legacy_plane_has_high_agency_risk(authority_risk)
        if disposition == "release_blocker":
            if not blockers:
                raise ValueError("release-blocker legacy authority planes require at least one blocker.")
            return
        if blockers:
            raise ValueError("non-blocking legacy authority planes cannot carry release blockers.")
        if disposition in {"removed", "quarantined"}:
            return
        if disposition == "evidence_adapter":
            if high_agency_risk:
                raise ValueError("evidence adapters cannot retain high-agency execution risk.")
            if not evidence_only or consumer_of_governor:
                raise ValueError("evidence_adapter requires evidence_only and no consumer authority.")
        if disposition == "canonical_consumer":
            if not (governor_required and consumer_of_governor and ledger_required):
                raise ValueError("canonical legacy consumers require Governor authority and tool ledgers.")
