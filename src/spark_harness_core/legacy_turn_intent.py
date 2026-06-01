from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Any, Literal

from spark_harness_core.kernel import HarnessKernel, artifact_ref, evidence_ref, trace_ref
from spark_harness_core.schemas import validate_instance


MutationClass = Literal[
    "none",
    "read_only",
    "writes_memory",
    "writes_files",
    "launches_mission",
    "creates_schedule",
    "deletes_schedule",
    "creates_chip",
    "publishes",
    "external_network",
]

_MUTATION_CLASSES = frozenset(
    {
        "none",
        "read_only",
        "writes_memory",
        "writes_files",
        "launches_mission",
        "creates_schedule",
        "deletes_schedule",
        "creates_chip",
        "publishes",
        "external_network",
    }
)

_SURFACES = frozenset(
    {
        "telegram",
        "cli",
        "builder",
        "spawner",
        "memory",
        "startup_operator",
        "recursive_swarm",
        "voice",
        "domain_chip",
        "browser",
        "computer_use",
        "api",
        "test_harness",
        "future_surface",
    }
)


@dataclass(frozen=True)
class HarnessDirective:
    mode: str
    no_execution: bool
    no_publish: bool
    local_only: bool
    explanation_only: bool
    quoted_or_meta_language: bool


@dataclass(frozen=True)
class HarnessSelectedIntent:
    kind: str
    owner_system: str
    action: str | None
    confidence: str
    requires_confirmation: bool
    source: str


@dataclass(frozen=True)
class HarnessSessionScope:
    session_key: str
    surface: str
    conversation_kind: str
    user_ref: str
    chat_ref: str | None
    memory_load_policy: str
    pending_state_scope: str


@dataclass(frozen=True)
class HarnessToolPolicy:
    allowed_tools: tuple[str, ...]
    denied_tools: tuple[str, ...]
    enabled_toolsets: tuple[str, ...]
    mutation_classes_allowed: tuple[MutationClass, ...]
    requires_approval_for: tuple[MutationClass, ...]
    network_policy: str
    elevated_allowed: bool


@dataclass(frozen=True)
class HarnessExecutionPolicy:
    can_mutate_files: bool
    can_launch_mission: bool
    can_write_memory: bool
    can_delete_schedule: bool
    can_create_chip: bool
    can_publish: bool
    can_use_external_network: bool


@dataclass(frozen=True)
class TurnIntentEnvelope:
    schema: Literal["spark.turn_intent.v1"]
    turn_id: str
    trace_id: str
    surface: str
    directive: HarnessDirective
    selected_intent: HarnessSelectedIntent
    session_scope: HarnessSessionScope
    tool_policy: HarnessToolPolicy
    execution_policy: HarnessExecutionPolicy
    threat_reason_codes: tuple[str, ...]


@dataclass(frozen=True)
class LegacyToolAuthorization:
    verdict: Literal["allowed", "blocked"]
    reason_codes: tuple[str, ...]
    turn_intent_envelope_vnext: dict[str, Any] | None
    proposed_action: dict[str, Any] | None
    authorization_decision: dict[str, Any] | None
    tool_call_ledger: dict[str, Any] | None


def _require_dict(value: Any, field: str) -> dict[str, Any]:
    nested = value.get(field) if isinstance(value, dict) else None
    if not isinstance(nested, dict):
        raise ValueError(f"Turn intent envelope missing object field: {field}")
    return nested


def _require_str(value: dict[str, Any], field: str) -> str:
    item = value.get(field)
    if not isinstance(item, str) or not item:
        raise ValueError(f"Turn intent envelope missing string field: {field}")
    return item


def _bool(value: dict[str, Any], field: str) -> bool:
    return bool(value.get(field))


def _tuple_str(value: dict[str, Any], field: str) -> tuple[str, ...]:
    items = value.get(field)
    if not isinstance(items, list):
        raise ValueError(f"Turn intent envelope missing list field: {field}")
    return tuple(str(item) for item in items if isinstance(item, str))


def _safe_id(prefix: str, raw: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9_.:-]+", "-", str(raw or "")).strip("._:-").lower()
    if not normalized:
        normalized = "item"
    value = f"{prefix}:{normalized}"
    if len(value) <= 127 and re.match(r"^[a-z][a-z0-9_.:-]{2,127}$", value):
        return value
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]
    budget = max(4, 126 - len(prefix) - len(digest) - 2)
    trimmed = normalized[:budget].strip("._:-") or "item"
    value = f"{prefix}:{trimmed}:{digest}"
    if re.match(r"^[a-z][a-z0-9_.:-]{2,127}$", value):
        return value
    return f"{prefix}:item:{digest}"


def _surface(value: str) -> str:
    return value if value in _SURFACES else "future_surface"


def _confidence(value: str) -> float:
    return {
        "explicit": 0.95,
        "contextual": 0.72,
        "ambiguous": 0.42,
        "blocked": 0.0,
    }.get(value, 0.5)


def parse_turn_intent_envelope(payload: dict[str, Any]) -> TurnIntentEnvelope:
    if not isinstance(payload, dict):
        raise ValueError("Turn intent envelope must be an object")
    if payload.get("schema") != "spark.turn_intent.v1":
        raise ValueError("Unsupported turn intent envelope schema")

    directive = _require_dict(payload, "directive")
    selected_intent = _require_dict(payload, "selectedIntent")
    session_scope = _require_dict(payload, "sessionScope")
    tool_policy = _require_dict(payload, "toolPolicy")
    execution_policy = _require_dict(payload, "executionPolicy")
    threat_defense = _require_dict(payload, "threatDefense")

    return TurnIntentEnvelope(
        schema="spark.turn_intent.v1",
        turn_id=_require_str(payload, "turnId"),
        trace_id=_require_str(payload, "traceId"),
        surface=_require_str(payload, "surface"),
        directive=HarnessDirective(
            mode=_require_str(directive, "mode"),
            no_execution=_bool(directive, "noExecution"),
            no_publish=_bool(directive, "noPublish"),
            local_only=_bool(directive, "localOnly"),
            explanation_only=_bool(directive, "explanationOnly"),
            quoted_or_meta_language=_bool(directive, "quotedOrMetaLanguage"),
        ),
        selected_intent=HarnessSelectedIntent(
            kind=_require_str(selected_intent, "kind"),
            owner_system=_require_str(selected_intent, "ownerSystem"),
            action=selected_intent.get("action") if isinstance(selected_intent.get("action"), str) else None,
            confidence=_require_str(selected_intent, "confidence"),
            requires_confirmation=_bool(selected_intent, "requiresConfirmation"),
            source=_require_str(selected_intent, "source"),
        ),
        session_scope=HarnessSessionScope(
            session_key=_require_str(session_scope, "sessionKey"),
            surface=_require_str(session_scope, "surface"),
            conversation_kind=_require_str(session_scope, "conversationKind"),
            user_ref=_require_str(session_scope, "userRef"),
            chat_ref=session_scope.get("chatRef") if isinstance(session_scope.get("chatRef"), str) else None,
            memory_load_policy=_require_str(session_scope, "memoryLoadPolicy"),
            pending_state_scope=_require_str(session_scope, "pendingStateScope"),
        ),
        tool_policy=HarnessToolPolicy(
            allowed_tools=_tuple_str(tool_policy, "allowedTools"),
            denied_tools=_tuple_str(tool_policy, "deniedTools"),
            enabled_toolsets=_tuple_str(tool_policy, "enabledToolsets"),
            mutation_classes_allowed=tuple(
                item for item in _tuple_str(tool_policy, "mutationClassesAllowed") if item in _MUTATION_CLASSES
            ),
            requires_approval_for=tuple(
                item for item in _tuple_str(tool_policy, "requiresApprovalFor") if item in _MUTATION_CLASSES
            ),
            network_policy=_require_str(tool_policy, "networkPolicy"),
            elevated_allowed=_bool(tool_policy, "elevatedAllowed"),
        ),
        execution_policy=HarnessExecutionPolicy(
            can_mutate_files=_bool(execution_policy, "canMutateFiles"),
            can_launch_mission=_bool(execution_policy, "canLaunchMission"),
            can_write_memory=_bool(execution_policy, "canWriteMemory"),
            can_delete_schedule=_bool(execution_policy, "canDeleteSchedule"),
            can_create_chip=_bool(execution_policy, "canCreateChip"),
            can_publish=_bool(execution_policy, "canPublish"),
            can_use_external_network=_bool(execution_policy, "canUseExternalNetwork"),
        ),
        threat_reason_codes=_tuple_str(threat_defense, "reasonCodes"),
    )


def _action_type(mutation_class: MutationClass, publishes: bool, external_network: bool) -> str:
    if publishes or mutation_class == "publishes":
        return "publish"
    if external_network or mutation_class == "external_network":
        return "external_api_call"
    return {
        "none": "read",
        "read_only": "read",
        "writes_memory": "write_memory",
        "writes_files": "edit_file",
        "launches_mission": "launch_mission",
        "creates_schedule": "schedule",
        "deletes_schedule": "schedule",
        "creates_chip": "create_domain_chip",
    }.get(mutation_class, "run_command")


def _risk_tier(mutation_class: MutationClass, publishes: bool, external_network: bool) -> str:
    if publishes or mutation_class == "publishes":
        return "high"
    if external_network or mutation_class == "external_network":
        return "medium"
    return {
        "none": "none",
        "read_only": "read",
        "writes_memory": "low",
        "writes_files": "medium",
        "launches_mission": "medium",
        "creates_schedule": "medium",
        "deletes_schedule": "medium",
        "creates_chip": "medium",
    }.get(mutation_class, "medium")


def _policy_reasons(
    envelope: TurnIntentEnvelope,
    *,
    tool_name: str,
    owner_system: str,
    mutation_class: MutationClass,
    publishes: bool,
    external_network: bool,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if envelope.directive.no_execution and mutation_class not in ("none", "read_only"):
        reasons.append("no_execution_boundary")
    if envelope.directive.no_publish and publishes:
        reasons.append("no_publish_boundary")
    if external_network and not envelope.execution_policy.can_use_external_network:
        reasons.append("external_network_not_authorized")
    if external_network and envelope.tool_policy.network_policy == "none":
        reasons.append("network_policy_blocks_external")
    if tool_name in envelope.tool_policy.denied_tools:
        reasons.append("tool_denied_by_policy")
    if "*" not in envelope.tool_policy.allowed_tools and tool_name not in envelope.tool_policy.allowed_tools:
        reasons.append("tool_not_allowed_by_policy")
    if mutation_class not in envelope.tool_policy.mutation_classes_allowed:
        reasons.append("mutation_class_not_authorized")
    if owner_system != envelope.selected_intent.owner_system and owner_system != "spark-telegram-bot":
        reasons.append("owner_mismatch")
    if mutation_class == "writes_memory" and not envelope.execution_policy.can_write_memory:
        reasons.append("write_memory_not_authorized")
    if mutation_class == "writes_files" and not envelope.execution_policy.can_mutate_files:
        reasons.append("file_mutation_not_authorized")
    if mutation_class == "launches_mission" and not envelope.execution_policy.can_launch_mission:
        reasons.append("mission_launch_not_authorized")
    if mutation_class == "deletes_schedule" and not envelope.execution_policy.can_delete_schedule:
        reasons.append("schedule_delete_not_authorized")
    if mutation_class == "creates_chip" and not envelope.execution_policy.can_create_chip:
        reasons.append("chip_creation_not_authorized")
    if (publishes or mutation_class == "publishes") and not envelope.execution_policy.can_publish:
        reasons.append("publish_not_authorized")
    return tuple(reasons)


def _core_evidence(envelope: TurnIntentEnvelope) -> list[dict[str, Any]]:
    confidence = _confidence(envelope.selected_intent.confidence)
    trace = trace_ref("legacy_turn", f"Legacy TurnIntent V1 trace {envelope.trace_id}.", redaction_class="private")
    evidence = [
        evidence_ref(
            "fresh_user_intent",
            envelope.surface,
            f"Fresh turn selected {envelope.selected_intent.kind}/{envelope.selected_intent.action or envelope.directive.mode}.",
            confidence=confidence,
        ),
        evidence_ref(
            "route_candidate",
            envelope.selected_intent.owner_system,
            f"Legacy route candidate came from {envelope.selected_intent.source}.",
            confidence=confidence,
        ),
    ]
    for item in evidence:
        item["trace_refs"] = [trace]
    if envelope.directive.no_execution:
        evidence.append(
            evidence_ref("negative_intent", envelope.surface, "Legacy directive blocks execution.", confidence=0.98)
        )
    if envelope.directive.quoted_or_meta_language:
        evidence.append(
            evidence_ref("meta_language", envelope.surface, "Legacy directive marks quoted or meta-language.", confidence=0.95)
        )
    return evidence


def _proposed_action(
    kernel: HarnessKernel,
    envelope: TurnIntentEnvelope,
    *,
    tool_name: str,
    owner_system: str,
    mutation_class: MutationClass,
    publishes: bool,
    external_network: bool,
) -> dict[str, Any]:
    action_type = _action_type(mutation_class, publishes, external_network)
    risk_tier = _risk_tier(mutation_class, publishes, external_network)
    return kernel.proposed_action(
        capability_id=_safe_id("capability", f"{owner_system}:{tool_name}"),
        action_type=action_type,
        risk_tier=risk_tier,
        summary=f"Builder bridge proposed {action_type} via {tool_name}.",
        args_path=f"builder://turns/{_safe_id('turn', envelope.turn_id)}/actions/{_safe_id('tool', tool_name)}",
        requires_confirmation=risk_tier in {"high", "critical"} or mutation_class in envelope.tool_policy.requires_approval_for,
    )


def _vnext_envelope(
    kernel: HarnessKernel,
    legacy: TurnIntentEnvelope,
    action: dict[str, Any],
    *,
    policy_allowed: bool,
) -> dict[str, Any]:
    if not policy_allowed:
        selected_move = "chat_explain"
        proposed_actions: list[dict[str, Any]] = []
        authority_state = "chat_only"
    elif action["action_type"] == "read":
        selected_move = "read_current_state"
        proposed_actions = [action]
        authority_state = "read_only"
    else:
        selected_move = "execute_action"
        proposed_actions = [action]
        authority_state = "executable"

    envelope = kernel.create_envelope(
        selected_move=selected_move,
        intent_summary=(
            f"Builder bridge consumed legacy {legacy.schema} as evidence for "
            f"{legacy.selected_intent.kind}/{legacy.selected_intent.action or legacy.directive.mode}."
        ),
        raw_turn_summary=f"Legacy TurnIntent trace {legacy.trace_id}; raw text remains offloaded.",
        evidence=_core_evidence(legacy),
        proposed_actions=proposed_actions,
        authority_state=authority_state,
        risk_tier=action["risk_tier"] if proposed_actions else "none",
        confidence=_confidence(legacy.selected_intent.confidence),
    )
    envelope["surface"] = _surface(legacy.surface)
    return validate_instance("turn-intent-envelope-vnext", envelope)


def _deny_decision(
    decision: dict[str, Any],
    reasons: tuple[str, ...],
) -> dict[str, Any]:
    denied = dict(decision)
    denied["verdict"] = "deny"
    denied["reasons"] = list(reasons)
    denied["approval"] = {"required": False, "status": "not_required"}
    denied["restrictions"] = {
        **dict(denied.get("restrictions") or {}),
        "network_allowed": False,
        "write_allowed": False,
        "publish_allowed": False,
    }
    return validate_instance("authorization-decision-v1", denied)


def authorize_legacy_tool_call(
    envelope: TurnIntentEnvelope | None,
    *,
    tool_name: str,
    owner_system: str,
    mutation_class: MutationClass,
    publishes: bool = False,
    external_network: bool = False,
) -> LegacyToolAuthorization:
    if envelope is None:
        return LegacyToolAuthorization("blocked", ("missing_or_invalid_envelope",), None, None, None, None)

    kernel = HarnessKernel(surface=_surface(envelope.surface), actor_id_ref=envelope.session_scope.user_ref)
    reasons = _policy_reasons(
        envelope,
        tool_name=tool_name,
        owner_system=owner_system,
        mutation_class=mutation_class,
        publishes=publishes,
        external_network=external_network,
    )
    action = _proposed_action(
        kernel,
        envelope,
        tool_name=tool_name,
        owner_system=owner_system,
        mutation_class=mutation_class,
        publishes=publishes,
        external_network=external_network,
    )
    vnext = _vnext_envelope(kernel, envelope, action, policy_allowed=not reasons)
    approval_ref = None
    if (
        not reasons
        and action["risk_tier"] in {"high", "critical"}
        and envelope.selected_intent.confidence == "explicit"
        and not envelope.selected_intent.requires_confirmation
    ):
        approval_ref = evidence_ref(
            "human_confirmation",
            envelope.surface,
            "Fresh explicit TurnIntent envelope grants approval for this high-risk action.",
            confidence=0.95,
        )
    decision = kernel.authorize(vnext, action, approval_ref=approval_ref)
    if reasons:
        decision = _deny_decision(decision, reasons)
    ledger = kernel.record_tool_call(
        envelope=vnext,
        action=action,
        authorization=decision,
        tool_name=tool_name,
        status="not_started",
        output_path=f"builder://turns/{_safe_id('turn', envelope.turn_id)}/tool-ledgers/{_safe_id('tool', tool_name)}",
        summary=(
            "Tool call authorized and awaiting execution."
            if decision["verdict"] == "allow"
            else "Tool call blocked by Harness Core authorization."
        ),
    )

    if decision["verdict"] == "allow":
        return LegacyToolAuthorization("allowed", (), vnext, action, decision, ledger)
    return LegacyToolAuthorization(
        "blocked",
        tuple(str(reason) for reason in decision["reasons"]),
        vnext,
        action,
        decision,
        ledger,
    )


def authorize_tool_call(
    envelope: TurnIntentEnvelope | None,
    *,
    tool_name: str,
    owner_system: str,
    mutation_class: MutationClass,
    publishes: bool = False,
    external_network: bool = False,
) -> tuple[Literal["allowed", "blocked"], tuple[str, ...]]:
    authorization = authorize_legacy_tool_call(
        envelope,
        tool_name=tool_name,
        owner_system=owner_system,
        mutation_class=mutation_class,
        publishes=publishes,
        external_network=external_network,
    )
    return authorization.verdict, authorization.reason_codes


def _matching_vnext_action(
    envelope: dict[str, Any],
    *,
    expected_capability_id: str,
    expected_action_type: str,
) -> dict[str, Any] | None:
    for action in envelope.get("proposed_actions") or []:
        if not isinstance(action, dict):
            continue
        if action.get("capability_id") == expected_capability_id and action.get("action_type") == expected_action_type:
            return action
    return None


def authorize_vnext_tool_call(
    envelope_payload: dict[str, Any] | None,
    *,
    tool_name: str,
    owner_system: str,
    mutation_class: MutationClass,
    publishes: bool = False,
    external_network: bool = False,
) -> LegacyToolAuthorization:
    if not isinstance(envelope_payload, dict):
        return LegacyToolAuthorization("blocked", ("missing_or_invalid_envelope",), None, None, None, None)
    try:
        envelope = validate_instance("turn-intent-envelope-vnext", envelope_payload)
    except Exception:
        return LegacyToolAuthorization("blocked", ("missing_or_invalid_envelope",), None, None, None, None)

    kernel = HarnessKernel(
        surface=_surface(str(envelope.get("surface") or "future_surface")),
        actor_id_ref=str((envelope.get("actor") or {}).get("id_ref") or "human:redacted"),
    )
    expected_action_type = _action_type(mutation_class, publishes, external_network)
    expected_capability_id = _safe_id("capability", f"{owner_system}:{tool_name}")
    action = _matching_vnext_action(
        envelope,
        expected_capability_id=expected_capability_id,
        expected_action_type=expected_action_type,
    )
    reasons: list[str] = []
    freshness = envelope.get("freshness") if isinstance(envelope.get("freshness"), dict) else {}
    if not freshness.get("fresh_user_intent_present"):
        reasons.append("fresh_user_intent_missing")
    if action is None:
        reasons.append("proposed_action_not_authorized")
        action = kernel.proposed_action(
            capability_id=expected_capability_id,
            action_type=expected_action_type,
            risk_tier=_risk_tier(mutation_class, publishes, external_network),
            summary=f"Builder bridge expected {expected_action_type} via {tool_name}.",
            args_path=f"builder://vnext/actions/{_safe_id('tool', tool_name)}",
            requires_confirmation=False,
        )

    approval_ref = None
    authority = envelope.get("action_authority") if isinstance(envelope.get("action_authority"), dict) else {}
    if isinstance(authority.get("confirmation_ref"), dict):
        approval_ref = authority.get("confirmation_ref")
    decision = kernel.authorize(envelope, action, approval_ref=approval_ref)
    if reasons:
        decision = _deny_decision(decision, tuple(reasons))
    ledger = kernel.record_tool_call(
        envelope=envelope,
        action=action,
        authorization=decision,
        tool_name=tool_name,
        status="not_started",
        output_path=f"builder://turns/{_safe_id('turn', str(envelope.get('turn_id') or 'vnext'))}/tool-ledgers/{_safe_id('tool', tool_name)}",
        summary=(
            "Tool call authorized and awaiting execution."
            if decision["verdict"] == "allow"
            else "Tool call blocked by Harness Core authorization."
        ),
    )
    if decision["verdict"] == "allow":
        return LegacyToolAuthorization("allowed", (), envelope, action, decision, ledger)
    return LegacyToolAuthorization(
        "blocked",
        tuple(str(reason) for reason in decision["reasons"]),
        envelope,
        action,
        decision,
        ledger,
    )


def finalize_legacy_tool_call_ledger(
    ledger: dict[str, Any],
    *,
    status: str,
    output_path: str,
    summary: str,
    surface: str = "builder",
    error_path: str | None = None,
    rollback_path: str | None = None,
) -> dict[str, Any]:
    kernel = HarnessKernel(surface=_surface(surface))
    return kernel.finalize_tool_call_ledger(
        ledger,
        status=status,
        output_path=output_path,
        summary=summary,
        error_path=error_path,
        rollback_path=rollback_path,
    )
