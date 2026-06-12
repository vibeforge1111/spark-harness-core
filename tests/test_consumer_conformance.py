from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from spark_harness_core.consumer_conformance import build_toy_consumer_artifacts, run_consumer_conformance


ROOT = Path(__file__).resolve().parents[1]


def test_toy_consumer_conformance_fixture_passes_all_doc30_checks() -> None:
    report = run_consumer_conformance(build_toy_consumer_artifacts())

    assert report["passed"] is True
    assert [check["id"] for check in report["checks"]] == [
        "propose",
        "decision_through",
        "envelope_bound",
        "finalize_all_paths",
        "refusal_surfacing",
        "attested_ledger",
        "expiry",
        "signatures",
        "fail_closed",
    ]
    assert all(check["passed"] for check in report["checks"])


def test_broken_consumer_conformance_fixture_fails_targeted_check() -> None:
    report = run_consumer_conformance(build_toy_consumer_artifacts(broken="finalize_all_paths"))

    assert report["passed"] is False
    failed = {check["id"] for check in report["checks"] if not check["passed"]}
    assert failed == {"finalize_all_paths"}


def test_consumer_conformance_module_exits_nonzero_for_broken_fixture() -> None:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT / "src")
    result = subprocess.run(
        [sys.executable, "-m", "spark_harness_core.consumer_conformance", "--fixture", "broken"],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    assert '"id": "finalize_all_paths"' in result.stdout
    assert '"passed": false' in result.stdout
