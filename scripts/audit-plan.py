#!/usr/bin/env python3
"""Audit a completed build plan: verify every stage has a valid marker.

Reads a prose build plan, computes the content hash for each stage's
action+verify, and checks that a matching marker file exists on disk.

Exit 0 if every stage has a verified marker.
Exit 1 if any marker is missing or the hash doesn't match.

No dependencies beyond Python 3. No Lobster, no executor. Safe for any
agent to run, including ephemeral subagents spawned purely for audit.
"""
import sys
import hashlib
import re
from pathlib import Path


def parse_stages(plan_path):
    """Return list of dicts: {id, action, verify, side_effect}."""
    with open(plan_path) as f:
        content = f.read()

    stages = []
    current = None
    for line in content.split('\n'):
        if line.startswith('### Stage '):
            if current is not None:
                stages.append(current)
            m = re.match(r'### Stage (\d+) (—|-) (.+)', line)
            if m:
                current = {
                    'id': int(m.group(1)),
                    'action': '',
                    'verify': '',
                }
            else:
                current = None
        elif current is not None:
            if line.startswith('Action:'):
                current['action'] = line.split(':', 1)[1].strip()
            elif line.startswith('Verify:'):
                current['verify'] = line.split(':', 1)[1].strip()

    if current is not None:
        stages.append(current)

    return stages


def check_stage(plan_dir, plan_key, stage):
    """Return (status, detail) for one stage.

    status: 'PASS', 'FAIL (no marker)', 'FAIL (hash mismatch)'
    """
    content_hash = hashlib.sha256(
        f"{stage['action']}\0{stage['verify']}".encode()
    ).hexdigest()[:12]

    marker_dir = plan_dir / '.buildplan-run' / plan_key
    expected = marker_dir / f'stage-{stage["id"]}.{content_hash}.ok'

    if expected.exists():
        return ('PASS', str(expected))
    else:
        # Check if any marker exists for this stage (maybe stale hash)
        any_marker = list(marker_dir.glob(f'stage-{stage["id"]}.*.ok'))
        if any_marker:
            return (
                'FAIL (hash mismatch)',
                f'found {any_marker[0].name}, expected stage-{stage["id"]}.{content_hash}.ok'
            )
        else:
            return ('FAIL (no marker)', 'no marker file found')


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 audit-plan.py <plan.md>")
        sys.exit(1)

    plan_path = Path(sys.argv[1]).resolve()
    if not plan_path.exists():
        print(f"FAIL: plan file not found: {plan_path}")
        sys.exit(1)

    stages = parse_stages(str(plan_path))
    if not stages:
        print("FAIL: no stages found in plan")
        sys.exit(1)

    plan_dir = plan_path.parent
    plan_key = plan_path.stem
    total = len(stages)
    passed = 0
    failed = []

    print(f"Auditing {total} stages for {plan_path.name}...\n")

    for stage in stages:
        status, detail = check_stage(plan_dir, plan_key, stage)
        if status == 'PASS':
            passed += 1
        else:
            failed.append((stage['id'], status, detail))
        print(f"  Stage {stage['id']}: {status}")

    print(f"\n{passed}/{total} stages verified")

    if failed:
        print("\nFailed stages:")
        for sid, status, detail in failed:
            print(f"  Stage {sid}: {detail}")
        sys.exit(1)
    else:
        print("All stages complete and verified.")
        sys.exit(0)


if __name__ == '__main__':
    main()