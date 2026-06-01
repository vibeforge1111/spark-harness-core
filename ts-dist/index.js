"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.HARNESS_CORE_RISK_ORDER = void 0;
exports.safeHarnessCoreId = safeHarnessCoreId;
exports.createHarnessCoreTraceRef = createHarnessCoreTraceRef;
exports.createHarnessCoreArtifactRef = createHarnessCoreArtifactRef;
exports.createHarnessCoreEvidenceRef = createHarnessCoreEvidenceRef;
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
