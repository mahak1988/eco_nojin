#!/usr/bin/env python3
"""Check mutation score from mutmut results."""

import subprocess
import sys

result = subprocess.run(
    ['mutmut', 'results', '--dict-class=mutmut.trampoline.Dict'],
    capture_output=True,
    text=True
)

print(result.stdout)

if 'killed:' in result.stdout and 'survived:' in result.stdout:
    lines = result.stdout.strip().split('\n')
    for line in lines:
        if 'killed:' in line:
            parts = line.split()
            killed = int(parts[1])
            survived = int(parts[3])
            total = killed + survived
            score = (killed / total * 100) if total > 0 else 0
            print(f'Mutation score: {score:.1f}%')
            if score < 70:
                print(f'::error::Mutation score {score:.1f}% below threshold 70%')
                sys.exit(1)
            else:
                print(f'Mutation score {score:.1f}% meets threshold 70%')
                sys.exit(0)

print('Could not parse mutation results')
sys.exit(1)