"""Promote the tested calculation-only change, rejecting workspace drift."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys

root = Path('experiments/daily-1110')
digest = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
provenance = json.loads((root / 'provenance.json').read_text())
for path, expected in provenance['sources'].items():
    assert digest(path) == expected, ('source drift', path)
assert digest('dist/bot.py') == provenance['baseline_sha256']
checks = [json.loads(line) for line in (root / 'histogram-checks.jsonl').read_text().splitlines()]
assert len(checks) == 8 and all(r['exit'] == 0 for r in checks)
stress = [json.loads(line) for line in (root / 'histogram-stress.jsonl').read_text().splitlines()]
assert len(stress) == 3 and stress[-1]['sha256'] == digest(root / 'histogram.py')
for row in stress[:2]:
    assert not row['forfeits']
    assert all(not leg['bots'][0]['notices'] and not leg['bots'][0]['diagnostics'] for leg in row['legs'])
timing = json.loads((root / 'histogram-timing.json').read_text())
assert all(row['savings_percent'] > 0 for row in timing.values())
sys.path.insert(0, str(Path('tools').resolve()))
from matrix import read
read(str(root / 'exact-friend.jsonl'))  # Complete current-opponent validation, regardless of wins.

for output, source in [('checkpoints/pre-daily-1110.py', 'dist/bot.py'),
                       ('checkpoints/pre-daily-1110.release.json', 'dist/release.json'),
                       ('checkpoints/daily-1110-histogram.py', str(root / 'histogram.py')),
                       (str(root / 'vector_equity-before.py'), 'src/vector_equity.py')]:
    with Path(output).open('xb') as f:
        f.write(Path(source).read_bytes())

source = Path('src/vector_equity.py')
raw = source.read_bytes()
before = b'    counts = (values[:, :, None] == ranks).sum(axis=1)'
newline = b'\r\n' if b'\r\n' in raw else b'\n'
after = newline.join([b'    # Count (row, rank) bins directly without a rows x cards x 13 boolean array.',
                      b'    bins = values + 13 * np.arange(len(cards))[:, None]',
                      b'    counts = np.bincount(bins.ravel(), minlength=13 * len(cards)).reshape(len(cards), 13)'])
assert raw.count(before) == 1
source.write_bytes(raw.replace(before, after))
subprocess.run([sys.executable, '-B', 'tools/build_submission.py', '--output', str(root / 'histogram-rebuild.py')], check=True)
assert (root / 'histogram-rebuild.py').read_bytes() == (root / 'histogram.py').read_bytes()
subprocess.run([sys.executable, '-B', 'tools/build_submission.py'], check=True)
assert digest('dist/bot.py') == digest(root / 'histogram.py')
note = ('Direct rank histograms replace the temporary rank-comparison tensor. '
        '16,536 rank rows and 60 full fixed-draw posterior cases exactly match the prior release; '
        'single-CPU warm median equity time improved 4.8-6.8% locally. '
        'Both full current-format stages passed one-CPU/1-GiB validation, eight check invocations passed. '
        'Fresh exact-artifact matches against the fetched teammate bot are separate from the river-order strategy screen. '
        'No stronger win-rate claim follows from a calculation-only change. See experiments/daily-1110/RESULTS.md.')
subprocess.run([sys.executable, '-B', 'tools/release_manifest.py',
                '--selected', 'checkpoints/daily-1110-histogram.py',
                '--fallback', 'checkpoints/pre-daily-1110.py',
                '--fallback-report', 'experiments/rules-update-1110/retained-stress.jsonl',
                '--report', str(root / 'histogram-stress.jsonl'),
                '--final-report', str(root / 'exact-friend.jsonl'), '--validation-note', note], check=True)
with (root / 'promotion.json').open('x') as f:
    json.dump(dict(artifact='dist/bot.py', sha256=digest('dist/bot.py'),
                   source_sha256=digest(source), fallback_sha256=provenance['baseline_sha256'],
                   policy_change=False, manifest_sha256=digest('dist/release.json')), f, indent=2)
print('Promoted exact validated calculation-only artifact', digest('dist/bot.py'))
