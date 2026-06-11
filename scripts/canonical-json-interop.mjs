import fs from 'node:fs';
import {
  canonicalHarnessCoreJson,
  harnessCoreGovernorDecisionSignatureReasonCodes,
  signHarnessCoreGovernorDecision
} from '../ts-dist/index.js';

const mode = process.argv[2];
const key = process.argv[3] || '';
const input = JSON.parse(fs.readFileSync(0, 'utf8'));

if (mode === 'canonical') {
  process.stdout.write(canonicalHarnessCoreJson(input));
} else if (mode === 'verify') {
  process.stdout.write(
    JSON.stringify(
      harnessCoreGovernorDecisionSignatureReasonCodes({
        governor_decision: input,
        key,
        require_signature: true
      })
    )
  );
} else if (mode === 'sign') {
  process.stdout.write(
    JSON.stringify(
      signHarnessCoreGovernorDecision(input, {
        key,
        key_id: 'local',
        nonce: 'ts-to-python-canonical-json',
        created_at: '2026-06-11T00:00:00Z'
      })
    )
  );
} else {
  console.error(`unknown mode: ${mode}`);
  process.exit(2);
}
