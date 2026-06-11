from __future__ import annotations

import hashlib
import hmac
import json
from copy import deepcopy
from datetime import UTC, datetime
from secrets import token_urlsafe
from typing import Any


SIGNATURE_SCHEMA_VERSION = "governor-decision-signature-v1"
SIGNATURE_ALGORITHM = "hmac-sha256"


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def unsigned_governor_decision(decision: dict[str, Any]) -> dict[str, Any]:
    unsigned = deepcopy(decision)
    unsigned.pop("signature", None)
    return unsigned


def governor_decision_signature_payload(
    decision: dict[str, Any],
    signature: dict[str, Any],
) -> str:
    return canonical_json(
        {
            "decision": unsigned_governor_decision(decision),
            "signature": {
                "schema_version": signature.get("schema_version"),
                "alg": signature.get("alg"),
                "key_id": signature.get("key_id"),
                "nonce": signature.get("nonce"),
                "created_at": signature.get("created_at"),
            },
        }
    )


def sign_governor_decision(
    decision: dict[str, Any],
    *,
    key: str,
    key_id: str = "local",
    nonce: str | None = None,
    created_at: str | None = None,
) -> dict[str, Any]:
    key_value = str(key or "").strip()
    if not key_value:
        raise ValueError("key is required")
    signed = deepcopy(decision)
    signature = {
        "schema_version": SIGNATURE_SCHEMA_VERSION,
        "alg": SIGNATURE_ALGORITHM,
        "key_id": str(key_id or "local").strip() or "local",
        "nonce": nonce or token_urlsafe(24),
        "created_at": created_at or datetime.now(UTC).isoformat().replace("+00:00", "Z"),
    }
    signature["signature"] = _hmac_sha256_hex(governor_decision_signature_payload(signed, signature), key_value)
    signed["signature"] = signature
    return signed


def governor_decision_signature_reason_codes(
    governor_decision: dict[str, Any] | None,
    *,
    key: str | None = None,
    expected_key_id: str | None = None,
    require_signature: bool = False,
) -> list[str]:
    key_value = str(key or "").strip()
    signature_required = require_signature or bool(key_value)
    if not signature_required:
        return []
    if not key_value:
        return ["governor_signature_key_missing"]
    if not isinstance(governor_decision, dict):
        return ["missing_governor_decision"]

    signature = governor_decision.get("signature")
    if not isinstance(signature, dict):
        return ["governor_signature_missing"]

    reason_codes: list[str] = []
    if str(signature.get("schema_version") or "") != SIGNATURE_SCHEMA_VERSION:
        reason_codes.append("governor_signature_schema_invalid")
    if str(signature.get("alg") or "") != SIGNATURE_ALGORITHM:
        reason_codes.append("governor_signature_alg_invalid")
    if expected_key_id and str(signature.get("key_id") or "") != expected_key_id:
        reason_codes.append("governor_signature_key_id_mismatch")

    raw_signature = str(signature.get("signature") or "")
    if len(raw_signature) != 64:
        reason_codes.append("governor_signature_invalid")
    if reason_codes:
        return _dedupe(reason_codes)

    expected_signature = _hmac_sha256_hex(governor_decision_signature_payload(governor_decision, signature), key_value)
    if not hmac.compare_digest(raw_signature, expected_signature):
        reason_codes.append("governor_signature_invalid")
    return _dedupe(reason_codes)


def _hmac_sha256_hex(payload: str, key: str) -> str:
    return hmac.new(key.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        deduped.append(value)
    return deduped
