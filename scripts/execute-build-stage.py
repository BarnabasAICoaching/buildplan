#!/usr/bin/env python3
"""Execute a stage from a build plan markdown file and report PASS/FAIL/SKIP.

Idempotent: a passed stage writes a content-hashed marker next to the plan file.
On re-run, an existing matching marker prints SKIP and exits 0 without re-executing.
"""
import subprocess
import sys
import re
import hashlib
from pathlib import Path

plan_path = sys.argv[1]
stage_id = int(sys.argv[2])

# Parse plan first (needed for hash before marker check)
with open(plan_path) as f:
    content = f.read()

# Parse stages
stages = []
current = {}
for line in content.split('\n'):
    if line.startswith('### Stage '):
        if current:
            stages.append(current)
        m = re.match(r'### Stage (\d+) (—|-) (.+)', line)
        current = {'id': int(m.group(1)), 'title': m.group(2), 'action': '', 'verify': ''}
    elif line.startswith('Action:'):
        current['action'] = line.split(':', 1)[1].strip()
    elif line.startswith('Verify:'):
        current['verify'] = line.split(':', 1)[1].strip()

if current:
    stages.append(current)

stage = next((s for s in stages if s['id'] == stage_id), None)
if not stage:
    print(f"FAIL: stage {stage_id} not found")
    sys.exit(1)

# Marker anchored to plan location (not cwd) with content hash
action = stage.get('action', '')
verify = stage.get('verify', '')
content_hash = hashlib.sha256(f"{action}\0{verify}".encode()).hexdigest()[:12]
MARKER_DIR = Path(plan_path).resolve().parent / '.buildplan-run'
plan_key = Path(plan_path).stem
marker = MARKER_DIR / plan_key / f'stage-{stage_id}.{content_hash}.ok'

if marker.exists():
    print(f'SKIP: stage {stage_id} (already passed)')
    sys.exit(0)

# Run action if present and not "(none)"
if action and action != '(none)':
    r = subprocess.run(['bash', '-c', action], capture_output=True, text=True)
    if r.returncode != 0:
        print(f"FAIL: stage {stage_id} action exited {r.returncode}")
        if r.stderr:
            print(r.stderr[:200])
        sys.exit(r.returncode)

# Run verify if present and not "(none)"
if verify and verify != '(none)':
    r = subprocess.run(['bash', '-c', verify], capture_output=True, text=True)
    if r.returncode != 0:
        print(f"FAIL: stage {stage_id} verify: {r.stderr[:200] if r.stderr else r.stdout[:200]}")
        sys.exit(r.returncode)

# Mark passed
marker.parent.mkdir(parents=True, exist_ok=True)
marker.write_text('ok')
print(f"PASS: stage {stage_id}")
sys.exit(0)
