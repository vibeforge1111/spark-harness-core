"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.HARNESS_CORE_RISK_ORDER = void 0;
exports.safeHarnessCoreId = safeHarnessCoreId;
exports.createHarnessCoreTraceRef = createHarnessCoreTraceRef;
exports.createHarnessCoreArtifactRef = createHarnessCoreArtifactRef;
exports.createHarnessCoreEvidenceRef = createHarnessCoreEvidenceRef;
exports.createHarnessCoreReadinessScore = createHarnessCoreReadinessScore;
exports.createHarnessCoreExperienceIndex = createHarnessCoreExperienceIndex;
exports.createHarnessCoreResourceRegistry = createHarnessCoreResourceRegistry;
exports.HARNESS_CORE_RISK_ORDER = Object.freeze({
    none: 0,
    read: 1,
    low: 2,
    medium: 3,
    high: 4,
    critical: 5
});
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
function createHarnessCoreReadinessScore(input) {
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
    const status = gates.public_ready && gates.network_absorbable && score >= 0.95 && !blockers
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
