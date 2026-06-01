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
