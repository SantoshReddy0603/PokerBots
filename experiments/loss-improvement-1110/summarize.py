"""Strict complete-matrix comparisons; never select on partial results."""
from pathlib import Path
from random import Random
from statistics import mean
import json
import subprocess
import sys

sys.path.insert(0,str(Path('tools').resolve()))
from matrix import read
root = Path('experiments/loss-improvement-1110')
phase = sys.argv[1]
names = sys.argv[2:] or ['baseline','selective','response','combined']
assert 'baseline' in names
all_rows = {}
metas = {}
results = {}
for name in names:
    meta, rows = read(str(root/(phase+'-'+name+'.jsonl')))
    metas[name], all_rows[name] = meta,rows
    values = list(rows.values())
    results[name] = dict(wdl=[sum(r['candidate_points']==p for r in values) for p in (1,.5,0)],
                         by_stage={str(stage):[sum(r['candidate_points']==p for r in values if r['stage']==stage) for p in (1,.5,0)] for stage in (1,2)},
                         by_opponent={opp:[sum(r['candidate_points']==p for r in values if r['opponent']==opp) for p in (1,.5,0)] for opp in meta['opponents']},
                         forfeits=sum(bool(r['forfeits']) for r in values),
                         notices=sum(r['bots'][int(r['reverse'])]['notices'] for r in values),
                         diagnostics=sum(r['bots'][int(r['reverse'])]['diagnostics'] for r in values),
                         max_leg_bank_s=max(leg['bots'][int(r['reverse'])]['bank_s'] for r in values for leg in r['legs']))
for name in names:
    if name=='baseline':
        continue
    command=[sys.executable,'-B','tools/compare.py',str(root/(phase+'-'+name+'.jsonl')),str(root/(phase+'-baseline.jsonl'))]
    comparison=subprocess.run(command,capture_output=True,text=True,check=True)
    with (root/(phase+'-'+name+'-comparison.txt')).open('x') as f:
        f.write(comparison.stdout)
    a,b=all_rows[name],all_rows['baseline']
    blocks=[mean(a[k]['candidate_points']-b[k]['candidate_points'] for k in a if k[1]==seed) for seed in metas[name]['seeds']]
    rng=Random(111026)
    boot=sorted(mean(rng.choices(blocks,k=len(blocks))) for _ in range(10000))
    results[name]['paired_points']=mean(blocks)
    results[name]['point_blocks']=blocks
    results[name]['point_interval']=[boot[250],boot[9749]]
    results[name]['stage_differences']={str(stage):mean(a[k]['candidate_points']-b[k]['candidate_points'] for k in a if k[0]==stage) for stage in (1,2)}
with (root/(phase+'-summary.json')).open('x') as f:
    json.dump(results,f,indent=2)
print(json.dumps(results,indent=2))
