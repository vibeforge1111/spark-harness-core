"""Spark Harness Core newborn kernel."""

from spark_harness_core.kernel import (
    READINESS_CATEGORIES,
    HarnessKernel,
    artifact_ref,
    evidence_ref,
    trace_ref,
)
from spark_harness_core.legacy_turn_intent import (
    LegacyToolAuthorization,
    TurnIntentEnvelope,
    authorize_legacy_tool_call,
    authorize_tool_call,
    parse_turn_intent_envelope,
)
from spark_harness_core.schemas import SchemaValidationError, load_schema, validate_instance

__all__ = [
    "HarnessKernel",
    "LegacyToolAuthorization",
    "READINESS_CATEGORIES",
    "SchemaValidationError",
    "TurnIntentEnvelope",
    "artifact_ref",
    "authorize_legacy_tool_call",
    "authorize_tool_call",
    "evidence_ref",
    "load_schema",
    "parse_turn_intent_envelope",
    "trace_ref",
    "validate_instance",
]
