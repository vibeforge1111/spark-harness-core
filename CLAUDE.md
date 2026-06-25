# Spark Harness Core Agent Rules

This repo owns the newborn Spark harness kernel: authority envelopes, tool lifecycle contracts, resource/version registries, experience ledgers, readiness scoring, and the self-evolution protocol.

## Authority

- The Governor is the only component that converts raw language into high-agency authority.
- Surface adapters, route matchers, memory, pending state, provider names, domain chips, and local classifiers may submit evidence; they must not execute from words alone.
- High-agency actions require a validated envelope, an authorization decision, a ledger entry, and a result verdict.
- Normal conversation must remain useful without requiring defensive phrasing from the user.

## Design

- Schemas are the public contract; code is the enforcement kernel.
- Every schema must be language-neutral and usable by Telegram, CLI, Builder, Spawner, memory, startup operator, recursive/swarm, voice, domain chips, and future Spark repos.
- Keep deterministic mechanics explicit: validation, authorization, risk tiering, hooks, state, traces, resource versions, rollback, and verification.
- Keep model judgment inside bounded decisions with observable evidence and confidence.
- Do not put secrets, raw private prompts, raw account ids, provider payloads, or unredacted transcripts in fixtures, docs, traces, or schemas.

## Evolution

- Self-evolution can propose harness edits only through a change manifest.
- Self-evolution cannot mutate verifier logic, benchmark cases, model config, or authority policy without explicit human approval.
- Every improvement must declare predicted fixes, predicted regression risks, required tests, rollback plan, observed delta, and verdict.
- Failed or regressive edits must be reversible at file/component level.

## Branch Policy

- The installed Spark harness-core module tracks `main` release tags only. Reconcile feature or rescue branches into `main`, tag the verified release point, then update the installed registry pin to that tag commit instead of deepening long-lived runtime branches.

## Testing

- Run schema validation and kernel tests before claiming this repo is ready for integration.
- Add negative tests for authority escalation, word hijack, missing approval, missing trace, invalid resources, and unscored readiness categories.
- Treat test fixtures as contracts that downstream Spark repos can implement against.


<!-- SPARK FLEET STANDARD BLOCK v1 — canonical source: spark-compete/fleet/AGENT_GUIDE.md.
     This same block is mirrored into every repo's AGENTS.md and CLAUDE.md. Keep in sync. -->
## How agents work in this repo (Claude, Codex, Gemini — every LLM)

Many agents and sessions work these repos at the same time. There is a tiny **automatic**
workflow that keeps you from colliding. **There are no human-review steps — CI is the only
gate, and it is automatic.** This is coordination, not bureaucracy: claim, work, PR.

### Start of work — one command, then just work normally
```
python3 ~/spark-compete/scripts/fleet.py claim <this-repo-path> <area> <task>
```
You get your **own private worktree + branch + a lease** on `<area>`, so no other agent
edits the same files. It prints the folder to `cd` into. Work there and commit as usual —
a pre-commit hook **auto-checks and renews your lease**; you never manage it by hand.

- `fleet board` — see who's working on what, right now
- `fleet handoff <agent> --note "..."` — pass your work to another agent (with context)
- `fleet release --here` — done (frees the area + removes the worktree)

### Landing work — fully automatic, no human approval
1. Open a PR to the default branch.
2. **CI is the gate.** When it's green, the PR merges. No human reviews anything.
3. Never push directly to the protected branch; never commit from the shared checkout —
   always from your worktree.

### The rules (enforced by CI, not by people)
Full ruleset: **`spark-cli/docs/harness-discipline/`** — `01_RULESET.md` (7 Prime
Directives · Red Lines RL-01..21 · Rules R-01..28) and `07_FLEET_DISCIPLINE.md` (this
workflow). The day-to-day essentials:
- A real fix targets the **root cause**, not a symptom (R-05).
- No regex / keyword / canned answer **owns authority** — it is evidence only (RL-01).
- A failure **surfaces** with a clear reason; it never becomes a fake success (RL-08).
- One worktree per task; PRs only; nothing bypasses the CI gate (F-01 / F-09).

That's the whole contract. The system handles coordination and the gate for you —
automatically, with no human in the loop.
<!-- END SPARK FLEET STANDARD BLOCK v1 -->
