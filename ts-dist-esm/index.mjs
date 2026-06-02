export const HARNESS_CORE_RISK_ORDER = Object.freeze({
    none: 0,
    read: 1,
    low: 2,
    medium: 3,
    high: 4,
    critical: 5
});
const HARNESS_CORE_EXECUTED_TOOL_STATUSES = new Set([
    'success',
    'failure',
    'partial',
    'rolled_back'
]);
export function safeHarnessCoreId(prefix, raw) {
    const normalized = raw.toLowerCase().replace(/[^a-z0-9_.:-]+/g, '-').replace(/^-+|-+$/g, '');
    const suffix = normalized || Math.random().toString(16).slice(2, 14);
    const id = suffix.startsWith(`${prefix}:`) || suffix.startsWith(`${prefix}_`) ? suffix : `${prefix}:${suffix}`;
    return id.slice(0, 128);
}
export function createHarnessCoreTraceRef(input) {
    return {
        id: safeHarnessCoreId('trace', input.id),
        ...(input.href ? { href: input.href } : {}),
        redaction_class: input.redaction_class || 'metadata_only',
        summary: input.summary
    };
}
export function createHarnessCoreArtifactRef(input) {
    return {
        id: safeHarnessCoreId('artifact', input.id),
        kind: input.kind,
        path_or_uri: input.path_or_uri,
        ...(input.sha256 ? { sha256: input.sha256 } : {}),
        redaction_class: input.redaction_class || 'metadata_only',
        summary: input.summary
    };
}
export function createHarnessCoreEvidenceRef(input) {
    return {
        id: safeHarnessCoreId('evidence', input.id),
        kind: input.kind,
        source: input.source,
        summary: input.summary,
        confidence: input.confidence,
        trace_refs: input.trace_refs || []
    };
}
export function actionTypeForHarnessMutation(mutationClass, publishes = false) {
    if (publishes || mutationClass === 'publishes')
        return 'publish';
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
export function riskTierForHarnessMutation(input) {
    if (input.publishes || input.mutationClass === 'publishes')
        return 'high';
    if (input.externalNetwork || input.mutationClass === 'external_network')
        return 'medium';
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
export function createHarnessCoreActionEnvelopeVNext(input) {
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
    const requiresConfirmation = input.requiresHumanConfirmation === true || HARNESS_CORE_RISK_ORDER[riskTier] >= HARNESS_CORE_RISK_ORDER.high;
    const turnId = safeHarnessCoreId('turn', `${input.surface}:${input.source}:${requestId}`);
    const trace = createHarnessCoreTraceRef({
        id: `${input.surface}:${input.source}:${requestId}`,
        summary: input.reason,
        redaction_class: 'metadata_only'
    });
    const actionId = safeHarnessCoreId('action', `${turnId}:${input.toolName}`);
    const target = input.target?.trim() || input.toolName;
    const action = {
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
    const selectedMove = requiresConfirmation ? 'confirm_action' : actionType === 'read' ? 'read_current_state' : 'execute_action';
    const authorityState = selectedMove === 'confirm_action' ? 'confirmation_required' : selectedMove === 'read_current_state' ? 'read_only' : 'executable';
    const evidenceKind = actorKind === 'human' ? 'fresh_user_intent' : 'surface_signal';
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
function governorOutcomeFor(input) {
    const { envelope, authorizations } = input;
    const state = envelope.action_authority.state;
    const verdicts = new Set(authorizations.map((authorization) => authorization.verdict));
    if (state === 'executable' && verdicts.has('allow'))
        return 'execute';
    if (state === 'confirmation_required' || verdicts.has('interrupt'))
        return 'interrupt';
    if (state === 'read_only')
        return 'read_only';
    if (state === 'prepare_allowed')
        return 'prepare';
    if (state === 'blocked' || verdicts.has('deny'))
        return 'deny';
    if (envelope.selected_move.startsWith('chat_') && envelope.proposed_actions.length === 0)
        return 'chat_only';
    return 'degrade';
}
function defaultGovernorReplyStyle(outcome) {
    return outcome === 'degrade' ? 'compact_status' : 'human_conversational';
}
function defaultGovernorReplyInstruction(outcome) {
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
function governorReasonsFor(input) {
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
            if (!reasons.includes(reason))
                reasons.push(reason);
        }
    }
    if (input.envelope.action_authority.requires_human_confirmation) {
        reasons.push('human_confirmation_required_by_envelope');
    }
    return reasons;
}
export function createHarnessCoreGovernorDecision(input) {
    const authorizations = input.authorizations || [];
    const toolLedgers = input.tool_ledgers || [];
    const outcome = governorOutcomeFor({ envelope: input.envelope, authorizations });
    const authorizedActionCount = authorizations.filter((authorization) => authorization.verdict === 'allow').length;
    const requiresHumanConfirmation = input.envelope.action_authority.requires_human_confirmation ||
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
export function createHarnessCoreAuthorizedGovernorDecision(input) {
    const action = input.envelope.proposed_actions.find((candidate) => input.action_id
        ? candidate.action_id === input.action_id
        : input.capability_id
            ? candidate.capability_id === input.capability_id
            : true) || input.envelope.proposed_actions[0];
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
    const verdict = action.requires_confirmation ? 'interrupt' : 'allow';
    const authorization = {
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
    const ledger = {
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
function executeStageVerdictForHarnessStatus(status) {
    if (status === 'not_started')
        return 'skipped';
    if (status === 'success' || status === 'partial')
        return 'passed';
    return 'failed';
}
function assertHarnessCoreExecutionStatusAuthorized(authorizationVerdict, status) {
    if (HARNESS_CORE_EXECUTED_TOOL_STATUSES.has(status) && authorizationVerdict !== 'allow') {
        throw new Error('Tool execution status requires allow authorization; blocked or interrupted actions may only record a not_started ledger.');
    }
}
export function finalizeHarnessCoreToolCallLedger(input) {
    assertHarnessCoreExecutionStatusAuthorized(input.ledger.authorization.verdict, input.status);
    const now = input.now || new Date().toISOString();
    const executeStage = {
        stage: 'execute',
        at: now,
        verdict: executeStageVerdictForHarnessStatus(input.status),
        summary: input.summary
    };
    const lifecycle = [...input.ledger.lifecycle];
    if (lifecycle.length > 0 && lifecycle[lifecycle.length - 1].stage === 'execute') {
        lifecycle[lifecycle.length - 1] = executeStage;
    }
    else {
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
export function createHarnessCoreReadinessScore(input) {
    const values = Object.values(input.categories).map((category) => category.score);
    const score = values.length ? Number((values.reduce((sum, item) => sum + item, 0) / values.length).toFixed(4)) : 0;
    const blockers = Object.values(input.categories).some((category) => category.blockers.length > 0);
    const gates = {
        public_ready: false,
        network_absorbable: false,
        telegram_live_proven: false,
        startup_benchmark_proven: false,
        performance_budget_proven: false,
        governance_rulesets_proven: false,
        zero_high_agency_legacy_local_gates: false,
        ...(input.promotion_gates || {})
    };
    const status = gates.public_ready && gates.network_absorbable && gates.performance_budget_proven && gates.governance_rulesets_proven && score >= 0.95 && !blockers
        ? 'public_ready'
        : score >= 0.85 && gates.telegram_live_proven && gates.startup_benchmark_proven && gates.performance_budget_proven && gates.governance_rulesets_proven && !blockers
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
export function createHarnessCoreExperienceIndex(input) {
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
export function createHarnessCoreResourceRegistry(input) {
    return {
        schema_version: 'resource-registry-v1',
        registry_id: safeHarnessCoreId('resource-registry', input.id),
        created_at: new Date().toISOString(),
        resources: input.resources
    };
}
export function createHarnessCoreEvaluationPack(input) {
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
            rubric_ref: input.jury?.rubric_ref ||
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
export function createHarnessCoreHarnessRun(input) {
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
export function createTelegramLiveQaEvidencePacket(input) {
    const generatedAt = input.generated_at || new Date().toISOString();
    const riskCounts = {
        safe: 0,
        mission: 0,
        writes_files: 0,
        external: 0
    };
    const summary = {
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
        }
        else {
            summary[entry.verdict] += 1;
        }
    }
    const defaultSessionEvidence = {
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
const PROTECTED_HARNESS_COMPONENT_TYPES = new Set([
    'verifier',
    'benchmark',
    'model_config',
    'authority_policy'
]);
const HARNESS_CORE_READINESS_STATUS_RANK = Object.freeze({
    blocked: 0,
    private_ready: 1,
    release_candidate: 2,
    public_ready: 3
});
export function createHarnessCoreChangeManifest(input) {
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
export function createHarnessCoreSelfEvolutionRun(input) {
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
function assertHarnessCoreSelfEvolutionPolicy(input) {
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
    const approvedComponentIds = new Set(input.change_manifests
        .filter((manifest) => Boolean(manifest.human_approval_ref))
        .map((manifest) => manifest.target_component.component_id));
    for (const component of input.target_components) {
        if (PROTECTED_HARNESS_COMPONENT_TYPES.has(component.component_type) && !approvedComponentIds.has(component.component_id)) {
            throw new Error(`protected self-evolution component ${component.component_id} requires approval evidence`);
        }
    }
}
