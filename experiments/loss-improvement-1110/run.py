from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import os
import subprocess
import sys

root = Path('experiments/loss-improvement-1110')
phase = sys.argv[1]
names = sys.argv[2:] or ['baseline','selective','response','combined']
assert phase in ('screen','confirmation')
pool = ['experiments/requested-field-test-1110/friend.py',
        'experiments/friend-review/pokerbots-discard-holdem-main/bot.py',
        'opponents/league/confirmation/trap.py','opponents/league/confirmation/tightjam.py']
if phase=='confirmation':
    pool += ['opponents/league/confirmation/range.py','opponents/league/confirmation/polar.py']
env = dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
def play(name):
    cmd = [sys.executable,'-B','tools/evaluate.py',str(root/(name+'.py')),*pool,
           '--manifest',str(root/'seeds.json'),'--split',phase,'--count','2' if phase=='screen' else '4',
           '--engine-format','legs','--jobs','2','--out',str(root/(phase+'-'+name+'.jsonl'))]
    with (root/(phase+'-'+name+'.stdout.txt')).open('x') as out, (root/(phase+'-'+name+'.stderr.txt')).open('x') as err:
        subprocess.run(cmd,stdout=out,stderr=err,env=env,check=True)
    print(phase,name,'complete',flush=True)
# Eight concurrent matches when all four artifacts are screened, separately
# recorded from each matrix's two-worker setting. All artifacts start together.
with ThreadPoolExecutor(4) as pool_executor:
    list(pool_executor.map(play,names))
