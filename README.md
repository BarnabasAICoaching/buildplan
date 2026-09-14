# Buildplan

Lobster-powered multi-stage build plans for OpenClaw. Write a prose plan, get verified results with approval gates enforced by the gateway itself.

## The old way

You have an idea, you tell your agent to build a plan. You spend an hour tweaking markdown, telling it how to run, then go to bed. The agent dies 15 minutes in on an error and sits waiting till morning. You wake up to nothing. Or worse, it built something different and pushed to main without approval.

## The right way: Build Plan with harness gates

- Not agent judgment calls. Every risky step hits a gate.
- Verification requirements for every step with hashes of completed work.
- Automated ticker keeps it always moving forward one right step at a time.

## Once installed, the flow

Tell your agent your idea. Tell it to run a build plan. Agent breaks implementation into individual tasks. Each task gets a definition of success. Every step is gated by the harness itself. If a step needs approval, the approval MUST come from the user. The agent cannot approve directly (enforced by the harness, not the agent). A timer keeps the process moving. If an agent dies, stops, or refuses, the timer resumes and forces the step through with a clean sub-agent if necessary. You review and approve the whole plan before work starts. You go to bed. You wake to a clean, verified, tested, fully complete plan with per-task completion hashes for full auditability.

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

## Limits

- Stages are shell commands, not per-stage LLM calls.
- Lobster `cwd` is lost on resume — every plan action must use absolute paths. The normalize step handles this by replacing `__SKILL_DIR__`.
- `$step.exit_code` conditions are unsupported. Not needed: a failing step stops the workflow.
- No real-time watchdog. Use managed flow records (`flowControllerId` + `flowGoal`) and schedule a manual audit.

## License

MIT
