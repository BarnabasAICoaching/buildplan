# Buildplan

A Lobster-powered multi-stage build plan executor for OpenClaw gateways.

## What it does

The buildplan system converts prose build plans (markdown with action/verify per stage) into YAML `.lobster` workflows that execute stages in order and pause at approval gates for side effects. Approval gates are enforced by the Lobster runtime, not by the agent, so the workflow pauses at each gate and waits for explicit owner approval before proceeding. Idempotency is achieved through content-hashed marker files that skip completed stages on re-run.

## What it does not do

- Stages are fixed shell commands, not per-stage LLM agent calls.
- A retry is a full workflow re-run. Markers make it cheap by skipping completed stages.
- No real-time watchdog. Use managed flow records (`flowControllerId` + `flowGoal`) and schedule a manual audit for stall detection.

## Install

1. `openclaw plugins install @openclaw/lobster` and restart the gateway.
2. Add `"lobster"` to `tools.alsoAllow` in the agent config.
3. `openclaw skills install @<owner>/buildplan` (with `<owner>` as placeholder).
4. Verify installation with the checklist below.

## Plan file format

Each plan is a markdown file with stages defined as:

```markdown
### Stage N — Title
Action: `bash command here`
Verify: `verification command here`
Side effect: true
```

- `### Stage N — Title`: stage number and title (N is 1-based).
- `Action:`: the command to execute. Use `(none)` if no action.
- `Verify:`: the verification command. Use `(none)` if no verify.
- `Side effect: true`: marks this stage as a side-effect gate requiring approval.
- `Manual verify: true`: adds a manual approval gate with a comment preview.

### Example plan

```markdown
### Stage 1 — Create directory
Action: `mkdir -p /tmp/build-output`
Verify: `test -d /tmp/build-output`
Side effect: false

### Stage 2 — Write artifact
Action: `echo "v1.0" > /tmp/build-output/artifact.txt`
Verify: `cat /tmp/build-output/artifact.txt | grep -q "v1.0"`
Side effect: false

### Stage 3 — Deploy
Action: `rsync -avz /tmp/build-output/ deploy@server:/opt/app/`
Verify: `ssh deploy@server "test -f /opt/app/artifact.txt"`
Side effect: true
```

## Approval gate rules

- **Approvals are per-instance.** Every gate pauses independently. Denying one gate does not skip or auto-approve the others.
- **The plan document names the actions each stage will perform.** It does not pre-authorize anything. Each gate is a fresh decision.

## Known Lobster runner limits

- `cwd` is lost on resume: every plan action must use absolute paths. The normalize step resolves the skill dir and bakes absolute paths into the generated `.lobster` so this is handled automatically.
- `$step.exit_code` conditions are unsupported. Not needed for linear plans: a failing step stops the workflow.
- Colons in quoted YAML values cause a parser error. Avoid colons in echo strings inside workflow YAML.
- `timeoutMs` and `maxStdoutBytes` must be set per build in the kickoff call. The defaults (20 seconds, small buffer) will break long-running builds.

## Verification checklist

Run these after installing to verify the skill works:

1. **Executor smoke test**: Run two stages from the smoke-test plan.
   ```
   cd /Users/apollo/.openclaw/workspace/buildplan
   python3 scripts/execute-build-stage.py examples/smoke-test.md 1
   python3 scripts/execute-build-stage.py examples/smoke-test.md 1
   ```
   Expected output: `PASS: stage 1` then `SKIP: stage 1 (already passed)`.

2. **Cwd-independent idempotency**: Run the same executor from a different directory.
   ```
   cd /tmp && python3 /Users/apollo/.openclaw/workspace/buildplan/scripts/execute-build-stage.py /Users/apollo/.openclaw/workspace/buildplan/examples/smoke-test.md 2
   ```
   Expected output: `SKIP: stage 2 (already passed)`.

3. **Content hash invalidation**: Change the action and re-run.
   ```
   echo '### Stage 1 — Write test file
Action: echo "changed" > /tmp/buildplan-smoke-test.txt
Verify: cat /tmp/buildplan-smoke-test.txt | grep -q "changed"
Side effect: false' > /tmp/test-change.md
   python3 /Users/apollo/.openclaw/workspace/buildplan/scripts/execute-build-stage.py /tmp/test-change.md 1
   ```
   Expected output: `PASS: stage 1` (new hash).

4. **Full workflow**: Run a 2-step test workflow through lobster.
   ```
   lobster action=run pipeline=/Users/apollo/.openclaw/workspace/buildplan/examples/test-workflow.lobster timeoutMs=3600000 maxStdoutBytes=2048000 flowControllerId=buildplan flowGoal="Test build"
   ```
   Expected output: `status: ok`.

5. **Approval gate**: Create a workflow with `approval: required`, verify it returns `needs_approval`.
   ```
   lobster action=run pipeline=/Users/apollo/.openclaw/workspace/buildplan/examples/gate-test.lobster timeoutMs=3600000 maxStdoutBytes=2048000 flowControllerId=buildplan flowGoal="Gate test"
   ```
   Expected output: `status: needs_approval`.

6. **Failure propagation**: Create a workflow with a failing step, verify it stops.
   ```
   lobster action=run pipeline=/Users/apollo/.openclaw/workspace/buildplan/examples/fail-test.lobster timeoutMs=3600000 maxStdoutBytes=2048000 flowControllerId=buildplan flowGoal="Fail test"
   ```
   Expected output: `status: error`.

Static security scan: [PASS] — no download+exec, no network calls, no obfuscation.
