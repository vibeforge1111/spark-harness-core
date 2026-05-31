from __future__ import annotations

import argparse
import json
from pathlib import Path

from spark_harness_core.schemas import check_all_schemas, list_schema_ids, validate_instance


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="spark-harness-core")
    subcommands = parser.add_subparsers(dest="command", required=True)

    subcommands.add_parser("validate-schemas", help="validate all JSON Schema documents")

    validate = subcommands.add_parser("validate", help="validate an instance JSON file")
    validate.add_argument("schema")
    validate.add_argument("instance")

    subcommands.add_parser("list-schemas", help="list schema ids")

    args = parser.parse_args(argv)

    if args.command == "validate-schemas":
        check_all_schemas()
        print("ok")
        return 0

    if args.command == "list-schemas":
        for schema_id in list_schema_ids():
            print(schema_id)
        return 0

    if args.command == "validate":
        with Path(args.instance).open("r", encoding="utf-8") as handle:
            instance = json.load(handle)
        validate_instance(args.schema, instance)
        print("ok")
        return 0

    raise AssertionError(f"unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())

