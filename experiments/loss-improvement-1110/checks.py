from pathlib import Path
import json
import os
import subprocess
import sys
root = Path('experiments/loss-improvement-1110')
env = dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
commands = [[sys.executable,'-B','tests/selective_response.py']]
for name in ('selective','response','combined'):
    for test in ('protocol','selection','evaluator','learning','review_decisions','leg_compatibility'):
        commands.append([sys.executable,'-B','tests/'+test+'.py',str(root/(name+'.py'))])
commands += [[sys.executable,'-S','-B','tests/leg_compatibility.py',str(root/'combined.py')]]
with (root/'checks.jsonl').open('x') as out:
    for command in commands:
        r = subprocess.run(command,capture_output=True,text=True,env=env)
        out.write(json.dumps(dict(command=command,exit=r.returncode,stdout=r.stdout,stderr=r.stderr))+'\n')
        out.flush()
        print(command[-2:],r.returncode,flush=True)
        if r.returncode:
            raise SystemExit(r.returncode)
