from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TypeScriptContractTests(unittest.TestCase):
    def test_node_package_exports_canonical_contract_helpers(self) -> None:
        script = textwrap.dedent(
            """
            const core = require('./ts-dist/index.js');
            const trace = core.createHarnessCoreTraceRef({
              id: 'telegram-turn',
              summary: 'Fresh turn trace.'
            });
            const artifact = core.createHarnessCoreArtifactRef({
              id: 'telegram-args',
              kind: 'tool_args',
              path_or_uri: 'telegram://turns/test/actions/read',
              summary: 'Sanitized action args.'
            });
            const evidence = core.createHarnessCoreEvidenceRef({
              id: 'fresh-intent',
              kind: 'fresh_user_intent',
              source: 'spark-telegram-bot',
              summary: 'Fresh user turn outranks stale route state.',
              confidence: 0.96,
              trace_refs: [trace]
            });
            console.log(JSON.stringify({
              highRiskOrder: core.HARNESS_CORE_RISK_ORDER.high,
              trace,
              artifact,
              evidence
            }));
            """
        )
        result = subprocess.run(
            ["node", "-e", script],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(result.stdout)
        self.assertEqual(payload["highRiskOrder"], 4)
        self.assertEqual(payload["trace"]["id"], "trace:telegram-turn")
        self.assertEqual(payload["artifact"]["redaction_class"], "metadata_only")
        self.assertEqual(payload["evidence"]["kind"], "fresh_user_intent")


if __name__ == "__main__":
    unittest.main()
