"""Hindsight-only exact runouts for expensive calls against shown holdings."""
from collections import defaultdict
from itertools import combinations
from pathlib import Path
import json
import runpy
import sys

root = Path('experiments/loss-improvement-1110')
b = runpy.run_path(str(root/'baseline.py'))
np = b['np']
summaries = defaultdict(list)
examples = []
terminal_turn_calls = []
badbeat_examples = []
for folder in sorted((root/'replays').glob('*')):
    if not (folder/'result.json').exists():
        continue
    for trace in folder.glob('trace-*.jsonl'):
        initial = None
        decisions = []
        for line in trace.read_text().splitlines():
            record = json.loads(line)
            if 'decision' in record:
                decisions.append(record['decision'])
                continue
            m = record['input']
            if m['type']=='new_hand':
                initial = m
                decisions = []
            elif m['type']=='hand_result' and m['result']=='showdown':
                hero = tuple(b['CARD_ID'][c] for c in m['my_hole_cards'])
                opp = tuple(b['CARD_ID'][c] for c in m['opp_hole_cards'])
                known = set(hero+opp+tuple(b['CARD_ID'][c] for c in initial['hole_cards']))
                if m.get('opp_discard'):
                    known.add(b['CARD_ID'][m['opp_discard']])
                for d in decisions:
                    req = d['req']
                    if d['chosen'][0]!='call' or req['to_call']<20 or not d['values']:
                        continue
                    board = tuple(b['CARD_ID'][c] for c in req['board'])
                    unseen = [c for c in range(52) if c not in known and c not in board]
                    runouts = list(combinations(unseen,5-len(board)))
                    full = np.asarray([board+r for r in runouts])
                    mine = b['batch_rank'](np.concatenate((np.broadcast_to(hero,(len(full),2)),full),axis=1))
                    theirs = b['batch_rank'](np.concatenate((np.broadcast_to(opp,(len(full),2)),full),axis=1))
                    actual = float(np.mean((mine>theirs)+.5*(mine==theirs)))
                    estimated = max(d['values'])
                    terminal = req['opp_stack']==0 or req['to_call']>=req['my_stack'] or req['street']=='river'
                    if terminal and req['street']=='turn':
                        conditional_ev = actual * (req['pot'] + req['to_call']) - req['to_call']
                        terminal_turn_calls.append(dict(net=m['net'],conditional_call_ev=conditional_ev))
                        if conditional_ev>0 and m['net']<0 and len(badbeat_examples)<3:
                            badbeat_examples.append(dict(folder=folder.name,hand=m['hand_id'],hero=m['my_hole_cards'],
                                                         opponent=m['opp_hole_cards'],visible_board=req['board'],
                                                         estimated=estimated,known_holding_equity=actual,
                                                         cost=req['to_call'],pot=req['pot'],net=m['net']))
                    key = req['street']+'|'+('terminal' if terminal else 'nonterminal')
                    summaries[key].append((estimated,actual,req['to_call']))
                    if estimated-actual>.35 and m['net']<=-100 and len(examples)<12:
                        examples.append(dict(folder=folder.name,hand=m['hand_id'],street=req['street'],
                                             hero=m['my_hole_cards'],opponent=m['opp_hole_cards'],visible_board=req['board'],
                                             call=req['to_call'],pot=req['pot'],estimated=estimated,
                                             known_holding_equity=actual,net=m['net'],terminal=terminal))
summary = {k:dict(calls=len(v),mean_estimated=sum(x[0] for x in v)/len(v),
                  mean_known_holding=sum(x[1] for x in v)/len(v),total_call=sum(x[2] for x in v)) for k,v in summaries.items()}
tag = sys.argv[1] if len(sys.argv)>1 else 'known-hand'
with (root/(tag+'.json')).open('x') as f:
    json.dump(dict(groups=summary,examples=examples,badbeat_examples=badbeat_examples,
                   terminal_turn_classification=dict(calls=len(terminal_turn_calls),
                       negative_holding_ev=sum(r['conditional_call_ev']<0 for r in terminal_turn_calls),
                       positive_holding_ev=sum(r['conditional_call_ev']>=0 for r in terminal_turn_calls),
                       lost_despite_positive_holding_ev=sum(r['conditional_call_ev']>=0 and r['net']<0 for r in terminal_turn_calls)),
                   note='Conditional on eventually shown holdings and actual retained pairs/discards. Selection bias; not an unbiased opponent-range equity estimate or a causal accounting of losses.'),f,indent=2)
print(json.dumps(summary,indent=2))
