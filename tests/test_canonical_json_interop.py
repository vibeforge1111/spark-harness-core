from __future__ import annotations

import hashlib
import hmac
import json
import subprocess
from pathlib import Path
from typing import Any

from spark_harness_core import HarnessKernel
from spark_harness_core.governor_signature import (
    canonical_json,
    governor_decision_signature_reason_codes,
    sign_governor_decision,
)


ROOT = Path(__file__).resolve().parents[1]
VECTOR_PATH = ROOT / "conformance" / "vectors" / "canonical-json-signature.json"
SIGNATURE_KEY = "shared-key-123"


def _node(mode: str, payload: dict[str, Any] | list[Any] | str | int | float | bool | None, key: str = SIGNATURE_KEY) -> str:
    result = subprocess.run(
        ["node", "scripts/canonical-json-interop.mjs", mode, key],
        cwd=ROOT,
        input=json.dumps(payload),
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=True,
    )
    return result.stdout


def _sample_governor_decision() -> dict[str, Any]:
    kernel = HarnessKernel(surface="telegram")
    envelope = kernel.create_envelope(
        selected_move="chat_explain",
        intent_summary="User asked for a signed cross-language conformance check.",
        raw_turn_summary="Check signature interop with confidence one.",
        confidence=1.0,
    )
    return kernel.governor_decision(envelope, authorizations=[], tool_ledgers=[])


def test_canonical_json_vector_matches_python_and_typescript() -> None:
    vector = json.loads(VECTOR_PATH.read_text(encoding="utf-8"))
    value = vector["input"]["canonical_value"]
    expected = vector["expected"]["canonical_json"]
    assert canonical_json(value) == expected
    assert _node("canonical", value) == expected

    digest = hmac.new(vector["input"]["hmac_key"].encode("utf-8"), expected.encode("utf-8"), hashlib.sha256)
    assert digest.hexdigest() == vector["expected"]["hmac_sha256"]


def test_python_signed_decision_verifies_in_typescript() -> None:
    decision = _sample_governor_decision()
    signed = sign_governor_decision(
        decision,
        key=SIGNATURE_KEY,
        key_id="local",
        nonce="python-to-ts-canonical-json",
        created_at="2026-06-11T00:00:00Z",
    )
    assert json.loads(_node("verify", signed)) == []


def test_typescript_signed_decision_verifies_in_python() -> None:
    decision = _sample_governor_decision()
    signed = json.loads(_node("sign", decision))
    assert governor_decision_signature_reason_codes(signed, key=SIGNATURE_KEY, require_signature=True) == []
