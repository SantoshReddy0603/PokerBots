"""Check the exact calculation-only artifact against the fetched opponent."""
from pathlib import Path
import json
import os
import secrets
import subprocess
import sys

root = Path('experiments/daily-1110')
manifest = root / 'exact-friend-seed.json'
with manifest.open('x') as f:
    json.dump({'validation': ['daily1110-exact-friend-' + secrets.token_hex(10)]}, f, indent=2)
cmd = [sys.executable, '-B', 'tools/evaluate.py', str(root / 'histogram.py'), str(root / 'friend-current.py'),
       '--engine-format', 'legs', '--manifest', str(manifest), '--split', 'validation',
       '--count', '1', '--jobs', '2', '--out', str(root / 'exact-friend.jsonl')]
with (root / 'exact-friend.stdout.txt').open('x') as out, (root / 'exact-friend.stderr.txt').open('x') as err:
    subprocess.run(cmd, stdout=out, stderr=err, check=True,
                   env=dict(os.environ, OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1'))
print('Exact artifact versus current friend: complete', flush=True)
