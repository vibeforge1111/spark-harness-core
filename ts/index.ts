export type HarnessCoreSchemaVersion = 'turn-intent-envelope-vnext';
export type HarnessCoreAuthorizationSchemaVersion = 'authorization-decision-v1';
export type HarnessCoreToolLedgerSchemaVersion = 'tool-call-ledger-v1';

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
    zero_high_agency_legacy_local_gates: false,
    ...(input.promotion_gates || {})
  };
  const status: ReadinessScoreV1['overall']['status'] =
    gates.public_ready && gates.network_absorbable && score >= 0.95 && !blockers
      ? 'public_ready'
      : score >= 0.85 && gates.telegram_live_proven && gates.startup_benchmark_proven && !blockers
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

const PROTECTED_HARNESS_COMPONENT_TYPES = new Set<HarnessComponentV1['component_type']>([
  'verifier',
  'benchmark',
  'model_config',
  'authority_policy'
]);

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
