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
    authorize_vnext_tool_call,
    build_vnext_action_intent_envelope,
    build_vnext_tool_intent_envelope,
    finalize_legacy_tool_call_ledger,
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

    def test_governor_decision_keeps_chat_only_turns_non_executing(self) -> None:
        kernel = HarnessKernel(surface="telegram")
        envelope = kernel.create_envelope(
            selected_move="chat_explain",
            intent_summary="User is discussing build, memory, and publish as examples.",
            raw_turn_summary="Action words are present as discussion vocabulary.",
            confidence=0.87,
        )
        decision = kernel.governor_decision(envelope)
        self.assertEqual(decision["schema_version"], "governor-decision-v1")
        self.assertEqual(decision["outcome"], "chat_only")
        self.assertFalse(decision["execution_boundary"]["action_authorized"])
        self.assertEqual(decision["execution_boundary"]["action_count"], 0)
        self.assertTrue(decision["execution_boundary"]["legacy_authority_demoted"])
        self.assertEqual(decision["reply_contract"]["style"], "human_conversational")
        self.assertFalse(decision["reply_contract"]["should_interrupt"])

    def test_governor_decision_executes_only_after_authorization(self) -> None:
        kernel = HarnessKernel(surface="cli")
        action = kernel.proposed_action(
            capability_id="capability:schema-validation",
            action_type="run_command",
            risk_tier="low",
            summary="Run local schema validation.",
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
            confidence=0.94,
        )
        authorization = kernel.authorize(envelope, action)
        ledger = kernel.record_tool_call(
            envelope=envelope,
            action=action,
            authorization=authorization,
            tool_name="spark-harness-core.validate",
            status="not_started",
            output_path="experience/private/not-started.json",
            summary="Execution is authorized but not started in this proof.",
        )
        decision = kernel.governor_decision(envelope, authorizations=[authorization], tool_ledgers=[ledger])
        self.assertEqual(decision["outcome"], "execute")
        self.assertTrue(decision["execution_boundary"]["action_authorized"])
        self.assertEqual(decision["execution_boundary"]["authorized_action_count"], 1)
        self.assertEqual(decision["tool_ledgers"][0]["result"]["status"], "not_started")

    def test_governor_decision_interrupts_high_risk_actions(self) -> None:
        kernel = HarnessKernel(surface="telegram")
        action = kernel.proposed_action(
            capability_id="capability:publish",
            action_type="publish",
            risk_tier="high",
            summary="Publish a reviewed Spark release.",
            args_path="experience/private/publish-args.json",
            requires_confirmation=True,
        )
        envelope = kernel.create_envelope(
            selected_move="confirm_action",
            intent_summary="User appears to request a publish action.",
            raw_turn_summary="Publish the reviewed Spark release.",
            proposed_actions=[action],
            authority_state="confirmation_required",
            risk_tier="high",
            confidence=0.9,
            requires_human_confirmation=True,
        )
        authorization = kernel.authorize(envelope, action)
        decision = kernel.governor_decision(envelope, authorizations=[authorization])
        self.assertEqual(decision["outcome"], "interrupt")
        self.assertFalse(decision["execution_boundary"]["action_authorized"])
        self.assertTrue(decision["execution_boundary"]["requires_human_confirmation"])
        self.assertTrue(decision["reply_contract"]["should_interrupt"])

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

    def test_tool_ledger_cannot_record_execution_without_allow_authorization(self) -> None:
        kernel = HarnessKernel(surface="telegram")
        action = kernel.proposed_action(
            capability_id="capability:publish",
            action_type="publish",
            risk_tier="high",
            summary="Publish a Spark release.",
            args_path="experience/private/publish-args.json",
            requires_confirmation=True,
        )
        envelope = kernel.create_envelope(
            selected_move="confirm_action",
            intent_summary="User appears to request a publish action.",
            raw_turn_summary="Publish the Spark release.",
            proposed_actions=[action],
            authority_state="confirmation_required",
            risk_tier="high",
            confidence=0.91,
            requires_human_confirmation=True,
        )
        decision = kernel.authorize(envelope, action)
        self.assertEqual(decision["verdict"], "interrupt")

        with self.assertRaises(ValueError):
            kernel.record_tool_call(
                envelope=envelope,
                action=action,
                authorization=decision,
                tool_name="spark.publish",
                status="success",
                output_path="experience/private/publish-output.json",
                summary="This must not be representable before approval.",
            )

        ledger = kernel.record_tool_call(
            envelope=envelope,
            action=action,
            authorization=decision,
            tool_name="spark.publish",
            status="not_started",
            output_path="experience/private/publish-not-started.json",
            summary="Publish was interrupted before execution.",
        )
        self.assertEqual(ledger["result"]["status"], "not_started")
        self.assertEqual(ledger["lifecycle"][-1]["verdict"], "skipped")

        with self.assertRaises(ValueError):
            kernel.finalize_tool_call_ledger(
                ledger,
                status="success",
                output_path="experience/private/publish-output.json",
                summary="This must not be representable before approval.",
            )

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
        self.assertIsNotNone(result.tool_call_ledger)
        assert result.turn_intent_envelope_vnext is not None
        assert result.authorization_decision is not None
        assert result.tool_call_ledger is not None
        self.assertEqual(result.turn_intent_envelope_vnext["schema_version"], "turn-intent-envelope-vnext")
        self.assertEqual(result.turn_intent_envelope_vnext["selected_move"], "execute_action")
        self.assertEqual(result.authorization_decision["schema_version"], "authorization-decision-v1")
        self.assertEqual(result.authorization_decision["verdict"], "allow")
        self.assertEqual(result.tool_call_ledger["schema_version"], "tool-call-ledger-v1")
        self.assertEqual(result.tool_call_ledger["result"]["status"], "not_started")
        self.assertEqual(result.tool_call_ledger["authorization"]["decision_id"], result.authorization_decision["decision_id"])
        validate_instance("turn-intent-envelope-vnext", result.turn_intent_envelope_vnext)
        validate_instance("authorization-decision-v1", result.authorization_decision)
        validate_instance("tool-call-ledger-v1", result.tool_call_ledger)

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

    def test_builds_native_vnext_tool_intent_for_memory_write(self) -> None:
        envelope = build_vnext_tool_intent_envelope(
            surface="telegram",
            actor_id_ref="human:test",
            request_id="req-native-memory-write",
            source_kind="telegram_runtime_profile_fact_observation",
            tool_name="memory.write",
            owner_system="domain-chip-memory",
            mutation_class="writes_memory",
            intent_summary="User explicitly shared a profile fact to remember.",
            raw_turn_summary="Telegram message summarized without raw private text.",
        )

        validate_instance("turn-intent-envelope-vnext", envelope)
        self.assertEqual(envelope["schema_version"], "turn-intent-envelope-vnext")
        self.assertEqual(envelope["surface"], "telegram")
        self.assertEqual(envelope["selected_move"], "execute_action")
        self.assertEqual(envelope["action_authority"]["state"], "executable")
        self.assertEqual(envelope["proposed_actions"][0]["action_type"], "write_memory")

        result = authorize_vnext_tool_call(
            envelope,
            tool_name="memory.write",
            owner_system="domain-chip-memory",
            mutation_class="writes_memory",
        )

        self.assertEqual(result.verdict, "allowed")
        self.assertEqual(result.reason_codes, ())

    def test_builds_native_vnext_tool_intent_for_memory_read(self) -> None:
        envelope = build_vnext_tool_intent_envelope(
            surface="telegram",
            actor_id_ref="human:test",
            request_id="req-native-memory-read",
            source_kind="telegram_runtime_current_plan_read",
            tool_name="memory.read",
            owner_system="domain-chip-memory",
            mutation_class="read_only",
            intent_summary="User asked to inspect current saved plan.",
            raw_turn_summary="Telegram memory read request summarized.",
        )

        validate_instance("turn-intent-envelope-vnext", envelope)
        self.assertEqual(envelope["selected_move"], "read_current_state")
        self.assertEqual(envelope["action_authority"]["state"], "read_only")
        self.assertEqual(envelope["action_authority"]["risk_tier"], "read")
        self.assertEqual(envelope["proposed_actions"][0]["action_type"], "read")

        result = authorize_vnext_tool_call(
            envelope,
            tool_name="memory.read",
            owner_system="domain-chip-memory",
            mutation_class="read_only",
        )

        self.assertEqual(result.verdict, "allowed")
        self.assertEqual(result.reason_codes, ())

    def test_builds_native_vnext_action_intent_for_voice_status_and_speak(self) -> None:
        envelope = build_vnext_action_intent_envelope(
            surface="cli",
            actor_id_ref="human:local-operator",
            request_id="req-voice-local-operator",
            source_kind="local_operator_harness_execute",
            intent_summary="Local operator explicitly asked Spark to speak through voice I/O.",
            raw_turn_summary="Local voice task summarized without raw private text.",
            actions=[
                {
                    "tool_name": "voice.status",
                    "owner_system": "spark-voice-comms",
                    "mutation_class": "read_only",
                },
                {
                    "tool_name": "voice.speak",
                    "owner_system": "spark-voice-comms",
                    "mutation_class": "external_network",
                    "external_network": True,
                },
            ],
        )

        validate_instance("turn-intent-envelope-vnext", envelope)
        self.assertEqual(envelope["selected_move"], "execute_action")
        self.assertEqual(envelope["action_authority"]["state"], "executable")
        self.assertEqual(envelope["action_authority"]["risk_tier"], "medium")
        self.assertEqual(len(envelope["proposed_actions"]), 2)

        status = authorize_vnext_tool_call(
            envelope,
            tool_name="voice.status",
            owner_system="spark-voice-comms",
            mutation_class="read_only",
        )
        speak = authorize_vnext_tool_call(
            envelope,
            tool_name="voice.speak",
            owner_system="spark-voice-comms",
            mutation_class="external_network",
            external_network=True,
        )

        self.assertEqual(status.verdict, "allowed")
        self.assertEqual(speak.verdict, "allowed")

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
        assert result.tool_call_ledger is not None
        self.assertEqual(result.authorization_decision["verdict"], "deny")
        self.assertEqual(result.tool_call_ledger["authorization"]["verdict"], "deny")
        self.assertEqual(result.tool_call_ledger["lifecycle"][1]["verdict"], "failed")

    def test_finalizes_legacy_tool_call_ledger_after_execution(self) -> None:
        envelope = parse_turn_intent_envelope(legacy_envelope_payload())
        result = authorize_legacy_tool_call(
            envelope,
            tool_name="memory.write",
            owner_system="domain-chip-memory",
            mutation_class="writes_memory",
        )
        assert result.tool_call_ledger is not None

        final_ledger = finalize_legacy_tool_call_ledger(
            result.tool_call_ledger,
            status="success",
            output_path="builder://turns/turn-test/results/memory-write",
            summary="Memory write completed.",
            surface="telegram",
        )

        self.assertEqual(final_ledger["ledger_id"], result.tool_call_ledger["ledger_id"])
        self.assertEqual(final_ledger["result"]["status"], "success")
        self.assertEqual(final_ledger["result"]["summary"], "Memory write completed.")
        self.assertEqual(final_ledger["lifecycle"][-1]["stage"], "execute")
        self.assertEqual(final_ledger["lifecycle"][-1]["verdict"], "passed")
        validate_instance("tool-call-ledger-v1", final_ledger)

    def test_authorizes_native_vnext_tool_call(self) -> None:
        legacy = parse_turn_intent_envelope(legacy_envelope_payload())
        converted = authorize_legacy_tool_call(
            legacy,
            tool_name="memory.write",
            owner_system="domain-chip-memory",
            mutation_class="writes_memory",
        )
        assert converted.turn_intent_envelope_vnext is not None

        result = authorize_vnext_tool_call(
            converted.turn_intent_envelope_vnext,
            tool_name="memory.write",
            owner_system="domain-chip-memory",
            mutation_class="writes_memory",
        )

        self.assertEqual(result.verdict, "allowed")
        self.assertEqual(result.reason_codes, ())
        self.assertIsNotNone(result.turn_intent_envelope_vnext)
        self.assertIsNotNone(result.authorization_decision)
        self.assertIsNotNone(result.tool_call_ledger)
        assert result.authorization_decision is not None
        assert result.tool_call_ledger is not None
        self.assertEqual(result.authorization_decision["verdict"], "allow")
        self.assertEqual(result.tool_call_ledger["authorization"]["decision_id"], result.authorization_decision["decision_id"])

    def test_blocks_native_vnext_without_matching_proposed_action(self) -> None:
        legacy = parse_turn_intent_envelope(legacy_envelope_payload())
        converted = authorize_legacy_tool_call(
            legacy,
            tool_name="memory.write",
            owner_system="domain-chip-memory",
            mutation_class="writes_memory",
        )
        assert converted.turn_intent_envelope_vnext is not None

        result = authorize_vnext_tool_call(
            converted.turn_intent_envelope_vnext,
            tool_name="memory.read",
            owner_system="domain-chip-memory",
            mutation_class="read_only",
        )

        self.assertEqual(result.verdict, "blocked")
        self.assertIn("proposed_action_not_authorized", result.reason_codes)
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
                "performance_budget_proven": False,
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

    def test_readiness_release_candidate_requires_performance_budget(self) -> None:
        kernel = HarnessKernel(surface="test_harness")
        evidence = [sample_evidence()]
        categories = {
            name: 1.0
            for name in ("execution", "tools", "context", "lifecycle", "observability", "verification", "governance")
        }

        readiness = kernel.readiness_score(
            target_kind="surface",
            target_id="surface:telegram",
            owner_repo="spark-telegram-bot",
            category_scores=categories,
            category_evidence={name: evidence for name in categories},
            promotion_gates={
                "telegram_live_proven": True,
                "startup_benchmark_proven": True,
                "zero_high_agency_legacy_local_gates": True,
            },
        )

        self.assertEqual(readiness["promotion_gates"]["performance_budget_proven"], False)
        self.assertEqual(readiness["overall"]["status"], "private_ready")

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
                "performance_budget_proven": True,
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

    def test_self_evolution_promotion_requires_accepted_manifest_and_readiness(self) -> None:
        kernel = HarnessKernel(surface="test_harness")
        evidence = [sample_evidence()]
        categories = {
            name: 0.9
            for name in ("execution", "tools", "context", "lifecycle", "observability", "verification", "governance")
        }
        readiness = kernel.readiness_score(
            target_kind="repo",
            target_id="repo:spark-harness-core",
            owner_repo="spark-harness-core",
            category_scores=categories,
            category_evidence={name: evidence for name in categories},
            promotion_gates={
                "telegram_live_proven": True,
                "startup_benchmark_proven": True,
                "performance_budget_proven": True,
                "zero_high_agency_legacy_local_gates": True,
            },
        )
        experience = kernel.experience_index(
            entries=[
                kernel.experience_entry(
                    entry_type="test_result",
                    summary="Self-evolution policy tests passed.",
                    artifact=artifact_ref("test_result", "experience/self-evolution-policy.json", "Policy proof."),
                    tags=["self_evolution", "policy"],
                )
            ]
        )
        component = kernel.component(
            component_id="component:surface-adapter",
            component_type="middleware",
            owner_repo="spark-telegram-bot",
            path="src/harnessCore.ts",
            summary="Surface adapter under self-evolution.",
            tests=["npm test"],
        )
        draft_manifest = kernel.change_manifest(
            target_component=component,
            failure_evidence=evidence,
            root_cause_hypothesis="A surface adapter needs stronger Harness Core records.",
            edit_summary="Route the adapter through canonical Harness Core records.",
            predicted_fixes=["High-agency actions emit envelope, authorization, and ledger records."],
            predicted_regression_risks=["Under-specified actions may now be rejected."],
            required_tests=["npm test"],
            rollback_plan="Revert the adapter change.",
        )

        with self.assertRaises(ValueError):
            kernel.self_evolution_run(
                mode="promote",
                experience_index=experience,
                readiness_score=readiness,
                commands=["npm test"],
                target_components=[component],
                change_manifests=[],
                verdict="promote_private",
            )
        with self.assertRaises(ValueError):
            kernel.self_evolution_run(
                mode="promote",
                experience_index=experience,
                readiness_score=readiness,
                commands=["npm test"],
                target_components=[component],
                change_manifests=[draft_manifest],
                verdict="promote_private",
            )

        accepted_manifest = kernel.change_manifest(
            target_component=component,
            failure_evidence=evidence,
            root_cause_hypothesis="A surface adapter needs stronger Harness Core records.",
            edit_summary="Route the adapter through canonical Harness Core records.",
            predicted_fixes=["High-agency actions emit envelope, authorization, and ledger records."],
            predicted_regression_risks=["Under-specified actions may now be rejected."],
            required_tests=["npm test"],
            rollback_plan="Revert the adapter change.",
            observed_delta=[kernel.metric(name="route_matrix_pass", value=True)],
            verdict="accepted",
        )
        promoted = kernel.self_evolution_run(
            mode="promote",
            experience_index=experience,
            readiness_score=readiness,
            commands=["npm test"],
            target_components=[component],
            change_manifests=[accepted_manifest],
            verdict="promote_private",
            summary="Accepted adapter change is ready for private promotion.",
        )
        self.assertEqual(promoted["promotion_decision"]["verdict"], "promote_private")

    def test_self_evolution_promotion_blocks_when_live_proof_is_still_required(self) -> None:
        kernel = HarnessKernel(surface="telegram")
        evidence = [sample_evidence()]
        categories = {
            name: 0.92
            for name in ("execution", "tools", "context", "lifecycle", "observability", "verification", "governance")
        }
        readiness = kernel.readiness_score(
            target_kind="surface",
            target_id="surface:telegram",
            owner_repo="spark-telegram-bot",
            category_scores=categories,
            category_evidence={name: evidence for name in categories},
            promotion_gates={
                "telegram_live_proven": True,
                "startup_benchmark_proven": True,
                "performance_budget_proven": True,
                "zero_high_agency_legacy_local_gates": True,
            },
        )
        experience = kernel.experience_index()
        component = kernel.component(
            component_id="component:telegram-live-adapter",
            component_type="middleware",
            owner_repo="spark-telegram-bot",
            path="src/index.ts",
            summary="Telegram live adapter under self-evolution.",
            tests=["npm test"],
        )
        manifest = kernel.change_manifest(
            target_component=component,
            failure_evidence=evidence,
            root_cause_hypothesis="Live Telegram routing proof is required before release.",
            edit_summary="Prepare live Telegram proof wiring.",
            predicted_fixes=["Live replies emit Harness Core evidence."],
            predicted_regression_risks=["Live proof could reveal route drift."],
            required_tests=["npm test"],
            rollback_plan="Revert the live proof wiring.",
            live_proof_required=True,
            verdict="accepted",
        )

        with self.assertRaises(ValueError):
            kernel.self_evolution_run(
                mode="promote",
                experience_index=experience,
                readiness_score=readiness,
                commands=["npm test"],
                target_components=[component],
                change_manifests=[manifest],
                verdict="promote_release_candidate",
                live_surface_required=True,
            )

    def test_kernel_builds_evaluation_pack_and_harness_run_records(self) -> None:
        kernel = HarnessKernel(surface="telegram")
        prompt = artifact_ref("prompt", "eval/prompts/telegram-meta-build.txt", "Redacted Telegram prompt.")
        case = kernel.evaluation_case(
            case_id="case:telegram-meta-build",
            case_type="negative_intent",
            prompt_ref=prompt,
            expected_move="chat_explain",
            expected_authority_state="chat_only",
        )
        pack = kernel.evaluation_pack(
            scope=["telegram"],
            cases=[case],
            metrics=[
                kernel.metric(name="route_pass", value=True),
                kernel.metric(name="latency_ms", value=1200, unit="ms", higher_is_better=False),
            ],
            promotion_rules=["Words alone must not authorize launch_mission."],
        )
        self.assertEqual(pack["cases"][0]["expected_authority_state"], "chat_only")
        validate_instance("evaluation-pack-v1", pack)

        run = kernel.harness_run(
            run_type="route_matrix",
            model_refs=["model:gpt-5.5"],
            artifacts=[artifact_ref("test_result", "experience/telegram-420.json", "420-case route matrix.")],
            metrics=[kernel.metric(name="case_count", value=420)],
            status="passed",
            summary="Telegram route matrix passed through Harness Core authority records.",
        )
        self.assertEqual(run["verdict"]["status"], "passed")
        validate_instance("harness-run-v1", run)

    def test_kernel_builds_telegram_live_qa_evidence_packet(self) -> None:
        kernel = HarnessKernel(surface="telegram")
        case = kernel.telegram_live_qa_case(
            ordinal=1,
            case_id="genesis-001",
            suite="genesis_normal_conversation",
            risk="safe",
            expected_route="chat_think_with_me",
            expected_outcome="Gives advice. Must not launch a mission.",
            prompts=["Should we use the startup operator more?"],
        )
        packet = kernel.telegram_live_qa_evidence_packet(
            cases=[case],
            catalog="genesis-live-telegram-100.json",
            title="Spark Genesis Telegram Live QA Evidence Packet",
            include_risky=True,
            required_session_evidence={
                "profile": "sparkqa-bot",
                "tester": "codex",
                "bot_runtime_commit": "abc1234",
                "harness_core_commit": "def5678",
                "spark_os_compile_ref": "/tmp/spark-os-compile.json",
                "spark_live_status_ref": "/tmp/spark-live-status.json",
                "spark_verify_provenance_ref": "/tmp/spark-verify.json",
                "telegram_chat_evidence_ref": "/tmp/telegram.png",
                "overall_verdict": "untested",
                "follow_up_commits": ["abc1234"],
                "pr_links": [],
                "remaining_risks": ["100 live prompts still incomplete"],
            },
            generated_at="2026-06-02T00:00:00Z",
        )

        self.assertEqual(packet["schema_version"], "spark.telegram_live_qa_evidence_packet.v1")
        self.assertEqual(packet["selection"]["case_count"], 1)
        self.assertEqual(packet["selection"]["risk_counts"]["safe"], 1)
        self.assertEqual(packet["summary"]["untested"], 1)
        self.assertEqual(packet["required_session_evidence"]["profile"], "sparkqa-bot")
        self.assertEqual(packet["required_session_evidence"]["bot_runtime_commit"], "abc1234")
        self.assertEqual(packet["required_session_evidence"]["remaining_risks"], ["100 live prompts still incomplete"])
        self.assertEqual(packet["cases"][0]["verdict"], "untested")
        self.assertIsNone(packet["cases"][0]["observed_turns"][0]["reply"])
        self.assertIn("does not prove release readiness", packet["authority_claim_boundary"])
        validate_instance("telegram-live-qa-evidence-packet-v1", packet)

        invalid = clone(packet)
        invalid["summary"]["untested"] = -1
        with self.assertRaises(SchemaValidationError):
            validate_instance("telegram-live-qa-evidence-packet-v1", invalid)

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
            ("evaluation-pack", "evaluation-pack-v1"),
            ("harness-run --status passed --summary harness-run-proof", "harness-run-v1"),
            ("governor-decision", "governor-decision-v1"),
            ("telegram-live-qa-packet --include-risky", "telegram-live-qa-evidence-packet-v1"),
            ("change-manifest", "change-manifest-v1"),
            (
                "readiness-score --category execution=1 --category tools=1 --category context=1 "
                "--category lifecycle=1 --category observability=1 --category verification=1 "
                "--category governance=1 --gate performance_budget_proven=true "
                "--gate zero_high_agency_legacy_local_gates=true",
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
