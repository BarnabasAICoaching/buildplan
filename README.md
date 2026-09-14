# Buildplan

Lobster-powered multi-stage build plans for OpenClaw. Write a prose plan, get verified results with approval gates enforced by the gateway itself.

## The old way

An agent takes a human readable implementation plan and starts chugging away on it. Something goes sideways (and something always goes sideways) and the agent stops. Or worse: it does something destructive without ever asking permission. You spend the next 4 hours debugging it all manually, or spend massive tokens to have another agent read your entire process history and try to debug for you.

## The new way: Build Plan with harness gates

An agent takes a human readable implementation plan and breaks it down into structured individual tasks, each with a verification step and an approval gate rating. That looks like this:

- **Do this one specific task.**
- **This is what 'done' looks like.**
- **(This is a risky task — require user approval.)** or **(This is a local-only edit task, no approval needed.)**
  - If the task is risky, the harness itself enforces the approval from you. The agent can't fake it. Enforced, not asked.
  - When done, verify the task was completed successfully. If so, mark it complete with a specific hash unique to that command, then continue to the next task.

### What a gate looks like

When Lobster hits a step with `approval: required`, it doesn't ask the agent nicely. It returns this to the gateway:

```json
{
  "status": "needs_approval",
  "requiresApproval": {
    "approvalId": "9d9531c0",
    "prompt": "Approve stage-1?"
  }
}
```

The agent can't generate this response. It arrives from the Lobster runtime, through the gateway, as a tool result. The agent wasn't asked to decide — it was told to present. The resume call requires the exact `approvalId` and `approve: true` from the same Lobster response. No approvalId, no resume.

That's what "enforced, not asked" means. Your agent shows you the prompt. You say yes or no. If you say yes, the workflow resumes at exactly that step — the gate was the pause, not the work. If you say no, the workflow stops. Either way, the agent didn't decide.

When something goes sideways you know the exact step it failed and why. So does your agent. Address the failure that occurred (by you or your agent), and resume the build exactly where it left off.

**This does several things:**

1. An agent can resume exactly where it left off after addressing a failure.
2. It creates a clear audit trail of every task taken — when, and what.
3. The agent knows what "done" is. Both per-task and in full.
4. An independent agent (no context, no bias) then audits the full path for you (included in SKILL).
5. Since every individual task was verified complete, correctly, and within permission bounds, you have very high confidence this project — and only the actual project you requested — was completed within accepted permission boundaries. Facts, not vibes.

## The full journey: idea to shipped build

Here's how it plays out from the moment you have an idea to the moment you verify it shipped:

1. **Talk it out.** You tell your agent about your idea. Back and forth until the picture is clear. When it feels complete, ask: *"Do you have enough info to build a full implementation plan? If not, ask me anything you need."*
2. **Agent drafts the plan.** Your agent writes the full human-readable prose plan in markdown. Every angle covered, every requirement captured. You can read it, tweak it, argue about it.
3. **You review.** Read the plan, make changes, send it back for revisions. You're the decider, not the rubber stamp.
4. **Lock it in.** Tell your agent: *"Convert this to a buildplan."* That triggers this skill.
5. **Agent normalizes.** The skill reads your prose plan, converts each stage into a Lobster workflow template, flags side-effect stages for approval gates, and shows you a report — stage count, gate count, manual verifies.
6. **You approve or adjust.** The plan is ready. Give the go.
7. **Lobster runs it.** Stages execute in order. Every risky step pauses at a gate. You get the preview, you say yes or no. If something fails, the workflow stops and you see exactly what broke.
8. **Recovery is cheap.** Fix the blocker. Re-run. Markers skip every stage that already passed. The only thing you repeat is the fix.
9. **Audit the result (optional).** Spawn an audit subagent to run `audit-plan.py` on the plan file. It checks every stage's marker independently. No overlap with the build agent. No session memory bias to want it to be right. It is either factually completed or it isn't, period.

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
