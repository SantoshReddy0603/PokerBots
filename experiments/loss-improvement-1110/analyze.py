"""Offline trace analysis; shown cards are never fed back into the live bot."""
from collections import Counter, defaultdict
from pathlib import Path
import json
import runpy
import sys

root = Path('experiments/loss-improvement-1110')
bot = runpy.run_path(str(root / 'baseline.py'))
hands = []
replays = []
for folder in sorted((root / 'replays').glob('*')):
    if not (folder / 'result.json').exists():
        continue
    result = json.loads((folder / 'result.json').read_text())
    replays.append(dict(folder=folder.name,original_net=result['original_net'],replay_net=result['candidate_net']))
    for trace in sorted(folder.glob('trace-*.jsonl')):
        current = None
        for line in trace.read_text().splitlines():
            record = json.loads(line)
            if 'decision' in record and current is not None:
                current['decisions'].append(record['decision'])
            elif 'input' in record:
                msg = record['input']
                if msg['type'] == 'new_hand':
                    current = dict(replay=folder.name, trace=trace.name, hand=msg['hand_id'],
                                   initial_hole=msg['hole_cards'],seat=msg['seat'],decisions=[])
                elif msg['type'] == 'hand_result' and current is not None:
                    current['result'] = msg
                    hands.append(current)
                    current = None

groups = defaultdict(lambda:dict(hands=0, net=0, wins=0, losses=0))
calls = []
raises = []
examples = []
for hand in hands:
    r = hand['result']
    net = r['net']
    key = 'showdown' if r['result'] == 'showdown' else 'nonshowdown'
    pre = any(e['street']=='preflop' and e['actor']=='me' and e.get('amount',0)>=20 for e in r['history'])
    allin = 'no_allin'
    for d in hand['decisions']:
        req, chosen = d['req'], d['chosen']
        if (chosen[0]=='call' and req['to_call']>=req['my_stack']) or (chosen[0]=='raise' and chosen[1]-req['my_bet']>=req['my_stack']):
            allin = 'allin_' + req['street']
            break
    for name in (key, 'preflop_20plus' if pre else 'preflop_under20', allin):
        g = groups[name]
        g['hands'] += 1
        g['net'] += net
        g['wins'] += net > 0
        g['losses'] += net < 0
    for d in hand['decisions']:
        req, chosen = d['req'], d['chosen']
        if req['street']=='preflop':
            table = bot['PREFLOP_EQUITY'][bot['preflop_key'](tuple(d['hole']))]
            cells = {tuple(k):v for k,v in d['model']}
            wins,count = cells.get(('preflop','raise'), (0,0))
            aggression = (wins+16*.30)/(count+16)
            uniform,premium = (x/1000 for x in table)
            d['preflop_equity'] = uniform + min(.8,max(0.,.65-aggression))*(premium-uniform)
            d['preflop_aggression'] = aggression
        if chosen[0]=='call' and req['to_call']>=20:
            calls.append(dict(street=req['street'],cost=req['to_call'],net=net,
                               eq=max(d['values']) if d['values'] else d.get('preflop_equity'),
                               odds=req['to_call']/(req['pot']+req['to_call'])))
        if chosen[0]=='raise' and req['street']!='preflop':
            choices = {tuple(k):v for k,v in d['choices']}
            passive = max((v for k,v in choices.items() if k[0]!='raise'), default=0)
            best = choices.get(tuple(chosen),0)
            raises.append(dict(street=req['street'],cost=chosen[1]-req['my_bet'],net=net,
                                equity=max(d['values']) if d['values'] else None, edge=best-passive,
                                facing=req['to_call']>0))
    if abs(net)>=100:
        examples.append(hand)

def aggregate(rows, fields):
    out = defaultdict(lambda:dict(count=0, net=0,cost=0,mean_equity=0))
    for row in rows:
        key = '|'.join(str(row[f]) for f in fields)
        g = out[key]
        g['count'] += 1
        g['net'] += row['net']
        g['cost'] += row['cost']
        g['mean_equity'] += row.get('equity', row.get('eq')) or 0
    for g in out.values():
        g['mean_equity'] /= g['count']
    return dict(out)
summary = dict(replays=replays, hands=len(hands), groups=dict(groups),
                expensive_calls=aggregate(calls,['street']),
                postflop_raises=aggregate(raises,['street','facing']),
                small_edge_expensive_raises=aggregate([r for r in raises if r['cost']>=20 and r['edge']<.1*r['cost']],['street']),
                note='Decision-level net columns repeat final hand net and are diagnostics, not additive causal losses. Showdown selection and runouts bias retrospective calibration.')
tag = sys.argv[1] if len(sys.argv)>1 else 'analysis'
with (root / (tag+'.json')).open('x') as f:
    json.dump(summary,f,indent=2)
with (root / (tag+'-examples.json')).open('x') as f:
    json.dump(sorted(examples,key=lambda h:h['result']['net'])[:80],f,indent=2)
print(json.dumps(summary,indent=2))
