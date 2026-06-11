from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012


class SchemaValidationError(ValueError):
    """Raised when a Spark harness object does not satisfy its contract."""


def schema_dir() -> Path:
    configured = os.environ.get("SPARK_HARNESS_SCHEMA_DIR")
    if configured:
        return Path(configured)
    return Path(__file__).resolve().parents[2] / "schemas"


@lru_cache(maxsize=1)
def load_schemas() -> dict[str, dict[str, Any]]:
    schemas: dict[str, dict[str, Any]] = {}
    for path in sorted(schema_dir().glob("*.schema.json")):
        with path.open("r", encoding="utf-8") as handle:
            schema = json.load(handle)
        schemas[path.name] = schema
        schemas[schema["$id"]] = schema
    return schemas


def load_schema(name_or_id: str) -> dict[str, Any]:
    schemas = load_schemas()
    if name_or_id in schemas:
        return schemas[name_or_id]
    filename = name_or_id
    if not filename.endswith(".schema.json"):
        filename = f"{filename}.schema.json"
    if filename in schemas:
        return schemas[filename]
    raise KeyError(f"unknown Spark harness schema: {name_or_id}")


@lru_cache(maxsize=1)
def schema_registry() -> Registry:
    registry = Registry()
    seen: set[str] = set()
    for schema in load_schemas().values():
        schema_id = schema["$id"]
        if schema_id in seen:
            continue
        seen.add(schema_id)
        resource = Resource.from_contents(schema, default_specification=DRAFT202012)
        registry = registry.with_resource(schema_id, resource)
    return registry


def check_all_schemas() -> None:
    seen: set[str] = set()
    for schema in load_schemas().values():
        schema_id = schema["$id"]
        if schema_id in seen:
            continue
        seen.add(schema_id)
        Draft202012Validator.check_schema(schema)


def validate_instance(schema_name_or_id: str, instance: dict[str, Any]) -> dict[str, Any]:
    schema = load_schema(schema_name_or_id)
    return validate_schema_ref(schema["$id"], instance)


def validate_schema_ref(schema_ref: str, instance: dict[str, Any]) -> dict[str, Any]:
    schema = {"$schema": "https://json-schema.org/draft/2020-12/schema", "$ref": schema_ref}
    validator = Draft202012Validator(schema, registry=schema_registry())
    errors = sorted(validator.iter_errors(instance), key=lambda error: list(error.path))
    if errors:
        details = "; ".join(
            f"{'/'.join(str(part) for part in error.path) or '<root>'}: {error.message}"
            for error in errors[:5]
        )
        raise SchemaValidationError(details)
    return instance


def list_schema_ids() -> list[str]:
    seen: set[str] = set()
    ids: list[str] = []
    for schema in load_schemas().values():
        schema_id = schema["$id"]
        if schema_id not in seen:
            seen.add(schema_id)
            ids.append(schema_id)
    return sorted(ids)

