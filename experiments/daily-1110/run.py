"""Run both artifacts with identical current-format match configurations."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import os
import subprocess
import sys

root = Path('experiments/daily-1110')
phase = sys.argv[1] if len(sys.argv) > 1 else 'screen'
assert phase in ('screen', 'confirmation')
pool = [str(root / 'friend-current.py'), 'opponents/league/confirmation/trap.py',
        'opponents/league/confirmation/pressure.py', 'experiments/review-fixes-1109/tight_reraise.py']
env = dict(os.environ, OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1')

def run(name):
    cmd = [sys.executable, '-B', 'tools/evaluate.py', str(root / (name + '.py')), *pool,
           '--engine-format', 'legs', '--manifest', str(root / 'seeds.json'),
           '--split', phase, '--count', '2' if phase == 'screen' else '4',
           '--jobs', '2', '--out', str(root / (phase + '-' + name + '.jsonl'))]
    with (root / (phase + '-' + name + '.stdout.txt')).open('x') as out, \
         (root / (phase + '-' + name + '.stderr.txt')).open('x') as err:
        subprocess.run(cmd, stdout=out, stderr=err, check=True, env=env)
    print(name, phase, 'complete', flush=True)

with ThreadPoolExecutor(2) as executor:
    list(executor.map(run, ['baseline', 'river-order']))
