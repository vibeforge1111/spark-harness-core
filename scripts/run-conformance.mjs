import { createHmac } from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import {
  canonicalHarnessCoreJson,
  createHarnessCoreActionEnvelopeVNext,
  createHarnessCoreAuthorizedGovernorDecision,
  createHarnessCoreGovernorDecision,
  signHarnessCoreGovernorDecision,
  verifyHarnessCoreGovernorExecutionAuthority
} from '../ts-dist/index.js';

const vectorDir = path.join(process.cwd(), 'conformance', 'vectors');
const actionCapabilityId = 'capability:spark-harness-core:validate';
const actionType = 'edit_file';
const toolName = 'spark-harness-core.validate';

function loadVectors() {
  return fs
    .readdirSync(vectorDir)
    .filter((name) => name.endsWith('.json'))
    .sort()
    .map((name) => JSON.parse(fs.readFileSync(path.join(vectorDir, name), 'utf8')));
}

function buildGovernedActionDecision(vector) {
  const input = vector.input;
  const requiresConfirmation = Boolean(input.requires_confirmation);
  const envelope = createHarnessCoreActionEnvelopeVNext({
    surface: 'telegram',
    ownerSystem: 'spark-harness-core',
    toolName: 'validate',
    mutationClass: 'writes_files',
    source: 'telegram',
    requestId: 'turn-conformance',
    reason: 'User explicitly asked Spark to update a validation artifact.',
    confidence: input.confidence ?? 0.95,
    createdAt: '2026-06-10T00:00:00.000Z',
    riskTier: requiresConfirmation ? 'high' : 'low',
    requiresHumanConfirmation: requiresConfirmation
  });

  let decision = createHarnessCoreAuthorizedGovernorDecision({
    envelope,
    tool_name: toolName,
    now: '2026-06-10T00:00:01.000Z'
  });
  if (input.authorization_expires_at && decision.authorizations[0]) {
    decision.authorizations[0].expires_at = input.authorization_expires_at;
    if (decision.tool_ledgers[0]) decision.tool_ledgers[0].authorization.expires_at = input.authorization_expires_at;
  }
  if (!input.include_authorization) {
    decision = createHarnessCoreGovernorDecision({ envelope, authorizations: [], tool_ledgers: [] });
  } else if (!input.include_ledger) {
    decision = createHarnessCoreGovernorDecision({ envelope, authorizations: decision.authorizations, tool_ledgers: [] });
  }
  if (input.sign) {
    decision = signHarnessCoreGovernorDecision(decision, {
      key: input.hmac_key,
      key_id: input.signature.key_id,
      nonce: input.signature.nonce,
      created_at: input.signature.created_at
    });
  }
  if (input.tamper_after_sign && decision.tool_ledgers[0]) {
    decision.tool_ledgers[0].action_id = 'action-tampered-after-signing';
  }
  return decision;
}

const failures = [];
for (const vector of loadVectors()) {
  if (vector.input.canonical_value) {
    const payload = canonicalHarnessCoreJson(vector.input.canonical_value);
    const digest = createHmac('sha256', vector.input.hmac_key).update(payload, 'utf8').digest('hex');
    if (payload !== vector.expected.canonical_json) {
      failures.push(`${vector.name}: canonical JSON mismatch`);
    }
    if (digest !== vector.expected.hmac_sha256) {
      failures.push(`${vector.name}: canonical HMAC mismatch`);
    }
    continue;
  }

  if (vector.input.case === 'governed_action') {
    const decision = buildGovernedActionDecision(vector);
    if (decision.outcome !== vector.expected.governor_outcome) {
      failures.push(`${vector.name}: outcome ${decision.outcome} !== ${vector.expected.governor_outcome}`);
    }
    const verification = verifyHarnessCoreGovernorExecutionAuthority({
      governor_decision: decision,
      expected_capability_id: actionCapabilityId,
      expected_action_type: actionType,
      tool_name: toolName,
      governor_hmac_key: vector.input.hmac_key,
      require_signature: Boolean(vector.input.sign),
      now: vector.input.now
    });
    if (verification.allowed !== vector.expected.verifier.allowed) {
      failures.push(`${vector.name}: allowed ${verification.allowed} !== ${vector.expected.verifier.allowed}`);
    }
    for (const reasonCode of vector.expected.verifier.reason_codes) {
      if (!verification.reason_codes.includes(reasonCode)) {
        failures.push(`${vector.name}: missing reason ${reasonCode}; got ${verification.reason_codes.join(',')}`);
      }
    }
    continue;
  }

  if (vector.input.case === 'mutation_mapping') {
    const envelope = createHarnessCoreActionEnvelopeVNext({
      surface: 'telegram',
      ownerSystem: vector.input.owner_system,
      toolName: vector.input.tool_name,
      mutationClass: vector.input.mutation_class,
      source: 'conformance',
      requestId: `req-${vector.name}`,
      reason: `Conformance mapping for ${vector.input.mutation_class}.`,
      confidence: 0.95,
      createdAt: '2026-06-10T00:00:00.000Z'
    });
    const action = envelope.proposed_actions[0];
    if (!action) {
      failures.push(`${vector.name}: missing proposed action`);
      continue;
    }
    if (action.action_type !== vector.expected.action_type) {
      failures.push(`${vector.name}: action_type ${action.action_type} !== ${vector.expected.action_type}`);
    }
    if (action.risk_tier !== vector.expected.risk_tier) {
      failures.push(`${vector.name}: risk_tier ${action.risk_tier} !== ${vector.expected.risk_tier}`);
    }
    if (envelope.action_authority.risk_tier !== vector.expected.risk_tier) {
      failures.push(`${vector.name}: envelope risk_tier ${envelope.action_authority.risk_tier} !== ${vector.expected.risk_tier}`);
    }
  }
}

if (failures.length > 0) {
  console.error(failures.join('\n'));
  process.exit(1);
}
console.log(`OK: ${loadVectors().length} vectors`);
