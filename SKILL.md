# buildplan

Execute multi-stage prose build plans with verified stages and side-effect approval gates enforced by the Lobster runtime, not by the agent.

## Normalize

Convert a prose build plan (markdown) into a `.lobster` workflow:

1. **Read the prose plan** and parse stages from `### Stage N — Title`, `Action:`, `Verify:`, `Side effect:`, and `Manual verify:` fields.

2. **Resolve the skill directory**: determine the absolute path to the folder containing this `SKILL.md`. The agent can discover this from the skill's location in the available_skills catalog or from the skill workshop.

3. **Copy the template** from `buildplan/templates/build-runner.lobster` and replace every `__SKILL_DIR__` with the resolved absolute path. The agent should also resolve `{{plan_path}}` to the absolute path of the plan file.

4. **Identify approval gates**: for each stage, add `approval: required` if the stage has `Side effect: true` or the action contains a dangerous command (`git push`, `git commit`, `rm -rf`, `sudo`, `ssh`, `scp`, `docker push`, `npm publish`, `gh release`, `kubectl apply`, `terraform apply`, `systemctl`, `launchctl`, `curl -X POST/PUT/DELETE`, `deploy`). For stages with `Manual verify: true`, add a manual approval gate with a comment. Before every gate, add a preview step that echoes the human-readable action.

5. **Validate commands** with `bash -n` before generating the workflow.

6. **Show a report** to the owner: stage count, gate count, manual verifies. HARD STOP — do not proceed without the owner's explicit go.

## Kickoff

Execute the normalized workflow:

1. **Pre-flight**: verify the `lobster` tool is available in the tools catalog.

2. **Show the normalize report** from the previous step. HARD STOP for the owner's go.

3. **Run the workflow** via:
   ```
   lobster action=run pipeline=<.lobster path> timeoutMs=3600000 maxStdoutBytes=2048000 flowControllerId=buildplan flowGoal="Execute <plan-name> build"
   ```

4. **Handle results**:
   - `status: ok` → all stages passed.
   - `status: error` → report the failure to the owner.
   - `status: needs_approval` → present the gate to the owner with preview context. On yes, resume via:
     ```
     lobster action=resume approvalId=<id> approve=true pipeline=<.lobster> timeoutMs=3600000 maxStdoutBytes=2048000
     ```
     Do NOT pass `flowControllerId`, `flowGoal`, or `flowStateJson` to resume.

5. **Report completion or failure** to the owner.

## Constraints

- **Description**: does not start with "lobster".
- **Slug**: `buildplan`.
- **No `run-build-stage.sh`** shipped or referenced.
- **No references** to Dru, Aaron, or workspace-specific paths. Use "the owner" and generic paths.
- **Cwd preservation**: Lobster cwd is lost on resume. Every plan action must use absolute paths. The normalize step resolves `__SKILL_DIR__` and bakes absolute paths into the generated `.lobster` so this is handled automatically.
