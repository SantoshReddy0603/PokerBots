from pathlib import Path
import json
root=Path('experiments/loss-improvement-1110')
scores=json.loads((root/'screen-summary.json').read_text())
base=scores['baseline']
eligible=[]
for name,row in scores.items():
    if name=='baseline':
        continue
    if row['wdl'][0]<=base['wdl'][0] or min(row['stage_differences'].values())<0:
        continue
    if any(row['by_opponent'][opp][0]<=wins[0]-2 for opp,wins in base['by_opponent'].items()):
        continue
    if row['forfeits'] or row['notices'] or row['diagnostics']:
        continue
    eligible.append(name)
best=max(eligible,key=lambda n:scores[n]['wdl'][0]) if eligible else None
assert best=='selective'
with (root/'selection.json').open('x') as f:
    json.dump(dict(eligible=eligible,selected_for_confirmation=best,screen_wins=scores[best]['wdl'][0],
                   baseline_screen_wins=base['wdl'][0],promotion=False,
                   note='Highest points under declared screen gates. No confirmation scores inspected.'),f,indent=2)
print(best)
