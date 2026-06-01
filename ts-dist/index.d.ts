export type HarnessCoreSchemaVersion = 'turn-intent-envelope-vnext';
export type HarnessCoreAuthorizationSchemaVersion = 'authorization-decision-v1';
export type HarnessCoreToolLedgerSchemaVersion = 'tool-call-ledger-v1';
export type HarnessCoreSurface = 'telegram' | 'cli' | 'builder' | 'spawner' | 'memory' | 'startup_operator' | 'recursive_swarm' | 'voice' | 'domain_chip' | 'browser' | 'computer_use' | 'api' | 'test_harness' | 'future_surface';
export type HarnessCoreMoveType = 'chat_explain' | 'chat_plan' | 'chat_compare' | 'chat_score' | 'chat_draft_text' | 'read_current_state' | 'prepare_action' | 'confirm_action' | 'execute_action';
export type HarnessCoreRiskTier = 'none' | 'read' | 'low' | 'medium' | 'high' | 'critical';
export type HarnessCoreAuthorityState = 'none' | 'chat_only' | 'read_only' | 'prepare_allowed' | 'confirmation_required' | 'executable' | 'blocked';
export type HarnessCoreRedactionClass = 'public' | 'internal' | 'private' | 'secret' | 'metadata_only' | 'redacted';
export type HarnessCoreActionType = 'read' | 'write_memory' | 'edit_file' | 'run_command' | 'launch_mission' | 'open_pr' | 'publish' | 'deploy' | 'schedule' | 'create_domain_chip' | 'send_message' | 'external_api_call' | 'browser_action' | 'computer_action';
export type HarnessCoreEvidenceKind = 'fresh_user_intent' | 'quoted_language' | 'meta_language' | 'negative_intent' | 'positive_command' | 'memory' | 'pending_state' | 'route_candidate' | 'tool_result' | 'runtime_state' | 'test_result' | 'human_confirmation' | 'surface_signal' | 'policy';
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
        stage: 'propose' | 'validate' | 'authorize' | 'approve' | 'interrupt' | 'execute' | 'sanitize' | 'store' | 'summarize' | 'continue' | 'rollback' | 'fail';
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
export type HarnessCoreReadinessCategoryName = 'execution' | 'tools' | 'context' | 'lifecycle' | 'observability' | 'verification' | 'governance';
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
        entry_type: 'raw_trace' | 'cleaned_trace' | 'trajectory_report' | 'score' | 'route_decision' | 'tool_ledger' | 'screenshot' | 'diff' | 'test_result' | 'live_reply' | 'failure_report' | 'success_pattern';
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
        resource_type: 'prompt' | 'agent' | 'subagent' | 'tool' | 'environment' | 'memory_store' | 'surface_adapter' | 'harness_spec' | 'eval_pack' | 'startup_policy' | 'surface_rule' | 'model_profile' | 'hook';
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
export type HarnessCoreActionMutationClass = 'none' | 'read_only' | 'writes_memory' | 'writes_files' | 'launches_mission' | 'controls_mission' | 'creates_schedule' | 'deletes_schedule' | 'creates_chip' | 'publishes' | 'external_network';
export declare const HARNESS_CORE_RISK_ORDER: Readonly<Record<HarnessCoreRiskTier, number>>;
export declare function safeHarnessCoreId(prefix: string, raw: string): string;
export declare function createHarnessCoreTraceRef(input: {
    id: string;
    summary: string;
    redaction_class?: HarnessCoreRedactionClass;
    href?: string;
}): HarnessCoreTraceRef;
export declare function createHarnessCoreArtifactRef(input: {
    id: string;
    kind: string;
    path_or_uri: string;
    summary: string;
    sha256?: string;
    redaction_class?: HarnessCoreRedactionClass;
}): HarnessCoreArtifactRef;
export declare function createHarnessCoreEvidenceRef(input: {
    id: string;
    kind: HarnessCoreEvidenceKind;
    source: string;
    summary: string;
    confidence: number;
    trace_refs?: HarnessCoreTraceRef[];
}): HarnessCoreEvidenceRef;
export declare function actionTypeForHarnessMutation(mutationClass: HarnessCoreActionMutationClass, publishes?: boolean): HarnessCoreActionType;
export declare function riskTierForHarnessMutation(input: {
    mutationClass: HarnessCoreActionMutationClass;
    publishes?: boolean;
    externalNetwork?: boolean;
}): HarnessCoreRiskTier;
export declare function createHarnessCoreActionEnvelopeVNext(input: {
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
}): TurnIntentEnvelopeVNext;
export declare function createHarnessCoreReadinessScore(input: {
    id: string;
    target_kind: ReadinessScoreV1['target']['kind'];
    target_id: string;
    owner_repo: string;
    categories: Record<HarnessCoreReadinessCategoryName, HarnessCoreCategoryScore>;
    promotion_gates?: Partial<ReadinessScoreV1['promotion_gates']>;
    summary?: string;
}): ReadinessScoreV1;
export declare function createHarnessCoreExperienceIndex(input: {
    id: string;
    entries?: ExperienceIndexV1['entries'];
    query_hints?: ExperienceIndexV1['query_hints'];
}): ExperienceIndexV1;
export declare function createHarnessCoreResourceRegistry(input: {
    id: string;
    resources: ResourceRegistryV1['resources'];
}): ResourceRegistryV1;
