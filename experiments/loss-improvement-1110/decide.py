"""Evaluate frozen confirmation and supplementary regression gates."""
from pathlib import Path
import hashlib
import json
root=Path('experiments/loss-improvement-1110')
confirmation=json.loads((root/'confirmation-summary.json').read_text())
regression=json.loads((root/'regression-summary.json').read_text())
checks={}
for phase,scores in [('confirmation',confirmation),('regression',regression)]:
    a,b=scores['selective'],scores['baseline']
    checks[phase+'_points']=a['paired_points']>0 if phase=='confirmation' else a['paired_points']>=0
    checks[phase+'_stages']=min(a['stage_differences'].values())>=0
    checks[phase+'_matchups']=all(a['by_opponent'][opp][0]>row[0]-2 for opp,row in b['by_opponent'].items())
    checks[phase+'_failures']=not (a['forfeits'] or a['notices'] or a['diagnostics'])
checks['confirmation_block_support']=confirmation['selective']['point_interval'][0]>0
champion=regression['selective']['by_opponent'][str(root/'baseline.py')]
checks['champion_points']=champion[0]+.5*champion[1]>=sum(champion)/2
stress=[json.loads(line) for line in (root/'selective-stress.jsonl').read_text().splitlines()]
digest=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
checks['stress_exact_bytes']=len(stress)==3 and stress[-1]['sha256']==digest(root/'selective.py')
checks['stress_failures']=all(not r['forfeits'] and not r['bots'][0]['notices'] and not r['bots'][0]['diagnostics'] for r in stress[:2])
checks['stress_banks']=all(leg['bots'][0]['bank_s']<{1:21,2:52.5}[r['stage']] for r in stress[:2] for leg in r['legs'])
test_rows=[json.loads(line) for line in (root/'checks.jsonl').read_text().splitlines()]
checks['correctness']=len(test_rows)==20 and all(r['exit']==0 for r in test_rows)
checks['audit']=json.loads((root/'selective-audit.json').read_text())['sha256']==digest(root/'selective.py')
checks['no_site_legs']='passed' in (root/'selective-no-site.txt').read_text()
checks['baseline_preserved']=digest('dist/bot.py')==digest(root/'baseline.py')
decision=dict(checks=checks,promote=all(checks.values()),selected='selective' if all(checks.values()) else 'baseline',
               caveat='Finite local tests do not guarantee no true regression or wins against every opponent. Four confirmation blocks limit uncertainty.')
with (root/'decision.json').open('x') as f:
    json.dump(decision,f,indent=2)
print(json.dumps(decision,indent=2))
