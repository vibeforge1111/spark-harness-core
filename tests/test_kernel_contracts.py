from __future__ import annotations

import json
import sys
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from spark_harness_core import HarnessKernel, SchemaValidationError, artifact_ref, evidence_ref
from spark_harness_core.legacy_turn_intent import (
    authorize_legacy_tool_call,
    authorize_tool_call,
    parse_turn_intent_envelope,
)
from spark_harness_core.cli import _parse_category_score, _parse_gate, main as cli_main
from spark_harness_core.schemas import check_all_schemas, load_schema, validate_instance


def clone(value: dict) -> dict:
    return json.loads(json.dumps(value))


def sample_component(component_type: str = "middleware") -> dict:
    return {
        "schema_version": "harness-component-v1",
        "component_id": "component:authority-governor",
        "component_type": component_type,
        "owner_repo": "spark-harness-core",
        "path": "src/spark_harness_core/kernel.py",
        "summary": "Authority Governor kernel component.",
        "editable_by_evolution": component_type not in {"verifier", "benchmark", "model_config", "authority_policy"},
        "authority_scope": ["telegram", "cli", "builder"],
        "dependencies": [],
        "tests": ["python3 -m unittest discover -s tests"],
    }


def sample_evidence(kind: str = "test_result") -> dict:
    return evidence_ref(kind, "tests", "Schema regression evidence.", confidence=0.91)


def legacy_envelope_payload(*, no_execution: bool = False, can_write_memory: bool = True) -> dict:
    return {
        "schema": "spark.turn_intent.v1",
        "turnId": "turn:test",
        "traceId": "trace:test",
        "surface": "telegram",
        "directive": {
            "mode": "execute" if not no_execution else "answer",
            "noExecution": no_execution,
            "noPublish": True,
            "localOnly": True,
            "explanationOnly": no_execution,
            "quotedOrMetaLanguage": no_execution,
        },
        "selectedIntent": {
            "kind": "memory_action",
            "ownerSystem": "domain-chip-memory",
            "action": "memory.write",
            "confidence": "explicit",
            "requiresConfirmation": False,
            "source": "explicit",
        },
        "sessionScope": {
            "sessionKey": "telegram:dm:chat:user",
            "surface": "telegram",
            "conversationKind": "dm",
            "userRef": "user:test",
            "chatRef": "chat:test",
            "memoryLoadPolicy": "bounded",
            "pendingStateScope": "fresh_turn",
        },
        "toolPolicy": {
            "allowedTools": ["answer.compose", "memory.write"],
            "deniedTools": [],
            "enabledToolsets": ["spark-harness-core", "domain-chip-memory"],
            "mutationClassesAllowed": ["none", "read_only", "writes_memory"],
            "requiresApprovalFor": [],
            "networkPolicy": "none",
            "elevatedAllowed": False,
        },
        "executionPolicy": {
            "canMutateFiles": False,
            "canLaunchMission": False,
            "canWriteMemory": can_write_memory,
            "canDeleteSchedule": False,
            "canCreateChip": False,
            "canPublish": False,
            "canUseExternalNetwork": False,
        },
        "threatDefense": {
            "reasonCodes": [
                "fresh_user_turn_is_authority",
                "telegram_memory_adapter_explicit_intent",
            ]
        },
    }


class KernelContractTests(unittest.TestCase):
    def test_all_schema_documents_are_valid(self) -> None:
        check_all_schemas()
        self.assertEqual(load_schema("turn-intent-envelope-vnext")["$id"], "https://spark.local/schemas/turn-intent-envelope-vnext.schema.json")

    def test_chat_envelope_handles_action_words_without_tool_authority(self) -> None:
        kernel = HarnessKernel(surface="telegram")
        envelope = kernel.create_envelope(
            selected_move="chat_explain",
            intent_summary="User is discussing build and mission routing, not asking Spark to execute.",
            raw_turn_summary="The turn mentions build and mission as bug-report vocabulary.",
            confidence=0.84,
        )
        self.assertEqual(envelope["action_authority"]["state"], "chat_only")
        self.assertEqual(envelope["proposed_actions"], [])

        invalid = clone(envelope)
        invalid["proposed_actions"] = [
            kernel.proposed_action(
                capability_id="capability:spawner",
                action_type="launch_mission",
                risk_tier="medium",
                summary="Incorrectly launch a mission from chat vocabulary.",
                args_path="experience/private/args.json",
                requires_confirmation=True,
            )
        ]
        with self.assertRaises(SchemaValidationError):
            validate_instance("turn-intent-envelope-vnext", invalid)

    def test_execute_action_requires_executable_authority(self) -> None:
        kernel = HarnessKernel(surface="cli")
        action = kernel.proposed_action(
            capability_id="capability:test-command",
            action_type="run_command",
            risk_tier="low",
            summary="Run a safe local schema validation command.",
            args_path="experience/private/validate-args.json",
            requires_confirmation=False,
        )
        envelope = kernel.create_envelope(
            selected_move="execute_action",
            intent_summary="User explicitly asked for schema validation.",
            raw_turn_summary="Run schema validation.",
            proposed_actions=[action],
            authority_state="executable",
            risk_tier="low",
            confidence=0.93,
        )
        self.assertEqual(envelope["selected_move"], "execute_action")

        invalid = clone(envelope)
        invalid["action_authority"]["state"] = "chat_only"
        with self.assertRaises(SchemaValidationError):
            validate_instance("turn-intent-envelope-vnext", invalid)

    def test_authorization_interrupts_high_risk_action_without_approval(self) -> None:
        kernel = HarnessKernel(surface="cli")
        action = kernel.proposed_action(
            capability_id="capability:publish",
            action_type="publish",
            risk_tier="high",
            summary="Publish a Spark artifact.",
            args_path="experience/private/publish-args.json",
            requires_confirmation=True,
        )
        envelope = kernel.create_envelope(
            selected_move="execute_action",
            intent_summary="User asked to publish after review.",
            raw_turn_summary="Publish the reviewed artifact.",
            proposed_actions=[action],
            authority_state="executable",
            risk_tier="high",
            confidence=0.9,
        )
        decision = kernel.authorize(envelope, action)
        self.assertEqual(decision["verdict"], "interrupt")
        self.assertTrue(decision["approval"]["required"])

    def test_authorization_sets_browser_action_restrictions_from_confirmation_boundary(self) -> None:
        kernel = HarnessKernel(surface="cli")
        read_action = kernel.proposed_action(
            capability_id="capability:browser-use",
            action_type="browser_action",
            risk_tier="read",
            summary="Open a page and read visible state.",
            args_path="experience/private/browser-read-args.json",
            requires_confirmation=False,
        )
        read_envelope = kernel.create_envelope(
            selected_move="execute_action",
            intent_summary="User explicitly asked Spark CLI to inspect a page.",
            raw_turn_summary="spark browser-use open https://example.com",
            proposed_actions=[read_action],
            authority_state="executable",
            risk_tier="read",
            confidence=0.95,
        )
        read_decision = kernel.authorize(read_envelope, read_action)
        self.assertTrue(read_decision["restrictions"]["network_allowed"])
        self.assertFalse(read_decision["restrictions"]["write_allowed"])

        task_action = kernel.proposed_action(
            capability_id="capability:browser-use",
            action_type="browser_action",
            risk_tier="high",
            summary="Run a browser agent task that may interact with a page.",
            args_path="experience/private/browser-task-args.json",
            requires_confirmation=True,
        )
        task_envelope = kernel.create_envelope(
            selected_move="execute_action",
            intent_summary="User explicitly asked Spark CLI to run a browser-use agent task.",
            raw_turn_summary="spark browser-use task review the page",
            proposed_actions=[task_action],
            authority_state="executable",
            risk_tier="high",
            confidence=0.96,
        )
        task_decision = kernel.authorize(
            task_envelope,
            task_action,
            approval_ref=sample_evidence("human_confirmation"),
        )
        self.assertEqual(task_decision["verdict"], "allow")
        self.assertTrue(task_decision["restrictions"]["network_allowed"])
        self.assertTrue(task_decision["restrictions"]["write_allowed"])

    def test_tool_ledger_requires_authorized_lifecycle(self) -> None:
        kernel = HarnessKernel(surface="cli")
        action = kernel.proposed_action(
            capability_id="capability:schema-validation",
            action_type="run_command",
            risk_tier="low",
            summary="Run unit tests.",
            args_path="experience/private/test-args.json",
            requires_confirmation=False,
        )
        envelope = kernel.create_envelope(
            selected_move="execute_action",
            intent_summary="User asked to validate the kernel.",
            raw_turn_summary="Run tests.",
            proposed_actions=[action],
            authority_state="executable",
            risk_tier="low",
            confidence=0.95,
        )
        decision = kernel.authorize(envelope, action)
        ledger = kernel.record_tool_call(
            envelope=envelope,
            action=action,
            authorization=decision,
            tool_name="python3 -m unittest",
            status="success",
            output_path="experience/private/unittest-output.txt",
            summary="Unit tests passed.",
        )
        self.assertEqual(ledger["result"]["status"], "success")

    def test_legacy_turn_intent_adapter_emits_vnext_authorization(self) -> None:
        envelope = parse_turn_intent_envelope(legacy_envelope_payload())
        result = authorize_legacy_tool_call(
            envelope,
            tool_name="memory.write",
            owner_system="domain-chip-memory",
            mutation_class="writes_memory",
        )

        self.assertEqual(result.verdict, "allowed")
        self.assertEqual(result.reason_codes, ())
        self.assertIsNotNone(result.turn_intent_envelope_vnext)
        self.assertIsNotNone(result.authorization_decision)
        assert result.turn_intent_envelope_vnext is not None
        assert result.authorization_decision is not None
        self.assertEqual(result.turn_intent_envelope_vnext["schema_version"], "turn-intent-envelope-vnext")
        self.assertEqual(result.turn_intent_envelope_vnext["selected_move"], "execute_action")
        self.assertEqual(result.authorization_decision["schema_version"], "authorization-decision-v1")
        self.assertEqual(result.authorization_decision["verdict"], "allow")
        validate_instance("turn-intent-envelope-vnext", result.turn_intent_envelope_vnext)
        validate_instance("authorization-decision-v1", result.authorization_decision)

    def test_read_current_state_authorizes_read_action(self) -> None:
        kernel = HarnessKernel(surface="builder")
        action = kernel.proposed_action(
            capability_id="capability:memory-read",
            action_type="read",
            risk_tier="read",
            summary="Read bounded current memory state.",
            args_path="experience/private/memory-read-args.json",
            requires_confirmation=False,
        )
        envelope = kernel.create_envelope(
            selected_move="read_current_state",
            intent_summary="User explicitly asked to inspect current memory state.",
            raw_turn_summary="What is my current plan?",
            proposed_actions=[action],
            authority_state="read_only",
            risk_tier="read",
            confidence=0.93,
        )
        decision = kernel.authorize(envelope, action)

        self.assertEqual(decision["verdict"], "allow")
        self.assertFalse(decision["restrictions"]["write_allowed"])

    def test_legacy_turn_intent_adapter_blocks_execution_policy_mismatch(self) -> None:
        envelope = parse_turn_intent_envelope(legacy_envelope_payload(can_write_memory=False))
        result = authorize_legacy_tool_call(
            envelope,
            tool_name="memory.write",
            owner_system="domain-chip-memory",
            mutation_class="writes_memory",
        )

        self.assertEqual(result.verdict, "blocked")
        self.assertIn("write_memory_not_authorized", result.reason_codes)
        assert result.authorization_decision is not None
        self.assertEqual(result.authorization_decision["verdict"], "deny")

    def test_legacy_turn_intent_tuple_api_uses_shared_core(self) -> None:
        envelope = parse_turn_intent_envelope(legacy_envelope_payload(no_execution=True))
        verdict, reasons = authorize_tool_call(
            envelope,
            tool_name="memory.write",
            owner_system="domain-chip-memory",
            mutation_class="writes_memory",
        )

        self.assertEqual(verdict, "blocked")
        self.assertIn("no_execution_boundary", reasons)

    def test_explicit_legacy_publish_approves_high_risk_action(self) -> None:
        payload = legacy_envelope_payload()
        payload["selectedIntent"]["ownerSystem"] = "spark-swarm"
        payload["selectedIntent"]["kind"] = "swarm_action"
        payload["selectedIntent"]["action"] = "swarm.upgrade.deliver"
        payload["directive"]["noPublish"] = False
        payload["toolPolicy"]["allowedTools"] = ["answer.compose", "swarm.upgrade.deliver"]
        payload["toolPolicy"]["enabledToolsets"] = ["spark-harness-core", "spark-swarm"]
        payload["toolPolicy"]["mutationClassesAllowed"] = ["none", "read_only", "external_network"]
        payload["toolPolicy"]["networkPolicy"] = "external"
        payload["executionPolicy"]["canWriteMemory"] = False
        payload["executionPolicy"]["canPublish"] = True
        payload["executionPolicy"]["canUseExternalNetwork"] = True
        envelope = parse_turn_intent_envelope(payload)

        authorization = authorize_legacy_tool_call(
            envelope,
            tool_name="swarm.upgrade.deliver",
            owner_system="spark-swarm",
            mutation_class="external_network",
            external_network=True,
            publishes=True,
        )

        self.assertEqual(authorization.verdict, "allowed")
        assert authorization.authorization_decision is not None
        self.assertEqual(authorization.authorization_decision["approval"]["status"], "approved")

    def test_change_manifest_requires_approval_for_authority_policy_edits(self) -> None:
        manifest = {
            "schema_version": "change-manifest-v1",
            "change_id": "change:authority-policy-attempt",
            "created_at": "2026-06-01T00:00:00Z",
            "target_component": sample_component("authority_policy"),
            "failure_evidence": [sample_evidence()],
            "root_cause_hypothesis": "Authority policy needs a deliberate human-approved change.",
            "edit_summary": "Tighten the high-agency promotion rule.",
            "predicted_fixes": ["High-agency local gates cannot bypass the Governor."],
            "predicted_regression_risks": ["Over-tightening could interrupt legitimate actions."],
            "required_tests": ["python3 -m unittest discover -s tests"],
            "live_proof_required": True,
            "rollback_plan": "Revert the authority policy component change.",
            "observed_delta": [],
            "verdict": "draft",
        }
        with self.assertRaises(SchemaValidationError):
            validate_instance("change-manifest-v1", manifest)

        manifest["human_approval_ref"] = sample_evidence("human_confirmation")
        validate_instance("change-manifest-v1", manifest)

    def test_readiness_score_requires_all_harness_layers(self) -> None:
        evidence = [sample_evidence()]
        category = {"score": 1.0, "evidence": evidence, "blockers": []}
        readiness = {
            "schema_version": "readiness-score-v1",
            "score_id": "readiness:spark-harness-core",
            "created_at": "2026-06-01T00:00:00Z",
            "target": {
                "kind": "repo",
                "id": "repo:spark-harness-core",
                "owner_repo": "spark-harness-core",
            },
            "categories": {
                "execution": category,
                "tools": category,
                "context": category,
                "lifecycle": category,
                "observability": category,
                "verification": category,
                "governance": category,
            },
            "promotion_gates": {
                "public_ready": False,
                "network_absorbable": False,
                "telegram_live_proven": False,
                "startup_benchmark_proven": False,
                "zero_high_agency_legacy_local_gates": True,
            },
            "overall": {
                "score": 0.71,
                "status": "private_ready",
                "summary": "Contracts are valid; runtime integrations remain pending.",
            },
        }
        validate_instance("readiness-score-v1", readiness)

        invalid = clone(readiness)
        del invalid["categories"]["governance"]
        with self.assertRaises(SchemaValidationError):
            validate_instance("readiness-score-v1", invalid)

    def test_surface_spec_keeps_runtime_logic_inspectable(self) -> None:
        spec = {
            "schema_version": "surface-spec-v1",
            "spec_id": "surface-spec:telegram",
            "surface": "telegram",
            "runtime_charter_ref": artifact_ref("spec", "specs/runtime-charter.md", "Runtime charter."),
            "contracts": [
                {
                    "name": "telegram-turn-authority",
                    "inputs": ["message metadata", "fresh user turn summary"],
                    "outputs": ["TurnIntentEnvelopeVNext"],
                    "validation_gates": ["chat moves have zero proposed actions"],
                    "retry_rules": ["retry only as chat when authority is absent"],
                    "stop_rules": ["stop before mission launch without executable authority"],
                }
            ],
            "roles": [
                {
                    "name": "surface-adapter",
                    "responsibilities": ["submit evidence to Governor"],
                    "tool_scope": ["read ingress metadata"],
                }
            ],
            "stages": [
                {
                    "name": "observe",
                    "purpose": "Summarize the fresh turn without granting action authority.",
                    "entry_conditions": ["new message received"],
                    "exit_conditions": ["evidence refs are available"],
                }
            ],
            "adapters": ["capability:telegram-ingress"],
            "state_semantics": ["memory and pending state are evidence only"],
            "failure_taxonomy": ["route_hijack", "pending_state_leak", "memory_override"],
            "permission_model": ["Telegram cannot execute missions locally"],
            "evidence_requirements": ["fresh user intent evidence"],
            "stop_rules": ["no proposed action from chat-only move"],
        }
        validate_instance("surface-spec-v1", spec)

    def test_kernel_builds_resource_experience_readiness_and_evolution_records(self) -> None:
        kernel = HarnessKernel(surface="test_harness")
        resource = kernel.resource(
            resource_id="resource:harness-core-kernel",
            resource_type="harness_spec",
            owner_repo="spark-harness-core",
            version="0.1.0",
            tests=["python3 -m unittest discover -s tests"],
        )
        registry = kernel.resource_registry([resource])
        self.assertEqual(registry["resources"][0]["resource_id"], "resource:harness-core-kernel")

        artifact = artifact_ref("test_result", "experience/kernel-tests.json", "Kernel test result.")
        experience = kernel.experience_index(
            entries=[
                kernel.experience_entry(
                    entry_type="test_result",
                    summary="Kernel contracts passed.",
                    artifact=artifact,
                    tags=["kernel", "contracts"],
                )
            ]
        )
        self.assertEqual(experience["entries"][0]["entry_type"], "test_result")

        evidence = [sample_evidence()]
        readiness = kernel.readiness_score(
            target_kind="repo",
            target_id="repo:spark-harness-core",
            owner_repo="spark-harness-core",
            category_scores={name: 0.9 for name in ("execution", "tools", "context", "lifecycle", "observability", "verification", "governance")},
            category_evidence={name: evidence for name in ("execution", "tools", "context", "lifecycle", "observability", "verification", "governance")},
            promotion_gates={
                "telegram_live_proven": True,
                "startup_benchmark_proven": True,
                "zero_high_agency_legacy_local_gates": True,
            },
        )
        self.assertEqual(readiness["overall"]["status"], "release_candidate")

        evolution = kernel.self_evolution_run(
            mode="observe",
            experience_index=experience,
            readiness_score=readiness,
            commands=["python3 -m unittest discover -s tests"],
            summary="Observed kernel evidence without promoting changes.",
        )
        self.assertEqual(evolution["promotion_decision"]["verdict"], "not_ready")

    def test_kernel_change_manifest_enforces_protected_component_approval(self) -> None:
        kernel = HarnessKernel(surface="test_harness")
        protected_component = kernel.component(
            component_id="component:authority-policy",
            component_type="authority_policy",
            owner_repo="spark-harness-core",
            path="src/spark_harness_core/kernel.py",
            summary="Authority policy is protected from self-evolution mutation.",
            tests=["python3 -m unittest discover -s tests"],
        )
        with self.assertRaises(SchemaValidationError):
            kernel.change_manifest(
                target_component=protected_component,
                failure_evidence=[sample_evidence()],
                root_cause_hypothesis="Authority policy changes need explicit human approval.",
                edit_summary="Change protected policy.",
                predicted_fixes=["Would tighten protected authority behavior."],
                predicted_regression_risks=["Could block valid actions."],
                required_tests=["python3 -m unittest discover -s tests"],
                rollback_plan="Revert the protected policy edit.",
            )

        manifest = kernel.change_manifest(
            target_component=protected_component,
            failure_evidence=[sample_evidence()],
            root_cause_hypothesis="Authority policy changes need explicit human approval.",
            edit_summary="Change protected policy with approval evidence.",
            predicted_fixes=["Would tighten protected authority behavior."],
            predicted_regression_risks=["Could block valid actions."],
            required_tests=["python3 -m unittest discover -s tests"],
            rollback_plan="Revert the protected policy edit.",
            human_approval_ref=sample_evidence("human_confirmation"),
        )
        self.assertEqual(manifest["verdict"], "draft")

    def test_cli_emits_valid_kernel_operating_records(self) -> None:
        commands = (
            ("resource-registry", "resource-registry-v1"),
            ("experience-index", "experience-index-v1"),
            (
                "readiness-score --category execution=1 --category tools=1 --category context=1 "
                "--category lifecycle=1 --category observability=1 --category verification=1 "
                "--category governance=1 --gate zero_high_agency_legacy_local_gates=true",
                "readiness-score-v1",
            ),
            ("self-evolution-run", "self-evolution-run-v1"),
        )
        for raw_command, schema_name in commands:
            with self.subTest(command=raw_command):
                stdout = StringIO()
                argv = raw_command.split()
                with redirect_stdout(stdout):
                    exit_code = cli_main(argv)
                self.assertEqual(exit_code, 0)
                payload = json.loads(stdout.getvalue())
                validate_instance(schema_name, payload)

    def test_cli_rejects_unknown_readiness_inputs(self) -> None:
        with self.assertRaises(ValueError):
            _parse_category_score(["mood=1"])
        with self.assertRaises(ValueError):
            _parse_gate(["nearly=true"])
        with self.assertRaises(ValueError):
            _parse_gate(["public_ready=maybe"])


if __name__ == "__main__":
    unittest.main()
