# Smoke Test Build Plan

A minimal 3-stage plan to verify the buildplan system.

### Stage 1 — Write test file
Action: bash -c 'echo "buildplan-v1-test" > /tmp/buildplan-smoke-test.txt'
Verify: bash -c 'test -f /tmp/buildplan-smoke-test.txt && cat /tmp/buildplan-smoke-test.txt | grep -q "buildplan-v1-test"'
Side effect: false

### Stage 2 — Verify content
Action: bash -c 'cat /tmp/buildplan-smoke-test.txt'
Verify: bash -c 'cat /tmp/buildplan-smoke-test.txt | grep -q "buildplan-v1-test"'
Side effect: false

### Stage 3 — Cleanup
Action: bash -c 'rm /tmp/buildplan-smoke-test.txt'
Verify: bash -c 'test ! -f /tmp/buildplan-smoke-test.txt'
Side effect: true
