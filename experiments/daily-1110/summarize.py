from pathlib import Path
from statistics import mean
import json
import subprocess
import sys

sys.path.insert(0, str(Path('tools').resolve()))
from matrix import read

root = Path('experiments/daily-1110')
phase = sys.argv[1] if len(sys.argv) > 1 else 'screen'
assert phase in ('screen', 'confirmation')
paths = [root / (phase + '-' + name + '.jsonl') for name in ('river-order', 'baseline')]
comparison = subprocess.run([sys.executable, '-B', 'tools/compare.py', *map(str, paths)],
                            check=True, capture_output=True, text=True)
with (root / (phase + '-comparison.txt')).open('x') as f:
    f.write(comparison.stdout)

def summary(path):
    meta, indexed = read(str(path))
    rows = list(indexed.values())
    points = [r['candidate_points'] for r in rows]
    return dict(sha256=meta['candidate_sha256'], wins=points.count(1), draws=points.count(.5), losses=points.count(0),
                by_opponent={opp: [sum(r['candidate_points'] == p for r in rows if r['opponent'] == opp)
                                   for p in (1, .5, 0)] for opp in meta['opponents']},
                by_stage={stage: dict(wdl=[sum(r['candidate_points'] == p for r in rows if r['stage'] == stage)
                                          for p in (1, .5, 0)],
                                     raw_chips_per_hand=mean(r['candidate_net'] / r['played'] for r in rows if r['stage'] == stage))
                          for stage in (1, 2)},
                forfeits=sum(bool(r['forfeits']) for r in rows),
                notices=sum(r['bots'][int(r['reverse'])]['notices'] for r in rows),
                diagnostics=sum(r['bots'][int(r['reverse'])]['diagnostics'] for r in rows),
                max_leg_bank_s=max(leg['bots'][int(r['reverse'])]['bank_s'] for r in rows for leg in r['legs']))

result = {name: summary(root / (phase + '-' + name + '.jsonl')) for name in ('baseline', 'river-order')}
if (root / 'exact-friend.jsonl').exists():
    result['exact-friend'] = summary(root / 'exact-friend.jsonl')
with (root / (phase + '-summary.json')).open('x') as f:
    json.dump(result, f, indent=2)
print(json.dumps(result, indent=2))
