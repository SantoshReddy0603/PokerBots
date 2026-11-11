"""Validate and report this frozen current-teammate head-to-head study."""
import hashlib
import json
from pathlib import Path
from random import Random
from statistics import mean
import sys

sys.path.insert(0, str(Path('tools').resolve()))
from matrix import read, digest

root = Path('experiments/improved-teammate-match-1110')
meta, matrix = read(root/'results.jsonl')
rows = list(matrix.values())
provenance = json.loads((root/'provenance.json').read_text())
assert digest(root/'ours.py') == provenance['ours_sha256'] == meta['candidate_sha256']
assert digest(root/'teammate.py') == provenance['teammate_sha256']
assert all(digest(p) == h for p,h in meta['harness'].items())
assert all(digest(p) == h for p,h in meta['opponents'].items())

def stats(group):
    return dict(matches=len(group), wins=sum(r['candidate_points']==1 for r in group),
                draws=sum(r['candidate_points']==.5 for r in group),
                losses=sum(r['candidate_points']==0 for r in group),
                net_chips=sum(r['candidate_net'] for r in group),
                capped_chips=sum(r['candidate_delta'] for r in group),
                forfeits=sum(bool(r['forfeits']) for r in group))

summary = dict(provenance=provenance, overall=stats(rows), stages={},
               seed_blocks=len(meta['seeds']), summed_match_wall_s=sum(r['wall_s'] for r in rows))
for stage in (1,2):
    group = [r for r in rows if r['stage']==stage]
    result = stats(group)
    for index,name in ((0,'ours'),(1,'teammate')):
        bots = [leg['bots'][int(r['reverse']) if index==0 else 1-int(r['reverse'])]
                for r in group for leg in r['legs']]
        result[name+'_resources'] = dict(max_leg_bank_s=max(b['bank_s'] for b in bots),
                                       max_reply_ms=max(b['max_ms'] for b in bots),
                                       notices=sum(b['notices'] for b in bots),
                                       diagnostics=sum(b['diagnostics'] for b in bots))
    summary['stages'][stage] = result
blocks = [mean(r['candidate_points'] for r in rows if r['seed']==seed) for seed in meta['seeds']]
rng = Random(111076)
draws = sorted(mean(rng.choices(blocks,k=len(blocks))) for _ in range(10000))
summary['points_per_seed_block'] = blocks
summary['conditional_seed_bootstrap_95'] = [draws[250],draws[9749]]
summary['warning'] = 'Four independent seed blocks, one opponent and time-adaptive play; this is not a hackathon win-probability estimate. Matrix used official clocks but no hard CPU/RAM sandbox.'
with (root/'summary.json').open('x',encoding='utf8') as f: json.dump(summary,f,indent=2)
lines = ['# Improved bot versus latest teammate: 10 November 2026','',
         'Frozen repository commit: `'+provenance['commit']+'`.',
         'Our SHA-256: `'+provenance['ours_sha256']+'`.',
         'Teammate SHA-256: `'+provenance['teammate_sha256']+'`.','',
         'Both updated competition stages, two fresh-process legs per match, four fresh seed blocks and both assignments. Linux CPython 3.11.9, jobs=2, BLAS threads=1. Official time banks/startup grace enabled; no hard CPU/RAM sandbox in this matrix. No playing code changed.','',
         '| Stage | Our wins | Draws | Teammate wins | Our net chips |',
         '|---|---:|---:|---:|---:|']
for stage,result in summary['stages'].items():
    lines.append(f"| {stage} ({400 if stage==1 else 1000} hands) | {result['wins']} | {result['draws']} | {result['losses']} | {result['net_chips']:+,} |")
s=summary['overall'];lines += [f"| **Total** | **{s['wins']}** | **{s['draws']}** | **{s['losses']}** | **{s['net_chips']:+,}** |",'',
    '## Match results','', '| Stage | Seed | Assignment reversed | Our net chips | Our match points | Forfeit |','|---|---|---|---:|---:|---|']
for row in sorted(rows,key=lambda r:(r['stage'],r['seed'],r['reverse'])):
    lines.append(f"| {row['stage']} | {row['seed']} | {row['reverse']} | {row['candidate_net']:+d} | {row['candidate_points']} | {row['forfeits']} |")
lines += ['', '## Runtime, failures and uncertainty','', '```json',json.dumps(summary,indent=2),'```','',
          'Complete matrix validation passed. Exact command: command.json. Immutable bot/harness hashes and configuration: results.meta.json. Raw per-leg metrics and outcomes: results.jsonl. Use a new output directory to repeat; existing results are never overwritten.',
          '', summary['warning']]
with (root/'RESULTS.md').open('x',encoding='utf8') as f:f.write('\n'.join(lines)+'\n')
print(json.dumps(summary,indent=2))

