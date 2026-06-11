from __future__ import annotations

import hashlib
import hmac
import json
import math
import re
from copy import deepcopy
from decimal import Decimal
from datetime import UTC, datetime
from secrets import token_urlsafe
from typing import Any


SIGNATURE_SCHEMA_VERSION = "governor-decision-signature-v1"
SIGNATURE_ALGORITHM = "hmac-sha256"


def canonical_json(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return _canonical_json_string(value)
    if isinstance(value, int) and not isinstance(value, bool):
        return str(value)
    if isinstance(value, float):
        return _canonical_json_float(value)
    if isinstance(value, list):
        return "[" + ",".join(canonical_json(item) for item in value) + "]"
    if isinstance(value, dict):
        parts = []
        for key in sorted(value.keys(), key=_utf16_sort_key):
            if not isinstance(key, str):
                raise TypeError("canonical JSON object keys must be strings")
            parts.append(f"{_canonical_json_string(key)}:{canonical_json(value[key])}")
        return "{" + ",".join(parts) + "}"
    raise TypeError(f"value of type {type(value).__name__} is not JSON-serializable")


def _canonical_json_string(value: str) -> str:
    _reject_lone_surrogates(value)
    return json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":"))


def _canonical_json_float(value: float) -> str:
    if not math.isfinite(value):
        raise ValueError("canonical JSON numbers must be finite")
    if value == 0:
        return "0"
    if value.is_integer() and abs(value) < 1e21:
        return str(int(value))

    text = repr(value).lower()
    if "e" in text:
        mantissa, exponent_text = text.split("e", 1)
        exponent = int(exponent_text)
        if 1e-6 <= abs(value) < 1e21:
            return _decimal_to_plain(text)
        mantissa = mantissa.rstrip("0").rstrip(".")
        return f"{mantissa}e{exponent:+d}"
    return text


def _decimal_to_plain(value: str) -> str:
    text = format(Decimal(value), "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text


def _utf16_sort_key(value: str) -> tuple[int, ...]:
    _reject_lone_surrogates(value)
    encoded = value.encode("utf-16-be")
    return tuple(int.from_bytes(encoded[index : index + 2], "big") for index in range(0, len(encoded), 2))


def _reject_lone_surrogates(value: str) -> None:
    if re.search(r"[\ud800-\udfff]", value):
        raise ValueError("canonical JSON strings must not contain lone surrogates")


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
