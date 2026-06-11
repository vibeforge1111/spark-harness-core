export type HarnessCoreSchemaVersion = 'turn-intent-envelope-vnext';
export type HarnessCoreAuthorizationSchemaVersion = 'authorization-decision-v1';
export type HarnessCoreToolLedgerSchemaVersion = 'tool-call-ledger-v1';
export type HarnessCoreGovernorSchemaVersion = 'governor-decision-v1';
export type HarnessCoreGovernorConsumerVerificationSchemaVersion = 'governor-consumer-verification-v1';
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
        fresh_user_intent_ref: HarnessCoreEvidenceRef | null;
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
export type HarnessCoreGovernorOutcome = 'chat_only' | 'read_only' | 'prepare' | 'execute' | 'interrupt' | 'deny' | 'degrade';
export interface GovernorDecisionSignatureV1 {
    schema_version: 'governor-decision-signature-v1';
    alg: 'hmac-sha256';
    key_id: string;
    nonce: string;
    created_at: string;
    signature: string;
}
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
    signature?: GovernorDecisionSignatureV1;
    trace: HarnessCoreTraceRef;
}
export declare function canonicalHarnessCoreJson(value: unknown): string;
export declare function unsignedHarnessCoreGovernorDecision<T extends Record<string, unknown>>(decision: T): Omit<T, 'signature'>;
export declare function harnessCoreGovernorDecisionSignaturePayload(decision: Record<string, unknown>, signature: Omit<GovernorDecisionSignatureV1, 'signature'>): string;
export declare function signHarnessCoreGovernorDecision<T extends GovernorDecisionV1>(decision: T, input: {
    key: string;
    key_id?: string;
    nonce?: string;
    created_at?: string;
}): T;
export declare function harnessCoreGovernorDecisionSignatureReasonCodes(input: {
    governor_decision?: GovernorDecisionV1 | null;
    key?: string | null;
    expected_key_id?: string | null;
    require_signature?: boolean;
}): string[];
export interface HarnessCoreGovernorConsumerVerification {
    schema_version: HarnessCoreGovernorConsumerVerificationSchemaVersion;
    allowed: boolean;
    reason_codes: string[];
    source_kind: 'governor_decision' | 'missing_governor_decision';
    decision_id: string | null;
    turn_id: string | null;
    outcome: HarnessCoreGovernorOutcome | null;
    expected_capability_id: string | null;
    expected_action_type: HarnessCoreActionType | null;
    tool_name: string | null;
    action_id: string | null;
    capability_id: string | null;
    authorization_decision_id: string | null;
    ledger_id: string | null;
}
export interface HarnessCoreBoundLedgerRow {
    turn_id: string | null;
    action_id: string | null;
    capability_id: string | null;
    authorization_decision_id: string | null;
    ledger_id: string | null;
    tool_name: string | null;
    owner_system: string | null;
    mutation_class: string | null;
    outcome: HarnessCoreGovernorOutcome | null;
    status: ToolCallLedgerV1['result']['status'] | null;
    surface: HarnessCoreSurface | string | null;
    request_id: string | null;
    trace_ref: string | null;
    summary: string | null;
    ledger_json: ToolCallLedgerV1;
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
        performance_budget_proven: boolean;
        governance_rulesets_proven: boolean;
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
        case_type: 'negative_intent' | 'positive_action' | 'mixed_intent' | 'stale_context' | 'pending_state' | 'startup_quality' | 'tool_lifecycle' | 'live_surface' | 'regression' | 'latency_cost';
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
    run_type: 'single_turn' | 'route_matrix' | 'live_surface_qa' | 'startup_benchmark' | 'blind_jury' | 'mission' | 'readiness_scan' | 'self_evolution' | 'release_gate';
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
export type LegacyAuthorityPlaneDisposition = 'removed' | 'quarantined' | 'evidence_adapter' | 'canonical_consumer' | 'release_blocker';
export type LegacyAuthorityPlaneType = 'keyword_detector' | 'regex_router' | 'pending_state_helper' | 'memory_override' | 'mission_helper' | 'machine_origin_policy' | 'local_dispatcher' | 'template_reply' | 'schedule_trigger' | 'publish_hook' | 'tool_launcher' | 'unknown';
export interface LegacyAuthorityRisk {
    can_execute: boolean;
    can_mutate_state: boolean;
    can_route_turns: boolean;
    can_write_memory: boolean;
    can_launch_mission: boolean;
    can_call_network: boolean;
    can_publish: boolean;
    can_schedule: boolean;
}
export interface LegacyAuthorityPlaneV1 {
    schema_version: 'legacy-authority-plane-v1';
    plane_id: string;
    created_at: string;
    owner_repo: string;
    surface: HarnessCoreSurface;
    plane_type: LegacyAuthorityPlaneType;
    source_ref: HarnessCoreArtifactRef;
    authority_risk: LegacyAuthorityRisk;
    disposition: LegacyAuthorityPlaneDisposition;
    harness_binding: {
        governor_required: boolean;
        evidence_only: boolean;
        consumer_of_governor: boolean;
        ledger_required: boolean;
        notes?: string;
    };
    evidence: HarnessCoreEvidenceRef[];
    blockers: string[];
    trace: HarnessCoreTraceRef;
}
export interface LegacyAuthorityInventoryV1 {
    schema_version: 'legacy-authority-inventory-v1';
    inventory_id: string;
    created_at: string;
    scope: {
        owner_repo: string;
        surfaces: HarnessCoreSurface[];
    };
    planes: LegacyAuthorityPlaneV1[];
    summary: {
        plane_count: number;
        removed_count: number;
        quarantined_count: number;
        evidence_adapter_count: number;
        canonical_consumer_count: number;
        release_blocker_count: number;
        high_agency_risk_count: number;
    };
    release_gate: {
        zero_high_agency_legacy_local_gates: boolean;
        ready_for_readiness_promotion: boolean;
        blockers: string[];
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
    component_type: 'system_prompt' | 'tool_description' | 'tool_implementation' | 'middleware' | 'skill' | 'subagent_config' | 'long_term_memory' | 'authority_policy' | 'surface_spec' | 'hook' | 'verifier' | 'benchmark' | 'model_config' | 'resource_registry' | 'experience_index' | 'kernel_code';
    owner_repo: string;
    path: string;
    summary: string;
    editable_by_evolution: boolean;
    authority_scope: HarnessCoreSurface[];
    dependencies: string[];
    tests: string[];
    rollback_ref?: HarnessCoreArtifactRef;
}
export type HarnessComponentType = HarnessComponentV1['component_type'];
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
export interface HarnessCoreChangeManifestRunnerDecision {
    verdict: SelfEvolutionRunV1['promotion_decision']['verdict'];
    summary: string;
    reasons: string[];
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
export declare function createHarnessCoreGovernorDecision(input: {
    envelope: TurnIntentEnvelopeVNext;
    authorizations?: AuthorizationDecisionV1[];
    tool_ledgers?: ToolCallLedgerV1[];
    reply_style?: GovernorDecisionV1['reply_contract']['style'];
    reply_instruction?: string;
}): GovernorDecisionV1;
export declare function boundHarnessCoreLedgerRow(input: {
    ledger: ToolCallLedgerV1;
    verdict: HarnessCoreGovernorConsumerVerification;
    owner_system?: string | null;
    mutation_class?: string | null;
    surface?: HarnessCoreSurface | string | null;
    request_id?: string | null;
    trace_ref?: string | null;
}): HarnessCoreBoundLedgerRow;
export declare const boundLedgerRow: typeof boundHarnessCoreLedgerRow;
export declare function verifyHarnessCoreGovernorExecutionAuthority(input: {
    governor_decision?: GovernorDecisionV1 | null;
    expected_capability_id: string;
    expected_action_type?: HarnessCoreActionType;
    tool_name?: string;
    action_id?: string;
    allow_read_only?: boolean;
    require_pre_execution_ledger?: boolean;
    governor_hmac_key?: string | null;
    governor_hmac_key_id?: string | null;
    require_signature?: boolean;
    now?: string | Date | null;
}): HarnessCoreGovernorConsumerVerification;
export declare function verifyHarnessCoreGovernorToolAuthority(input: {
    governor_decision?: GovernorDecisionV1 | null;
    tool_name: string;
    owner_system: string;
    action_type: HarnessCoreActionType;
    action_id?: string;
    allow_read_only?: boolean;
    require_pre_execution_ledger?: boolean;
    governor_hmac_key?: string | null;
    governor_hmac_key_id?: string | null;
    require_signature?: boolean;
    now?: string | Date | null;
}): HarnessCoreGovernorConsumerVerification;
export declare function createHarnessCoreAuthorizedGovernorDecision(input: {
    envelope: TurnIntentEnvelopeVNext;
    tool_name: string;
    action_id?: string;
    capability_id?: string;
    reasons?: string[];
    restrictions?: Partial<AuthorizationDecisionV1['restrictions']>;
    reply_style?: GovernorDecisionV1['reply_contract']['style'];
    reply_instruction?: string;
    now?: string;
}): GovernorDecisionV1;
export declare function finalizeHarnessCoreToolCallLedger(input: {
    ledger: ToolCallLedgerV1;
    status: ToolCallLedgerV1['result']['status'];
    summary: string;
    output_ref?: HarnessCoreArtifactRef;
    output_path_or_uri?: string;
    error_ref?: HarnessCoreArtifactRef;
    rollback_ref?: HarnessCoreArtifactRef;
    now?: string;
}): ToolCallLedgerV1;
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
export declare function createHarnessCoreEvaluationPack(input: {
    id: string;
    scope: HarnessCoreSurface[];
    cases: EvaluationPackV1['cases'];
    metrics: HarnessCoreMetric[];
    promotion_rules: string[];
    jury?: Partial<EvaluationPackV1['jury']>;
}): EvaluationPackV1;
export declare function createHarnessCoreHarnessRun(input: {
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
}): HarnessRunV1;
export declare function createHarnessCoreLegacyAuthorityPlane(input: {
    id: string;
    owner_repo: string;
    surface: HarnessCoreSurface;
    plane_type: LegacyAuthorityPlaneType;
    source_path: string;
    summary: string;
    authority_risk: Partial<LegacyAuthorityRisk>;
    disposition: LegacyAuthorityPlaneDisposition;
    evidence: HarnessCoreEvidenceRef[];
    governor_required?: boolean;
    evidence_only?: boolean;
    consumer_of_governor?: boolean;
    ledger_required?: boolean;
    blockers?: string[];
}): LegacyAuthorityPlaneV1;
export declare function createHarnessCoreLegacyAuthorityInventory(input: {
    id: string;
    owner_repo: string;
    surfaces: HarnessCoreSurface[];
    planes: LegacyAuthorityPlaneV1[];
}): LegacyAuthorityInventoryV1;
export declare function createTelegramLiveQaEvidencePacket(input: {
    generated_at?: string;
    run_id?: string;
    title?: string;
    catalog: string;
    suite?: string | null;
    include_risky?: boolean;
    required_session_evidence?: Partial<TelegramLiveQaEvidencePacketV1['required_session_evidence']>;
    cases: TelegramLiveQaEvidencePacketV1['cases'];
}): TelegramLiveQaEvidencePacketV1;
export declare const PROTECTED_HARNESS_COMPONENT_TYPES: ReadonlySet<HarnessComponentType>;
export declare function createHarnessCoreChangeManifest(input: {
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
}): ChangeManifestV1;
export declare function createHarnessCoreSelfEvolutionRun(input: {
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
}): SelfEvolutionRunV1;
export declare function createHarnessCoreChangeManifestRunner(input: {
    id: string;
    mode: SelfEvolutionRunV1['mode'];
    surface: HarnessCoreSurface;
    experience_index: ExperienceIndexV1;
    readiness_score: ReadinessScoreV1;
    commands: string[];
    target_components?: HarnessComponentV1[];
    change_manifests?: ChangeManifestV1[];
    evaluation_packs?: EvaluationPackV1[];
    requested_verdict?: SelfEvolutionRunV1['promotion_decision']['verdict'];
    roles?: Partial<SelfEvolutionRunV1['roles']>;
    live_surface_required?: boolean;
}): SelfEvolutionRunV1;
export declare function evaluateHarnessCoreChangeManifestRunner(input: {
    mode: SelfEvolutionRunV1['mode'];
    readiness_score: ReadinessScoreV1;
    target_components: HarnessComponentV1[];
    change_manifests: ChangeManifestV1[];
    requested_verdict?: SelfEvolutionRunV1['promotion_decision']['verdict'];
    live_surface_required: boolean;
}): HarnessCoreChangeManifestRunnerDecision;
export declare function isHarnessCoreProtectedComponentType(componentType: HarnessComponentType): boolean;
export declare function assertHarnessCoreComponentEditablePolicy(component: HarnessComponentV1): void;
