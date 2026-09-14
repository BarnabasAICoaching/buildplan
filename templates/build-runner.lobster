name: build-runner
description: Execute a prose build plan via Lobster with managed Task Flow
args:
  plan_path:
    type: string
    description: Absolute path to the prose build plan markdown file
steps:
  - id: stage-1
    command: python3 __SKILL_DIR__/scripts/execute-build-stage.py "${args.plan_path}" 1

  - id: stage-2
    command: python3 __SKILL_DIR__/scripts/execute-build-stage.py "${args.plan_path}" 2

  - id: preview-3
    command: echo "Side effect stage: see plan for action details"

  - id: stage-3
    command: python3 __SKILL_DIR__/scripts/execute-build-stage.py "${args.plan_path}" 3
    approval: required

  - id: stage-4
    command: python3 __SKILL_DIR__/scripts/execute-build-stage.py "${args.plan_path}" 4
    condition: $stage-3.approved

  - id: complete
    command: echo "Build complete: all stages passed."
    condition: $stage-3.approved