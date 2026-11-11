"""Additional fresh pressure, switching-style and champion checks."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import json
import os
import secrets
import subprocess
import sys
root=Path('experiments/loss-improvement-1110')
with (root/'regression-seeds.json').open('x') as f:
    json.dump({'regression':['loss1110-regression-'+secrets.token_hex(10) for _ in range(2)]},f,indent=2)
with (root/'regression-plan.json').open('x') as f:
    json.dump(dict(opponents=['pressure','switch','baseline champion'],matches_per_artifact=24,
                   gate='No lower total/stage points than baseline; no >=2-win opponent regression. Selected versus baseline champion must score at least half the match points. Zero protocol/resource failures.',
                   note='Supplementary guard against passive play and fitting one opponent. Declared before running.'),f,indent=2)
env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
def run(name):
    cmd=[sys.executable,'-B','tools/evaluate.py',str(root/(name+'.py')),
         'opponents/league/confirmation/pressure.py','opponents/league/confirmation/switch.py',str(root/'baseline.py'),
         '--manifest',str(root/'regression-seeds.json'),'--split','regression','--count','2',
         '--jobs','2','--engine-format','legs','--out',str(root/('regression-'+name+'.jsonl'))]
    with (root/('regression-'+name+'.stdout.txt')).open('x') as out, (root/('regression-'+name+'.stderr.txt')).open('x') as err:
        subprocess.run(cmd,stdout=out,stderr=err,env=env,check=True)
    print(name,'regression complete',flush=True)
with ThreadPoolExecutor(2) as executor:
    list(executor.map(run,['baseline','selective']))
