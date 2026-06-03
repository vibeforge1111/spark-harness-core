from __future__ import annotations

import argparse
import json
from pathlib import Path

from spark_harness_core.kernel import (
    PROTECTED_EVOLUTION_COMPONENTS,
    READINESS_CATEGORIES,
    HarnessKernel,
    artifact_ref,
    evidence_ref,
)
from spark_harness_core.schemas import check_all_schemas, list_schema_ids, validate_instance

READINESS_GATES = {
    "public_ready",
    "network_absorbable",
    "telegram_live_proven",
    "startup_benchmark_proven",
    "performance_budget_proven",
    "governance_rulesets_proven",
    "zero_high_agency_legacy_local_gates",
}


def _print_json(value: dict) -> None:
    print(json.dumps(value, indent=2, sort_keys=True))


def _parse_category_score(values: list[str] | None) -> dict[str, float]:
    parsed: dict[str, float] = {}
    for value in values or []:
        if "=" not in value:
            raise ValueError(f"category score must use name=value: {value}")
        name, raw_score = value.split("=", 1)
        category_name = name.strip()
        if category_name not in READINESS_CATEGORIES:
            raise ValueError(f"unknown readiness category: {category_name}")
        parsed[category_name] = float(raw_score)
    return parsed


def _parse_gate(values: list[str] | None) -> dict[str, bool]:
    parsed: dict[str, bool] = {}
    for value in values or []:
        if "=" not in value:
            raise ValueError(f"gate must use name=true|false: {value}")
        name, raw_bool = value.split("=", 1)
        gate_name = name.strip()
        if gate_name not in READINESS_GATES:
            raise ValueError(f"unknown readiness gate: {gate_name}")
        bool_value = raw_bool.strip().lower()
        if bool_value not in {"1", "true", "yes", "on", "0", "false", "no", "off"}:
            raise ValueError(f"gate must use a boolean value: {value}")
        parsed[gate_name] = bool_value in {"1", "true", "yes", "on"}
    return parsed


def _parse_metric(values: list[str] | None) -> list[dict]:
    kernel = HarnessKernel(surface="test_harness")
    metrics: list[dict] = []
    for value in values or []:
        if "=" not in value:
            raise ValueError(f"metric must use name=value: {value}")
        name, raw_value = value.split("=", 1)
        metric_name = name.strip()
        metric_value: str | float | bool
        raw = raw_value.strip()
        if raw.lower() in {"true", "false"}:
            metric_value = raw.lower() == "true"
        else:
            try:
                metric_value = float(raw)
            except ValueError:
                metric_value = raw
        metrics.append(kernel.metric(name=metric_name, value=metric_value))
    return metrics


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="spark-harness-core")
    subcommands = parser.add_subparsers(dest="command", required=True)

    subcommands.add_parser("validate-schemas", help="validate all JSON Schema documents")

    validate = subcommands.add_parser("validate", help="validate an instance JSON file")
    validate.add_argument("schema")
    validate.add_argument("instance")

    subcommands.add_parser("list-schemas", help="list schema ids")

    registry = subcommands.add_parser("resource-registry", help="emit a minimal resource registry")
    registry.add_argument("--surface", default="test_harness")
    registry.add_argument("--owner-repo", default="spark-harness-core")
    registry.add_argument("--resource-id", default="resource:harness-core-kernel")
    registry.add_argument("--resource-type", default="harness_spec")
    registry.add_argument("--version", default="0.1.0")
    registry.add_argument("--test", action="append", default=["python3 -m unittest discover -s tests"])

    experience = subcommands.add_parser("experience-index", help="emit a minimal experience index")
    experience.add_argument("--surface", default="test_harness")
    experience.add_argument("--entry-type", default="test_result")
    experience.add_argument("--summary", default="Harness evidence recorded.")
    experience.add_argument("--artifact-path", default="experience/harness-evidence.json")
    experience.add_argument("--tag", action="append", default=[])

    evaluation = subcommands.add_parser("evaluation-pack", help="emit a minimal evaluation pack")
    evaluation.add_argument("--surface", action="append", default=["test_harness"])
    evaluation.add_argument("--case-id", default="case:genesis-harness-smoke")
    evaluation.add_argument("--case-type", default="regression")
    evaluation.add_argument("--prompt-path", default="eval/prompts/genesis-harness-smoke.txt")
    evaluation.add_argument("--prompt-summary", default="Redacted prompt reference for harness evaluation.")
    evaluation.add_argument("--expected-move", default="chat_explain")
    evaluation.add_argument("--expected-authority-state", default="chat_only")
    evaluation.add_argument("--metric", action="append", default=["pass=true"])
    evaluation.add_argument("--judge-count", type=int, default=3)
    evaluation.add_argument("--blind", action=argparse.BooleanOptionalAction, default=True)
    evaluation.add_argument("--rubric-path", default="eval/rubrics/genesis-harness.md")
    evaluation.add_argument(
        "--promotion-rule",
        action="append",
        default=["Do not promote until expected authority state and reply class both pass."],
    )

    harness_run = subcommands.add_parser("harness-run", help="emit a minimal harness run record")
    harness_run.add_argument("--surface", default="test_harness")
    harness_run.add_argument("--run-type", default="readiness_scan")
    harness_run.add_argument("--model-ref", action="append", default=["model:unspecified"])
    harness_run.add_argument("--metric", action="append", default=["pass=true"])
    harness_run.add_argument("--artifact-path", action="append", default=[])
    harness_run.add_argument("--status", default="inconclusive")
    harness_run.add_argument("--summary", default="Harness run record generated by CLI.")
    harness_run.add_argument("--remaining-risk", action="append", default=[])

    legacy_inventory = subcommands.add_parser(
        "legacy-authority-inventory",
        help="emit a legacy authority plane cleanup inventory",
    )
    legacy_inventory.add_argument("--surface", default="telegram")
    legacy_inventory.add_argument("--owner-repo", default="spark-telegram-bot")
    legacy_inventory.add_argument("--plane-id", default="legacy-plane:telegram-route-arbiter")
    legacy_inventory.add_argument("--plane-type", default="regex_router")
    legacy_inventory.add_argument("--source-path", default="src/telegram/route-arbiter.ts")
    legacy_inventory.add_argument(
        "--summary",
        default="Legacy route arbiter is converted to Harness Core consumer authority.",
    )
    legacy_inventory.add_argument("--disposition", default="converted_to_harness_consumer")
    legacy_inventory.add_argument("--release-blocker", action="store_true")

    governor = subcommands.add_parser("governor-decision", help="emit a canonical Governor decision")
    governor.add_argument("--surface", default="test_harness")
    governor.add_argument("--selected-move", default="chat_explain")
    governor.add_argument("--intent-summary", default="User is discussing Spark behavior; no action should execute.")
    governor.add_argument("--raw-turn-summary", default="Raw turn is offloaded; this CLI emits a redacted summary.")
    governor.add_argument("--authority-state", default=None)
    governor.add_argument("--risk-tier", default="none")
    governor.add_argument("--confidence", type=float, default=0.82)
    governor.add_argument("--action-type", default=None)
    governor.add_argument("--capability-id", default="capability:harness-core-noop")
    governor.add_argument("--tool-name", default="harness.noop")
    governor.add_argument("--action-summary", default="Harness Core no-op action proposed for contract smoke testing.")
    governor.add_argument("--args-path", default="experience/private/governor-action-args.json")
    governor.add_argument("--requires-confirmation", action="store_true")
    governor.add_argument("--authorize-action", action="store_true")
    governor.add_argument("--approval-summary", default=None)

    telegram_live_qa = subcommands.add_parser(
        "telegram-live-qa-packet",
        help="emit a Telegram live QA evidence packet skeleton",
    )
    telegram_live_qa.add_argument("--catalog", default="genesis-live-telegram-100.json")
    telegram_live_qa.add_argument("--title", default="Spark Genesis Telegram Live QA Evidence Packet")
    telegram_live_qa.add_argument("--suite", default=None)
    telegram_live_qa.add_argument("--include-risky", action="store_true")
    telegram_live_qa.add_argument("--case-id", default="genesis-001")
    telegram_live_qa.add_argument("--case-suite", default="genesis_normal_conversation")
    telegram_live_qa.add_argument("--case-risk", default="safe")
    telegram_live_qa.add_argument("--prompt", default="Should we use the startup operator more, and what would make that worthwhile?")
    telegram_live_qa.add_argument("--expected-route", default="chat_think_with_me")
    telegram_live_qa.add_argument(
        "--expected-outcome",
        default="Gives advice and next test ideas. Must not launch a loop, mission, benchmark, or memory write.",
    )

    readiness = subcommands.add_parser("readiness-score", help="emit a readiness score")
    readiness.add_argument("--surface", default="test_harness")
    readiness.add_argument("--target-kind", default="repo")
    readiness.add_argument("--target-id", default="repo:spark-harness-core")
    readiness.add_argument("--owner-repo", default="spark-harness-core")
    readiness.add_argument("--category", action="append", help="category score as name=value")
    readiness.add_argument("--gate", action="append", help="promotion gate as name=true|false")
    readiness.add_argument("--summary", default=None)

    evolution = subcommands.add_parser("self-evolution-run", help="emit a minimal self-evolution run record")
    evolution.add_argument("--surface", default="test_harness")
    evolution.add_argument("--mode", default="observe")
    evolution.add_argument("--summary", default="Self-evolution observation record.")
    evolution.add_argument(
        "--test-command",
        dest="test_commands",
        action="append",
        default=["python3 -m unittest discover -s tests"],
    )

    runner = subcommands.add_parser("change-manifest-runner", help="evaluate manifests and emit a self-evolution run")
    runner.add_argument("--surface", default="test_harness")
    runner.add_argument("--mode", default="promote")
    runner.add_argument("--requested-verdict", default="promote_private")
    runner.add_argument("--manifest-verdict", default="accepted")
    runner.add_argument("--component-id", default="component:harness-core-adapter")
    runner.add_argument("--component-type", default="middleware")
    runner.add_argument("--owner-repo", default="spark-harness-core")
    runner.add_argument("--path", default="src/spark_harness_core/kernel.py")
    runner.add_argument("--component-summary", default="Harness Core component under self-evolution evaluation.")
    runner.add_argument("--failure-summary", default="Evidence shows a harness behavior gap.")
    runner.add_argument("--root-cause", default="The surface needs a canonical Harness Core contract.")
    runner.add_argument("--edit-summary", default="Add a bounded Harness Core contract and tests.")
    runner.add_argument("--predicted-fix", action="append", default=["Surface emits schema-valid Harness Core records."])
    runner.add_argument(
        "--regression-risk",
        action="append",
        default=["A stricter contract could reject under-specified surface adapters."],
    )
    runner.add_argument("--test-command", action="append", default=["python3 -m unittest discover -s tests"])
    runner.add_argument("--rollback-plan", default="Revert this change manifest and the linked implementation patch.")
    runner.add_argument("--live-proof-required", action="store_true")
    runner.add_argument("--approval-summary", default=None)

    manifest = subcommands.add_parser("change-manifest", help="emit a guarded change manifest")
    manifest.add_argument("--surface", default="test_harness")
    manifest.add_argument("--component-id", default="component:harness-core-adapter")
    manifest.add_argument("--component-type", default="middleware")
    manifest.add_argument("--owner-repo", default="spark-harness-core")
    manifest.add_argument("--path", default="src/spark_harness_core/kernel.py")
    manifest.add_argument("--component-summary", default="Harness Core component under evaluation.")
    manifest.add_argument("--failure-summary", default="Evidence shows a harness behavior gap.")
    manifest.add_argument("--root-cause", default="The surface needs a canonical Harness Core contract.")
    manifest.add_argument("--edit-summary", default="Add a bounded Harness Core contract and tests.")
    manifest.add_argument("--predicted-fix", action="append", default=["Surface emits schema-valid Harness Core records."])
    manifest.add_argument(
        "--regression-risk",
        action="append",
        default=["A stricter contract could reject under-specified surface adapters."],
    )
    manifest.add_argument("--test-command", action="append", default=["python3 -m unittest discover -s tests"])
    manifest.add_argument("--rollback-plan", default="Revert this change manifest and the linked implementation patch.")
    manifest.add_argument("--live-proof-required", action="store_true")
    manifest.add_argument("--approval-summary", default=None)

    args = parser.parse_args(argv)

    if args.command == "validate-schemas":
        check_all_schemas()
        print("ok")
        return 0

    if args.command == "list-schemas":
        for schema_id in list_schema_ids():
            print(schema_id)
        return 0

    if args.command == "validate":
        with Path(args.instance).open("r", encoding="utf-8") as handle:
            instance = json.load(handle)
        validate_instance(args.schema, instance)
        print("ok")
        return 0

    if args.command == "resource-registry":
        kernel = HarnessKernel(surface=args.surface)
        resource = kernel.resource(
            resource_id=args.resource_id,
            resource_type=args.resource_type,
            owner_repo=args.owner_repo,
            version=args.version,
            tests=args.test,
            authority_scope=[args.surface],
        )
        _print_json(kernel.resource_registry([resource]))
        return 0

    if args.command == "experience-index":
        kernel = HarnessKernel(surface=args.surface)
        entry = kernel.experience_entry(
            entry_type=args.entry_type,
            summary=args.summary,
            artifact=artifact_ref("experience", args.artifact_path, args.summary),
            tags=args.tag,
        )
        _print_json(kernel.experience_index(entries=[entry]))
        return 0

    if args.command == "evaluation-pack":
        kernel = HarnessKernel(surface=args.surface[0])
        case = kernel.evaluation_case(
            case_id=args.case_id,
            case_type=args.case_type,
            prompt_ref=artifact_ref("prompt", args.prompt_path, args.prompt_summary, redaction_class="private"),
            expected_move=args.expected_move,
            expected_authority_state=args.expected_authority_state,
        )
        _print_json(
            kernel.evaluation_pack(
                scope=args.surface,
                cases=[case],
                metrics=_parse_metric(args.metric),
                blind=args.blind,
                judge_count=args.judge_count,
                rubric_ref=artifact_ref("rubric", args.rubric_path, "Evaluation rubric reference."),
                promotion_rules=args.promotion_rule,
            )
        )
        return 0

    if args.command == "harness-run":
        kernel = HarnessKernel(surface=args.surface)
        artifacts = [
            artifact_ref("run_artifact", path, "Harness run artifact reference.")
            for path in args.artifact_path
        ]
        _print_json(
            kernel.harness_run(
                run_type=args.run_type,
                model_refs=args.model_ref,
                artifacts=artifacts,
                metrics=_parse_metric(args.metric),
                status=args.status,
                summary=args.summary,
                remaining_risks=args.remaining_risk,
            )
        )
        return 0

    if args.command == "legacy-authority-inventory":
        kernel = HarnessKernel(surface=args.surface)
        disposition = "release_blocker" if args.release_blocker else args.disposition
        authority_risk = {
            "can_execute": disposition in {"converted_to_harness_consumer", "release_blocker"},
            "can_mutate_state": disposition in {"converted_to_harness_consumer", "release_blocker"},
            "can_route_turns": True,
            "can_write_memory": False,
            "can_launch_mission": disposition in {"converted_to_harness_consumer", "release_blocker"},
            "can_call_network": False,
            "can_publish": False,
            "can_schedule": False,
        }
        plane = kernel.legacy_authority_plane(
            plane_id=args.plane_id,
            owner_repo=args.owner_repo,
            surface=args.surface,
            plane_type=args.plane_type,
            source_path=args.source_path,
            summary=args.summary,
            authority_risk=authority_risk,
            disposition=disposition,
            evidence=[
                evidence_ref("policy", "spark-harness-core.cli", "Legacy authority inventory generated by CLI.")
            ],
            governor_required=disposition == "converted_to_harness_consumer",
            evidence_only=disposition == "rebound_to_harness_evidence",
            consumer_of_governor=disposition == "converted_to_harness_consumer",
            ledger_required=disposition == "converted_to_harness_consumer",
            blockers=["legacy plane still has high-agency authority"]
            if disposition == "release_blocker"
            else [],
        )
        _print_json(
            kernel.legacy_authority_inventory(
                inventory_id="legacy-authority-inventory:cli",
                owner_repo=args.owner_repo,
                surfaces=[args.surface],
                planes=[plane],
            )
        )
        return 0

    if args.command == "governor-decision":
        kernel = HarnessKernel(surface=args.surface)
        actions = []
        if args.action_type:
            actions.append(
                kernel.proposed_action(
                    capability_id=args.capability_id,
                    action_type=args.action_type,
                    risk_tier=args.risk_tier,
                    summary=args.action_summary,
                    args_path=args.args_path,
                    requires_confirmation=args.requires_confirmation,
                )
            )
        envelope = kernel.create_envelope(
            selected_move=args.selected_move,
            intent_summary=args.intent_summary,
            raw_turn_summary=args.raw_turn_summary,
            proposed_actions=actions,
            authority_state=args.authority_state,
            risk_tier=args.risk_tier,
            confidence=args.confidence,
            requires_human_confirmation=args.requires_confirmation,
        )
        authorizations = []
        if args.authorize_action and actions:
            approval = (
                evidence_ref("human_confirmation", "spark-harness-core.cli", args.approval_summary)
                if args.approval_summary
                else None
            )
            authorizations.append(kernel.authorize(envelope, actions[0], approval_ref=approval))
        _print_json(kernel.governor_decision(envelope, authorizations=authorizations))
        return 0

    if args.command == "telegram-live-qa-packet":
        kernel = HarnessKernel(surface="telegram")
        case = kernel.telegram_live_qa_case(
            ordinal=1,
            case_id=args.case_id,
            suite=args.case_suite,
            risk=args.case_risk,
            expected_route=args.expected_route,
            expected_outcome=args.expected_outcome,
            prompts=[args.prompt],
        )
        _print_json(
            kernel.telegram_live_qa_evidence_packet(
                cases=[case],
                catalog=args.catalog,
                title=args.title,
                suite=args.suite,
                include_risky=args.include_risky,
            )
        )
        return 0

    if args.command == "readiness-score":
        kernel = HarnessKernel(surface=args.surface)
        category_scores = _parse_category_score(args.category)
        gates = _parse_gate(args.gate)
        evidence = evidence_ref("test_result", "spark-harness-core.cli", "Readiness score generated by CLI.")
        _print_json(
            kernel.readiness_score(
                target_kind=args.target_kind,
                target_id=args.target_id,
                owner_repo=args.owner_repo,
                category_scores=category_scores,
                category_evidence={name: [evidence] for name in category_scores},
                promotion_gates=gates,
                summary=args.summary,
            )
        )
        return 0

    if args.command == "change-manifest":
        kernel = HarnessKernel(surface=args.surface)
        component = kernel.component(
            component_id=args.component_id,
            component_type=args.component_type,
            owner_repo=args.owner_repo,
            path=args.path,
            summary=args.component_summary,
            tests=args.test_command,
        )
        approval = (
            evidence_ref("human_confirmation", "spark-harness-core.cli", args.approval_summary)
            if args.approval_summary
            else None
        )
        _print_json(
            kernel.change_manifest(
                target_component=component,
                failure_evidence=[
                    evidence_ref("test_result", "spark-harness-core.cli", args.failure_summary, confidence=0.8)
                ],
                root_cause_hypothesis=args.root_cause,
                edit_summary=args.edit_summary,
                predicted_fixes=args.predicted_fix,
                predicted_regression_risks=args.regression_risk,
                required_tests=args.test_command,
                rollback_plan=args.rollback_plan,
                live_proof_required=args.live_proof_required,
                human_approval_ref=approval,
            )
        )
        return 0

    if args.command == "self-evolution-run":
        kernel = HarnessKernel(surface=args.surface)
        index = kernel.experience_index(
            entries=[
                kernel.experience_entry(
                    entry_type="test_result",
                    summary=args.summary,
                    artifact=artifact_ref("experience", "experience/self-evolution-run.json", args.summary),
                    tags=["self_evolution", args.mode],
                )
            ]
        )
        readiness_score = kernel.readiness_score(
            target_kind="repo",
            target_id="repo:spark-harness-core",
            owner_repo="spark-harness-core",
            category_scores={name: 0.0 for name in ()},
            promotion_gates={"zero_high_agency_legacy_local_gates": True},
            summary="Self-evolution record is observational until proof is attached.",
        )
        _print_json(
            kernel.self_evolution_run(
                mode=args.mode,
                experience_index=index,
                readiness_score=readiness_score,
                commands=args.test_commands,
                summary=args.summary,
            )
        )
        return 0

    if args.command == "change-manifest-runner":
        kernel = HarnessKernel(surface=args.surface)
        component = kernel.component(
            component_id=args.component_id,
            component_type=args.component_type,
            owner_repo=args.owner_repo,
            path=args.path,
            summary=args.component_summary,
            tests=args.test_command,
        )
        approval = (
            evidence_ref("human_confirmation", "spark-harness-core.cli", args.approval_summary)
            if args.approval_summary
            else None
        )
        evidence = [evidence_ref("test_result", "spark-harness-core.cli", args.failure_summary, confidence=0.8)]
        manifests = []
        linked_change_id = None
        if args.component_type not in PROTECTED_EVOLUTION_COMPONENTS or approval is not None:
            manifest = kernel.change_manifest(
                target_component=component,
                failure_evidence=evidence,
                root_cause_hypothesis=args.root_cause,
                edit_summary=args.edit_summary,
                predicted_fixes=args.predicted_fix,
                predicted_regression_risks=args.regression_risk,
                required_tests=args.test_command,
                rollback_plan=args.rollback_plan,
                live_proof_required=args.live_proof_required,
                observed_delta=[kernel.metric(name="manifest_runner_cli", value=True)],
                verdict=args.manifest_verdict,
                human_approval_ref=approval,
            )
            manifests.append(manifest)
            linked_change_id = manifest["change_id"]
        index = kernel.experience_index(
            entries=[
                kernel.experience_entry(
                    entry_type="test_result",
                    summary="Change manifest runner CLI evidence.",
                    artifact=artifact_ref(
                        "experience",
                        "experience/change-manifest-runner.json",
                        "Change manifest runner CLI output.",
                    ),
                    tags=["self_evolution", "change_manifest_runner"],
                    linked_change_id=linked_change_id,
                )
            ]
        )
        readiness_score = kernel.readiness_score(
            target_kind="repo",
            target_id=f"repo:{args.owner_repo}",
            owner_repo=args.owner_repo,
            category_scores={name: 0.9 for name in READINESS_CATEGORIES},
            category_evidence={name: evidence for name in READINESS_CATEGORIES},
            promotion_gates={
                "telegram_live_proven": True,
                "startup_benchmark_proven": True,
                "performance_budget_proven": True,
                "governance_rulesets_proven": True,
                "zero_high_agency_legacy_local_gates": True,
            },
        )
        _print_json(
            kernel.change_manifest_runner(
                mode=args.mode,
                experience_index=index,
                readiness_score=readiness_score,
                commands=args.test_command,
                target_components=[component] if not manifests else None,
                change_manifests=manifests,
                requested_verdict=args.requested_verdict,
                live_surface_required=args.live_proof_required,
            )
        )
        return 0

    raise AssertionError(f"unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
