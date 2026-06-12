from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TypeScriptContractTests(unittest.TestCase):
    def test_with_governed_turn_finalizes_exception_exit_and_requires_decision(self) -> None:
        script = textwrap.dedent(
            """
            const core = require('./ts-dist/index.js');

            async function main() {
              const envelope = core.createHarnessCoreActionEnvelopeVNext({
                surface: 'telegram',
                ownerSystem: 'spawner-ui',
                toolName: 'spawner.dispatch',
                mutationClass: 'launches_mission',
                source: 'telegram',
                reason: 'User asked Spark to dispatch a mission.',
                requestId: 'governed-sdk-ts'
              });
              const governorDecision = core.createHarnessCoreAuthorizedGovernorDecision({
                envelope,
                tool_name: 'spawner.dispatch'
              });
              let finalized = null;
              let thrown = '';
              try {
                await core.withGovernedTurn({
                  governor_decision: governorDecision,
                  tool_name: 'spawner.dispatch',
                  owner_system: 'spawner-ui',
                  action_type: 'launch_mission',
                  failure_summary: 'Spawner dispatch raised inside the governed turn.',
                  failure_output_path_or_uri: 'spawner://missions/governed-sdk-ts/failure',
                  on_finalize: (ledger) => { finalized = ledger; }
                }, async (turn) => {
                  if (turn.ledger.result.status !== 'not_started') {
                    throw new Error('expected pending ledger');
                  }
                  throw new Error('dispatch failed');
                });
              } catch (error) {
                thrown = String(error && error.message || error);
              }

              let missingDecisionError = '';
              try {
                await core.withGovernedTurn({
                  governor_decision: null,
                  tool_name: 'spawner.dispatch',
                  owner_system: 'spawner-ui',
                  action_type: 'launch_mission'
                }, async () => {});
              } catch (error) {
                missingDecisionError = String(error && error.message || error);
              }

              console.log(JSON.stringify({ finalized, thrown, missingDecisionError }));
            }

            main().catch((error) => {
              console.error(error && error.stack || error);
              process.exit(1);
            });
            """
        )

        completed = subprocess.run(
            ["node", "-e", script],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["thrown"], "dispatch failed")
        self.assertIn("requires a governor decision", payload["missingDecisionError"])
        self.assertEqual(payload["finalized"]["result"]["status"], "failure")
        self.assertEqual(payload["finalized"]["result"]["summary"], "Spawner dispatch raised inside the governed turn.")
        self.assertEqual(payload["finalized"]["lifecycle"][-1]["stage"], "execute")
        self.assertEqual(payload["finalized"]["lifecycle"][-1]["verdict"], "failed")

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
                performance_budget_proven: true,
                governance_rulesets_proven: true,
                zero_high_agency_legacy_local_gates: true
              }
            });
            const readinessWithLegacyBlocker = core.createHarnessCoreReadinessScore({
              id: 'telegram-authority-legacy-blocked',
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
                performance_budget_proven: true,
                governance_rulesets_proven: true,
                zero_high_agency_legacy_local_gates: false
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
            const legacyRemovedPlane = core.createHarnessCoreLegacyAuthorityPlane({
              id: 'telegram-retired-route-helper',
              owner_repo: 'spark-telegram-bot',
              surface: 'telegram',
              plane_type: 'regex_router',
              source_path: 'removed://spark-telegram-bot/legacy-route-helper',
              summary: 'Legacy Telegram route helper is removed; Harness Core plus Governor owns authority.',
              authority_risk: {
                can_execute: false,
                can_mutate_state: false,
                can_route_turns: false,
                can_launch_mission: false
              },
              disposition: 'removed',
              evidence: [evidence],
            });
            const legacyEvidencePlane = core.createHarnessCoreLegacyAuthorityPlane({
              id: 'telegram-keyword-detector',
              owner_repo: 'spark-telegram-bot',
              surface: 'telegram',
              plane_type: 'keyword_detector',
              source_path: 'src/intent-keywords.ts',
              summary: 'Keyword detector now submits evidence only.',
              authority_risk: {},
              disposition: 'evidence_adapter',
              evidence: [evidence],
              evidence_only: true
            });
            const legacyInventory = core.createHarnessCoreLegacyAuthorityInventory({
              id: 'telegram-legacy-inventory',
              owner_repo: 'spark-telegram-bot',
              surfaces: ['telegram'],
              planes: [legacyRemovedPlane, legacyEvidencePlane]
            });
            let blockedLegacyPlaneError = '';
            try {
              core.createHarnessCoreLegacyAuthorityPlane({
                id: 'bad-local-dispatcher',
                owner_repo: 'spark-telegram-bot',
                surface: 'telegram',
                plane_type: 'local_dispatcher',
                source_path: 'src/bad-local-dispatcher.ts',
                summary: 'This local dispatcher still has high-agency authority.',
                authority_risk: {
                  can_execute: true,
                  can_mutate_state: true,
                  can_route_turns: true,
                  can_launch_mission: true
                },
                disposition: 'evidence_adapter',
                evidence: [evidence]
              });
            } catch (error) {
              blockedLegacyPlaneError = error instanceof Error ? error.message : String(error);
            }
            const telegramLiveQaPacket = core.createTelegramLiveQaEvidencePacket({
              generated_at: '2026-06-02T00:00:00.000Z',
              catalog: 'genesis-live-telegram-100.json',
              include_risky: true,
              title: 'Spark Genesis Telegram Live QA Evidence Packet',
              required_session_evidence: {
                profile: 'sparkqa-bot',
                tester: 'codex',
                bot_runtime_commit: 'abc1234',
                harness_core_commit: 'def5678',
                spark_os_compile_ref: '/tmp/spark-os-compile.json',
                spark_live_status_ref: '/tmp/spark-live-status.json',
                spark_verify_provenance_ref: '/tmp/spark-verify.json',
                telegram_chat_evidence_ref: '/tmp/telegram.png',
                overall_verdict: 'untested',
                follow_up_commits: ['abc1234'],
                pr_links: [],
                remaining_risks: ['100 live prompts still incomplete']
              },
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
            const runnerEvolution = core.createHarnessCoreChangeManifestRunner({
              id: 'telegram-evidence-runner',
              mode: 'promote',
              surface: 'telegram',
              experience_index: experience,
              readiness_score: readiness,
              commands: ['npm test'],
              change_manifests: [acceptedManifest],
              requested_verdict: 'promote_private'
            });
            const protectedComponent = {
              schema_version: 'harness-component-v1',
              component_id: 'component:authority-policy',
              component_type: 'authority_policy',
              owner_repo: 'spark-harness-core',
              path: 'src/spark_harness_core/kernel.py',
              summary: 'Protected authority policy.',
              editable_by_evolution: false,
              authority_scope: ['telegram'],
              dependencies: ['spark-harness-core'],
              tests: ['python3 -m unittest discover -s tests']
            };
            const unsafeProtectedComponent = {
              ...protectedComponent,
              component_id: 'component:verifier',
              component_type: 'verifier',
              path: 'tests/test_kernel_contracts.py',
              summary: 'Protected verifier must not be self-editable.',
              editable_by_evolution: true
            };
            let blockedEditableProtectedComponentError = '';
            try {
              core.assertHarnessCoreComponentEditablePolicy(unsafeProtectedComponent);
            } catch (error) {
              blockedEditableProtectedComponentError = error instanceof Error ? error.message : String(error);
            }
            let blockedEditableProtectedRunError = '';
            try {
              core.createHarnessCoreSelfEvolutionRun({
                id: 'unsafe-verifier-observe',
                mode: 'observe',
                surface: 'telegram',
                experience_index: experience,
                readiness_score: readiness,
                commands: ['python3 -m unittest discover -s tests'],
                target_components: [unsafeProtectedComponent]
              });
            } catch (error) {
              blockedEditableProtectedRunError = error instanceof Error ? error.message : String(error);
            }
            const protectedObserve = core.createHarnessCoreSelfEvolutionRun({
              id: 'authority-policy-observe',
              mode: 'observe',
              surface: 'telegram',
              experience_index: experience,
              readiness_score: readiness,
              commands: ['python3 -m unittest discover -s tests'],
              target_components: [protectedComponent]
            });
            const protectedRunner = core.createHarnessCoreChangeManifestRunner({
              id: 'authority-policy-runner',
              mode: 'promote',
              surface: 'telegram',
              experience_index: experience,
              readiness_score: readiness,
              commands: ['python3 -m unittest discover -s tests'],
              target_components: [protectedComponent],
              change_manifests: [],
              requested_verdict: 'promote_private'
            });
            const envelope = core.createHarnessCoreActionEnvelopeVNext({
              surface: 'spawner',
              ownerSystem: 'spawner-ui',
              toolName: 'spawner.dispatch',
              mutationClass: 'launches_mission',
              source: 'execution-panel',
              reason: 'User started execution from Spawner.',
              turnId: 'turn:spawner-edge',
              requestId: 'dispatch-vnext-test',
              target: 'mission-vnext-test'
            });
            const machineEnvelope = core.createHarnessCoreActionEnvelopeVNext({
              surface: 'spawner',
              ownerSystem: 'spawner-ui',
              toolName: 'spawner.dispatch',
              mutationClass: 'launches_mission',
              source: 'spawner-scheduler',
              reason: 'Machine scheduler proposed a dispatch without a fresh user turn.',
              requestId: 'dispatch-machine-vnext-test',
              actorKind: 'system',
              target: 'mission-vnext-test'
            });
            const machineGovernorDecision = core.createHarnessCoreAuthorizedGovernorDecision({
              envelope: machineEnvelope,
              tool_name: 'spawner.dispatch'
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
              now: '2026-06-09T11:50:00.000Z',
              restrictions: {
                network_allowed: false,
                write_allowed: true,
                publish_allowed: false
              }
            });
            const nonExpiringGovernorDecision = core.createHarnessCoreAuthorizedGovernorDecision({
              envelope,
              tool_name: 'spawner.dispatch',
              now: '2026-06-09T11:50:00.000Z',
              ttl_seconds: null
            });
            const finalizedAuthorizedLedger = core.finalizeHarnessCoreToolCallLedger({
              ledger: authorizedGovernorDecision.tool_ledgers[0],
              status: 'success',
              summary: 'Spawner dispatch completed after Governor allow authorization.',
              output_path_or_uri: 'spawner://missions/dispatch-vnext-test/result'
            });
            const governorConsumerVerification = core.verifyHarnessCoreGovernorToolAuthority({
              governor_decision: authorizedGovernorDecision,
              tool_name: 'spawner.dispatch',
              owner_system: 'spawner-ui',
              action_type: 'launch_mission',
              now: '2026-06-09T11:55:00.000Z'
            });
            const unsignedKeyedGovernorConsumerVerification = core.verifyHarnessCoreGovernorToolAuthority({
              governor_decision: authorizedGovernorDecision,
              tool_name: 'spawner.dispatch',
              owner_system: 'spawner-ui',
              action_type: 'launch_mission',
              governor_hmac_key: 'test-secret',
              now: '2026-06-09T11:55:00.000Z'
            });
            const signedGovernorDecision = core.signHarnessCoreGovernorDecision(authorizedGovernorDecision, {
              key: 'test-secret',
              key_id: 'local-test',
              nonce: 'nonce:test-governor',
              created_at: '2026-06-07T00:00:00.000Z'
            });
            const signedGovernorConsumerVerification = core.verifyHarnessCoreGovernorToolAuthority({
              governor_decision: signedGovernorDecision,
              tool_name: 'spawner.dispatch',
              owner_system: 'spawner-ui',
              action_type: 'launch_mission',
              governor_hmac_key: 'test-secret',
              governor_hmac_key_id: 'local-test',
              now: '2026-06-09T11:55:00.000Z'
            });
            const tamperedSignedGovernorDecision = JSON.parse(JSON.stringify(signedGovernorDecision));
            tamperedSignedGovernorDecision.tool_ledgers[0].tool_name = 'spawner.dispatch.forged';
            const tamperedSignedGovernorConsumerVerification = core.verifyHarnessCoreGovernorToolAuthority({
              governor_decision: tamperedSignedGovernorDecision,
              tool_name: 'spawner.dispatch',
              owner_system: 'spawner-ui',
              action_type: 'launch_mission',
              governor_hmac_key: 'test-secret',
              governor_hmac_key_id: 'local-test',
              now: '2026-06-09T11:55:00.000Z'
            });
            const boundLedgerRow = core.boundHarnessCoreLedgerRow({
              ledger: authorizedGovernorDecision.tool_ledgers[0],
              verdict: governorConsumerVerification,
              owner_system: 'spawner-ui',
              mutation_class: 'launches_mission',
              surface: 'spawner',
              request_id: 'dispatch-vnext-test',
              trace_ref: 'trace:dispatch-vnext-test'
            });
            const copiedGovernorDecision = JSON.parse(JSON.stringify(authorizedGovernorDecision));
            copiedGovernorDecision.tool_ledgers[0].action_id = 'action:copied-stale-ledger';
            copiedGovernorDecision.tool_ledgers[0].authorization.action_id = 'action:copied-stale-ledger';
            const copiedGovernorConsumerVerification = core.verifyHarnessCoreGovernorToolAuthority({
              governor_decision: copiedGovernorDecision,
              tool_name: 'spawner.dispatch',
              owner_system: 'spawner-ui',
              action_type: 'launch_mission',
              now: '2026-06-09T11:55:00.000Z'
            });
            const unboundFreshEnvelope = JSON.parse(JSON.stringify(envelope));
            unboundFreshEnvelope.freshness.fresh_user_intent_ref = {
              ...unboundFreshEnvelope.freshness.fresh_user_intent_ref,
              id: 'evidence:forged_fresh_intent'
            };
            const unboundFreshGovernorDecision = core.createHarnessCoreAuthorizedGovernorDecision({
              envelope: unboundFreshEnvelope,
              tool_name: 'spawner.dispatch'
            });
            const unboundFreshVerification = core.verifyHarnessCoreGovernorToolAuthority({
              governor_decision: unboundFreshGovernorDecision,
              tool_name: 'spawner.dispatch',
              owner_system: 'spawner-ui',
              action_type: 'launch_mission'
            });
            const expiringGovernorDecision = JSON.parse(JSON.stringify(authorizedGovernorDecision));
            expiringGovernorDecision.authorizations[0].expires_at = '2026-06-09T12:00:00Z';
            const expiredAuthorizationVerification = core.verifyHarnessCoreGovernorToolAuthority({
              governor_decision: expiringGovernorDecision,
              tool_name: 'spawner.dispatch',
              owner_system: 'spawner-ui',
              action_type: 'launch_mission',
              now: '2026-06-09T12:00:00Z'
            });
            const unexpiredAuthorizationVerification = core.verifyHarnessCoreGovernorToolAuthority({
              governor_decision: expiringGovernorDecision,
              tool_name: 'spawner.dispatch',
              owner_system: 'spawner-ui',
              action_type: 'launch_mission',
              now: '2026-06-09T11:00:00Z'
            });
            let copiedLedgerError = '';
            try {
              const copiedLedger = JSON.parse(JSON.stringify(authorizedGovernorDecision.tool_ledgers[0]));
              copiedLedger.action_id = 'action:copied-stale-ledger';
              core.finalizeHarnessCoreToolCallLedger({
                ledger: copiedLedger,
                status: 'success',
                summary: 'Copied ledger must not finalize as execution proof.',
                output_path_or_uri: 'spawner://missions/copied-ledger/result'
              });
            } catch (error) {
              copiedLedgerError = String(error && error.message || error);
            }
            const interruptedEnvelope = core.createHarnessCoreActionEnvelopeVNext({
              surface: 'telegram',
              ownerSystem: 'spark-publisher',
              toolName: 'spark.publish',
              mutationClass: 'publishes',
              source: 'telegram',
              reason: 'Publishing requires explicit approval before execution.',
              requestId: 'publish-vnext-test'
            });
            const interruptedGovernorDecision = core.createHarnessCoreAuthorizedGovernorDecision({
              envelope: interruptedEnvelope,
              tool_name: 'spark.publish'
            });
            let blockedFinalizeError = '';
            try {
              core.finalizeHarnessCoreToolCallLedger({
                ledger: interruptedGovernorDecision.tool_ledgers[0],
                status: 'success',
                summary: 'This must not be representable before approval.',
                output_path_or_uri: 'telegram://publish/success'
              });
            } catch (error) {
              blockedFinalizeError = String(error && error.message || error);
            }
            const interruptedNotStartedLedger = core.finalizeHarnessCoreToolCallLedger({
              ledger: interruptedGovernorDecision.tool_ledgers[0],
              status: 'not_started',
              summary: 'Publish was interrupted before execution.',
              output_path_or_uri: 'telegram://publish/not-started'
            });
            const oldNotStartedLedger = JSON.parse(JSON.stringify(authorizedGovernorDecision.tool_ledgers[0]));
            oldNotStartedLedger.created_at = '2026-06-10T00:00:00.000Z';
            const repairedStrandedLedger = core.repairHarnessCoreStrandedToolCallLedger({
              ledger: oldNotStartedLedger,
              now: '2026-06-10T02:00:01.000Z',
              stranded_after_seconds: 3600
            });
            const freshNotStartedLedger = JSON.parse(JSON.stringify(authorizedGovernorDecision.tool_ledgers[0]));
            freshNotStartedLedger.created_at = '2026-06-10T01:55:00.000Z';
            const repairedSweep = core.repairHarnessCoreStrandedToolCallLedgers({
              ledgers: [oldNotStartedLedger, freshNotStartedLedger, finalizedAuthorizedLedger],
              now: '2026-06-10T02:00:01.000Z',
              stranded_after_seconds: 3600
            });
            let refinalizeTerminalError = '';
            try {
              core.finalizeHarnessCoreToolCallLedger({
                ledger: finalizedAuthorizedLedger,
                status: 'failure',
                summary: 'A retry must not rewrite the evidence trail.',
                output_path_or_uri: 'spawner://missions/dispatch-vnext-test/failed'
              });
            } catch (error) {
              refinalizeTerminalError = String(error && error.message || error);
            }
            const idempotentGovernorDecision = core.createHarnessCoreAuthorizedGovernorDecision({
              envelope,
              tool_name: 'spawner.dispatch',
              idempotency_key: 'spawner-dispatch:idempotent-record'
            });
            const idempotentRetryGovernorDecision = core.createHarnessCoreAuthorizedGovernorDecision({
              envelope,
              tool_name: 'spawner.dispatch',
              idempotency_key: 'spawner-dispatch:idempotent-record'
            });
            const idempotentFinalLedger = core.finalizeHarnessCoreToolCallLedger({
              ledger: idempotentGovernorDecision.tool_ledgers[0],
              status: 'success',
              summary: 'Spawner dispatch completed once.',
              output_path_or_uri: 'spawner://missions/idempotent/result',
              idempotency_key: 'spawner-dispatch:idempotent-final'
            });
            const idempotentRetryFinalLedger = core.finalizeHarnessCoreToolCallLedger({
              ledger: idempotentFinalLedger,
              status: 'success',
              summary: 'Spawner dispatch completed once.',
              output_path_or_uri: 'spawner://missions/idempotent/result',
              idempotency_key: 'spawner-dispatch:idempotent-final'
            });
            console.log(JSON.stringify({
              highRiskOrder: core.HARNESS_CORE_RISK_ORDER.high,
              trace,
              artifact,
              evidence,
              readiness,
              readinessWithLegacyBlocker,
              experience,
              registry,
              evaluation,
              run,
              legacyInventory,
              blockedLegacyPlaneError,
              telegramLiveQaPacket,
              manifest,
              acceptedManifest,
              blockedPromotion,
              selfEvolution,
              runnerEvolution,
              protectedComponentIsProtected: core.isHarnessCoreProtectedComponentType('authority_policy'),
              adapterComponentIsProtected: core.isHarnessCoreProtectedComponentType('middleware'),
              blockedEditableProtectedComponentError,
              blockedEditableProtectedRunError,
              protectedObserve,
              protectedRunner,
              envelope,
              machineEnvelope,
              machineGovernorDecision,
              governorDecision,
              authorizedGovernorDecision,
              nonExpiringGovernorDecision,
              finalizedAuthorizedLedger,
              governorConsumerVerification,
              unsignedKeyedGovernorConsumerVerification,
              signedGovernorDecision,
              signedGovernorConsumerVerification,
              tamperedSignedGovernorConsumerVerification,
              boundLedgerRow,
              copiedGovernorConsumerVerification,
              unboundFreshGovernorDecision,
              unboundFreshVerification,
              expiredAuthorizationVerification,
              unexpiredAuthorizationVerification,
              copiedLedgerError,
              interruptedGovernorDecision,
              blockedFinalizeError,
              interruptedNotStartedLedger,
              repairedStrandedLedger,
              repairedSweep,
              refinalizeTerminalError,
              idempotentGovernorDecision,
              idempotentRetryGovernorDecision,
              idempotentFinalLedger,
              idempotentRetryFinalLedger
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
        self.assertEqual(payload["readinessWithLegacyBlocker"]["overall"]["status"], "blocked")
        self.assertEqual(payload["experience"]["entries"][0]["entry_type"], "test_result")
        self.assertEqual(payload["registry"]["resources"][0]["resource_type"], "harness_spec")
        self.assertEqual(payload["evaluation"]["schema_version"], "evaluation-pack-v1")
        self.assertEqual(payload["evaluation"]["cases"][0]["expected_authority_state"], "chat_only")
        self.assertEqual(payload["run"]["schema_version"], "harness-run-v1")
        self.assertEqual(payload["run"]["verdict"]["status"], "passed")
        self.assertEqual(payload["legacyInventory"]["schema_version"], "legacy-authority-inventory-v1")
        self.assertEqual(payload["legacyInventory"]["summary"]["removed_count"], 1)
        self.assertEqual(payload["legacyInventory"]["summary"]["canonical_consumer_count"], 0)
        self.assertEqual(payload["legacyInventory"]["summary"]["evidence_adapter_count"], 1)
        self.assertEqual(payload["legacyInventory"]["summary"]["high_agency_risk_count"], 0)
        self.assertTrue(payload["legacyInventory"]["release_gate"]["zero_high_agency_legacy_local_gates"])
        self.assertIn("evidence adapters cannot retain high-agency", payload["blockedLegacyPlaneError"])
        self.assertEqual(payload["telegramLiveQaPacket"]["schema_version"], "spark.telegram_live_qa_evidence_packet.v1")
        self.assertEqual(payload["telegramLiveQaPacket"]["selection"]["case_count"], 1)
        self.assertEqual(payload["telegramLiveQaPacket"]["summary"]["untested"], 1)
        self.assertEqual(payload["telegramLiveQaPacket"]["required_session_evidence"]["profile"], "sparkqa-bot")
        self.assertEqual(payload["telegramLiveQaPacket"]["required_session_evidence"]["remaining_risks"], ["100 live prompts still incomplete"])
        self.assertEqual(payload["manifest"]["schema_version"], "change-manifest-v1")
        self.assertTrue(payload["manifest"]["live_proof_required"])
        self.assertEqual(payload["acceptedManifest"]["verdict"], "accepted")
        self.assertIn("accepted change manifests", payload["blockedPromotion"])
        self.assertEqual(payload["selfEvolution"]["schema_version"], "self-evolution-run-v1")
        self.assertEqual(payload["selfEvolution"]["promotion_decision"]["verdict"], "promote_private")
        self.assertEqual(payload["runnerEvolution"]["promotion_decision"]["verdict"], "promote_private")
        self.assertIn("accepted_change_manifests_ready", payload["runnerEvolution"]["promotion_decision"]["summary"])
        self.assertTrue(payload["protectedComponentIsProtected"])
        self.assertFalse(payload["adapterComponentIsProtected"])
        self.assertIn("cannot be marked editable_by_evolution", payload["blockedEditableProtectedComponentError"])
        self.assertIn("cannot be marked editable_by_evolution", payload["blockedEditableProtectedRunError"])
        self.assertEqual(payload["protectedObserve"]["promotion_decision"]["verdict"], "not_ready")
        self.assertEqual(payload["protectedRunner"]["promotion_decision"]["verdict"], "not_ready")
        self.assertIn("protected_component_requires_approval", payload["protectedRunner"]["promotion_decision"]["summary"])
        self.assertEqual(payload["envelope"]["schema_version"], "turn-intent-envelope-vnext")
        self.assertEqual(payload["envelope"]["turn_id"], "turn:spawner-edge")
        self.assertEqual(payload["envelope"]["selected_move"], "execute_action")
        self.assertEqual(payload["envelope"]["action_authority"]["state"], "executable")
        self.assertEqual(payload["envelope"]["freshness"]["fresh_user_intent_ref"]["kind"], "fresh_user_intent")
        self.assertEqual(
            payload["envelope"]["proposed_actions"][0]["capability_id"],
            "capability:spawner-ui:spawner.dispatch",
        )
        self.assertEqual(payload["envelope"]["proposed_actions"][0]["action_type"], "launch_mission")
        self.assertEqual(payload["machineEnvelope"]["selected_move"], "prepare_action")
        self.assertEqual(payload["machineEnvelope"]["action_authority"]["state"], "prepare_allowed")
        self.assertFalse(payload["machineEnvelope"]["freshness"]["fresh_user_intent_present"])
        self.assertIsNone(payload["machineEnvelope"]["freshness"]["fresh_user_intent_ref"])
        self.assertEqual(payload["machineGovernorDecision"]["authorizations"][0]["verdict"], "deny")
        self.assertIn("envelope_not_executable", payload["machineGovernorDecision"]["authorizations"][0]["reasons"])
        self.assertEqual(payload["governorDecision"]["schema_version"], "governor-decision-v1")
        self.assertEqual(payload["governorDecision"]["outcome"], "degrade")
        self.assertTrue(payload["governorDecision"]["execution_boundary"]["legacy_authority_demoted"])
        self.assertEqual(payload["governorDecision"]["execution_boundary"]["authorized_action_count"], 1)
        self.assertFalse(payload["governorDecision"]["execution_boundary"]["action_authorized"])
        self.assertIn(
            "governor_missing_tool_ledger_for_authorized_execution",
            payload["governorDecision"]["execution_boundary"]["reasons"],
        )
        self.assertEqual(payload["authorizedGovernorDecision"]["schema_version"], "governor-decision-v1")
        self.assertEqual(payload["authorizedGovernorDecision"]["outcome"], "execute")
        self.assertEqual(payload["authorizedGovernorDecision"]["authorizations"][0]["verdict"], "allow")
        self.assertEqual(payload["authorizedGovernorDecision"]["authorizations"][0]["expires_at"], "2026-06-09T12:00:00.000Z")
        self.assertEqual(
            payload["authorizedGovernorDecision"]["tool_ledgers"][0]["authorization"]["expires_at"],
            "2026-06-09T12:00:00.000Z",
        )
        self.assertNotIn("expires_at", payload["nonExpiringGovernorDecision"]["authorizations"][0])
        self.assertEqual(payload["authorizedGovernorDecision"]["tool_ledgers"][0]["tool_name"], "spawner.dispatch")
        self.assertEqual(
            payload["authorizedGovernorDecision"]["tool_ledgers"][0]["authorization"]["capability_id"],
            "capability:spawner-ui:spawner.dispatch",
        )
        self.assertEqual(payload["finalizedAuthorizedLedger"]["result"]["status"], "success")
        self.assertEqual(payload["finalizedAuthorizedLedger"]["lifecycle"][-1]["verdict"], "passed")
        self.assertTrue(payload["governorConsumerVerification"]["allowed"])
        self.assertEqual(payload["governorConsumerVerification"]["ledger_id"], payload["authorizedGovernorDecision"]["tool_ledgers"][0]["ledger_id"])
        self.assertFalse(payload["unsignedKeyedGovernorConsumerVerification"]["allowed"])
        self.assertIn("governor_signature_missing", payload["unsignedKeyedGovernorConsumerVerification"]["reason_codes"])
        self.assertRegex(payload["signedGovernorDecision"]["signature"]["signature"], r"^[0-9a-f]{64}$")
        self.assertEqual(payload["signedGovernorDecision"]["signature"]["key_id"], "local-test")
        self.assertTrue(payload["signedGovernorConsumerVerification"]["allowed"])
        self.assertEqual(payload["signedGovernorConsumerVerification"]["reason_codes"], [])
        self.assertFalse(payload["tamperedSignedGovernorConsumerVerification"]["allowed"])
        self.assertIn("governor_signature_invalid", payload["tamperedSignedGovernorConsumerVerification"]["reason_codes"])
        self.assertEqual(payload["boundLedgerRow"]["turn_id"], payload["authorizedGovernorDecision"]["turn_id"])
        self.assertEqual(payload["boundLedgerRow"]["turn_id"], "turn:spawner-edge")
        self.assertEqual(
            payload["boundLedgerRow"]["authorization_decision_id"],
            payload["authorizedGovernorDecision"]["authorizations"][0]["decision_id"],
        )
        self.assertEqual(payload["boundLedgerRow"]["ledger_id"], payload["authorizedGovernorDecision"]["tool_ledgers"][0]["ledger_id"])
        self.assertEqual(payload["boundLedgerRow"]["status"], "not_started")
        self.assertEqual(payload["boundLedgerRow"]["owner_system"], "spawner-ui")
        self.assertEqual(payload["boundLedgerRow"]["mutation_class"], "launches_mission")
        self.assertFalse(payload["copiedGovernorConsumerVerification"]["allowed"])
        self.assertIn(
            "governor_missing_matching_tool_ledger",
            payload["copiedGovernorConsumerVerification"]["reason_codes"],
        )
        self.assertEqual(payload["unboundFreshGovernorDecision"]["outcome"], "deny")
        self.assertEqual(payload["unboundFreshGovernorDecision"]["authorizations"][0]["verdict"], "deny")
        self.assertIn("fresh_user_intent_evidence_unbound", payload["unboundFreshVerification"]["reason_codes"])
        self.assertFalse(payload["expiredAuthorizationVerification"]["allowed"])
        self.assertIn("authorization_expired", payload["expiredAuthorizationVerification"]["reason_codes"])
        self.assertTrue(payload["unexpiredAuthorizationVerification"]["allowed"])
        self.assertEqual(payload["unexpiredAuthorizationVerification"]["reason_codes"], [])
        self.assertIn("authorization binding mismatch", payload["copiedLedgerError"])
        self.assertEqual(payload["interruptedGovernorDecision"]["outcome"], "interrupt")
        self.assertEqual(payload["interruptedGovernorDecision"]["authorizations"][0]["verdict"], "interrupt")
        self.assertIn("allow authorization", payload["blockedFinalizeError"])
        self.assertEqual(payload["interruptedNotStartedLedger"]["result"]["status"], "not_started")
        self.assertEqual(payload["interruptedNotStartedLedger"]["lifecycle"][-1]["verdict"], "skipped")
        self.assertEqual(payload["repairedStrandedLedger"]["result"]["status"], "failure")
        self.assertIn("failure(stranded)", payload["repairedStrandedLedger"]["result"]["summary"])
        self.assertIn("error_ref", payload["repairedStrandedLedger"]["result"])
        self.assertEqual(payload["repairedStrandedLedger"]["lifecycle"][-1]["at"], "2026-06-10T02:00:01.000Z")
        self.assertEqual(payload["repairedStrandedLedger"]["lifecycle"][-1]["verdict"], "failed")
        self.assertEqual(len(payload["repairedSweep"]), 1)
        self.assertEqual(
            payload["repairedSweep"][0]["ledger_id"],
            payload["repairedStrandedLedger"]["ledger_id"],
        )
        self.assertIn("terminal tool-call ledger", payload["refinalizeTerminalError"])
        self.assertEqual(
            payload["idempotentRetryGovernorDecision"]["tool_ledgers"][0]["ledger_id"],
            payload["idempotentGovernorDecision"]["tool_ledgers"][0]["ledger_id"],
        )
        self.assertEqual(
            payload["idempotentRetryGovernorDecision"]["tool_ledgers"][0]["trace"]["id"],
            payload["idempotentGovernorDecision"]["tool_ledgers"][0]["trace"]["id"],
        )
        self.assertEqual(payload["idempotentFinalLedger"], payload["idempotentRetryFinalLedger"])

    def test_ts_authorized_governor_decision_rejects_missing_action_selector(self) -> None:
        script = textwrap.dedent(
            """
            const core = require('./ts-dist/index.js');
            const envelope = core.createHarnessCoreActionEnvelopeVNext({
              surface: 'spawner',
              ownerSystem: 'spawner-ui',
              toolName: 'spawner.dispatch',
              mutationClass: 'launches_mission',
              source: 'execution-panel',
              reason: 'User started execution from Spawner.',
              requestId: 'dispatch-missing-action-selector-test',
              target: 'mission-missing-action-selector-test'
            });
            const decision = core.createHarnessCoreAuthorizedGovernorDecision({
              envelope,
              tool_name: 'spawner.dispatch',
              action_id: 'action:not-in-envelope'
            });
            const verification = core.verifyHarnessCoreGovernorToolAuthority({
              governor_decision: decision,
              tool_name: 'spawner.dispatch',
              owner_system: 'spawner-ui',
              action_type: 'launch_mission'
            });
            console.log(JSON.stringify({ decision, verification }));
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
        self.assertEqual(payload["decision"]["outcome"], "degrade")
        self.assertEqual(payload["decision"]["authorizations"], [])
        self.assertEqual(payload["decision"]["tool_ledgers"], [])
        self.assertFalse(payload["verification"]["allowed"])
        self.assertIn("governor_missing_matching_authorization", payload["verification"]["reason_codes"])

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
              console.log(JSON.stringify({
                envelope,
                hasFinalizer: typeof core.finalizeHarnessCoreToolCallLedger === 'function'
              }));
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
        self.assertEqual(payload["envelope"]["schema_version"], "turn-intent-envelope-vnext")
        self.assertEqual(payload["envelope"]["surface"], "spawner")
        self.assertEqual(payload["envelope"]["proposed_actions"][0]["action_type"], "schedule")
        self.assertTrue(payload["hasFinalizer"])

    def test_typescript_verifier_denies_malformed_input_without_throwing(self) -> None:
        script = textwrap.dedent(
            """
            const core = require('./ts-dist/index.js');
            const cases = [
              null,
              {},
              { schema_version: 'governor-decision-v1', outcome: 'execute' },
              {
                schema_version: 'governor-decision-v1',
                turn_id: 'turn:malformed',
                outcome: 'execute',
                execution_boundary: { action_authorized: true },
                envelope: {},
                authorizations: [],
                tool_ledgers: []
              },
              {
                schema_version: 'governor-decision-v1',
                turn_id: 'turn:malformed',
                outcome: 'execute',
                execution_boundary: { action_authorized: true },
                envelope: { proposed_actions: [], freshness: {}, evidence: [] },
                authorizations: {},
                tool_ledgers: []
              }
            ];
            const results = cases.map((governor_decision) =>
              core.verifyHarnessCoreGovernorExecutionAuthority({
                governor_decision,
                expected_capability_id: 'capability:test',
                expected_action_type: 'run_command',
                tool_name: 'test.tool'
              })
            );
            console.log(JSON.stringify(results));
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
        self.assertEqual(len(payload), 5)
        self.assertFalse(any(item["allowed"] for item in payload))
        self.assertIn("missing_governor_decision", payload[0]["reason_codes"])
        for item in payload[1:]:
            self.assertIn("invalid_governor_decision", item["reason_codes"])


if __name__ == "__main__":
    unittest.main()
