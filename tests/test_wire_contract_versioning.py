from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from spark_harness_core import (  # noqa: E402
    HARNESS_CORE_WIRE_CONTRACT_VERSION,
    HarnessKernel,
    evidence_ref,
    negotiate_wire_contract,
)


class WireContractVersioningTests(unittest.TestCase):
    def _authorized_decision(self) -> dict:
        kernel = HarnessKernel(surface="spawner", actor_id_ref="human:test")
        action = kernel.proposed_action(
            capability_id="capability:spawner-ui:spawner.dispatch",
            action_type="launch_mission",
            risk_tier="medium",
            summary="Dispatch a governed mission.",
            args_path="spawner://actions/dispatch/pending",
            requires_confirmation=False,
        )
        envelope = kernel.create_envelope(
            selected_move="execute_action",
            intent_summary="User asked Spark to dispatch a mission.",
            raw_turn_summary="Fresh Spawner turn requested mission dispatch.",
            evidence=[evidence_ref("fresh_user_intent", "spawner", "User explicitly requested mission dispatch.")],
            proposed_actions=[action],
            authority_state="executable",
        )
        authorization = kernel.authorize(envelope, action)
        ledger = kernel.record_tool_call(
            envelope=envelope,
            action=action,
            authorization=authorization,
            tool_name="spawner.dispatch",
            status="not_started",
            output_path="spawner://missions/wire-contract/pending",
            summary="Spawner dispatch authorized and waiting for execution.",
        )
        return kernel.governor_decision(envelope, authorizations=[authorization], tool_ledgers=[ledger])

    def test_authority_artifacts_carry_wire_contract_version(self) -> None:
        decision = self._authorized_decision()

        self.assertEqual(decision["wire_contract_version"], HARNESS_CORE_WIRE_CONTRACT_VERSION)
        self.assertEqual(decision["authorizations"][0]["wire_contract_version"], HARNESS_CORE_WIRE_CONTRACT_VERSION)
        self.assertEqual(decision["tool_ledgers"][0]["wire_contract_version"], HARNESS_CORE_WIRE_CONTRACT_VERSION)
        self.assertEqual(
            decision["tool_ledgers"][0]["authorization"]["wire_contract_version"],
            HARNESS_CORE_WIRE_CONTRACT_VERSION,
        )

    def test_n_minus_one_consumer_negotiates_with_n_producer(self) -> None:
        negotiation = negotiate_wire_contract(
            producer_version=HARNESS_CORE_WIRE_CONTRACT_VERSION + 1,
            producer_min_version=HARNESS_CORE_WIRE_CONTRACT_VERSION,
            consumer_version=HARNESS_CORE_WIRE_CONTRACT_VERSION,
            consumer_min_version=HARNESS_CORE_WIRE_CONTRACT_VERSION,
        )

        self.assertTrue(negotiation.allowed)
        self.assertEqual(negotiation.agreed_version, HARNESS_CORE_WIRE_CONTRACT_VERSION)
        self.assertEqual(negotiation.reason_codes, ())

    def test_verifier_accepts_n_producer_when_n_minus_one_compatible(self) -> None:
        kernel = HarnessKernel(surface="spawner", actor_id_ref="human:test")
        decision = self._authorized_decision()
        decision["wire_contract_version"] = HARNESS_CORE_WIRE_CONTRACT_VERSION + 1

        verification = kernel.verify_governor_execution_authority(
            decision,
            expected_capability_id="capability:spawner-ui:spawner.dispatch",
            expected_action_type="launch_mission",
            tool_name="spawner.dispatch",
        )

        self.assertTrue(verification["allowed"])
        self.assertEqual(verification["reason_codes"], [])

    def test_non_overlapping_wire_contracts_are_rejected(self) -> None:
        negotiation = negotiate_wire_contract(
            producer_version=HARNESS_CORE_WIRE_CONTRACT_VERSION + 2,
            producer_min_version=HARNESS_CORE_WIRE_CONTRACT_VERSION + 1,
            consumer_version=HARNESS_CORE_WIRE_CONTRACT_VERSION,
            consumer_min_version=HARNESS_CORE_WIRE_CONTRACT_VERSION,
        )

        self.assertFalse(negotiation.allowed)
        self.assertIsNone(negotiation.agreed_version)
        self.assertEqual(negotiation.reason_codes, ("wire_contract_no_overlap",))

    def test_verifier_rejects_non_overlapping_wire_contract(self) -> None:
        kernel = HarnessKernel(surface="spawner", actor_id_ref="human:test")
        decision = self._authorized_decision()
        decision["wire_contract_version"] = HARNESS_CORE_WIRE_CONTRACT_VERSION + 2

        verification = kernel.verify_governor_execution_authority(
            decision,
            expected_capability_id="capability:spawner-ui:spawner.dispatch",
            expected_action_type="launch_mission",
            tool_name="spawner.dispatch",
        )

        self.assertFalse(verification["allowed"])
        self.assertIn("wire_contract_no_overlap", verification["reason_codes"])


if __name__ == "__main__":
    unittest.main()
