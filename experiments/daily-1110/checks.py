from pathlib import Path
import json
import os
import subprocess
import sys
import time

root = Path('experiments/daily-1110')
name = sys.argv[1] if len(sys.argv) > 1 else 'river-order'
assert name in ('river-order', 'histogram')
bot = str(root / (name + '.py'))
prefix = '' if name == 'river-order' else name + '-'
env = dict(os.environ, OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1')
commands = [[sys.executable, '-B', 'tests/' + name + '.py', bot]
            for name in ('protocol', 'selection', 'evaluator', 'learning', 'review_decisions', 'leg_compatibility')]
commands += [[sys.executable, '-S', '-B', 'tests/protocol.py', bot],
             [sys.executable, '-B', 'tools/audit_submission.py', bot, '--out', str(root / (prefix + 'audit.json'))]]
with (root / (prefix + 'checks.jsonl')).open('x') as output:
    for command in commands:
        start = time.perf_counter()
        result = subprocess.run(command, capture_output=True, text=True, env=env)
        row = dict(command=command, exit=result.returncode, elapsed_s=time.perf_counter() - start,
                   stdout=result.stdout, stderr=result.stderr)
        output.write(json.dumps(row) + '\n')
        output.flush()
        print(command[-2:], result.returncode, flush=True)
        if result.returncode:
            raise SystemExit(result.returncode)
