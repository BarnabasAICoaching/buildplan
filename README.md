# Buildplan

Lobster-powered multi-stage build plans for OpenClaw. Write prose, get verified results. Every risky step pauses for your explicit approval, enforced by the gateway itself.

```markdown
### Stage 1 — Build the site
Action: npm run build
Verify: test -d dist
Side effect: false

### Stage 3 — Deploy to production
Action: rsync -avz dist/ server:/var/www/
Verify: curl -sS https://example.com | grep -q "Hello"
Side effect: true     # ← pauses for your approval
```

## Why

Agent-driven builds have three problems: the agent does everything in one shot, risky steps happen inside its judgment call, and a crash restarts from zero. Buildplan fixes all three with one small toolchain.

## How it works

1. Your agent writes a prose plan with numbered stages.
2. The **normalize** step converts it to a Lobster YAML workflow, flagging side-effect stages for approval gates.
3. You review the stage report and say go.
4. The **kickoff** step runs the workflow. Stages execute in order.
5. Every side-effect stage hits an `approval: required` gate — the Lobster runtime returns `needs_approval` outside the agent's execution context. The agent cannot silently skip it.
6. Passed stages leave content-hashed markers next to the plan file. A re-run skips what already passed. Edit a stage and its hash changes, so it re-runs automatically.

## Install

```bash
openclaw plugins install @openclaw/lobster
openclaw skills install @AWILLTOLLC/buildplan
```

Add `"lobster"` to your agent config's `tools.alsoAllow` and restart the gateway.

## Quick start

```bash
cd /tmp
cat > deploy.md << 'EOF'
### Stage 1 — Write a test file
Action: echo "hello" > /tmp/buildplan-test.txt
Verify: test -f /tmp/buildplan-test.txt && grep -q hello /tmp/buildplan-test.txt
Side effect: false

### Stage 2 — Clean up
Action: rm /tmp/buildplan-test.txt
Verify: test ! -f /tmp/buildplan-test.txt
Side effect: true
EOF
python3 <skill-dir>/scripts/execute-build-stage.py deploy.md 1
python3 <skill-dir>/scripts/execute-build-stage.py deploy.md 1  # SKIPs
```

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
- Lobster `cwd` is lost on resume — every plan action must use absolute paths. The normalize step handles this.
- `$step.exit_code` conditions are unsupported. Not needed: a failing step stops the workflow.
- No real-time watchdog. Use managed flow records (`flowControllerId` + `flowGoal`) and schedule a manual audit.

## License

MIT