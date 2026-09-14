name: test-workflow
steps:
  stage-1:
    cmd: python3 /Users/apollo/.openclaw/workspace/buildplan/scripts/execute-build-stage.py /Users/apollo/.openclaw/workspace/buildplan/examples/smoke-test.md 1
    description: Execute stage 1
    sideEffect: true
  stage-2:
    cmd: python3 /Users/apollo/.openclaw/workspace/buildplan/scripts/execute-build-stage.py /Users/apollo/.openclaw/workspace/buildplan/examples/smoke-test.md 2
    description: Execute stage 2
    sideEffect: true
  complete:
    cmd: echo "done"
    condition: $step.stage-2.approved
