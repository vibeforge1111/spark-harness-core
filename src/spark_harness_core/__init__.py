"""Spark Harness Core newborn kernel."""

from spark_harness_core.kernel import HarnessKernel, artifact_ref, evidence_ref, trace_ref
from spark_harness_core.schemas import SchemaValidationError, load_schema, validate_instance

__all__ = [
    "HarnessKernel",
    "SchemaValidationError",
    "artifact_ref",
    "evidence_ref",
    "load_schema",
    "trace_ref",
    "validate_instance",
]

