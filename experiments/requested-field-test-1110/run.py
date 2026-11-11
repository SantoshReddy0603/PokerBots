from pathlib import Path
import os
import subprocess
import sys
import json

root = Path('experiments/requested-field-test-1110')
cmd = [sys.executable, '-B', 'tools/evaluate.py', str(root / 'our-bot.py'),
       *[str(root / (name + '.py')) for name in ('friend','trap','pressure','tightjam','range','polar')],
       '--manifest', str(root / 'seeds.json'), '--split', 'requested_test', '--count', '4',
       '--jobs', '4', '--engine-format', 'legs', '--out', str(root / 'results.jsonl')]
with (root / 'command.json').open('x') as f:
    json.dump(cmd, f, indent=2)
with (root / 'stdout.txt').open('x') as stdout, (root / 'stderr.txt').open('x') as stderr:
    result = subprocess.run(cmd, stdout=stdout, stderr=stderr,
                            env=dict(os.environ, OPENBLAS_NUM_THREADS='1',
                                     OMP_NUM_THREADS='1', MKL_NUM_THREADS='1'))
print('Full matrix process exit:', result.returncode, flush=True)
raise SystemExit(result.returncode)
