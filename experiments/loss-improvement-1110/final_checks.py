from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys

root=Path('experiments/loss-improvement-1110')
decision=json.loads((root/'decision.json').read_text())
digest=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
expected=digest(root/('selective.py' if decision['promote'] else 'baseline.py'))
assert digest('dist/bot.py')==expected
env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
if decision['promote']:
    commands=[[sys.executable,'-B','tests/protocol.py','dist/bot.py'],
              [sys.executable,'-B','tests/learning.py','dist/bot.py'],
              [sys.executable,'-S','-B','tests/leg_compatibility.py','dist/bot.py'],
              [sys.executable,'-B','tests/optimization.py'],
              [sys.executable,'-B','tools/audit_submission.py','dist/bot.py','--out',str(root/'final-audit.json')]]
    with (root/'final-checks.jsonl').open('x') as f:
        for command in commands:
            r=subprocess.run(command,capture_output=True,text=True,env=env)
            f.write(json.dumps(dict(command=command,exit=r.returncode,stdout=r.stdout,stderr=r.stderr))+'\n')
            f.flush()
            assert r.returncode==0, r.stdout+r.stderr
    subprocess.run([sys.executable,'-B','tools/build_submission.py','--output',str(root/'final-rebuild.py')],check=True,env=env)
    assert digest(root/'final-rebuild.py')==expected
    subprocess.run([sys.executable,'-B','tools/release_manifest.py','--output',str(root/'manifest-rebuild.json')],check=True,env=env)
    assert (root/'manifest-rebuild.json').read_bytes()==Path('dist/release.json').read_bytes()
    manifest=json.loads(Path('dist/release.json').read_text())
    assert manifest['sha256']==expected
    assert all(digest(p)==sha for p,sha in manifest['source_sha256'].items())
    assert digest('checkpoints/pre-selective-1110.py')==digest(root/'baseline.py')
assert digest('dist/bot.py')==expected
with (root/'final-state.json').open('x') as f:
    json.dump(dict(artifact_sha256=expected,bytes=Path('dist/bot.py').stat().st_size,
                   promoted=decision['promote'],all_declared_gates=decision['checks'],
                   manifest_sha256=digest('dist/release.json'),
                   baseline_sha256=digest(root/'baseline.py')),f,indent=2)
print('Final artifact, source hashes, fallback and rebuild checks passed',expected)
