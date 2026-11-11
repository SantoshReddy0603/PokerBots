"""Diagnostic current-format replays. Trace code never enters a submission."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import hashlib
import json
import os
import sys

sys.path.insert(0, str(Path('tools').resolve()))
from benchmark_legs import match

root = Path('experiments/loss-improvement-1110')
root.mkdir(exist_ok=True)
baseline = root / 'baseline.py'
with baseline.open('xb') as f:
    f.write(Path('dist/bot.py').read_bytes())
with (root / 'baseline.release.json').open('xb') as f:
    f.write(Path('dist/release.json').read_bytes())
source = baseline.read_text()
needle = '    return max(choices, key=choices.get)'
assert source.count(needle) == 1
instrumented = root / 'instrumented.py'
with instrumented.open('x') as f:
    f.write(source.replace(needle, '    state.trace_choices = [(list(k), float(v)) for k, v in choices.items()]\n' + needle))
with (root / 'before.json').open('x') as f:
    json.dump(dict(artifact_sha256=hashlib.sha256(baseline.read_bytes()).hexdigest(),
                   source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in Path('src').glob('*.py')},
                   note='Replays include all 14 losses plus both wins against the exact frozen friend opponent; instrumented paths can differ.'), f, indent=2)
wrapper = r'''
import json
import os
import runpy
scope = runpy.run_path(INSTRUMENTED)
stream = open(TRACE_BASE + '-' + str(os.getpid()) + '.jsonl', 'x', buffering=1)
loads = json.loads
def capture(line, *args, **kwargs):
    message = loads(line, *args, **kwargs)
    stream.write(json.dumps({'input':message}) + '\n')
    return message
json.loads = capture
g = scope['choose_action'].__globals__
old_estimate, old_action = g['estimate'], g['choose_action']
def estimate(state, *args):
    values = old_estimate(state, *args)
    state.trace_values = [float(x) for x in values]
    return values
def action(state, req):
    state.trace_values, state.trace_choices = None, []
    chosen = old_action(state, req)
    stream.write(json.dumps({'decision':dict(req=req, chosen=list(chosen),
                    hole=list(state.hole), dead=list(state.dead), seat=state.seat,
                    values=state.trace_values, choices=state.trace_choices,
                    model=[(list(k),v) for k,v in state.model.cells.items()])}) + '\n')
    return chosen
g['estimate'], g['choose_action'] = estimate, action
scope['main']()
'''
os.environ.update(OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1')
rows = [json.loads(line) for line in Path('experiments/requested-field-test-1110/results.jsonl').read_text().splitlines()]
rows = [r for r in rows if Path(r['opponent']).stem == 'friend']
assert len(rows) == 16 and sum(r['candidate_points']==0 for r in rows) == 14
def play(row):
    folder = root / 'replays' / f"s{row['stage']}-{row['seed']}-r{int(row['reverse'])}"
    folder.mkdir(parents=True, exist_ok=False)
    trace_bot = folder / 'trace_bot.py'
    trace_bot.write_text('INSTRUMENTED = ' + repr(str(instrumented.resolve())) + '\nTRACE_BASE = ' +
                         repr(str((folder / 'trace').resolve())) + '\n' + wrapper)
    a,b = (row['opponent'],str(trace_bot)) if row['reverse'] else (str(trace_bot),row['opponent'])
    result = match(a,b,row['stage'],row['seed'],str(folder))
    result.update(reverse=row['reverse'], original_net=row['candidate_net'],
                   original_points=row['candidate_points'],candidate_net=result['net']*(-1 if row['reverse'] else 1))
    with (folder / 'result.json').open('x') as f:
        json.dump(result,f,indent=2)
    print(folder.name, 'original',row['candidate_net'],'replay',result['candidate_net'],flush=True)
    return result
with (root / 'replays.jsonl').open('x') as f, ThreadPoolExecutor(4) as pool:
    for result in pool.map(play,rows):
        f.write(json.dumps(result)+'\n')
        f.flush()
