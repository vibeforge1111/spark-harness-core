"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.PROTECTED_HARNESS_COMPONENT_TYPES = exports.boundLedgerRow = exports.HARNESS_CORE_RISK_ORDER = exports.HARNESS_CORE_MIN_WIRE_CONTRACT_VERSION = exports.HARNESS_CORE_WIRE_CONTRACT_VERSION = void 0;
exports.canonicalHarnessCoreJson = canonicalHarnessCoreJson;
exports.unsignedHarnessCoreGovernorDecision = unsignedHarnessCoreGovernorDecision;
exports.harnessCoreGovernorDecisionSignaturePayload = harnessCoreGovernorDecisionSignaturePayload;
exports.signHarnessCoreGovernorDecision = signHarnessCoreGovernorDecision;
exports.negotiateHarnessCoreWireContract = negotiateHarnessCoreWireContract;
exports.harnessCoreGovernorDecisionSignatureReasonCodes = harnessCoreGovernorDecisionSignatureReasonCodes;
exports.safeHarnessCoreId = safeHarnessCoreId;
exports.createHarnessCoreTraceRef = createHarnessCoreTraceRef;
exports.createHarnessCoreArtifactRef = createHarnessCoreArtifactRef;
exports.createHarnessCoreEvidenceRef = createHarnessCoreEvidenceRef;
exports.actionTypeForHarnessMutation = actionTypeForHarnessMutation;
exports.riskTierForHarnessMutation = riskTierForHarnessMutation;
exports.createHarnessCoreActionEnvelopeVNext = createHarnessCoreActionEnvelopeVNext;
exports.createHarnessCoreGovernorDecision = createHarnessCoreGovernorDecision;
exports.boundHarnessCoreLedgerRow = boundHarnessCoreLedgerRow;
exports.verifyHarnessCoreGovernorExecutionAuthority = verifyHarnessCoreGovernorExecutionAuthority;
exports.verifyHarnessCoreGovernorToolAuthority = verifyHarnessCoreGovernorToolAuthority;
exports.createHarnessCoreAuthorizedGovernorDecision = createHarnessCoreAuthorizedGovernorDecision;
exports.finalizeHarnessCoreToolCallLedger = finalizeHarnessCoreToolCallLedger;
exports.withGovernedTurn = withGovernedTurn;
exports.repairHarnessCoreStrandedToolCallLedger = repairHarnessCoreStrandedToolCallLedger;
exports.repairHarnessCoreStrandedToolCallLedgers = repairHarnessCoreStrandedToolCallLedgers;
exports.createHarnessCoreReadinessScore = createHarnessCoreReadinessScore;
exports.createHarnessCoreExperienceIndex = createHarnessCoreExperienceIndex;
exports.createHarnessCoreResourceRegistry = createHarnessCoreResourceRegistry;
exports.createHarnessCoreEvaluationPack = createHarnessCoreEvaluationPack;
exports.createHarnessCoreHarnessRun = createHarnessCoreHarnessRun;
exports.createHarnessCoreLegacyAuthorityPlane = createHarnessCoreLegacyAuthorityPlane;
exports.createHarnessCoreLegacyAuthorityInventory = createHarnessCoreLegacyAuthorityInventory;
exports.createTelegramLiveQaEvidencePacket = createTelegramLiveQaEvidencePacket;
exports.createHarnessCoreChangeManifest = createHarnessCoreChangeManifest;
exports.createHarnessCoreSelfEvolutionRun = createHarnessCoreSelfEvolutionRun;
exports.createHarnessCoreChangeManifestRunner = createHarnessCoreChangeManifestRunner;
exports.evaluateHarnessCoreChangeManifestRunner = evaluateHarnessCoreChangeManifestRunner;
exports.isHarnessCoreProtectedComponentType = isHarnessCoreProtectedComponentType;
exports.assertHarnessCoreComponentEditablePolicy = assertHarnessCoreComponentEditablePolicy;
const node_crypto_1 = require("node:crypto");
const DEFAULT_AUTHORIZATION_TTL_SECONDS = 600;
exports.HARNESS_CORE_WIRE_CONTRACT_VERSION = 1;
exports.HARNESS_CORE_MIN_WIRE_CONTRACT_VERSION = 1;
function canonicalHarnessCoreJson(value) {
    if (value === undefined)
        return 'null';
    if (typeof value === 'number' && !Number.isFinite(value))
        throw new Error('canonical JSON numbers must be finite');
    if (value === null || typeof value !== 'object')
        return JSON.stringify(value) ?? 'null';
    if (Array.isArray(value))
        return `[${value.map((item) => canonicalHarnessCoreJson(item)).join(',')}]`;
    const entries = Object.entries(value)
        .filter(([, entryValue]) => entryValue !== undefined)
        .sort(([left], [right]) => compareUtf16Strings(left, right));
    return `{${entries
        .map(([key, entryValue]) => `${JSON.stringify(key)}:${canonicalHarnessCoreJson(entryValue)}`)
        .join(',')}}`;
}
function compareUtf16Strings(left, right) {
    const length = Math.min(left.length, right.length);
    for (let index = 0; index < length; index += 1) {
        const diff = left.charCodeAt(index) - right.charCodeAt(index);
        if (diff !== 0)
            return diff;
    }
    return left.length - right.length;
}
function unsignedHarnessCoreGovernorDecision(decision) {
    const { signature: _signature, ...unsigned } = decision;
    return unsigned;
}
function harnessCoreGovernorDecisionSignaturePayload(decision, signature) {
    return canonicalHarnessCoreJson({
        decision: unsignedHarnessCoreGovernorDecision(decision),
        signature
    });
}
function signHarnessCoreGovernorDecision(decision, input) {
    const key = (input.key || '').trim();
    if (!key)
        throw new Error('key is required');
    const signature = {
        schema_version: 'governor-decision-signature-v1',
        alg: 'hmac-sha256',
        key_id: (input.key_id || '').trim() || 'local',
        nonce: input.nonce || (0, node_crypto_1.randomUUID)(),
        created_at: input.created_at || new Date().toISOString()
    };
    return {
        ...decision,
        signature: {
            ...signature,
            signature: hmacSha256Hex(harnessCoreGovernorDecisionSignaturePayload(decision, signature), key)
        }
    };
}
function negotiateHarnessCoreWireContract(input) {
    const consumerVersion = input.consumer_version ?? exports.HARNESS_CORE_WIRE_CONTRACT_VERSION;
    const producerMin = input.producer_min_version ?? Math.max(1, input.producer_version - 1);
    const consumerMin = input.consumer_min_version ?? Math.max(1, consumerVersion - 1);
    if (input.producer_version < producerMin || consumerVersion < consumerMin) {
        return { allowed: false, agreed_version: null, reason_codes: ['wire_contract_invalid_range'] };
    }
    const agreedVersion = Math.min(input.producer_version, consumerVersion);
    if (agreedVersion < Math.max(producerMin, consumerMin)) {
        return { allowed: false, agreed_version: null, reason_codes: ['wire_contract_no_overlap'] };
    }
    return { allowed: true, agreed_version: agreedVersion, reason_codes: [] };
}
function harnessCoreSimulationMarker(reason) {
    return {
        dry_run: true,
        execution_skipped: true,
        reason
    };
}
function simulatedHarnessCoreGovernorDecision(decision, reason) {
    if (decision.signature) {
        throw new Error('dry-run mode cannot retrofit a signed governor decision');
    }
    const marker = harnessCoreSimulationMarker(reason);
    const simulated = JSON.parse(JSON.stringify(decision));
    simulated.simulation = marker;
    for (const authorization of simulated.authorizations || []) {
        authorization.simulation = marker;
    }
    for (const ledger of simulated.tool_ledgers || []) {
        ledger.simulation = marker;
        ledger.authorization.simulation = marker;
    }
    return simulated;
}
function harnessCoreGovernorDecisionSignatureReasonCodes(input) {
    const key = (input.key || '').trim();
    const signatureRequired = Boolean(input.require_signature || key);
    if (!signatureRequired)
        return [];
    if (!key)
        return ['governor_signature_key_missing'];
    const decision = input.governor_decision || null;
    if (!decision)
        return ['missing_governor_decision'];
    const signature = decision.signature || null;
    if (!signature)
        return ['governor_signature_missing'];
    const reasonCodes = [];
    if (signature.schema_version !== 'governor-decision-signature-v1')
        reasonCodes.push('governor_signature_schema_invalid');
    if (signature.alg !== 'hmac-sha256')
        reasonCodes.push('governor_signature_alg_invalid');
    if (input.expected_key_id && signature.key_id !== input.expected_key_id)
        reasonCodes.push('governor_signature_key_id_mismatch');
    if (!/^[0-9a-f]{64}$/.test(signature.signature || ''))
        reasonCodes.push('governor_signature_invalid');
    if (reasonCodes.length > 0)
        return dedupeStrings(reasonCodes);
    const expected = hmacSha256Hex(harnessCoreGovernorDecisionSignaturePayload(decision, {
        schema_version: signature.schema_version,
        alg: signature.alg,
        key_id: signature.key_id,
        nonce: signature.nonce,
        created_at: signature.created_at
    }), key);
    if (!constantTimeEqualHex(signature.signature, expected))
        reasonCodes.push('governor_signature_invalid');
    return dedupeStrings(reasonCodes);
}
function hmacSha256Hex(payload, key) {
    return (0, node_crypto_1.createHmac)('sha256', key).update(payload, 'utf8').digest('hex');
}
function constantTimeEqualHex(left, right) {
    if (left.length !== right.length)
        return false;
    let diff = 0;
    for (let index = 0; index < left.length; index += 1) {
        diff |= left.charCodeAt(index) ^ right.charCodeAt(index);
    }
    return diff === 0;
}
function dedupeStrings(values) {
    const seen = new Set();
    const deduped = [];
    for (const value of values) {
        if (seen.has(value))
            continue;
        seen.add(value);
        deduped.push(value);
    }
    return deduped;
}
exports.HARNESS_CORE_RISK_ORDER = Object.freeze({
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
const HARNESS_CORE_FRESH_USER_INTENT_REQUIRED_MOVES = new Set([
    'read_current_state',
    'confirm_action',
    'execute_action'
]);
function safeHarnessCoreId(prefix, raw) {
    const normalized = raw.toLowerCase().replace(/[^a-z0-9_.:-]+/g, '-').replace(/^-+|-+$/g, '');
    const suffix = normalized || Math.random().toString(16).slice(2, 14);
    const id = suffix.startsWith(`${prefix}:`) || suffix.startsWith(`${prefix}_`) ? suffix : `${prefix}:${suffix}`;
    return id.slice(0, 128);
}
function createHarnessCoreTraceRef(input) {
    return {
        id: safeHarnessCoreId('trace', input.id),
        ...(input.href ? { href: input.href } : {}),
        redaction_class: input.redaction_class || 'metadata_only',
        summary: input.summary
    };
}
function createHarnessCoreArtifactRef(input) {
    return {
        id: safeHarnessCoreId('artifact', input.id),
        kind: input.kind,
        path_or_uri: input.path_or_uri,
        ...(input.sha256 ? { sha256: input.sha256 } : {}),
        redaction_class: input.redaction_class || 'metadata_only',
        summary: input.summary
    };
}
function createHarnessCoreEvidenceRef(input) {
    return {
        id: safeHarnessCoreId('evidence', input.id),
        kind: input.kind,
        source: input.source,
        summary: input.summary,
        confidence: input.confidence,
        trace_refs: input.trace_refs || []
    };
}
function freshUserIntentAuthorityReasonCodes(envelope) {
    if (!HARNESS_CORE_FRESH_USER_INTENT_REQUIRED_MOVES.has(envelope.selected_move))
        return [];
    const reasons = [];
    if (envelope.actor.kind !== 'human')
        reasons.push('fresh_user_intent_actor_not_human');
    if (!envelope.freshness.fresh_user_intent_present)
        reasons.push('fresh_user_intent_missing');
    if (envelope.freshness.stale_state_used_as_authority)
        reasons.push('stale_state_used_as_authority');
    if (envelope.freshness.memory_used_as_instruction)
        reasons.push('memory_used_as_instruction');
    if (envelope.freshness.pending_state_used_as_authority)
        reasons.push('pending_state_used_as_authority');
    const freshRef = envelope.freshness.fresh_user_intent_ref;
    if (!freshRef) {
        reasons.push('fresh_user_intent_ref_missing');
        return [...new Set(reasons)];
    }
    if (freshRef.kind !== 'fresh_user_intent')
        reasons.push('fresh_user_intent_ref_not_fresh_user_intent');
    const bound = envelope.evidence.some((item) => item.id === freshRef.id && item.kind === 'fresh_user_intent' && item.source === freshRef.source);
    if (!bound)
        reasons.push('fresh_user_intent_evidence_unbound');
    return [...new Set(reasons)];
}
function actionTypeForHarnessMutation(mutationClass, publishes = false) {
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
function riskTierForHarnessMutation(input) {
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
function createHarnessCoreActionEnvelopeVNext(input) {
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
    const requiresConfirmation = input.requiresHumanConfirmation === true || exports.HARNESS_CORE_RISK_ORDER[riskTier] >= exports.HARNESS_CORE_RISK_ORDER.high;
    const turnId = input.turnId?.trim() || safeHarnessCoreId('turn', `${input.surface}:${input.source}:${requestId}`);
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
    const selectedMove = actorKind !== 'human'
        ? 'prepare_action'
        : requiresConfirmation
            ? 'confirm_action'
            : actionType === 'read'
                ? 'read_current_state'
                : 'execute_action';
    const authorityState = selectedMove === 'prepare_action'
        ? 'prepare_allowed'
        : selectedMove === 'confirm_action'
            ? 'confirmation_required'
            : selectedMove === 'read_current_state'
                ? 'read_only'
                : 'executable';
    const evidenceKind = actorKind === 'human' ? 'fresh_user_intent' : 'surface_signal';
    const authorityEvidence = createHarnessCoreEvidenceRef({
        id: `${turnId}:fresh-authority`,
        kind: evidenceKind,
        source: input.source,
        summary: input.reason,
        confidence,
        trace_refs: [trace]
    });
    const evidence = [
        authorityEvidence,
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
            fresh_user_intent_ref: actorKind === 'human' ? authorityEvidence : null,
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
            reason: actorKind !== 'human'
                ? 'Machine-origin evidence may prepare an action but cannot execute without source-bound fresh user intent.'
                : requiresConfirmation
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
    if (freshUserIntentAuthorityReasonCodes(envelope).length > 0)
        return 'deny';
    if (state === 'executable' && verdicts.has('allow')) {
        return hasMatchingExecutionLedger({
            envelope,
            authorizations,
            toolLedgers: input.toolLedgers || []
        })
            ? 'execute'
            : 'degrade';
    }
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
function hasMatchingExecutionLedger(input) {
    const allowedActionKeys = new Set(input.authorizations
        .filter((authorization) => authorization.verdict === 'allow')
        .map((authorization) => `${authorization.action_id}\n${authorization.capability_id}`));
    if (allowedActionKeys.size === 0)
        return false;
    const proposedActionIds = new Set(input.envelope.proposed_actions.map((action) => action.action_id));
    return input.toolLedgers.some((ledger) => {
        const actionKey = `${ledger.action_id}\n${ledger.capability_id}`;
        return (ledger.turn_id === input.envelope.turn_id &&
            proposedActionIds.has(ledger.action_id) &&
            allowedActionKeys.has(actionKey) &&
            ledger.authorization.verdict === 'allow' &&
            ledger.authorization.turn_id === input.envelope.turn_id &&
            ledger.authorization.action_id === ledger.action_id &&
            ledger.authorization.capability_id === ledger.capability_id &&
            ledger.authorization.decision_id.length > 0);
    });
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
        case 'degrade':
            if (input.envelope.action_authority.state === 'executable' &&
                input.authorizations.some((authorization) => authorization.verdict === 'allow')) {
                reasons.push('governor_missing_tool_ledger_for_authorized_execution');
            }
            else {
                reasons.push('governor_degrades_to_safe_surface_behavior');
            }
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
    for (const reason of freshUserIntentAuthorityReasonCodes(input.envelope)) {
        if (!reasons.includes(reason))
            reasons.push(reason);
    }
    return reasons;
}
function createHarnessCoreGovernorDecision(input) {
    const authorizations = input.authorizations || [];
    const toolLedgers = input.tool_ledgers || [];
    const outcome = governorOutcomeFor({ envelope: input.envelope, authorizations, toolLedgers });
    const authorizedActionCount = authorizations.filter((authorization) => authorization.verdict === 'allow').length;
    const requiresHumanConfirmation = input.envelope.action_authority.requires_human_confirmation ||
        authorizations.some((authorization) => authorization.approval.required);
    return {
        schema_version: 'governor-decision-v1',
        wire_contract_version: exports.HARNESS_CORE_WIRE_CONTRACT_VERSION,
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
function createGovernorConsumerVerification(input) {
    return {
        schema_version: 'governor-consumer-verification-v1',
        allowed: input.allowed,
        reason_codes: input.reasonCodes,
        source_kind: input.governorDecision ? 'governor_decision' : 'missing_governor_decision',
        decision_id: input.governorDecision?.decision_id || null,
        turn_id: input.governorDecision?.turn_id || null,
        outcome: input.governorDecision?.outcome || null,
        expected_capability_id: input.expectedCapabilityId || null,
        expected_action_type: input.expectedActionType || null,
        tool_name: input.toolName || null,
        action_id: input.authorization?.action_id || null,
        capability_id: input.authorization?.capability_id || null,
        authorization_decision_id: input.authorization?.decision_id || null,
        ledger_id: input.ledger?.ledger_id || null
    };
}
function stringOrNull(value) {
    if (value === null || value === undefined)
        return null;
    const text = String(value).trim();
    return text.length > 0 ? text : null;
}
function authorizationExpiryReasonCode(authorization, now) {
    if (authorization.approval.status === 'expired')
        return 'authorization_approval_expired';
    const expiresAt = stringOrNull(authorization.expires_at);
    if (!expiresAt)
        return null;
    const expiresMs = Date.parse(expiresAt);
    if (Number.isNaN(expiresMs))
        return 'authorization_expiry_invalid';
    const nowMs = now instanceof Date ? now.getTime() : now ? Date.parse(now) : Date.now();
    if (Number.isNaN(nowMs))
        return 'authorization_expiry_invalid';
    if (expiresMs <= nowMs)
        return 'authorization_expired';
    return null;
}
function boundHarnessCoreLedgerRow(input) {
    const summary = stringOrNull(input.ledger.result.summary) || stringOrNull(input.ledger.trace.summary);
    return {
        turn_id: stringOrNull(input.ledger.turn_id),
        action_id: stringOrNull(input.ledger.action_id),
        capability_id: stringOrNull(input.ledger.capability_id),
        authorization_decision_id: stringOrNull(input.verdict.authorization_decision_id) || stringOrNull(input.ledger.authorization.decision_id),
        ledger_id: stringOrNull(input.ledger.ledger_id),
        tool_name: stringOrNull(input.ledger.tool_name),
        owner_system: stringOrNull(input.owner_system),
        mutation_class: stringOrNull(input.mutation_class),
        outcome: input.verdict.outcome || null,
        status: input.ledger.result.status || null,
        surface: stringOrNull(input.surface),
        request_id: stringOrNull(input.request_id),
        trace_ref: stringOrNull(input.trace_ref) || stringOrNull(input.ledger.trace.id),
        summary,
        ledger_json: input.ledger
    };
}
exports.boundLedgerRow = boundHarnessCoreLedgerRow;
function isHarnessCoreRecord(value) {
    return value !== null && typeof value === 'object' && !Array.isArray(value);
}
function isHarnessCoreGovernorDecisionVerifierShape(value) {
    if (!isHarnessCoreRecord(value))
        return false;
    if (value.schema_version !== 'governor-decision-v1')
        return false;
    if (typeof value.turn_id !== 'string' || value.turn_id.length === 0)
        return false;
    if (typeof value.outcome !== 'string' || value.outcome.length === 0)
        return false;
    if (!isHarnessCoreRecord(value.execution_boundary))
        return false;
    if (typeof value.execution_boundary.action_authorized !== 'boolean')
        return false;
    if (!isHarnessCoreRecord(value.envelope))
        return false;
    if (!Array.isArray(value.envelope.proposed_actions))
        return false;
    if (!isHarnessCoreRecord(value.envelope.freshness))
        return false;
    if (!Array.isArray(value.envelope.evidence))
        return false;
    if (!Array.isArray(value.authorizations))
        return false;
    if (!Array.isArray(value.tool_ledgers))
        return false;
    return true;
}
function verifyHarnessCoreGovernorExecutionAuthority(input) {
    const governorDecision = input.governor_decision || null;
    if (!governorDecision) {
        return createGovernorConsumerVerification({
            allowed: false,
            reasonCodes: ['missing_governor_decision'],
            governorDecision: null,
            expectedCapabilityId: input.expected_capability_id,
            expectedActionType: input.expected_action_type || null,
            toolName: input.tool_name || null
        });
    }
    if (!isHarnessCoreGovernorDecisionVerifierShape(governorDecision)) {
        return createGovernorConsumerVerification({
            allowed: false,
            reasonCodes: ['invalid_governor_decision'],
            governorDecision: null,
            expectedCapabilityId: input.expected_capability_id,
            expectedActionType: input.expected_action_type || null,
            toolName: input.tool_name || null
        });
    }
    const reasonCodes = [];
    reasonCodes.push(...negotiateHarnessCoreWireContract({
        producer_version: Number(governorDecision.wire_contract_version || 0)
    }).reason_codes);
    reasonCodes.push(...harnessCoreGovernorDecisionSignatureReasonCodes({
        governor_decision: governorDecision,
        key: input.governor_hmac_key || null,
        expected_key_id: input.governor_hmac_key_id || null,
        require_signature: input.require_signature
    }));
    const allowedOutcomes = new Set(['execute']);
    if (input.allow_read_only)
        allowedOutcomes.add('read_only');
    if (!allowedOutcomes.has(governorDecision.outcome)) {
        reasonCodes.push(`governor_outcome_${governorDecision.outcome || 'missing'}`);
    }
    if (governorDecision.outcome === 'execute' && !governorDecision.execution_boundary.action_authorized) {
        reasonCodes.push('governor_action_not_authorized');
    }
    reasonCodes.push(...freshUserIntentAuthorityReasonCodes(governorDecision.envelope));
    const matchingAuthorization = governorDecision.authorizations.find((authorization) => {
        if (authorization.verdict !== 'allow')
            return false;
        if (authorization.turn_id !== governorDecision.turn_id)
            return false;
        if (authorization.capability_id !== input.expected_capability_id)
            return false;
        if (input.action_id && authorization.action_id !== input.action_id)
            return false;
        return authorization.decision_id.length > 0;
    });
    if (!matchingAuthorization) {
        reasonCodes.push('governor_missing_matching_authorization');
    }
    else {
        const expiryReason = authorizationExpiryReasonCode(matchingAuthorization, input.now);
        if (expiryReason)
            reasonCodes.push(expiryReason);
    }
    const hasMatchingProposedAction = matchingAuthorization
        ? governorDecision.envelope.proposed_actions.some((action) => {
            if (action.action_id !== matchingAuthorization.action_id)
                return false;
            if (action.capability_id !== matchingAuthorization.capability_id)
                return false;
            if (input.expected_action_type && action.action_type !== input.expected_action_type)
                return false;
            return true;
        })
        : false;
    if (matchingAuthorization && !hasMatchingProposedAction) {
        reasonCodes.push('governor_missing_matching_proposed_action');
    }
    const requirePreExecutionLedger = input.require_pre_execution_ledger !== false;
    const matchingLedger = matchingAuthorization
        ? governorDecision.tool_ledgers.find((ledger) => {
            if (ledger.turn_id !== governorDecision.turn_id)
                return false;
            if (ledger.action_id !== matchingAuthorization.action_id)
                return false;
            if (ledger.capability_id !== input.expected_capability_id)
                return false;
            if (input.tool_name && ledger.tool_name !== input.tool_name)
                return false;
            if (requirePreExecutionLedger && ledger.result.status !== 'not_started')
                return false;
            if (ledger.authorization.verdict !== 'allow')
                return false;
            if (ledger.authorization.turn_id !== governorDecision.turn_id)
                return false;
            if (ledger.authorization.action_id !== matchingAuthorization.action_id)
                return false;
            if (ledger.authorization.capability_id !== input.expected_capability_id)
                return false;
            if (ledger.authorization.decision_id !== matchingAuthorization.decision_id)
                return false;
            return true;
        })
        : undefined;
    if (governorDecision.outcome === 'execute' && !matchingLedger) {
        reasonCodes.push('governor_missing_matching_tool_ledger');
    }
    return createGovernorConsumerVerification({
        allowed: reasonCodes.length === 0,
        reasonCodes,
        governorDecision,
        authorization: matchingAuthorization || null,
        ledger: matchingLedger || null,
        expectedCapabilityId: input.expected_capability_id,
        expectedActionType: input.expected_action_type || null,
        toolName: input.tool_name || null
    });
}
function verifyHarnessCoreGovernorToolAuthority(input) {
    return verifyHarnessCoreGovernorExecutionAuthority({
        governor_decision: input.governor_decision,
        expected_capability_id: safeHarnessCoreId('capability', `${input.owner_system}:${input.tool_name}`),
        expected_action_type: input.action_type,
        tool_name: input.tool_name,
        action_id: input.action_id,
        allow_read_only: input.allow_read_only,
        require_pre_execution_ledger: input.require_pre_execution_ledger,
        governor_hmac_key: input.governor_hmac_key || null,
        governor_hmac_key_id: input.governor_hmac_key_id || null,
        require_signature: input.require_signature,
        now: input.now || null
    });
}
function createHarnessCoreAuthorizedGovernorDecision(input) {
    const hasActionSelector = Boolean(input.action_id || input.capability_id);
    const action = input.envelope.proposed_actions.find((candidate) => input.action_id
        ? candidate.action_id === input.action_id
        : input.capability_id
            ? candidate.capability_id === input.capability_id
            : true) || (hasActionSelector ? undefined : input.envelope.proposed_actions[0]);
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
    const freshnessReasons = freshUserIntentAuthorityReasonCodes(input.envelope);
    const authorityAllowsAction = input.envelope.action_authority.state === 'executable' ||
        (input.envelope.action_authority.state === 'read_only' && action.action_type === 'read') ||
        input.envelope.action_authority.state === 'confirmation_required';
    const authorityReasons = authorityAllowsAction ? [] : ['envelope_not_executable'];
    const verdict = freshnessReasons.length > 0 || authorityReasons.length > 0
        ? 'deny'
        : action.requires_confirmation
            ? 'interrupt'
            : 'allow';
    const ttlSeconds = input.ttl_seconds === undefined ? DEFAULT_AUTHORIZATION_TTL_SECONDS : input.ttl_seconds;
    const expiresAt = verdict === 'allow' && ttlSeconds !== null
        ? new Date(Date.parse(now) + ttlSeconds * 1000).toISOString()
        : undefined;
    const simulation = input.dry_run
        ? harnessCoreSimulationMarker(input.dry_run_reason || 'Dry-run governed turn skipped execution.')
        : undefined;
    const authorization = {
        schema_version: 'authorization-decision-v1',
        wire_contract_version: exports.HARNESS_CORE_WIRE_CONTRACT_VERSION,
        decision_id: safeHarnessCoreId('decision', `${input.envelope.turn_id}:${action.action_id}`),
        created_at: now,
        turn_id: input.envelope.turn_id,
        action_id: action.action_id,
        capability_id: action.capability_id,
        verdict,
        risk_tier: action.risk_tier,
        reasons: input.reasons && input.reasons.length > 0
            ? input.reasons
            : freshnessReasons.length > 0
                ? freshnessReasons
                : authorityReasons.length > 0
                    ? authorityReasons
                    : action.requires_confirmation
                        ? ['harness_core_authorized', 'explicit_human_confirmation_required']
                        : ['harness_core_authorized'],
        evidence: input.envelope.evidence,
        approval: {
            required: freshnessReasons.length === 0 && authorityReasons.length === 0 && action.requires_confirmation,
            status: freshnessReasons.length > 0 || authorityReasons.length > 0
                ? 'not_required'
                : action.requires_confirmation
                    ? 'requested'
                    : 'not_required'
        },
        restrictions: {
            network_allowed: freshnessReasons.length === 0 &&
                authorityReasons.length === 0 &&
                (action.action_type === 'external_api_call' || action.action_type === 'browser_action' || action.action_type === 'computer_action'),
            write_allowed: freshnessReasons.length === 0 && authorityReasons.length === 0 && !['read'].includes(action.action_type),
            publish_allowed: freshnessReasons.length === 0 && authorityReasons.length === 0 && action.action_type === 'publish',
            ...(freshnessReasons.length === 0 && authorityReasons.length === 0 ? input.restrictions || {} : {})
        },
        ...(expiresAt ? { expires_at: expiresAt } : {}),
        ...(simulation ? { simulation } : {}),
        trace
    };
    const ledgerId = safeHarnessCoreId('ledger', input.idempotency_key || `${input.envelope.turn_id}:${action.action_id}`);
    const ledger = {
        schema_version: 'tool-call-ledger-v1',
        wire_contract_version: exports.HARNESS_CORE_WIRE_CONTRACT_VERSION,
        ledger_id: ledgerId,
        created_at: now,
        turn_id: input.envelope.turn_id,
        action_id: action.action_id,
        capability_id: action.capability_id,
        tool_name: input.tool_name,
        lifecycle: [
            { stage: 'propose', at: input.envelope.created_at, verdict: 'passed', summary: 'Harness Core proposed the action.' },
            { stage: 'validate', at: now, verdict: 'passed', summary: 'Harness Core validated the authority record.' },
            {
                stage: 'authorize',
                at: now,
                verdict: verdict === 'allow' ? 'passed' : verdict === 'interrupt' ? 'pending' : 'failed',
                summary: 'Governor authorization recorded before execution.'
            },
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
        ...(simulation ? { simulation } : {}),
        trace: input.idempotency_key
            ? createHarnessCoreTraceRef({
                id: `record:${input.idempotency_key}`,
                summary: `Governor authorization for ${input.tool_name}.`,
                redaction_class: 'metadata_only'
            })
            : trace
    };
    const governorDecision = createHarnessCoreGovernorDecision({
        envelope: input.envelope,
        authorizations: [authorization],
        tool_ledgers: [ledger],
        reply_style: input.reply_style,
        reply_instruction: input.reply_instruction
    });
    return simulation ? { ...governorDecision, simulation } : governorDecision;
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
function assertHarnessCoreLedgerAuthorizationBinding(ledger) {
    const mismatches = [];
    if (ledger.authorization.turn_id !== ledger.turn_id)
        mismatches.push('turn_id');
    if (ledger.authorization.action_id !== ledger.action_id)
        mismatches.push('action_id');
    if (ledger.authorization.capability_id !== ledger.capability_id)
        mismatches.push('capability_id');
    if (!ledger.authorization.decision_id)
        mismatches.push('decision_id');
    if (mismatches.length > 0) {
        throw new Error(`Tool ledger authorization binding mismatch: ${mismatches.join(', ')}`);
    }
}
function finalizeHarnessCoreToolCallLedger(input) {
    const finalTraceId = input.idempotency_key
        ? safeHarnessCoreId('trace', `finalize:${input.ledger.ledger_id}:${input.idempotency_key}`)
        : null;
    assertHarnessCoreLedgerAuthorizationBinding(input.ledger);
    if (HARNESS_CORE_EXECUTED_TOOL_STATUSES.has(input.ledger.result.status)) {
        if (finalTraceId && input.ledger.trace.id === finalTraceId) {
            if (input.ledger.result.status !== input.status) {
                throw new Error('idempotency key already finalized ledger with a different status');
            }
            return input.ledger;
        }
        throw new Error('terminal tool-call ledger cannot be finalized again');
    }
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
            id: input.idempotency_key
                ? `finalize:${input.ledger.ledger_id}:${input.idempotency_key}`
                : `${input.ledger.ledger_id}:${input.status}:final`,
            summary: `Final ledger for ${input.ledger.tool_name}.`
        })
    };
}
async function withGovernedTurn(input, execute) {
    const dryRunSummary = input.dry_run_summary || 'Dry-run governed turn skipped execution.';
    const governorDecision = input.governor_decision && input.dry_run
        ? simulatedHarnessCoreGovernorDecision(input.governor_decision, dryRunSummary)
        : input.governor_decision || null;
    if (!governorDecision) {
        throw new Error('withGovernedTurn requires a governor decision');
    }
    const expectedCapabilityId = input.expected_capability_id ||
        (input.owner_system ? safeHarnessCoreId('capability', `${input.owner_system}:${input.tool_name}`) : null);
    if (!expectedCapabilityId) {
        throw new Error('withGovernedTurn requires owner_system or expected_capability_id');
    }
    const verification = verifyHarnessCoreGovernorExecutionAuthority({
        governor_decision: governorDecision,
        expected_capability_id: expectedCapabilityId,
        expected_action_type: input.action_type,
        tool_name: input.tool_name,
        action_id: input.action_id,
        allow_read_only: input.allow_read_only,
        require_pre_execution_ledger: input.require_pre_execution_ledger,
        governor_hmac_key: input.governor_hmac_key || null,
        governor_hmac_key_id: input.governor_hmac_key_id || null,
        require_signature: input.require_signature,
        now: input.now || null
    });
    if (!verification.allowed) {
        throw new Error(`withGovernedTurn refused by Governor verification: ${verification.reason_codes.join(', ') || 'unknown'}`);
    }
    const ledger = governorDecision.tool_ledgers.find((item) => item.ledger_id === verification.ledger_id);
    if (!ledger) {
        throw new Error('withGovernedTurn requires a matching pre-execution ledger');
    }
    let activeLedger = JSON.parse(JSON.stringify(ledger));
    let finalizedLedger = null;
    const turn = {
        governor_decision: governorDecision,
        verification,
        ledger: activeLedger,
        finalized_ledger: null,
        finalize(finalizeInput) {
            if (finalizedLedger)
                return finalizedLedger;
            finalizedLedger = finalizeHarnessCoreToolCallLedger({
                ledger: activeLedger,
                status: finalizeInput.status,
                summary: finalizeInput.summary,
                output_ref: finalizeInput.output_ref,
                output_path_or_uri: finalizeInput.output_path_or_uri,
                error_ref: finalizeInput.error_ref,
                rollback_ref: finalizeInput.rollback_ref,
                now: finalizeInput.now,
                idempotency_key: finalizeInput.idempotency_key
            });
            activeLedger = finalizedLedger;
            turn.ledger = finalizedLedger;
            turn.finalized_ledger = finalizedLedger;
            if (input.on_finalize)
                input.on_finalize(finalizedLedger);
            return finalizedLedger;
        }
    };
    if (input.dry_run) {
        turn.finalize({
            status: 'not_started',
            summary: dryRunSummary,
            output_path_or_uri: input.dry_run_output_path_or_uri || `harness-core://governed-turns/${activeLedger.ledger_id}/dry-run`
        });
        return undefined;
    }
    try {
        const result = await execute(turn);
        if (!finalizedLedger) {
            turn.finalize({
                status: 'success',
                summary: input.success_summary || 'Governed turn completed.',
                output_path_or_uri: input.success_output_path_or_uri || `harness-core://governed-turns/${activeLedger.ledger_id}/success`
            });
        }
        return result;
    }
    catch (error) {
        if (!finalizedLedger) {
            turn.finalize({
                status: 'failure',
                summary: input.failure_summary || 'Governed turn failed during execution.',
                output_path_or_uri: input.failure_output_path_or_uri || `harness-core://governed-turns/${activeLedger.ledger_id}/failure`,
                error_ref: input.failure_error_ref
            });
        }
        throw error;
    }
}
function repairHarnessCoreStrandedToolCallLedger(input) {
    if (input.ledger.result.status !== 'not_started')
        return null;
    const createdMs = Date.parse(input.ledger.created_at);
    const nowMs = input.now ? Date.parse(input.now) : Date.now();
    if (Number.isNaN(createdMs) || Number.isNaN(nowMs))
        return null;
    const strandedAfterSeconds = input.stranded_after_seconds ?? 3600;
    if ((nowMs - createdMs) / 1000 < strandedAfterSeconds)
        return null;
    const summary = input.summary || `failure(stranded): not_started ledger exceeded ${strandedAfterSeconds}s without finalization.`;
    const outputPath = input.output_path_or_uri || `harness-core://repairs/${input.ledger.ledger_id}/stranded`;
    const executeStage = {
        stage: 'execute',
        at: input.now || new Date(nowMs).toISOString(),
        verdict: 'failed',
        summary
    };
    const lifecycle = [...input.ledger.lifecycle];
    if (lifecycle.length > 0 && lifecycle[lifecycle.length - 1].stage === 'execute') {
        lifecycle[lifecycle.length - 1] = executeStage;
    }
    else {
        lifecycle.push(executeStage);
    }
    return {
        ...input.ledger,
        lifecycle,
        result: {
            status: 'failure',
            summary,
            sanitized_output_ref: createHarnessCoreArtifactRef({
                id: `${input.ledger.ledger_id}:stranded:output`,
                kind: 'tool_output',
                path_or_uri: outputPath,
                summary,
                redaction_class: 'metadata_only'
            }),
            error_ref: createHarnessCoreArtifactRef({
                id: `${input.ledger.ledger_id}:stranded:error`,
                kind: 'tool_error',
                path_or_uri: `${outputPath}/error`,
                summary: 'Stranded ledger repair provenance.',
                redaction_class: 'metadata_only'
            })
        },
        trace: createHarnessCoreTraceRef({
            id: `${input.ledger.ledger_id}:stranded:repair`,
            summary: `Stranded ledger repair for ${input.ledger.tool_name}.`
        })
    };
}
function repairHarnessCoreStrandedToolCallLedgers(input) {
    return input.ledgers
        .map((ledger) => repairHarnessCoreStrandedToolCallLedger({
        ledger,
        now: input.now,
        stranded_after_seconds: input.stranded_after_seconds
    }))
        .filter((ledger) => ledger !== null);
}
function createHarnessCoreReadinessScore(input) {
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
    const status = gates.public_ready && gates.network_absorbable && gates.performance_budget_proven && gates.governance_rulesets_proven && gates.zero_high_agency_legacy_local_gates && score >= 0.95 && !blockers
        ? 'public_ready'
        : score >= 0.85 && gates.telegram_live_proven && gates.startup_benchmark_proven && gates.performance_budget_proven && gates.governance_rulesets_proven && gates.zero_high_agency_legacy_local_gates && !blockers
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
function createHarnessCoreExperienceIndex(input) {
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
function createHarnessCoreResourceRegistry(input) {
    return {
        schema_version: 'resource-registry-v1',
        registry_id: safeHarnessCoreId('resource-registry', input.id),
        created_at: new Date().toISOString(),
        resources: input.resources
    };
}
function createHarnessCoreEvaluationPack(input) {
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
function createHarnessCoreHarnessRun(input) {
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
const LEGACY_AUTHORITY_RISK_KEYS = [
    'can_execute',
    'can_mutate_state',
    'can_route_turns',
    'can_write_memory',
    'can_launch_mission',
    'can_call_network',
    'can_publish',
    'can_schedule'
];
function legacyAuthorityHasHighAgencyRisk(authorityRisk) {
    return LEGACY_AUTHORITY_RISK_KEYS.some((key) => Boolean(authorityRisk[key]));
}
function assertLegacyAuthorityPlaneDisposition(input) {
    const highAgencyRisk = legacyAuthorityHasHighAgencyRisk(input.authority_risk);
    if (input.disposition === 'release_blocker') {
        if (input.blockers.length === 0) {
            throw new Error('release-blocker legacy authority planes require at least one blocker');
        }
        return;
    }
    if (input.blockers.length > 0) {
        throw new Error('non-blocking legacy authority planes cannot carry release blockers');
    }
    if (input.disposition === 'removed' || input.disposition === 'quarantined')
        return;
    if (input.disposition === 'evidence_adapter') {
        if (highAgencyRisk) {
            throw new Error('evidence adapters cannot retain high-agency execution risk');
        }
        if (!input.evidence_only || input.consumer_of_governor) {
            throw new Error('evidence_adapter requires evidence_only and no consumer authority');
        }
    }
    if (input.disposition === 'canonical_consumer') {
        if (!(input.governor_required && input.consumer_of_governor && input.ledger_required)) {
            throw new Error('canonical legacy consumers require Governor authority and tool ledgers');
        }
    }
}
function createHarnessCoreLegacyAuthorityPlane(input) {
    const authorityRisk = {
        can_execute: Boolean(input.authority_risk.can_execute),
        can_mutate_state: Boolean(input.authority_risk.can_mutate_state),
        can_route_turns: Boolean(input.authority_risk.can_route_turns),
        can_write_memory: Boolean(input.authority_risk.can_write_memory),
        can_launch_mission: Boolean(input.authority_risk.can_launch_mission),
        can_call_network: Boolean(input.authority_risk.can_call_network),
        can_publish: Boolean(input.authority_risk.can_publish),
        can_schedule: Boolean(input.authority_risk.can_schedule)
    };
    const governorRequired = Boolean(input.governor_required);
    const evidenceOnly = Boolean(input.evidence_only);
    const consumerOfGovernor = Boolean(input.consumer_of_governor);
    const ledgerRequired = Boolean(input.ledger_required);
    const blockers = input.blockers || [];
    assertLegacyAuthorityPlaneDisposition({
        authority_risk: authorityRisk,
        disposition: input.disposition,
        governor_required: governorRequired,
        evidence_only: evidenceOnly,
        consumer_of_governor: consumerOfGovernor,
        ledger_required: ledgerRequired,
        blockers
    });
    return {
        schema_version: 'legacy-authority-plane-v1',
        plane_id: safeHarnessCoreId('legacy-plane', input.id),
        created_at: new Date().toISOString(),
        owner_repo: input.owner_repo,
        surface: input.surface,
        plane_type: input.plane_type,
        source_ref: createHarnessCoreArtifactRef({
            id: `${input.id}:source`,
            kind: 'legacy_authority_source',
            path_or_uri: input.source_path,
            summary: input.summary,
            redaction_class: 'metadata_only'
        }),
        authority_risk: authorityRisk,
        disposition: input.disposition,
        harness_binding: {
            governor_required: governorRequired,
            evidence_only: evidenceOnly,
            consumer_of_governor: consumerOfGovernor,
            ledger_required: ledgerRequired,
            notes: input.summary
        },
        evidence: input.evidence,
        blockers,
        trace: createHarnessCoreTraceRef({
            id: `${input.id}:legacy-authority-plane`,
            summary: input.summary
        })
    };
}
function createHarnessCoreLegacyAuthorityInventory(input) {
    const counts = {
        removed: 0,
        quarantined: 0,
        evidence_adapter: 0,
        canonical_consumer: 0,
        release_blocker: 0
    };
    const blockers = [];
    let highAgencyRiskCount = 0;
    for (const plane of input.planes) {
        counts[plane.disposition] += 1;
        if (legacyAuthorityHasHighAgencyRisk(plane.authority_risk))
            highAgencyRiskCount += 1;
        blockers.push(...plane.blockers);
        if (plane.disposition === 'release_blocker')
            blockers.push(`${plane.plane_id} is a release blocker`);
    }
    const ready = counts.release_blocker === 0 && blockers.length === 0;
    return {
        schema_version: 'legacy-authority-inventory-v1',
        inventory_id: safeHarnessCoreId('legacy-authority-inventory', input.id),
        created_at: new Date().toISOString(),
        scope: {
            owner_repo: input.owner_repo,
            surfaces: input.surfaces
        },
        planes: input.planes,
        summary: {
            plane_count: input.planes.length,
            removed_count: counts.removed,
            quarantined_count: counts.quarantined,
            evidence_adapter_count: counts.evidence_adapter,
            canonical_consumer_count: counts.canonical_consumer,
            release_blocker_count: counts.release_blocker,
            high_agency_risk_count: highAgencyRiskCount
        },
        release_gate: {
            zero_high_agency_legacy_local_gates: ready,
            ready_for_readiness_promotion: ready,
            blockers
        }
    };
}
function createTelegramLiveQaEvidencePacket(input) {
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
exports.PROTECTED_HARNESS_COMPONENT_TYPES = new Set([
    'verifier',
    'benchmark',
    'model_config',
    'authority_policy'
]);
const MUTATING_HARNESS_EVOLUTION_MODES = new Set(['sandbox', 'promote', 'rollback']);
const HARNESS_CORE_READINESS_STATUS_RANK = Object.freeze({
    blocked: 0,
    private_ready: 1,
    release_candidate: 2,
    public_ready: 3
});
function createHarnessCoreChangeManifest(input) {
    assertHarnessCoreComponentEditablePolicy(input.target_component);
    if (exports.PROTECTED_HARNESS_COMPONENT_TYPES.has(input.target_component.component_type) && !input.human_approval_ref) {
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
function createHarnessCoreSelfEvolutionRun(input) {
    const verdict = input.verdict || 'not_ready';
    const manifests = input.change_manifests || [];
    const components = input.target_components || [];
    components.forEach(assertHarnessCoreComponentEditablePolicy);
    manifests.forEach((manifest) => assertHarnessCoreComponentEditablePolicy(manifest.target_component));
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
function createHarnessCoreChangeManifestRunner(input) {
    const manifests = input.change_manifests || [];
    const components = [...(input.target_components || [])];
    components.forEach(assertHarnessCoreComponentEditablePolicy);
    manifests.forEach((manifest) => assertHarnessCoreComponentEditablePolicy(manifest.target_component));
    const knownComponentIds = new Set(components.map((component) => component.component_id));
    for (const manifest of manifests) {
        const component = manifest.target_component;
        if (!knownComponentIds.has(component.component_id)) {
            components.push(component);
            knownComponentIds.add(component.component_id);
        }
    }
    const decision = evaluateHarnessCoreChangeManifestRunner({
        mode: input.mode,
        readiness_score: input.readiness_score,
        target_components: components,
        change_manifests: manifests,
        requested_verdict: input.requested_verdict,
        live_surface_required: input.live_surface_required ?? false
    });
    return createHarnessCoreSelfEvolutionRun({
        id: input.id,
        mode: input.mode,
        surface: input.surface,
        experience_index: input.experience_index,
        readiness_score: input.readiness_score,
        commands: input.commands,
        target_components: components,
        change_manifests: manifests,
        evaluation_packs: input.evaluation_packs,
        verdict: decision.verdict,
        summary: decision.summary,
        roles: input.roles,
        live_surface_required: input.live_surface_required
    });
}
function evaluateHarnessCoreChangeManifestRunner(input) {
    const reasons = [];
    input.target_components.forEach(assertHarnessCoreComponentEditablePolicy);
    input.change_manifests.forEach((manifest) => assertHarnessCoreComponentEditablePolicy(manifest.target_component));
    if (input.mode === 'observe') {
        return runnerDecision('not_ready', ['observe_mode_records_evidence_only']);
    }
    if (input.requested_verdict === 'rollback' || input.mode === 'rollback') {
        if (input.mode !== 'rollback')
            reasons.push('rollback_requires_rollback_mode');
        if (!input.change_manifests.some((manifest) => manifest.verdict === 'rolled_back')) {
            reasons.push('rollback_requires_rolled_back_manifest');
        }
        return runnerDecision(reasons.length === 0 ? 'rollback' : 'not_ready', reasons.length ? reasons : ['rollback_manifest_present']);
    }
    if (input.mode !== 'promote')
        reasons.push(`${input.mode}_mode_cannot_promote`);
    if (input.change_manifests.length === 0)
        reasons.push('no_change_manifests');
    const nonAccepted = input.change_manifests
        .filter((manifest) => manifest.verdict !== 'accepted')
        .map((manifest) => manifest.change_id);
    if (nonAccepted.length > 0)
        reasons.push(`non_accepted_change_manifests:${nonAccepted.join(',')}`);
    if (input.live_surface_required || input.change_manifests.some((manifest) => manifest.live_proof_required)) {
        reasons.push('live_proof_still_required');
    }
    const missingApproval = protectedComponentsMissingApproval(input.target_components, input.change_manifests);
    if (missingApproval.length > 0) {
        reasons.push(`protected_component_requires_approval:${missingApproval.join(',')}`);
    }
    let requested = input.requested_verdict === 'promote_private' || input.requested_verdict === 'promote_release_candidate'
        ? input.requested_verdict
        : HARNESS_CORE_READINESS_STATUS_RANK[input.readiness_score.overall.status] >=
            HARNESS_CORE_READINESS_STATUS_RANK.release_candidate
            ? 'promote_release_candidate'
            : 'promote_private';
    const requiredStatus = requested === 'promote_private' ? 'private_ready' : 'release_candidate';
    const readinessStatus = input.readiness_score.overall.status;
    if (HARNESS_CORE_READINESS_STATUS_RANK[readinessStatus] < HARNESS_CORE_READINESS_STATUS_RANK[requiredStatus]) {
        reasons.push(`readiness_below_${requiredStatus}:${readinessStatus}`);
    }
    if (reasons.length > 0)
        return runnerDecision('not_ready', reasons);
    return runnerDecision(requested, ['accepted_change_manifests_ready']);
}
function runnerDecision(verdict, reasons) {
    const reasonText = reasons.length ? reasons.join(', ') : 'no_blockers';
    if (verdict === 'not_ready') {
        return { verdict, reasons, summary: `Change manifest runner is not ready to promote: ${reasonText}.` };
    }
    if (verdict === 'rollback') {
        return { verdict, reasons, summary: `Change manifest runner selected rollback: ${reasonText}.` };
    }
    return { verdict, reasons, summary: `Change manifest runner selected ${verdict}: ${reasonText}.` };
}
function isHarnessCoreProtectedComponentType(componentType) {
    return exports.PROTECTED_HARNESS_COMPONENT_TYPES.has(componentType);
}
function assertHarnessCoreComponentEditablePolicy(component) {
    if (exports.PROTECTED_HARNESS_COMPONENT_TYPES.has(component.component_type) && component.editable_by_evolution) {
        throw new Error('protected Harness Core components cannot be marked editable_by_evolution');
    }
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
    if (selfEvolutionRequiresProtectedApproval(input.mode, input.verdict)) {
        const missingApproval = protectedComponentsMissingApproval(input.target_components, input.change_manifests);
        if (missingApproval.length > 0) {
            throw new Error(`protected self-evolution components require approval evidence: ${missingApproval.join(', ')}`);
        }
    }
}
function selfEvolutionRequiresProtectedApproval(mode, verdict) {
    return (verdict !== 'not_ready' &&
        (MUTATING_HARNESS_EVOLUTION_MODES.has(mode) ||
            verdict === 'promote_private' ||
            verdict === 'promote_release_candidate' ||
            verdict === 'rollback'));
}
function protectedComponentsMissingApproval(targetComponents, changeManifests) {
    const approvedComponentIds = new Set(changeManifests
        .filter((manifest) => Boolean(manifest.human_approval_ref))
        .map((manifest) => manifest.target_component.component_id));
    return targetComponents
        .filter((component) => exports.PROTECTED_HARNESS_COMPONENT_TYPES.has(component.component_type))
        .filter((component) => !approvedComponentIds.has(component.component_id))
        .map((component) => component.component_id || component.component_type);
}
