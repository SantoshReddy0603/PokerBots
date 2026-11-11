"""Fresh latest-teammate test of the improved release; no strategy changes."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import os
import secrets
import subprocess
import sys

root=Path('experiments/improved-teammate-match-1110')
repo=Path('experiments/teammate-match-1110/repository')
commit=subprocess.check_output(['git','-C',str(repo),'rev-parse','origin/main'],text=True).strip()
peer=subprocess.check_output(['git','-C',str(repo),'show',commit+':bot.py'])
compile(peer,'teammate.py','exec')
for name,data in [('ours.py',Path('dist/bot.py').read_bytes()),('teammate.py',peer)]:
    with (root/name).open('xb') as f:f.write(data)
digest=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
with (root/'provenance.json').open('x') as f:
    json.dump(dict(repository='https://github.com/sricharanreddycheruku/pokerbots-discard-holdem',
                   commit=commit,ours_sha256=digest(root/'ours.py'),teammate_sha256=digest(root/'teammate.py'),
                   fetched_utc=datetime.now(timezone.utc).isoformat()),f,indent=2)
with (root/'seeds.json').open('x') as f:
    json.dump({'confirmation':['improved-peer-1110-'+secrets.token_hex(12) for _ in range(4)]},f,indent=2)
cmd=[sys.executable,'-B','tools/evaluate.py',str(root/'ours.py'),str(root/'teammate.py'),
     '--manifest',str(root/'seeds.json'),'--split','confirmation','--count','4','--jobs','2',
     '--engine-format','legs','--out',str(root/'results.jsonl')]
with (root/'command.json').open('x') as f:json.dump(cmd,f,indent=2)
with (root/'run.stdout.txt').open('x') as out,(root/'run.stderr.txt').open('x') as err:
    subprocess.run(cmd,stdout=out,stderr=err,check=True,
                   env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1'))
assert digest('dist/bot.py')==digest(root/'ours.py'),'Current release changed; frozen results remain valid'
print('All 16 latest-teammate matches completed',flush=True)
