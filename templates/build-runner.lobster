name: build-runner
steps:
  stage-1:
    cmd: |
      python3 __SKILL_DIR__/scripts/execute-build-stage.py {{plan_path}} 1
    description: Execute stage 1 from build plan
    sideEffect: true

  stage-1-preview:
    cmd: echo "Stage 1 preview: {{action_stage_1}}"
    description: Preview action for stage 1
    condition: $step.stage-1.approved

  stage-2:
    cmd: |
      python3 __SKILL_DIR__/scripts/execute-build-stage.py {{plan_path}} 2
    description: Execute stage 2 from build plan
    sideEffect: true
    approval: required

  stage-2-preview:
    cmd: echo "Stage 2 preview: {{action_stage_2}}"
    description: Preview action for stage 2
    condition: $step.stage-2.approved

  stage-N:
    cmd: |
      python3 __SKILL_DIR__/scripts/execute-build-stage.py {{plan_path}} N
    description: Execute final stage N from build plan
    sideEffect: true
    approval: required

  post-gate:
    cmd: echo "All side-effect gates passed"
    description: Post-gate verification
    condition: $step.stage-N.approved

  complete:
    cmd: echo "Build plan completed successfully"
    condition: $step.post-gate.approved
