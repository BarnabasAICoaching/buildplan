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
- **A ticker that never sleeps.** An automated watchdog keeps the plan moving forward, one right step at a time. If an agent dies, stalls, or just sulks, the process resumes and forces the step through, with a clean sub-agent if needed.

## Once installed, the flow

Once it's installed, here's the whole dance:

1. Tell your agent about your new awesome idea.
2. Tell it to run a build plan for the implementation.
3. The agent breaks the full strategy into individual tasks.
4. Each task gets a definition of success: what done looks like, and how to prove it.
5. Every step is gated by the harness itself. Need approval? That's your call, and only yours. The agent can't self-approve. Enforced, not asked nicely.
6. A timer keeps the process marching forward. Agent dies? Stops? Refuses? The timer resumes and forces the step through, spinning up a clean sub-agent if necessary.
7. You review and approve the whole plan before any work starts.
8. You go to bed.
9. You wake up to a clean, verified, tested, fully complete plan. Every step carries its completion hash for full auditability.
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

## Limits

- Stages are shell commands, not per-stage LLM calls.
- Lobster `cwd` is lost on resume — every plan action must use absolute paths. The normalize step handles this by replacing `__SKILL_DIR__`.
- `$step.exit_code` conditions are unsupported. Not needed: a failing step stops the workflow.
- No real-time watchdog. Use managed flow records (`flowControllerId` + `flowGoal`) and schedule a manual audit.

## License

MIT
