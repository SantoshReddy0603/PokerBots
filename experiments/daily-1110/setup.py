"""Freeze one isolated study without touching the selected release."""
from pathlib import Path
import hashlib
import json
import secrets
import subprocess
import sys

root = Path('experiments/daily-1110')
sources = ['src/learning_protocol.py', 'src/poker.py', 'src/preflop_key.py',
           'src/preflop_table.py', 'src/friend_ranges.py', 'src/learning.py',
           'src/vector_equity.py', 'src/river_order_equity.py', 'src/learning_policy.py']
output = root / 'river-order.py'
body = '\n\n'.join(Path(p).read_text(encoding='utf-8-sig').strip() for p in sources)
body += '\n\nif __name__ == "__main__":\n    main()\n'
compile(body, str(output), 'exec')
with output.open('xb') as f:
    f.write(body.encode())
with (root / 'baseline.py').open('xb') as f:
    f.write(Path('dist/bot.py').read_bytes())
digest = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
with (root / 'provenance.json').open('x') as f:
    json.dump(dict(sources={p: digest(p) for p in sources},
                   candidate_sha256=digest(output), baseline_sha256=digest('dist/bot.py'),
                   friend_sha256=digest(root / 'friend-current.py'),
                   friend_git_blob='a5c8b01162763bb9c67051a5a625eb06607baf5a',
                   friend_url='https://github.com/sricharanreddycheruku/pokerbots-discard-holdem/blob/main/bot.py',
                   hypothesis='Exact river ordering improves range and continuation selection; no nonriver change.',
                   promotion='Fresh positive paired match points with convincing block support, no severe matchup regression, then constrained validation. Otherwise retain release.',
                   environment={'OPENBLAS_NUM_THREADS': '1', 'OMP_NUM_THREADS': '1', 'MKL_NUM_THREADS': '1'}), f, indent=2)
with (root / 'seeds.json').open('x') as f:
    json.dump({phase: ['daily1110-' + phase + '-' + secrets.token_hex(10) for _ in range(count)]
               for phase, count in [('screen', 2), ('confirmation', 4)]}, f, indent=2)
print('Frozen baseline, candidate, provenance and screen/untouched confirmation seeds')
