export type HarnessCoreSchemaVersion = 'turn-intent-envelope-vnext';
export type HarnessCoreAuthorizationSchemaVersion = 'authorization-decision-v1';
export type HarnessCoreToolLedgerSchemaVersion = 'tool-call-ledger-v1';
export type HarnessCoreGovernorSchemaVersion = 'governor-decision-v1';

export type HarnessCoreSurface =
  | 'telegram'
  | 'cli'
  | 'builder'
  | 'spawner'
  | 'memory'
  | 'startup_operator'
  | 'recursive_swarm'
  | 'voice'
  | 'domain_chip'
  | 'browser'
  | 'computer_use'
  | 'api'
  | 'test_harness'
  | 'future_surface';

export type HarnessCoreMoveType =
  | 'chat_explain'
  | 'chat_plan'
  | 'chat_compare'
  | 'chat_score'
  | 'chat_draft_text'
  | 'read_current_state'
  | 'prepare_action'
  | 'confirm_action'
  | 'execute_action';

export type HarnessCoreRiskTier = 'none' | 'read' | 'low' | 'medium' | 'high' | 'critical';

export type HarnessCoreAuthorityState =
  | 'none'
  | 'chat_only'
  | 'read_only'
  | 'prepare_allowed'
  | 'confirmation_required'
  | 'executable'
  | 'blocked';

export type HarnessCoreRedactionClass = 'public' | 'internal' | 'private' | 'secret' | 'metadata_only' | 'redacted';

export type HarnessCoreActionType =
  | 'read'
  | 'write_memory'
  | 'edit_file'
  | 'run_command'
  | 'launch_mission'
  | 'open_pr'
  | 'publish'
  | 'deploy'
  | 'schedule'
  | 'create_domain_chip'
  | 'send_message'
  | 'external_api_call'
  | 'browser_action'
  | 'computer_action';

export type HarnessCoreEvidenceKind =
  | 'fresh_user_intent'
  | 'quoted_language'
  | 'meta_language'
  | 'negative_intent'
  | 'positive_command'
  | 'memory'
  | 'pending_state'
  | 'route_candidate'
  | 'tool_result'
  | 'runtime_state'
  | 'test_result'
  | 'human_confirmation'
  | 'surface_signal'
  | 'policy';

export interface HarnessCoreTraceRef {
  id: string;
  href?: string;
  redaction_class: HarnessCoreRedactionClass;
  summary: string;
}

export interface HarnessCoreArtifactRef {
  id: string;
  kind: string;
  path_or_uri: string;
  sha256?: string;
  redaction_class: HarnessCoreRedactionClass;
  summary: string;
}

export interface HarnessCoreEvidenceRef {
  id: string;
  kind: HarnessCoreEvidenceKind;
  source: string;
  summary: string;
  confidence: number;
  trace_refs: HarnessCoreTraceRef[];
}

export interface HarnessCoreProposedAction {
  action_id: string;
  capability_id: string;
  action_type: HarnessCoreActionType;
  risk_tier: HarnessCoreRiskTier;
  summary: string;
  args_ref: HarnessCoreArtifactRef;
  requires_confirmation: boolean;
}

export interface TurnIntentEnvelopeVNext {
  schema_version: HarnessCoreSchemaVersion;
  turn_id: string;
  created_at: string;
  surface: HarnessCoreSurface;
  actor: {
    kind: 'human' | 'agent' | 'system';
    id_ref: string;
    redaction_class: HarnessCoreRedactionClass;
  };
  raw_turn_ref: HarnessCoreTraceRef;
  selected_move: HarnessCoreMoveType;
  intent_summary: string;
  freshness: {
    fresh_user_intent_present: boolean;
    stale_state_used_as_authority: false;
    memory_used_as_instruction: false;
    pending_state_used_as_authority: false;
  };
  evidence: HarnessCoreEvidenceRef[];
  action_authority: {
    state: HarnessCoreAuthorityState;
    risk_tier: HarnessCoreRiskTier;
    confidence: number;
    requires_human_confirmation: boolean;
    confirmation_ref?: HarnessCoreEvidenceRef;
    reason: string;
  };
  proposed_actions: HarnessCoreProposedAction[];
  blocked_routes: Array<{
    route_id: string;
    reason: string;
    evidence?: HarnessCoreEvidenceRef;
  }>;
  context_policy: {
    raw_private_text_in_context: boolean;
    store_raw_turn: boolean;
    summary_required: boolean;
    offload_artifacts: HarnessCoreArtifactRef[];
  };
  trace: HarnessCoreTraceRef;
}

export interface AuthorizationDecisionV1 {
  schema_version: HarnessCoreAuthorizationSchemaVersion;
  decision_id: string;
  created_at: string;
  turn_id: string;
  action_id: string;
  capability_id: string;
  verdict: 'allow' | 'deny' | 'interrupt' | 'degrade';
  risk_tier: HarnessCoreRiskTier;
  reasons: string[];
  evidence: HarnessCoreEvidenceRef[];
  approval: {
    required: boolean;
    status: 'not_required' | 'requested' | 'approved' | 'denied' | 'expired';
    approval_ref?: HarnessCoreEvidenceRef;
  };
  restrictions: {
    max_runtime_seconds?: number;
    allowed_paths?: string[];
    denied_paths?: string[];
    network_allowed?: boolean;
    write_allowed?: boolean;
    publish_allowed?: boolean;
  };
  expires_at?: string;
  trace: HarnessCoreTraceRef;
}

export interface ToolCallLedgerV1 {
  schema_version: HarnessCoreToolLedgerSchemaVersion;
  ledger_id: string;
  created_at: string;
  turn_id: string;
  action_id: string;
  capability_id: string;
  tool_name: string;
  lifecycle: Array<{
    stage:
      | 'propose'
      | 'validate'
      | 'authorize'
      | 'approve'
      | 'interrupt'
      | 'execute'
      | 'sanitize'
      | 'store'
      | 'summarize'
      | 'continue'
      | 'rollback'
      | 'fail';
    at: string;
    verdict: 'pending' | 'passed' | 'failed' | 'skipped';
    summary?: string;
  }>;
  authorization: AuthorizationDecisionV1;
  arguments: {
    schema_valid: boolean;
    raw_ref: HarnessCoreArtifactRef;
    sanitized_ref: HarnessCoreArtifactRef;
  };
  result: {
    status: 'not_started' | 'success' | 'failure' | 'partial' | 'rolled_back';
    summary: string;
    sanitized_output_ref: HarnessCoreArtifactRef;
    error_ref?: HarnessCoreArtifactRef;
    rollback_ref?: HarnessCoreArtifactRef;
  };
  trace: HarnessCoreTraceRef;
}

export type HarnessCoreGovernorOutcome =
  | 'chat_only'
  | 'read_only'
  | 'prepare'
  | 'execute'
  | 'interrupt'
  | 'deny'
  | 'degrade';

export interface GovernorDecisionV1 {
  schema_version: HarnessCoreGovernorSchemaVersion;
  decision_id: string;
  created_at: string;
  surface: HarnessCoreSurface;
  turn_id: string;
  selected_move: HarnessCoreMoveType;
  authority_state: HarnessCoreAuthorityState;
  risk_tier: HarnessCoreRiskTier;
  outcome: HarnessCoreGovernorOutcome;
  envelope: TurnIntentEnvelopeVNext;
  authorizations: AuthorizationDecisionV1[];
  tool_ledgers: ToolCallLedgerV1[];
  execution_boundary: {
    action_authorized: boolean;
    action_count: number;
    authorized_action_count: number;
    requires_human_confirmation: boolean;
    legacy_authority_demoted: true;
    reasons: string[];
  };
  reply_contract: {
    style: 'human_conversational' | 'compact_status' | 'dense_card' | 'raw_json' | 'no_reply';
    instruction: string;
    inspect_link_allowed: boolean;
    should_interrupt: boolean;
  };
  evidence: HarnessCoreEvidenceRef[];
  trace: HarnessCoreTraceRef;
}

export type HarnessCoreReadinessCategoryName =
  | 'execution'
  | 'tools'
  | 'context'
  | 'lifecycle'
  | 'observability'
  | 'verification'
  | 'governance';

export interface HarnessCoreCategoryScore {
  score: number;
  evidence: HarnessCoreEvidenceRef[];
  blockers: string[];
}

export interface ReadinessScoreV1 {
  schema_version: 'readiness-score-v1';
  score_id: string;
  created_at: string;
  target: {
    kind: 'repo' | 'surface' | 'capability' | 'release' | 'resource';
    id: string;
    owner_repo: string;
  };
  categories: Record<HarnessCoreReadinessCategoryName, HarnessCoreCategoryScore>;
  promotion_gates: {
    public_ready: boolean;
    network_absorbable: boolean;
    telegram_live_proven: boolean;
    startup_benchmark_proven: boolean;
    performance_budget_proven: boolean;
    zero_high_agency_legacy_local_gates: boolean;
  };
  overall: {
    score: number;
    status: 'blocked' | 'private_ready' | 'release_candidate' | 'public_ready';
    summary: string;
  };
}

export interface ExperienceIndexV1 {
  schema_version: 'experience-index-v1';
  index_id: string;
  created_at: string;
  entries: Array<{
    entry_id: string;
    entry_type:
      | 'raw_trace'
      | 'cleaned_trace'
      | 'trajectory_report'
      | 'score'
      | 'route_decision'
      | 'tool_ledger'
      | 'screenshot'
      | 'diff'
      | 'test_result'
      | 'live_reply'
      | 'failure_report'
      | 'success_pattern';
    surface: HarnessCoreSurface;
    summary: string;
    artifact: HarnessCoreArtifactRef;
    tags: string[];
    linked_run_id?: string;
    linked_change_id?: string;
  }>;
  query_hints: Array<{
    name: string;
    description: string;
    glob: string;
  }>;
}

export interface ResourceRegistryV1 {
  schema_version: 'resource-registry-v1';
  registry_id: string;
  created_at: string;
  resources: Array<{
    resource_id: string;
    resource_type:
      | 'prompt'
      | 'agent'
      | 'subagent'
      | 'tool'
      | 'environment'
      | 'memory_store'
      | 'surface_adapter'
      | 'harness_spec'
      | 'eval_pack'
      | 'startup_policy'
      | 'surface_rule'
      | 'model_profile'
      | 'hook';
    owner_repo: string;
    lifecycle_state: 'draft' | 'active' | 'quarantined' | 'deprecated' | 'archived';
    version: string;
    authority_scope: HarnessCoreSurface[];
    tests: string[];
    lineage: {
      created_from: string;
      change_manifest_refs: string[];
      rollback_ref: HarnessCoreArtifactRef;
    };
  }>;
}

export interface HarnessCoreMetric {
  name: string;
  value: number | boolean | string;
  unit?: string;
  higher_is_better?: boolean;
}

export interface EvaluationPackV1 {
  schema_version: 'evaluation-pack-v1';
  pack_id: string;
  created_at: string;
  scope: HarnessCoreSurface[];
  cases: Array<{
    case_id: string;
    case_type:
      | 'negative_intent'
      | 'positive_action'
      | 'mixed_intent'
      | 'stale_context'
      | 'pending_state'
      | 'startup_quality'
      | 'tool_lifecycle'
      | 'live_surface'
      | 'regression'
      | 'latency_cost';
    prompt_ref: HarnessCoreArtifactRef;
    expected_move: HarnessCoreMoveType;
    expected_authority_state: HarnessCoreAuthorityState;
  }>;
  metrics: HarnessCoreMetric[];
  jury: {
    blind: boolean;
    judge_count: number;
    rubric_ref: HarnessCoreArtifactRef;
  };
  promotion_rules: string[];
}

export interface HarnessRunV1 {
  schema_version: 'harness-run-v1';
  run_id: string;
  created_at: string;
  run_type:
    | 'single_turn'
    | 'route_matrix'
    | 'live_surface_qa'
    | 'startup_benchmark'
    | 'blind_jury'
    | 'mission'
    | 'readiness_scan'
    | 'self_evolution'
    | 'release_gate';
  surface: HarnessCoreSurface;
  model_refs: string[];
  envelopes: TurnIntentEnvelopeVNext[];
  tool_ledgers: ToolCallLedgerV1[];
  artifacts: HarnessCoreArtifactRef[];
  metrics: HarnessCoreMetric[];
  verdict: {
    status: 'passed' | 'failed' | 'blocked' | 'inconclusive';
    summary: string;
    remaining_risks?: string[];
  };
}

export type TelegramLiveQaRisk = 'safe' | 'mission' | 'writes_files' | 'external';
export type TelegramLiveQaVerdict = 'pass' | 'fail' | 'blocked' | 'needs-retest' | 'untested';

export interface TelegramLiveQaEvidencePacketV1 {
  schema_version: 'spark.telegram_live_qa_evidence_packet.v1';
  generated_at: string;
  run_id: string;
  title: string;
  catalog: string;
  selection: {
    suite: string | null;
    include_risky: boolean;
    case_count: number;
    risk_counts: Record<TelegramLiveQaRisk, number>;
  };
  authority_claim_boundary: string;
  required_session_evidence: {
    profile: string | null;
    tester: string | null;
    bot_runtime_commit: string | null;
    harness_core_commit: string | null;
    spark_os_compile_ref: string | null;
    spark_live_status_ref: string | null;
    spark_verify_provenance_ref: string | null;
    telegram_chat_evidence_ref: string | null;
    overall_verdict: TelegramLiveQaVerdict;
    follow_up_commits: string[];
    pr_links: string[];
    remaining_risks: string[];
  };
  verdict_values: TelegramLiveQaVerdict[];
  cases: Array<{
    ordinal: number;
    id: string;
    suite: string;
    risk: TelegramLiveQaRisk;
    expected_route: string;
    expected_outcome: string;
    verdict: TelegramLiveQaVerdict;
    actual_route: string | null;
    actual_outcome: string | null;
    observed_turns: Array<{
      turn_index: number;
      prompt: string;
      reply: string | null;
      reply_timestamp: string | null;
    }>;
    side_effects: {
      files_changed: boolean | null;
      memory_written: boolean | null;
      mission_started: boolean | null;
      external_network_called: boolean | null;
      pr_opened: boolean | null;
      publish_or_deploy_started: boolean | null;
      schedule_changed: boolean | null;
      tool_or_browser_used: boolean | null;
    };
    evidence_refs: {
      authorization_ledgers: string[];
      tool_ledgers: string[];
      traces: string[];
      runtime_status: string[];
      screenshots: string[];
      commits: string[];
      prs: string[];
    };
    issue: string | null;
    fix_commit: string | null;
    retest_required: boolean;
  }>;
  summary: {
    pass: number;
    fail: number;
    blocked: number;
    needs_retest: number;
    untested: number;
  };
}

export interface HarnessComponentV1 {
  schema_version: 'harness-component-v1';
  component_id: string;
  component_type:
    | 'system_prompt'
    | 'tool_description'
    | 'tool_implementation'
    | 'middleware'
    | 'skill'
    | 'subagent_config'
    | 'long_term_memory'
    | 'authority_policy'
    | 'surface_spec'
    | 'hook'
    | 'verifier'
    | 'benchmark'
    | 'model_config'
    | 'resource_registry'
    | 'experience_index'
    | 'kernel_code';
  owner_repo: string;
  path: string;
  summary: string;
  editable_by_evolution: boolean;
  authority_scope: HarnessCoreSurface[];
  dependencies: string[];
  tests: string[];
  rollback_ref?: HarnessCoreArtifactRef;
}

export interface ChangeManifestV1 {
  schema_version: 'change-manifest-v1';
  change_id: string;
  created_at: string;
  target_component: HarnessComponentV1;
  failure_evidence: HarnessCoreEvidenceRef[];
  root_cause_hypothesis: string;
  edit_summary: string;
  predicted_fixes: string[];
  predicted_regression_risks: string[];
  required_tests: string[];
  live_proof_required: boolean;
  human_approval_ref?: HarnessCoreEvidenceRef;
  rollback_plan: string;
  observed_delta: HarnessCoreMetric[];
  verdict: 'draft' | 'accepted' | 'rejected' | 'rolled_back' | 'needs_more_evidence';
}

export interface SelfEvolutionRunV1 {
  schema_version: 'self-evolution-run-v1';
  evolution_id: string;
  created_at: string;
  mode: 'observe' | 'propose' | 'sandbox' | 'live_qa' | 'promote' | 'rollback';
  roles: {
    harness_scientist: string;
    surface_operator: string;
    verifier: string;
  };
  experience_index: ExperienceIndexV1;
  target_components: HarnessComponentV1[];
  change_manifests: ChangeManifestV1[];
  test_plan: {
    evaluation_packs: EvaluationPackV1[];
    live_surface_required: boolean;
    commands: string[];
  };
  promotion_decision: {
    verdict: 'not_ready' | 'promote_private' | 'promote_release_candidate' | 'rollback';
    summary: string;
    readiness_score: ReadinessScoreV1;
  };
}

export type HarnessCoreActionMutationClass =
  | 'none'
  | 'read_only'
  | 'writes_memory'
  | 'writes_files'
  | 'launches_mission'
  | 'controls_mission'
  | 'creates_schedule'
  | 'deletes_schedule'
  | 'creates_chip'
  | 'publishes'
  | 'external_network';

export const HARNESS_CORE_RISK_ORDER: Readonly<Record<HarnessCoreRiskTier, number>> = Object.freeze({
  none: 0,
  read: 1,
  low: 2,
  medium: 3,
  high: 4,
  critical: 5
});

const HARNESS_CORE_EXECUTED_TOOL_STATUSES = new Set<ToolCallLedgerV1['result']['status']>([
  'success',
  'failure',
  'partial',
  'rolled_back'
]);

export function safeHarnessCoreId(prefix: string, raw: string): string {
  const normalized = raw.toLowerCase().replace(/[^a-z0-9_.:-]+/g, '-').replace(/^-+|-+$/g, '');
  const suffix = normalized || Math.random().toString(16).slice(2, 14);
  const id = suffix.startsWith(`${prefix}:`) || suffix.startsWith(`${prefix}_`) ? suffix : `${prefix}:${suffix}`;
  return id.slice(0, 128);
}

export function createHarnessCoreTraceRef(input: {
  id: string;
  summary: string;
  redaction_class?: HarnessCoreRedactionClass;
  href?: string;
}): HarnessCoreTraceRef {
  return {
    id: safeHarnessCoreId('trace', input.id),
    ...(input.href ? { href: input.href } : {}),
    redaction_class: input.redaction_class || 'metadata_only',
    summary: input.summary
  };
}

export function createHarnessCoreArtifactRef(input: {
  id: string;
  kind: string;
  path_or_uri: string;
  summary: string;
  sha256?: string;
  redaction_class?: HarnessCoreRedactionClass;
}): HarnessCoreArtifactRef {
  return {
    id: safeHarnessCoreId('artifact', input.id),
    kind: input.kind,
    path_or_uri: input.path_or_uri,
    ...(input.sha256 ? { sha256: input.sha256 } : {}),
    redaction_class: input.redaction_class || 'metadata_only',
    summary: input.summary
  };
}

export function createHarnessCoreEvidenceRef(input: {
  id: string;
  kind: HarnessCoreEvidenceKind;
  source: string;
  summary: string;
  confidence: number;
  trace_refs?: HarnessCoreTraceRef[];
}): HarnessCoreEvidenceRef {
  return {
    id: safeHarnessCoreId('evidence', input.id),
    kind: input.kind,
    source: input.source,
    summary: input.summary,
    confidence: input.confidence,
    trace_refs: input.trace_refs || []
  };
}

export function actionTypeForHarnessMutation(mutationClass: HarnessCoreActionMutationClass, publishes = false): HarnessCoreActionType {
  if (publishes || mutationClass === 'publishes') return 'publish';
  switch (mutationClass) {
    case 'none':
    case 'read_only':
      return 'read';
    case 'writes_memory':
      return 'write_memory';
    case 'writes_files':
      return 'edit_file';
    case 'launches_mission':
      return 'launch_mission';
    case 'creates_schedule':
    case 'deletes_schedule':
      return 'schedule';
    case 'creates_chip':
      return 'create_domain_chip';
    case 'external_network':
      return 'external_api_call';
    default:
      return 'run_command';
  }
}

export function riskTierForHarnessMutation(input: {
  mutationClass: HarnessCoreActionMutationClass;
  publishes?: boolean;
  externalNetwork?: boolean;
}): HarnessCoreRiskTier {
  if (input.publishes || input.mutationClass === 'publishes') return 'high';
  if (input.externalNetwork || input.mutationClass === 'external_network') return 'medium';
  switch (input.mutationClass) {
    case 'none':
      return 'none';
    case 'read_only':
      return 'read';
    case 'writes_memory':
      return 'low';
    case 'writes_files':
    case 'launches_mission':
    case 'controls_mission':
    case 'creates_schedule':
    case 'deletes_schedule':
    case 'creates_chip':
      return 'medium';
    default:
      return 'medium';
  }
}

export function createHarnessCoreActionEnvelopeVNext(input: {
  surface: HarnessCoreSurface;
  ownerSystem: string;
  toolName: string;
  mutationClass: HarnessCoreActionMutationClass;
  source: string;
  reason: string;
  requestId?: string | null;
  actorKind?: 'human' | 'agent' | 'system';
  actorIdRef?: string | null;
  target?: string | null;
  createdAt?: string;
  confidence?: number;
  riskTier?: HarnessCoreRiskTier;
  publishes?: boolean;
  externalNetwork?: boolean;
  requiresHumanConfirmation?: boolean;
}): TurnIntentEnvelopeVNext {
  const createdAt = input.createdAt || new Date().toISOString();
  const requestId = input.requestId?.trim() || `${input.source}:${createdAt}`;
  const actorKind = input.actorKind || 'human';
  const confidence = typeof input.confidence === 'number' ? input.confidence : actorKind === 'human' ? 0.95 : 0.9;
  const riskTier = input.riskTier || riskTierForHarnessMutation({
    mutationClass: input.mutationClass,
    publishes: input.publishes,
    externalNetwork: input.externalNetwork
  });
  const actionType = actionTypeForHarnessMutation(input.mutationClass, input.publishes);
  const requiresConfirmation =
    input.requiresHumanConfirmation === true || HARNESS_CORE_RISK_ORDER[riskTier] >= HARNESS_CORE_RISK_ORDER.high;
  const turnId = safeHarnessCoreId('turn', `${input.surface}:${input.source}:${requestId}`);
  const trace = createHarnessCoreTraceRef({
    id: `${input.surface}:${input.source}:${requestId}`,
    summary: input.reason,
    redaction_class: 'metadata_only'
  });
  const actionId = safeHarnessCoreId('action', `${turnId}:${input.toolName}`);
  const target = input.target?.trim() || input.toolName;
  const action: HarnessCoreProposedAction = {
    action_id: actionId,
    capability_id: safeHarnessCoreId('capability', `${input.ownerSystem}:${input.toolName}`),
    action_type: actionType,
    risk_tier: riskTier,
    summary: input.reason,
    args_ref: createHarnessCoreArtifactRef({
      id: `${actionId}:args`,
      kind: 'tool_args',
      path_or_uri: `${input.surface}://actions/${encodeURIComponent(input.toolName)}/${encodeURIComponent(requestId)}`,
      summary: `${input.surface} action arguments are retained by the surface adapter.`,
      redaction_class: 'metadata_only'
    }),
    requires_confirmation: requiresConfirmation
  };
  const selectedMove: HarnessCoreMoveType =
    requiresConfirmation ? 'confirm_action' : actionType === 'read' ? 'read_current_state' : 'execute_action';
  const authorityState: HarnessCoreAuthorityState =
    selectedMove === 'confirm_action' ? 'confirmation_required' : selectedMove === 'read_current_state' ? 'read_only' : 'executable';
  const evidenceKind: HarnessCoreEvidenceKind = actorKind === 'human' ? 'fresh_user_intent' : 'surface_signal';
  const evidence = [
    createHarnessCoreEvidenceRef({
      id: `${turnId}:fresh-authority`,
      kind: evidenceKind,
      source: input.source,
      summary: input.reason,
      confidence,
      trace_refs: [trace]
    }),
    createHarnessCoreEvidenceRef({
      id: `${turnId}:surface-action`,
      kind: 'surface_signal',
      source: input.surface,
      summary: `${input.surface} submitted ${input.toolName} for ${target}.`,
      confidence: Math.min(confidence, 0.9),
      trace_refs: [trace]
    })
  ];

  return {
    schema_version: 'turn-intent-envelope-vnext',
    turn_id: turnId,
    created_at: createdAt,
    surface: input.surface,
    actor: {
      kind: actorKind,
      id_ref: input.actorIdRef?.trim() || `${input.surface}-${actorKind}`,
      redaction_class: 'metadata_only'
    },
    raw_turn_ref: trace,
    selected_move: selectedMove,
    intent_summary: input.reason,
    freshness: {
      fresh_user_intent_present: actorKind === 'human',
      stale_state_used_as_authority: false,
      memory_used_as_instruction: false,
      pending_state_used_as_authority: false
    },
    evidence,
    action_authority: {
      state: authorityState,
      risk_tier: riskTier,
      confidence,
      requires_human_confirmation: requiresConfirmation,
      reason: requiresConfirmation
        ? 'Harness Core requires confirmation before this high-risk action can execute.'
        : 'Fresh surface evidence authorizes this action through Harness Core.'
    },
    proposed_actions: [action],
    blocked_routes: [],
    context_policy: {
      raw_private_text_in_context: false,
      store_raw_turn: false,
      summary_required: true,
      offload_artifacts: []
    },
    trace
  };
}

function governorOutcomeFor(input: {
  envelope: TurnIntentEnvelopeVNext;
  authorizations: AuthorizationDecisionV1[];
}): HarnessCoreGovernorOutcome {
  const { envelope, authorizations } = input;
  const state = envelope.action_authority.state;
  const verdicts = new Set(authorizations.map((authorization) => authorization.verdict));
  if (state === 'executable' && verdicts.has('allow')) return 'execute';
  if (state === 'confirmation_required' || verdicts.has('interrupt')) return 'interrupt';
  if (state === 'read_only') return 'read_only';
  if (state === 'prepare_allowed') return 'prepare';
  if (state === 'blocked' || verdicts.has('deny')) return 'deny';
  if (envelope.selected_move.startsWith('chat_') && envelope.proposed_actions.length === 0) return 'chat_only';
  return 'degrade';
}

function defaultGovernorReplyStyle(outcome: HarnessCoreGovernorOutcome): GovernorDecisionV1['reply_contract']['style'] {
  return outcome === 'degrade' ? 'compact_status' : 'human_conversational';
}

function defaultGovernorReplyInstruction(outcome: HarnessCoreGovernorOutcome): string {
  switch (outcome) {
    case 'execute':
      return 'Proceed only with the authorized action and record the result ledger.';
    case 'interrupt':
      return 'Ask for explicit approval before any high-agency action executes.';
    case 'read_only':
      return 'Answer from fresh read-only state; do not mutate state.';
    case 'prepare':
      return 'Prepare the action plan without executing tools or mutating state.';
    case 'deny':
      return 'Briefly explain why the action boundary was denied and stay conversational.';
    case 'degrade':
      return 'Use the safest non-executing surface behavior and preserve evidence for review.';
    default:
      return 'Answer conversationally; do not launch, write, schedule, publish, or run tools.';
  }
}

function governorReasonsFor(input: {
  outcome: HarnessCoreGovernorOutcome;
  envelope: TurnIntentEnvelopeVNext;
  authorizations: AuthorizationDecisionV1[];
}): string[] {
  const reasons = ['fresh_user_intent_is_authority', 'legacy_detectors_are_evidence_only'];
  switch (input.outcome) {
    case 'execute':
      reasons.push('governor_authorized_execution');
      break;
    case 'interrupt':
      reasons.push('governor_requires_explicit_confirmation');
      break;
    case 'read_only':
      reasons.push('governor_allows_read_only_state_access');
      break;
    case 'chat_only':
      reasons.push('governor_keeps_turn_conversational');
      break;
    case 'prepare':
      reasons.push('governor_allows_preparation_without_execution');
      break;
    case 'deny':
      reasons.push('governor_denies_action_boundary');
      break;
    default:
      reasons.push('governor_degrades_to_safe_surface_behavior');
      break;
  }
  for (const authorization of input.authorizations) {
    for (const reason of authorization.reasons) {
      if (!reasons.includes(reason)) reasons.push(reason);
    }
  }
  if (input.envelope.action_authority.requires_human_confirmation) {
    reasons.push('human_confirmation_required_by_envelope');
  }
  return reasons;
}

export function createHarnessCoreGovernorDecision(input: {
  envelope: TurnIntentEnvelopeVNext;
  authorizations?: AuthorizationDecisionV1[];
  tool_ledgers?: ToolCallLedgerV1[];
  reply_style?: GovernorDecisionV1['reply_contract']['style'];
  reply_instruction?: string;
}): GovernorDecisionV1 {
  const authorizations = input.authorizations || [];
  const toolLedgers = input.tool_ledgers || [];
  const outcome = governorOutcomeFor({ envelope: input.envelope, authorizations });
  const authorizedActionCount = authorizations.filter((authorization) => authorization.verdict === 'allow').length;
  const requiresHumanConfirmation =
    input.envelope.action_authority.requires_human_confirmation ||
    authorizations.some((authorization) => authorization.approval.required);
  return {
    schema_version: 'governor-decision-v1',
    decision_id: safeHarnessCoreId('governor-decision', `${input.envelope.turn_id}:${outcome}`),
    created_at: new Date().toISOString(),
    surface: input.envelope.surface,
    turn_id: input.envelope.turn_id,
    selected_move: input.envelope.selected_move,
    authority_state: input.envelope.action_authority.state,
    risk_tier: input.envelope.action_authority.risk_tier,
    outcome,
    envelope: input.envelope,
    authorizations,
    tool_ledgers: toolLedgers,
    execution_boundary: {
      action_authorized: outcome === 'execute',
      action_count: input.envelope.proposed_actions.length,
      authorized_action_count: authorizedActionCount,
      requires_human_confirmation: requiresHumanConfirmation,
      legacy_authority_demoted: true,
      reasons: governorReasonsFor({ outcome, envelope: input.envelope, authorizations })
    },
    reply_contract: {
      style: input.reply_style || defaultGovernorReplyStyle(outcome),
      instruction: input.reply_instruction || defaultGovernorReplyInstruction(outcome),
      inspect_link_allowed: ['read_only', 'execute', 'interrupt', 'degrade'].includes(outcome),
      should_interrupt: outcome === 'interrupt'
    },
    evidence: input.envelope.evidence,
    trace: createHarnessCoreTraceRef({
      id: `${input.envelope.turn_id}:governor`,
      summary: 'Governor decision created by Spark Harness Core.'
    })
  };
}

export function createHarnessCoreAuthorizedGovernorDecision(input: {
  envelope: TurnIntentEnvelopeVNext;
  tool_name: string;
  action_id?: string;
  capability_id?: string;
  reasons?: string[];
  restrictions?: Partial<AuthorizationDecisionV1['restrictions']>;
  reply_style?: GovernorDecisionV1['reply_contract']['style'];
  reply_instruction?: string;
  now?: string;
}): GovernorDecisionV1 {
  const action =
    input.envelope.proposed_actions.find((candidate) =>
      input.action_id
        ? candidate.action_id === input.action_id
        : input.capability_id
          ? candidate.capability_id === input.capability_id
          : true
    ) || input.envelope.proposed_actions[0];
  if (!action) {
    return createHarnessCoreGovernorDecision({
      envelope: input.envelope,
      reply_style: input.reply_style,
      reply_instruction: input.reply_instruction
    });
  }

  const now = input.now || new Date().toISOString();
  const trace = createHarnessCoreTraceRef({
    id: `${input.envelope.turn_id}:${input.tool_name}:authorization`,
    summary: `Governor authorization for ${input.tool_name}.`,
    redaction_class: 'metadata_only'
  });
  const verdict: AuthorizationDecisionV1['verdict'] = action.requires_confirmation ? 'interrupt' : 'allow';
  const authorization: AuthorizationDecisionV1 = {
    schema_version: 'authorization-decision-v1',
    decision_id: safeHarnessCoreId('decision', `${input.envelope.turn_id}:${action.action_id}`),
    created_at: now,
    turn_id: input.envelope.turn_id,
    action_id: action.action_id,
    capability_id: action.capability_id,
    verdict,
    risk_tier: action.risk_tier,
    reasons: input.reasons && input.reasons.length > 0
      ? input.reasons
      : action.requires_confirmation
        ? ['harness_core_authorized', 'explicit_human_confirmation_required']
        : ['harness_core_authorized'],
    evidence: input.envelope.evidence,
    approval: {
      required: action.requires_confirmation,
      status: action.requires_confirmation ? 'requested' : 'not_required'
    },
    restrictions: {
      network_allowed: action.action_type === 'external_api_call' || action.action_type === 'browser_action' || action.action_type === 'computer_action',
      write_allowed: !['read'].includes(action.action_type),
      publish_allowed: action.action_type === 'publish',
      ...(input.restrictions || {})
    },
    trace
  };
  const ledger: ToolCallLedgerV1 = {
    schema_version: 'tool-call-ledger-v1',
    ledger_id: safeHarnessCoreId('ledger', `${input.envelope.turn_id}:${action.action_id}`),
    created_at: now,
    turn_id: input.envelope.turn_id,
    action_id: action.action_id,
    capability_id: action.capability_id,
    tool_name: input.tool_name,
    lifecycle: [
      { stage: 'propose', at: input.envelope.created_at, verdict: 'passed', summary: 'Harness Core proposed the action.' },
      { stage: 'validate', at: now, verdict: 'passed', summary: 'Harness Core validated the authority record.' },
      { stage: 'authorize', at: now, verdict: action.requires_confirmation ? 'pending' : 'passed', summary: 'Governor authorization recorded before execution.' },
      { stage: 'execute', at: now, verdict: 'pending', summary: 'Execution has not started yet.' }
    ],
    authorization,
    arguments: {
      schema_valid: true,
      raw_ref: action.args_ref,
      sanitized_ref: action.args_ref
    },
    result: {
      status: 'not_started',
      summary: 'Tool execution has not started yet.',
      sanitized_output_ref: createHarnessCoreArtifactRef({
        id: `${input.envelope.turn_id}:${action.action_id}:pending-output`,
        kind: 'tool_output',
        path_or_uri: `${input.envelope.surface}://actions/${encodeURIComponent(input.tool_name)}/${encodeURIComponent(input.envelope.turn_id)}/pending`,
        summary: 'Pending tool output reference.',
        redaction_class: 'metadata_only'
      })
    },
    trace
  };

  return createHarnessCoreGovernorDecision({
    envelope: input.envelope,
    authorizations: [authorization],
    tool_ledgers: [ledger],
    reply_style: input.reply_style,
    reply_instruction: input.reply_instruction
  });
}

function executeStageVerdictForHarnessStatus(status: ToolCallLedgerV1['result']['status']): ToolCallLedgerV1['lifecycle'][number]['verdict'] {
  if (status === 'not_started') return 'skipped';
  if (status === 'success' || status === 'partial') return 'passed';
  return 'failed';
}

function assertHarnessCoreExecutionStatusAuthorized(
  authorizationVerdict: AuthorizationDecisionV1['verdict'],
  status: ToolCallLedgerV1['result']['status']
): void {
  if (HARNESS_CORE_EXECUTED_TOOL_STATUSES.has(status) && authorizationVerdict !== 'allow') {
    throw new Error(
      'Tool execution status requires allow authorization; blocked or interrupted actions may only record a not_started ledger.'
    );
  }
}

export function finalizeHarnessCoreToolCallLedger(input: {
  ledger: ToolCallLedgerV1;
  status: ToolCallLedgerV1['result']['status'];
  summary: string;
  output_ref?: HarnessCoreArtifactRef;
  output_path_or_uri?: string;
  error_ref?: HarnessCoreArtifactRef;
  rollback_ref?: HarnessCoreArtifactRef;
  now?: string;
}): ToolCallLedgerV1 {
  assertHarnessCoreExecutionStatusAuthorized(input.ledger.authorization.verdict, input.status);
  const now = input.now || new Date().toISOString();
  const executeStage: ToolCallLedgerV1['lifecycle'][number] = {
    stage: 'execute',
    at: now,
    verdict: executeStageVerdictForHarnessStatus(input.status),
    summary: input.summary
  };
  const lifecycle = [...input.ledger.lifecycle];
  if (lifecycle.length > 0 && lifecycle[lifecycle.length - 1].stage === 'execute') {
    lifecycle[lifecycle.length - 1] = executeStage;
  } else {
    lifecycle.push(executeStage);
  }
  const sanitizedOutputRef = input.output_ref || createHarnessCoreArtifactRef({
    id: `${input.ledger.ledger_id}:${input.status}:output`,
    kind: 'tool_output',
    path_or_uri: input.output_path_or_uri || `${input.ledger.tool_name}://outputs/${input.ledger.ledger_id}/${input.status}`,
    summary: input.summary,
    redaction_class: 'metadata_only'
  });
  return {
    ...input.ledger,
    lifecycle,
    result: {
      status: input.status,
      summary: input.summary,
      sanitized_output_ref: sanitizedOutputRef,
      ...(input.error_ref ? { error_ref: input.error_ref } : {}),
      ...(input.rollback_ref ? { rollback_ref: input.rollback_ref } : {})
    },
    trace: createHarnessCoreTraceRef({
      id: `${input.ledger.ledger_id}:${input.status}:final`,
      summary: `Final ledger for ${input.ledger.tool_name}.`
    })
  };
}

export function createHarnessCoreReadinessScore(input: {
  id: string;
  target_kind: ReadinessScoreV1['target']['kind'];
  target_id: string;
  owner_repo: string;
  categories: Record<HarnessCoreReadinessCategoryName, HarnessCoreCategoryScore>;
  promotion_gates?: Partial<ReadinessScoreV1['promotion_gates']>;
  summary?: string;
}): ReadinessScoreV1 {
  const values = Object.values(input.categories).map((category) => category.score);
  const score = values.length ? Number((values.reduce((sum, item) => sum + item, 0) / values.length).toFixed(4)) : 0;
  const blockers = Object.values(input.categories).some((category) => category.blockers.length > 0);
  const gates = {
    public_ready: false,
    network_absorbable: false,
    telegram_live_proven: false,
    startup_benchmark_proven: false,
    performance_budget_proven: false,
    zero_high_agency_legacy_local_gates: false,
    ...(input.promotion_gates || {})
  };
  const status: ReadinessScoreV1['overall']['status'] =
    gates.public_ready && gates.network_absorbable && gates.performance_budget_proven && score >= 0.95 && !blockers
      ? 'public_ready'
      : score >= 0.85 && gates.telegram_live_proven && gates.startup_benchmark_proven && gates.performance_budget_proven && !blockers
        ? 'release_candidate'
        : score >= 0.7 && gates.zero_high_agency_legacy_local_gates
          ? 'private_ready'
          : 'blocked';
  return {
    schema_version: 'readiness-score-v1',
    score_id: safeHarnessCoreId('readiness', input.id),
    created_at: new Date().toISOString(),
    target: {
      kind: input.target_kind,
      id: input.target_id,
      owner_repo: input.owner_repo
    },
    categories: input.categories,
    promotion_gates: gates,
    overall: {
      score,
      status,
      summary: input.summary || `${input.owner_repo} readiness is ${status}.`
    }
  };
}

export function createHarnessCoreExperienceIndex(input: {
  id: string;
  entries?: ExperienceIndexV1['entries'];
  query_hints?: ExperienceIndexV1['query_hints'];
}): ExperienceIndexV1 {
  return {
    schema_version: 'experience-index-v1',
    index_id: safeHarnessCoreId('experience-index', input.id),
    created_at: new Date().toISOString(),
    entries: input.entries || [],
    query_hints: input.query_hints || [
      {
        name: 'harness evidence',
        description: 'Search generated harness evidence, traces, scores, and change records.',
        glob: 'experience/**/*.json'
      }
    ]
  };
}

export function createHarnessCoreResourceRegistry(input: {
  id: string;
  resources: ResourceRegistryV1['resources'];
}): ResourceRegistryV1 {
  return {
    schema_version: 'resource-registry-v1',
    registry_id: safeHarnessCoreId('resource-registry', input.id),
    created_at: new Date().toISOString(),
    resources: input.resources
  };
}

export function createHarnessCoreEvaluationPack(input: {
  id: string;
  scope: HarnessCoreSurface[];
  cases: EvaluationPackV1['cases'];
  metrics: HarnessCoreMetric[];
  promotion_rules: string[];
  jury?: Partial<EvaluationPackV1['jury']>;
}): EvaluationPackV1 {
  return {
    schema_version: 'evaluation-pack-v1',
    pack_id: safeHarnessCoreId('evaluation-pack', input.id),
    created_at: new Date().toISOString(),
    scope: input.scope,
    cases: input.cases,
    metrics: input.metrics,
    jury: {
      blind: input.jury?.blind ?? true,
      judge_count: input.jury?.judge_count ?? 3,
      rubric_ref:
        input.jury?.rubric_ref ||
        createHarnessCoreArtifactRef({
          id: `${input.id}:rubric`,
          kind: 'rubric',
          path_or_uri: 'eval/rubric.md',
          summary: 'Evaluation rubric reference.'
        })
    },
    promotion_rules: input.promotion_rules
  };
}

export function createHarnessCoreHarnessRun(input: {
  id: string;
  run_type: HarnessRunV1['run_type'];
  surface: HarnessCoreSurface;
  model_refs: string[];
  envelopes?: TurnIntentEnvelopeVNext[];
  tool_ledgers?: ToolCallLedgerV1[];
  artifacts?: HarnessCoreArtifactRef[];
  metrics?: HarnessCoreMetric[];
  status: HarnessRunV1['verdict']['status'];
  summary: string;
  remaining_risks?: string[];
}): HarnessRunV1 {
  return {
    schema_version: 'harness-run-v1',
    run_id: safeHarnessCoreId('harness-run', input.id),
    created_at: new Date().toISOString(),
    run_type: input.run_type,
    surface: input.surface,
    model_refs: input.model_refs,
    envelopes: input.envelopes || [],
    tool_ledgers: input.tool_ledgers || [],
    artifacts: input.artifacts || [],
    metrics: input.metrics || [],
    verdict: {
      status: input.status,
      summary: input.summary,
      ...(input.remaining_risks ? { remaining_risks: input.remaining_risks } : {})
    }
  };
}

export function createTelegramLiveQaEvidencePacket(input: {
  generated_at?: string;
  run_id?: string;
  title?: string;
  catalog: string;
  suite?: string | null;
  include_risky?: boolean;
  required_session_evidence?: Partial<TelegramLiveQaEvidencePacketV1['required_session_evidence']>;
  cases: TelegramLiveQaEvidencePacketV1['cases'];
}): TelegramLiveQaEvidencePacketV1 {
  const generatedAt = input.generated_at || new Date().toISOString();
  const riskCounts: Record<TelegramLiveQaRisk, number> = {
    safe: 0,
    mission: 0,
    writes_files: 0,
    external: 0
  };
  const summary: TelegramLiveQaEvidencePacketV1['summary'] = {
    pass: 0,
    fail: 0,
    blocked: 0,
    needs_retest: 0,
    untested: 0
  };
  for (const entry of input.cases) {
    riskCounts[entry.risk] += 1;
    if (entry.verdict === 'needs-retest') {
      summary.needs_retest += 1;
    } else {
      summary[entry.verdict] += 1;
    }
  }
  const defaultSessionEvidence: TelegramLiveQaEvidencePacketV1['required_session_evidence'] = {
    profile: null,
    tester: null,
    bot_runtime_commit: null,
    harness_core_commit: null,
    spark_os_compile_ref: null,
    spark_live_status_ref: null,
    spark_verify_provenance_ref: null,
    telegram_chat_evidence_ref: null,
    overall_verdict: 'untested',
    follow_up_commits: [],
    pr_links: [],
    remaining_risks: []
  };
  const sessionEvidence = {
    ...defaultSessionEvidence,
    ...(input.required_session_evidence || {}),
    follow_up_commits: input.required_session_evidence?.follow_up_commits || defaultSessionEvidence.follow_up_commits,
    pr_links: input.required_session_evidence?.pr_links || defaultSessionEvidence.pr_links,
    remaining_risks: input.required_session_evidence?.remaining_risks || defaultSessionEvidence.remaining_risks
  };
  return {
    schema_version: 'spark.telegram_live_qa_evidence_packet.v1',
    generated_at: generatedAt,
    run_id: input.run_id || `telegram-live-qa-${generatedAt.replace(/[:.]/g, '-')}`,
    title: input.title || 'Spark Telegram Live QA Evidence Packet',
    catalog: input.catalog,
    selection: {
      suite: input.suite?.trim() || null,
      include_risky: Boolean(input.include_risky),
      case_count: input.cases.length,
      risk_counts: riskCounts
    },
    authority_claim_boundary: [
      'This packet is a live QA evidence container.',
      'It does not prove release readiness until each case has observed replies, side-effect checks, ledger or trace evidence where required, and a human verdict.',
      'It must not be treated as authority to execute high-agency actions.'
    ].join(' '),
    required_session_evidence: sessionEvidence,
    verdict_values: ['pass', 'fail', 'blocked', 'needs-retest', 'untested'],
    cases: input.cases,
    summary
  };
}

const PROTECTED_HARNESS_COMPONENT_TYPES = new Set<HarnessComponentV1['component_type']>([
  'verifier',
  'benchmark',
  'model_config',
  'authority_policy'
]);

const HARNESS_CORE_READINESS_STATUS_RANK: Readonly<Record<ReadinessScoreV1['overall']['status'], number>> = Object.freeze({
  blocked: 0,
  private_ready: 1,
  release_candidate: 2,
  public_ready: 3
});

export function createHarnessCoreChangeManifest(input: {
  id: string;
  target_component: HarnessComponentV1;
  failure_evidence: HarnessCoreEvidenceRef[];
  root_cause_hypothesis: string;
  edit_summary: string;
  predicted_fixes: string[];
  predicted_regression_risks: string[];
  required_tests: string[];
  live_proof_required: boolean;
  rollback_plan: string;
  observed_delta?: HarnessCoreMetric[];
  verdict?: ChangeManifestV1['verdict'];
  human_approval_ref?: HarnessCoreEvidenceRef;
}): ChangeManifestV1 {
  if (PROTECTED_HARNESS_COMPONENT_TYPES.has(input.target_component.component_type) && !input.human_approval_ref) {
    throw new Error('protected Harness Core components require explicit human approval evidence');
  }
  return {
    schema_version: 'change-manifest-v1',
    change_id: safeHarnessCoreId('change', input.id),
    created_at: new Date().toISOString(),
    target_component: input.target_component,
    failure_evidence: input.failure_evidence,
    root_cause_hypothesis: input.root_cause_hypothesis,
    edit_summary: input.edit_summary,
    predicted_fixes: input.predicted_fixes,
    predicted_regression_risks: input.predicted_regression_risks,
    required_tests: input.required_tests,
    live_proof_required: input.live_proof_required,
    ...(input.human_approval_ref ? { human_approval_ref: input.human_approval_ref } : {}),
    rollback_plan: input.rollback_plan,
    observed_delta: input.observed_delta || [],
    verdict: input.verdict || 'draft'
  };
}

export function createHarnessCoreSelfEvolutionRun(input: {
  id: string;
  mode: SelfEvolutionRunV1['mode'];
  surface: HarnessCoreSurface;
  experience_index: ExperienceIndexV1;
  readiness_score: ReadinessScoreV1;
  commands: string[];
  target_components?: HarnessComponentV1[];
  change_manifests?: ChangeManifestV1[];
  evaluation_packs?: EvaluationPackV1[];
  verdict?: SelfEvolutionRunV1['promotion_decision']['verdict'];
  summary?: string;
  roles?: Partial<SelfEvolutionRunV1['roles']>;
  live_surface_required?: boolean;
}): SelfEvolutionRunV1 {
  const verdict = input.verdict || 'not_ready';
  const manifests = input.change_manifests || [];
  const components = input.target_components || [];
  const liveSurfaceRequired = input.live_surface_required ?? false;
  assertHarnessCoreSelfEvolutionPolicy({
    mode: input.mode,
    verdict,
    readiness_score: input.readiness_score,
    target_components: components,
    change_manifests: manifests,
    live_surface_required: liveSurfaceRequired
  });
  return {
    schema_version: 'self-evolution-run-v1',
    evolution_id: safeHarnessCoreId('evolution', input.id),
    created_at: new Date().toISOString(),
    mode: input.mode,
    roles: {
      harness_scientist: input.roles?.harness_scientist || 'spark-harness-core',
      surface_operator: input.roles?.surface_operator || input.surface,
      verifier: input.roles?.verifier || 'spark-harness-core'
    },
    experience_index: input.experience_index,
    target_components: components,
    change_manifests: manifests,
    test_plan: {
      evaluation_packs: input.evaluation_packs || [],
      live_surface_required: liveSurfaceRequired,
      commands: input.commands
    },
    promotion_decision: {
      verdict,
      summary: input.summary || 'Self-evolution run recorded by Spark Harness Core.',
      readiness_score: input.readiness_score
    }
  };
}

function assertHarnessCoreSelfEvolutionPolicy(input: {
  mode: SelfEvolutionRunV1['mode'];
  verdict: SelfEvolutionRunV1['promotion_decision']['verdict'];
  readiness_score: ReadinessScoreV1;
  target_components: HarnessComponentV1[];
  change_manifests: ChangeManifestV1[];
  live_surface_required: boolean;
}): void {
  if (input.mode === 'observe' && input.verdict !== 'not_ready') {
    throw new Error('observe mode cannot promote or roll back changes');
  }
  if (input.verdict === 'promote_private' || input.verdict === 'promote_release_candidate') {
    if (input.change_manifests.length === 0) {
      throw new Error('self-evolution promotion requires at least one accepted change manifest');
    }
    const nonAccepted = input.change_manifests
      .filter((manifest) => manifest.verdict !== 'accepted')
      .map((manifest) => manifest.change_id);
    if (nonAccepted.length > 0) {
      throw new Error(`self-evolution promotion requires accepted change manifests; not accepted: ${nonAccepted.join(', ')}`);
    }
    if (input.live_surface_required || input.change_manifests.some((manifest) => manifest.live_proof_required)) {
      throw new Error('self-evolution promotion cannot proceed while live proof is still required');
    }
    const requiredStatus = input.verdict === 'promote_private' ? 'private_ready' : 'release_candidate';
    const readinessStatus = input.readiness_score.overall.status;
    if (HARNESS_CORE_READINESS_STATUS_RANK[readinessStatus] < HARNESS_CORE_READINESS_STATUS_RANK[requiredStatus]) {
      throw new Error(`self-evolution ${input.verdict} requires readiness status ${requiredStatus} or better; got ${readinessStatus}`);
    }
  }
  if (input.verdict === 'rollback') {
    if (input.mode !== 'rollback') {
      throw new Error('rollback verdict requires rollback mode');
    }
    if (!input.change_manifests.some((manifest) => manifest.verdict === 'rolled_back')) {
      throw new Error('rollback verdict requires at least one rolled_back change manifest');
    }
  }
  const approvedComponentIds = new Set(
    input.change_manifests
      .filter((manifest) => Boolean(manifest.human_approval_ref))
      .map((manifest) => manifest.target_component.component_id)
  );
  for (const component of input.target_components) {
    if (PROTECTED_HARNESS_COMPONENT_TYPES.has(component.component_type) && !approvedComponentIds.has(component.component_id)) {
      throw new Error(`protected self-evolution component ${component.component_id} requires approval evidence`);
    }
  }
}
