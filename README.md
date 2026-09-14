# Buildplan

Lobster-powered multi-stage build plans for OpenClaw. Write a prose plan, get verified results with approval gates enforced by the gateway itself.

## The old way

You have an idea. You tell your agent all about it, and tell it to build a plan. You spend an hour reading and tweaking the plan's markdown. You tell it to run, and head to bed, dreaming of shipped features.

The agent runs for a few steps, hits an error 15 minutes in, and sits there waiting for you like a dog by an empty food bowl. You wake up expecting something to review and find almost nothing happened.

Or worse: it built something vastly different and published it to main without asking. Surprise!

## The right way: Build Plan with harness gates

Build Plan doesn't trust agent judgment calls, and neither should you:

- Every risky step hits a **harness gate**. If a step needs approval, the approval MUST come from you. The agent cannot approve itself. That's enforced by the harness, not the agent's good intentions.
- **Verification with receipts.** Every step carries verification requirements, and completed work gets stamped with content hashes. Proof, not vibes.
- **A build that picks up where it left off.** The whole plan runs under Lobster with managed Task Flow. If the gateway restarts mid-build, the stalled flow is visible via `openclaw tasks flow list`. Recovery is one re-run: content-hashed markers skip every stage that already passed. You're back at the problem in seconds, not redoing the whole thing.

## The full journey: idea to shipped build

Here's how it plays out from the moment you have an idea to the moment you verify it shipped:

1. **Talk it out.** You tell your agent about your idea. Back and forth until the picture is clear. When it feels complete, ask: *"Do you have enough info to build a full implementation plan? If not, ask me anything you need."*
2. **Agent drafts the plan.** Your agent writes a complete implementation plan — numbered stages, actions, verify steps, side-effect flags. Human-readable prose. You can read it, tweak it, argue about it.
3. **You review.** Read the plan, make changes, send it back for revisions. You're the decider, not the rubber stamp.
4. **Lock it in.** Tell your agent: *"Convert this to a buildplan."* That triggers this skill.
5. **Agent normalizes.** The skill reads your prose plan, converts each stage into a Lobster workflow template, flags side-effect stages for approval gates, and shows you a report — stage count, gate count, manual verifies.
6. **You approve or adjust.** The plan is ready. Give the go.
7. **Lobster runs it.** Stages execute in order. Every risky step pauses at a gate. You get the preview, you say yes or no. If something fails, the workflow stops and you see exactly what broke.
8. **Recovery is cheap.** Fix the blocker. Re-run. Markers skip every stage that already passed. The only thing you repeat is the fix.
9. **Audit the result (optional).** Spawn an audit subagent to run `audit-plan.py` on the plan file. It checks every stage's marker independently. No overlap with the build agent.

## Once installed, the flow

Once it's installed, here's the whole dance:

1. Tell your agent about your new awesome idea.
2. Tell it to run a build plan for the implementation.
3. The agent decomposes the full strategy into numbered stages with verifiable success criteria.
4. Every stage has a clear action, a verify check, and a side-effect flag for gating.
5. Every step is gated by the harness itself. Need approval? That's your call, and only yours. The agent can't self-approve. Enforced, not asked nicely.
6. If the process stops — a failed stage, a gateway restart — you fix the blocker and re-run. Content-hashed markers skip every stage that already passed. You don't repeat success.
7. You review and approve the whole plan before any work starts.
8. You go to bed.
9. You wake up to a finished build — or, if something broke, a clear failure report showing exactly what failed and where. Fix and re-run in seconds. Every completed stage carries a content-hashed marker for full auditability.
10. You smile, thank your agent, and go pet a puppy.

## Installation (agent instructions)

Paste this entire README URL to your agent and it will wire it up: https://github.com/BarnabasAICoaching/buildplan

**Step 1: Install the skill**

```bash
openclaw skills install @BarnabasAICoaching/buildplan
```

**Step 2: Verify the lobster tool**

The skill requires the `@openclaw/lobster` plugin. Add `"lobster"` to your agent config's `tools.alsoAllow` section:

```json
{
  "tools": {
    "alsoAllow": ["lobster"]
  }
}
```

Then restart the gateway.

**Step 3: Run a smoke test**

Create a test plan file:

```bash
cat > /tmp/test-plan.md << 'EOF'
### Stage 1 — Write a test file
Action: bash -c 'echo "buildplan-v1-test" > /tmp/buildplan-smoke-test.txt'
Verify: bash -c 'test -f /tmp/buildplan-smoke-test.txt && cat /tmp/buildplan-smoke-test.txt | grep -q "buildplan-v1-test"'
Side effect: false

### Stage 2 — Cleanup
Action: bash -c 'rm /tmp/buildplan-smoke-test.txt'
Verify: bash -c 'test ! -f /tmp/buildplan-smoke-test.txt'
Side effect: true
EOF
```

**Step 4: Run the agent**

Tell your agent:

> Run buildplan on /tmp/test-plan.md

The agent will:
1. Parse the prose plan
2. Convert it to a Lobster workflow using `templates/build-runner.lobster`
3. Replace `__SKILL_DIR__` with the absolute path to the skill directory
4. Add `approval: required` gates for `Side effect: true` stages
5. Show you a report: stage count, gate count, manual verifies
6. Wait for your explicit go before running

**Expected output:**

- `PASS: stage 1` with marker file created at `.buildplan-run/test-plan/stage-1.<hash>.ok`
- `needs_approval` for stage 2 with side effect
- After approval: `PASS: stage 2`
- `Build complete: all stages passed.`

## Files

| Path | Purpose |
|------|---------|
| `SKILL.md` | Agent-facing skill instructions (normalize + kickoff) |
| `scripts/execute-build-stage.py` | Stage executor with content-hashed marker idempotency |
| `templates/build-runner.lobster` | YAML workflow template |
| `examples/smoke-test.md` | 3-stage test plan |
| `examples/gate-test.lobster` | Lobster workflow with approval gate |
| `examples/fail-test.lobster` | Lobster workflow with failure propagation |
| `scripts/audit-plan.py` | Post-build audit: checks every stage's marker exists with the correct hash. Run by any agent, zero Lobster dependency |

## Audit (optional, after a build)

A completed buildplan leaves a trail: one marker file per stage at `.buildplan-run/<plan-name>/stage-N.<hash>.ok`. Any agent — not just the one that ran the build — can inspect this trail.

Run the audit from an ephemeral subagent:

```bash
python3 <skill-dir>/scripts/audit-plan.py <plan.md>
```

**Sample output:**
```
Auditing 2 stages for test-plan.md...

  Stage 1: PASS
  Stage 2: PASS

2/2 stages verified
All stages complete and verified.
```

The audit script needs no Lobster, no workflow, no token. It reads the plan, computes hashes, checks markers, exits 0 only if every stage passes. A failed audit can alert the owner without involving the build agent at all.

## Limits

- Stages are shell commands, not per-stage LLM calls.
- Lobster `cwd` is lost on resume — every plan action must use absolute paths. The normalize step handles this by replacing `__SKILL_DIR__`.
- `$step.exit_code` conditions are unsupported. Not needed: a failing step stops the workflow.
- No real-time watchdog. Use managed flow records (`flowControllerId` + `flowGoal`) and schedule a manual audit.

## License

MIT
