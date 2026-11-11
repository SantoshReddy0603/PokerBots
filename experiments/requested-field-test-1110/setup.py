"""Freeze the selected artifact and a fresh, declared six-opponent matrix."""
from pathlib import Path
import hashlib
import json
import secrets

root = Path('experiments/requested-field-test-1110')
digest = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
sources = {'our-bot.py': 'dist/bot.py',
           'friend.py': 'experiments/daily-1110/friend-current.py',
           **{name + '.py': 'opponents/league/confirmation/' + name + '.py'
              for name in ('trap', 'pressure', 'tightjam', 'range', 'polar')}}
manifest = json.loads(Path('dist/release.json').read_text())
assert digest('dist/bot.py') == manifest['sha256']
for name, path in sources.items():
    with (root / name).open('xb') as f:
        f.write(Path(path).read_bytes())
with (root / 'seeds.json').open('x') as f:
    json.dump({'requested_test': ['requested1110-' + secrets.token_hex(12) for _ in range(4)]}, f, indent=2)
with (root / 'plan.json').open('x') as f:
    json.dump(dict(matches=96, opponents=6, blocks=4, assignments=2, stages=[400,1000],
                   legs_per_match=2, clocks='official per-leg banks enabled',
                   python='Linux CPython 3.11.9', numpy='2.2.6', concurrency=4,
                   source_sha256={p: digest(p) for p in sources.values()},
                   frozen_sha256={name: digest(root / name) for name in sources},
                   friend_git_blob='a5c8b01162763bb9c67051a5a625eb06607baf5a',
                   friend_checked='GitHub connector fetched current main/bot.py again before this test; unchanged.',
                   environment={key:'1' for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS')},
                   purpose='Measure the exact current release; no strategy selection or tuning during the run.'), f, indent=2)
print('Frozen 96-match test plan and seven exact bot files')
