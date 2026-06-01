from __future__ import annotations

import argparse
import json
from pathlib import Path

from spark_harness_core.kernel import READINESS_CATEGORIES, HarnessKernel, artifact_ref, evidence_ref
from spark_harness_core.schemas import check_all_schemas, list_schema_ids, validate_instance

READINESS_GATES = {
    "public_ready",
    "network_absorbable",
    "telegram_live_proven",
    "startup_benchmark_proven",
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

    raise AssertionError(f"unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
