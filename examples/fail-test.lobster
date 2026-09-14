name: fail-test
steps:
  - id: first
    command: echo "step 1 ran" && false
  - id: second
    command: echo "step 2 ran"