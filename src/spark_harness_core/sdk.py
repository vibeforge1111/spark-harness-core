from __future__ import annotations

import re
from copy import deepcopy
from dataclasses import dataclass
from types import TracebackType
from typing import Any

from spark_harness_core.kernel import HarnessKernel


def _safe_id(prefix: str, raw: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9_.:-]+", "-", str(raw or "")).strip("._:-").lower()
    if not normalized:
        normalized = "item"
    value = f"{prefix}:{normalized}"
    if len(value) <= 127 and re.match(r"^[a-z][a-z0-9_.:-]{2,127}$", value):
        return value
    return f"{prefix}:item"


def _ledger_by_id(governor_decision: dict[str, Any], ledger_id: str | None) -> dict[str, Any]:
    if not ledger_id:
        raise PermissionError("governed_turn requires a matching pre-execution ledger")
    for ledger in governor_decision.get("tool_ledgers") or []:
        if isinstance(ledger, dict) and ledger.get("ledger_id") == ledger_id:
            return deepcopy(ledger)
    raise PermissionError("governed_turn requires a matching pre-execution ledger")


def _simulation(reason: str) -> dict[str, Any]:
    return {
        "dry_run": True,
        "execution_skipped": True,
        "reason": reason,
    }


def _simulated_governor_decision(governor_decision: dict[str, Any], reason: str) -> dict[str, Any]:
    simulated = deepcopy(governor_decision)
    if simulated.get("signature"):
        raise ValueError("dry-run mode cannot retrofit a signed governor decision")
    marker = _simulation(reason)
    simulated["simulation"] = marker
    for authorization in simulated.get("authorizations") or []:
        if isinstance(authorization, dict):
            authorization["simulation"] = marker
    for ledger in simulated.get("tool_ledgers") or []:
        if not isinstance(ledger, dict):
            continue
        ledger["simulation"] = marker
        authorization = ledger.get("authorization")
        if isinstance(authorization, dict):
            authorization["simulation"] = marker
    return simulated


@dataclass
class GovernedTurn:
    kernel: HarnessKernel
    governor_decision: dict[str, Any]
    verification: dict[str, Any]
    ledger: dict[str, Any]
    success_summary: str = "Governed turn completed."
    failure_summary: str = "Governed turn failed during execution."
    success_output_path: str | None = None
    failure_output_path: str | None = None
    error_path: str | None = None
    dry_run: bool = False
    should_execute: bool = True
    dry_run_summary: str = "Dry-run governed turn skipped execution."
    dry_run_output_path: str | None = None
    finalized_ledger: dict[str, Any] | None = None

    def __enter__(self) -> "GovernedTurn":
        if self.dry_run and self.finalized_ledger is None:
            self.finalize(
                status="not_started",
                summary=self.dry_run_summary,
                output_path=self.dry_run_output_path
                or f"harness-core://governed-turns/{self.ledger['ledger_id']}/dry-run",
            )
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> bool:
        if self.finalized_ledger is None:
            if exc_type is None:
                self.finalize(
                    status="success",
                    summary=self.success_summary,
                    output_path=self.success_output_path or f"harness-core://governed-turns/{self.ledger['ledger_id']}/success",
                )
            else:
                self.finalize(
                    status="failure",
                    summary=self.failure_summary,
                    output_path=self.failure_output_path or f"harness-core://governed-turns/{self.ledger['ledger_id']}/failure",
                    error_path=self.error_path or f"harness-core://governed-turns/{self.ledger['ledger_id']}/error",
                )
        return False

    def finalize(
        self,
        *,
        status: str,
        summary: str,
        output_path: str,
        error_path: str | None = None,
        rollback_path: str | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        if self.finalized_ledger is not None:
            return deepcopy(self.finalized_ledger)
        self.finalized_ledger = self.kernel.finalize_tool_call_ledger(
            self.ledger,
            status=status,
            output_path=output_path,
            summary=summary,
            error_path=error_path,
            rollback_path=rollback_path,
            idempotency_key=idempotency_key,
        )
        self.ledger = self.finalized_ledger
        return deepcopy(self.finalized_ledger)


def governed_turn(
    *,
    governor_decision: dict[str, Any] | None,
    tool_name: str,
    action_type: str,
    owner_system: str | None = None,
    expected_capability_id: str | None = None,
    action_id: str | None = None,
    kernel: HarnessKernel | None = None,
    allow_read_only: bool = False,
    require_pre_execution_ledger: bool = True,
    governor_hmac_key: str | None = None,
    governor_hmac_key_id: str | None = None,
    require_signature: bool = False,
    now: str | None = None,
    success_summary: str = "Governed turn completed.",
    failure_summary: str = "Governed turn failed during execution.",
    success_output_path: str | None = None,
    failure_output_path: str | None = None,
    error_path: str | None = None,
    dry_run: bool = False,
    dry_run_summary: str = "Dry-run governed turn skipped execution.",
    dry_run_output_path: str | None = None,
) -> GovernedTurn:
    if not isinstance(governor_decision, dict):
        raise ValueError("governed_turn requires a governor decision")
    if expected_capability_id is None:
        if not owner_system:
            raise ValueError("governed_turn requires owner_system or expected_capability_id")
        expected_capability_id = _safe_id("capability", f"{owner_system}:{tool_name}")

    effective_governor_decision = (
        _simulated_governor_decision(governor_decision, dry_run_summary) if dry_run else governor_decision
    )
    active_kernel = kernel or HarnessKernel(surface=str(effective_governor_decision.get("surface") or "future_surface"))
    verification = active_kernel.verify_governor_execution_authority(
        effective_governor_decision,
        expected_capability_id=expected_capability_id,
        expected_action_type=action_type,
        tool_name=tool_name,
        action_id=action_id,
        allow_read_only=allow_read_only,
        require_pre_execution_ledger=require_pre_execution_ledger,
        governor_hmac_key=governor_hmac_key,
        governor_hmac_key_id=governor_hmac_key_id,
        require_signature=require_signature,
        now=now,
    )
    if not verification.get("allowed"):
        reason_codes = ", ".join(str(reason) for reason in verification.get("reason_codes") or [])
        raise PermissionError(f"governed_turn refused by Governor verification: {reason_codes or 'unknown'}")

    ledger = _ledger_by_id(effective_governor_decision, verification.get("ledger_id"))
    return GovernedTurn(
        kernel=active_kernel,
        governor_decision=deepcopy(effective_governor_decision),
        verification=verification,
        ledger=ledger,
        success_summary=success_summary,
        failure_summary=failure_summary,
        success_output_path=success_output_path,
        failure_output_path=failure_output_path,
        error_path=error_path,
        dry_run=dry_run,
        should_execute=not dry_run,
        dry_run_summary=dry_run_summary,
        dry_run_output_path=dry_run_output_path,
    )
