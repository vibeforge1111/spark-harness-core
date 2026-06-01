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
            const category = { score: 1, evidence: [evidence], blockers: [] };
            const readiness = core.createHarnessCoreReadinessScore({
              id: 'telegram-authority',
              target_kind: 'surface',
              target_id: 'surface:telegram',
              owner_repo: 'spark-telegram-bot',
              categories: {
                execution: category,
                tools: category,
                context: category,
                lifecycle: category,
                observability: category,
                verification: category,
                governance: category
              },
              promotion_gates: {
                telegram_live_proven: true,
                startup_benchmark_proven: true,
                zero_high_agency_legacy_local_gates: true
              }
            });
            const experience = core.createHarnessCoreExperienceIndex({
              id: 'telegram-proof',
              entries: [{
                entry_id: 'experience:telegram-proof',
                entry_type: 'test_result',
                surface: 'telegram',
                summary: 'Telegram authority proof passed.',
                artifact,
                tags: ['telegram', 'authority']
              }]
            });
            const registry = core.createHarnessCoreResourceRegistry({
              id: 'spark-core',
              resources: [{
                resource_id: 'resource:harness-core',
                resource_type: 'harness_spec',
                owner_repo: 'spark-harness-core',
                lifecycle_state: 'active',
                version: '0.1.0',
                authority_scope: ['telegram'],
                tests: ['npm run build'],
                lineage: {
                  created_from: 'spark-harness-core',
                  change_manifest_refs: [],
                  rollback_ref: artifact
                }
              }]
            });
            const evaluation = core.createHarnessCoreEvaluationPack({
              id: 'telegram-route-pack',
              scope: ['telegram'],
              cases: [{
                case_id: 'case:telegram-meta-build',
                case_type: 'negative_intent',
                prompt_ref: artifact,
                expected_move: 'chat_explain',
                expected_authority_state: 'chat_only'
              }],
              metrics: [{ name: 'case_count', value: 1 }],
              promotion_rules: ['Words alone must not authorize launch_mission.']
            });
            const run = core.createHarnessCoreHarnessRun({
              id: 'telegram-route-run',
              run_type: 'route_matrix',
              surface: 'telegram',
              model_refs: ['model:gpt-5.5'],
              artifacts: [artifact],
              metrics: [{ name: 'case_count', value: 1 }],
              status: 'passed',
              summary: 'Route matrix passed.'
            });
            const component = {
              schema_version: 'harness-component-v1',
              component_id: 'component:telegram-evidence-adapter',
              component_type: 'middleware',
              owner_repo: 'spark-telegram-bot',
              path: 'src/harnessCore.ts',
              summary: 'Telegram evidence adapter.',
              editable_by_evolution: true,
              authority_scope: ['telegram'],
              dependencies: ['spark-harness-core'],
              tests: ['npm test']
            };
            const manifest = core.createHarnessCoreChangeManifest({
              id: 'telegram-evidence-adapter-change',
              target_component: component,
              failure_evidence: [evidence],
              root_cause_hypothesis: 'Telegram needs a canonical evidence adapter.',
              edit_summary: 'Route through Harness Core records.',
              predicted_fixes: ['High-agency Telegram actions use Harness Core authority.'],
              predicted_regression_risks: ['Under-specified actions may now be rejected.'],
              required_tests: ['npm test'],
              live_proof_required: true,
              rollback_plan: 'Revert the adapter change.'
            });
            const envelope = core.createHarnessCoreActionEnvelopeVNext({
              surface: 'spawner',
              ownerSystem: 'spawner-ui',
              toolName: 'spawner.dispatch',
              mutationClass: 'launches_mission',
              source: 'execution-panel',
              reason: 'User started execution from Spawner.',
              requestId: 'dispatch-vnext-test',
              target: 'mission-vnext-test'
            });
            console.log(JSON.stringify({
              highRiskOrder: core.HARNESS_CORE_RISK_ORDER.high,
              trace,
              artifact,
              evidence,
              readiness,
              experience,
              registry,
              evaluation,
              run,
              manifest,
              envelope
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
        self.assertEqual(payload["readiness"]["schema_version"], "readiness-score-v1")
        self.assertEqual(payload["readiness"]["overall"]["status"], "release_candidate")
        self.assertEqual(payload["experience"]["entries"][0]["entry_type"], "test_result")
        self.assertEqual(payload["registry"]["resources"][0]["resource_type"], "harness_spec")
        self.assertEqual(payload["evaluation"]["schema_version"], "evaluation-pack-v1")
        self.assertEqual(payload["evaluation"]["cases"][0]["expected_authority_state"], "chat_only")
        self.assertEqual(payload["run"]["schema_version"], "harness-run-v1")
        self.assertEqual(payload["run"]["verdict"]["status"], "passed")
        self.assertEqual(payload["manifest"]["schema_version"], "change-manifest-v1")
        self.assertTrue(payload["manifest"]["live_proof_required"])
        self.assertEqual(payload["envelope"]["schema_version"], "turn-intent-envelope-vnext")
        self.assertEqual(payload["envelope"]["selected_move"], "execute_action")
        self.assertEqual(payload["envelope"]["action_authority"]["state"], "executable")
        self.assertEqual(
            payload["envelope"]["proposed_actions"][0]["capability_id"],
            "capability:spawner-ui:spawner.dispatch",
        )
        self.assertEqual(payload["envelope"]["proposed_actions"][0]["action_type"], "launch_mission")

    def test_esm_package_face_exports_action_envelope_helper(self) -> None:
        script = textwrap.dedent(
            """
            (async () => {
              const core = await import('./ts-dist-esm/index.mjs');
              const envelope = core.createHarnessCoreActionEnvelopeVNext({
                surface: 'spawner',
                ownerSystem: 'spawner-ui',
                toolName: 'spawner.schedule.create',
                mutationClass: 'creates_schedule',
                source: 'mission-board',
                reason: 'User scheduled a Spark action.',
                requestId: 'schedule-vnext-test'
              });
              console.log(JSON.stringify(envelope));
            })().catch((error) => {
              console.error(error);
              process.exit(1);
            });
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
        self.assertEqual(payload["schema_version"], "turn-intent-envelope-vnext")
        self.assertEqual(payload["surface"], "spawner")
        self.assertEqual(payload["proposed_actions"][0]["action_type"], "schedule")


if __name__ == "__main__":
    unittest.main()
