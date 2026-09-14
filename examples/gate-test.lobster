name: gate-test
steps:
  - id: before-gate
    command: echo "prep done"
  - id: gate
    command: echo "simulated side effect"
    approval: required
  - id: after-gate
    command: echo "post-gate ran"
    condition: $gate.approved