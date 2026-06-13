from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "verify_distribution_drift.py"
spec = importlib.util.spec_from_file_location("verify_distribution_drift", SCRIPT_PATH)
assert spec and spec.loader
verify_distribution_drift = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verify_distribution_drift)


def _write_fixture(root: Path, *, drift: bool = False) -> tuple[Path, Path]:
    mirror = root / "mirror"
    consumer = root / "consumer" / "vendor" / "harness-core"
    for base in (mirror, consumer):
        (base / "ts-dist").mkdir(parents=True)
        (base / "ts-dist-esm").mkdir()
        (base / "schemas").mkdir()
        (base / "package.json").write_text(
            '{"name":"@spark/harness-core","files":["ts-dist","ts-dist-esm","schemas"]}\n',
            encoding="utf-8",
        )
        (base / "ts-dist" / "index.js").write_text("module.exports = { ok: true };\n", encoding="utf-8")
        (base / "ts-dist" / "index.d.ts").write_text("export declare const ok: boolean;\n", encoding="utf-8")
        (base / "ts-dist-esm" / "index.mjs").write_text("export const ok = true;\n", encoding="utf-8")
        (base / "schemas" / "sample.schema.json").write_text('{"type":"object"}\n', encoding="utf-8")
    if drift:
        (consumer / "ts-dist" / "index.js").write_text("module.exports = { ok: false };\n", encoding="utf-8")
    return mirror, root / "consumer"


def test_compare_consumer_accepts_byte_identical_vendor_tree(tmp_path: Path) -> None:
    mirror, consumer = _write_fixture(tmp_path)

    assert verify_distribution_drift.compare_consumer(mirror, consumer) == []


def test_compare_consumer_reports_byte_drift(tmp_path: Path) -> None:
    mirror, consumer = _write_fixture(tmp_path, drift=True)

    errors = verify_distribution_drift.compare_consumer(mirror, consumer)

    assert errors == ["byte drift: ts-dist/index.js"]


def test_fixture_cli_passes_for_committed_fixture() -> None:
    fixture = ROOT / "tests" / "fixtures" / "distribution-drift"

    assert verify_distribution_drift.main(["--fixture", str(fixture), "--check"]) == 0
