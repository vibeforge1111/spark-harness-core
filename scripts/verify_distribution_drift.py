"""Verify consumer-vendored harness artifacts match the built mirror.

HS-12 guardrail: the files published by the harness package must be byte
identical in each consumer vendor tree. This intentionally compares only the
package artifact surface from package.json "files" plus package.json itself,
so consumer-local manifest files can stay local.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONSUMERS = {
    "bot": Path(r"C:\Users\USER\Desktop\spark-telegram-bot"),
    "spawner": Path(r"C:\Users\USER\.spark\modules\spawner-ui\source"),
}


def _repo_root_from_fixture(path: Path) -> tuple[Path, list[tuple[str, Path]]]:
    mirror = path / "mirror"
    consumers_dir = path / "consumers"
    consumers = [(child.name, child) for child in sorted(consumers_dir.iterdir()) if child.is_dir()]
    return mirror, consumers


def _parse_consumer_spec(value: str) -> tuple[str, Path]:
    if "=" not in value:
        path = Path(value)
        return path.name, path
    name, raw_path = value.split("=", 1)
    return name.strip(), Path(raw_path.strip())


def _consumer_specs_from_env() -> list[tuple[str, Path]]:
    raw = os.environ.get("SPARK_HARNESS_DISTRIBUTION_CONSUMERS", "").strip()
    if not raw:
        return []
    return [_parse_consumer_spec(item) for item in raw.split(";") if item.strip()]


def _resolve_vendor_root(path: Path) -> Path:
    repo_vendor = path / "vendor" / "harness-core"
    if repo_vendor.exists():
        return repo_vendor
    return path


def _walk_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    return sorted(child for child in path.rglob("*") if child.is_file())


def artifact_paths(mirror_root: Path) -> list[str]:
    package_path = mirror_root / "package.json"
    package = json.loads(package_path.read_text(encoding="utf-8"))
    paths: set[str] = {"package.json"}
    for entry in package.get("files", []):
        abs_entry = mirror_root / str(entry)
        for file_path in _walk_files(abs_entry):
            paths.add(file_path.relative_to(mirror_root).as_posix())
    return sorted(paths)


def compare_consumer(mirror_root: Path, consumer_root: Path) -> list[str]:
    vendor_root = _resolve_vendor_root(consumer_root)
    errors: list[str] = []
    if not mirror_root.exists():
        return [f"mirror root missing: {mirror_root}"]
    if not vendor_root.exists():
        return [f"consumer vendor root missing: {vendor_root}"]
    for rel_path in artifact_paths(mirror_root):
        mirror_path = mirror_root / rel_path
        vendor_path = vendor_root / rel_path
        if not vendor_path.exists():
            errors.append(f"missing vendored artifact: {rel_path}")
            continue
        if mirror_path.read_bytes() != vendor_path.read_bytes():
            errors.append(f"byte drift: {rel_path}")
    return errors


def _default_consumers() -> list[tuple[str, Path]]:
    return [(name, path) for name, path in DEFAULT_CONSUMERS.items() if path.exists()]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mirror", type=Path, default=ROOT, help="Built spark-harness-core mirror root.")
    parser.add_argument(
        "--consumer",
        action="append",
        default=[],
        help="Consumer repo root or vendor root. Use NAME=PATH to label errors.",
    )
    parser.add_argument("--fixture", type=Path, help="Fixture root with mirror/ and consumers/* dirs.")
    parser.add_argument("--check", action="store_true", help="Compatibility flag for fixture check commands.")
    args = parser.parse_args(argv)

    if args.fixture:
        mirror_root, consumers = _repo_root_from_fixture(args.fixture)
    else:
        mirror_root = args.mirror
        consumers = [_parse_consumer_spec(value) for value in args.consumer]
        if not consumers:
            consumers = _consumer_specs_from_env()
        if not consumers:
            consumers = _default_consumers()

    if not consumers:
        print("distribution drift check has no consumers to verify", file=sys.stderr)
        return 1

    errors: list[str] = []
    for name, consumer_root in consumers:
        consumer_errors = compare_consumer(mirror_root, consumer_root)
        errors.extend(f"{name}: {error}" for error in consumer_errors)

    if errors:
        print("distribution drift detected:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    labels = ", ".join(name for name, _ in consumers)
    print(f"distribution drift check ok for {labels}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
