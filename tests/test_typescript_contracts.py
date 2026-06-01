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
            const telegramLiveQaPacket = core.createTelegramLiveQaEvidencePacket({
              generated_at: '2026-06-02T00:00:00.000Z',
              catalog: 'genesis-live-telegram-100.json',
              include_risky: true,
              title: 'Spark Genesis Telegram Live QA Evidence Packet',
              cases: [{
                ordinal: 1,
                id: 'genesis-001',
                suite: 'genesis_normal_conversation',
                risk: 'safe',
                expected_route: 'chat_think_with_me',
                expected_outcome: 'Gives advice. Must not launch a mission.',
                verdict: 'untested',
                actual_route: null,
                actual_outcome: null,
                observed_turns: [{
                  turn_index: 1,
                  prompt: 'Should we use the startup operator more?',
                  reply: null,
                  reply_timestamp: null
                }],
                side_effects: {
                  files_changed: null,
                  memory_written: null,
                  mission_started: null,
                  external_network_called: null,
                  pr_opened: null,
                  publish_or_deploy_started: null,
                  schedule_changed: null,
                  tool_or_browser_used: null
                },
                evidence_refs: {
                  authorization_ledgers: [],
                  tool_ledgers: [],
                  traces: [],
                  runtime_status: [],
                  screenshots: [],
                  commits: [],
                  prs: []
                },
                issue: null,
                fix_commit: null,
                retest_required: false
              }]
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
            const acceptedManifest = core.createHarnessCoreChangeManifest({
              id: 'telegram-evidence-adapter-accepted-change',
              target_component: component,
              failure_evidence: [evidence],
              root_cause_hypothesis: 'Telegram needs a canonical evidence adapter.',
              edit_summary: 'Route through Harness Core records.',
              predicted_fixes: ['High-agency Telegram actions use Harness Core authority.'],
              predicted_regression_risks: ['Under-specified actions may now be rejected.'],
              required_tests: ['npm test'],
              live_proof_required: false,
              rollback_plan: 'Revert the adapter change.',
              observed_delta: [{ name: 'route_matrix_pass', value: true }],
              verdict: 'accepted'
            });
            let blockedPromotion = '';
            try {
              core.createHarnessCoreSelfEvolutionRun({
                id: 'blocked-evolution',
                mode: 'promote',
                surface: 'telegram',
                experience_index: experience,
                readiness_score: readiness,
                commands: ['npm test'],
                target_components: [component],
                change_manifests: [manifest],
                verdict: 'promote_private'
              });
            } catch (error) {
              blockedPromotion = error instanceof Error ? error.message : String(error);
            }
            const selfEvolution = core.createHarnessCoreSelfEvolutionRun({
              id: 'telegram-evidence-evolution',
              mode: 'promote',
              surface: 'telegram',
              experience_index: experience,
              readiness_score: readiness,
              commands: ['npm test'],
              target_components: [component],
              change_manifests: [acceptedManifest],
              verdict: 'promote_private',
              summary: 'Accepted Telegram adapter change is ready for private promotion.'
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
            const action = envelope.proposed_actions[0];
            const authorization = {
              schema_version: 'authorization-decision-v1',
              decision_id: 'decision:spawner-dispatch',
              created_at: '2026-06-02T00:00:00.000Z',
              turn_id: envelope.turn_id,
              action_id: action.action_id,
              capability_id: action.capability_id,
              verdict: 'allow',
              risk_tier: action.risk_tier,
              reasons: ['harness_core_authorized'],
              evidence: envelope.evidence,
              approval: { required: false, status: 'not_required' },
              restrictions: {
                network_allowed: false,
                write_allowed: false,
                publish_allowed: false
              },
              trace
            };
            const governorDecision = core.createHarnessCoreGovernorDecision({
              envelope,
              authorizations: [authorization]
            });
            const authorizedGovernorDecision = core.createHarnessCoreAuthorizedGovernorDecision({
              envelope,
              tool_name: 'spawner.dispatch',
              restrictions: {
                network_allowed: false,
                write_allowed: true,
                publish_allowed: false
              }
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
              telegramLiveQaPacket,
              manifest,
              acceptedManifest,
              blockedPromotion,
              selfEvolution,
              envelope,
              governorDecision,
              authorizedGovernorDecision
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
        self.assertEqual(payload["telegramLiveQaPacket"]["schema_version"], "spark.telegram_live_qa_evidence_packet.v1")
        self.assertEqual(payload["telegramLiveQaPacket"]["selection"]["case_count"], 1)
        self.assertEqual(payload["telegramLiveQaPacket"]["summary"]["untested"], 1)
        self.assertEqual(payload["manifest"]["schema_version"], "change-manifest-v1")
        self.assertTrue(payload["manifest"]["live_proof_required"])
        self.assertEqual(payload["acceptedManifest"]["verdict"], "accepted")
        self.assertIn("accepted change manifests", payload["blockedPromotion"])
        self.assertEqual(payload["selfEvolution"]["schema_version"], "self-evolution-run-v1")
        self.assertEqual(payload["selfEvolution"]["promotion_decision"]["verdict"], "promote_private")
        self.assertEqual(payload["envelope"]["schema_version"], "turn-intent-envelope-vnext")
        self.assertEqual(payload["envelope"]["selected_move"], "execute_action")
        self.assertEqual(payload["envelope"]["action_authority"]["state"], "executable")
        self.assertEqual(
            payload["envelope"]["proposed_actions"][0]["capability_id"],
            "capability:spawner-ui:spawner.dispatch",
        )
        self.assertEqual(payload["envelope"]["proposed_actions"][0]["action_type"], "launch_mission")
        self.assertEqual(payload["governorDecision"]["schema_version"], "governor-decision-v1")
        self.assertEqual(payload["governorDecision"]["outcome"], "execute")
        self.assertTrue(payload["governorDecision"]["execution_boundary"]["legacy_authority_demoted"])
        self.assertEqual(payload["governorDecision"]["execution_boundary"]["authorized_action_count"], 1)
        self.assertEqual(payload["authorizedGovernorDecision"]["schema_version"], "governor-decision-v1")
        self.assertEqual(payload["authorizedGovernorDecision"]["outcome"], "execute")
        self.assertEqual(payload["authorizedGovernorDecision"]["authorizations"][0]["verdict"], "allow")
        self.assertEqual(payload["authorizedGovernorDecision"]["tool_ledgers"][0]["tool_name"], "spawner.dispatch")
        self.assertEqual(
            payload["authorizedGovernorDecision"]["tool_ledgers"][0]["authorization"]["capability_id"],
            "capability:spawner-ui:spawner.dispatch",
        )

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
