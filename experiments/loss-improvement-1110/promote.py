"""Promote only after every frozen gate passes; preserve exact fallbacks."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys

root=Path('experiments/loss-improvement-1110')
decision=json.loads((root/'decision.json').read_text())
assert decision['promote'] and all(decision['checks'].values())
digest=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
recipe=json.loads((root/'recipes.json').read_text())['selective']
for path,expected in recipe['sources'].items():
    assert digest(path)==expected, ('source drift',path)
assert digest('dist/bot.py')==digest(root/'baseline.py')
assert digest(root/'selective.py')==recipe['sha256']
for output,source in [('checkpoints/pre-selective-1110.py',str(root/'baseline.py')),
                      ('checkpoints/pre-selective-1110.release.json',str(root/'baseline.release.json')),
                      ('checkpoints/selective-1110.py',str(root/'selective.py')),
                      (str(root/'build_submission-before.py'),'tools/build_submission.py'),
                      (str(root/'release_manifest-before.py'),'tools/release_manifest.py'),
                      (str(root/'optimization-before.py'),'tests/optimization.py')]:
    with Path(output).open('xb') as f:
        f.write(Path(source).read_bytes())

builder=Path('tools/build_submission.py')
raw=builder.read_bytes()
assert raw.count(b'"src/vector_equity.py"')==1
builder.write_bytes(raw.replace(b'"src/vector_equity.py"',b'"src/selective_equity.py"'))

# Keep the strong equality assertions on the historical calculation-only
# change. A range-model update intentionally changes posterior weights.
optimization=Path('tests/optimization.py')
raw=optimization.read_bytes()
needle=b'p.add_argument("candidate", nargs="?", default="dist/bot.py")'
assert raw.count(needle)==1
optimization.write_bytes(raw.replace(needle,b'p.add_argument("candidate", nargs="?", default="checkpoints/daily-1110-histogram.py")'))

scores=json.loads((root/'confirmation-summary.json').read_text())
old=scores['baseline']['wdl']; new=scores['selective']['wdl']
note=(f"Selective postflop aggression ranges: weak-hand likelihood floor scales with learned large-bet/reraise frequency; "
      f"ordinary/frequent aggression, preflop policy and evaluator are unchanged. Fresh four-block confirmation "
      f"selected {new[0]}/96 wins versus prior {old[0]}/96; both assignments/stages, six declared opponent snapshots. "
      f"Supplementary pressure/switch/champion test selected 24/24, including 8/8 head-to-head. "
      f"Exact candidate passed one-CPU/1-GiB Linux current-format resource tests and correctness/protocol/audit checks. "
      f"Finite local evidence does not guarantee no true regression. See experiments/loss-improvement-1110/RESULTS.md.")
manifest_tool=Path('tools/release_manifest.py')
text=manifest_tool.read_text()
replacements={'checkpoints/daily-1110-histogram.py':'checkpoints/selective-1110.py',
              'checkpoints/pre-daily-1110.py':'checkpoints/pre-selective-1110.py',
              'experiments/rules-update-1110/retained-stress.jsonl':'experiments/loss-improvement-1110/confirmation-baseline.jsonl',
              'experiments/daily-1110/histogram-stress.jsonl':'experiments/loss-improvement-1110/selective-stress.jsonl',
              'experiments/daily-1110/exact-friend.jsonl':'experiments/loss-improvement-1110/confirmation-selective.jsonl',
              'src/vector_equity.py':'src/selective_equity.py'}
for before,after in replacements.items():
    assert text.count(before)==1, before
    text=text.replace(before,after)
start=text.index('    p.add_argument("--validation-note",')
end=text.index('    p.add_argument("--numpy-note",',start)
text=text[:start]+'    p.add_argument("--validation-note", default='+repr(note)+')\n'+text[end:]
manifest_tool.write_text(text,encoding='utf-8',newline='\n')
subprocess.run([sys.executable,'-B','tools/build_submission.py','--output',str(root/'default-rebuild.py')],check=True)
assert (root/'default-rebuild.py').read_bytes()==(root/'selective.py').read_bytes()
subprocess.run([sys.executable,'-B','tools/build_submission.py'],check=True)
assert digest('dist/bot.py')==recipe['sha256']
subprocess.run([sys.executable,'-B','tools/release_manifest.py'],check=True)
manifest=json.loads(Path('dist/release.json').read_text())
assert manifest['sha256']==digest('dist/bot.py')
assert manifest['source_sha256']==recipe['sources']
with (root/'promotion.json').open('x') as f:
    json.dump(dict(sha256=digest('dist/bot.py'),bytes=Path('dist/bot.py').stat().st_size,
                   fallback_sha256=digest('checkpoints/pre-selective-1110.py'),
                   default_rebuild_identical=True,sources=recipe['sources']),f,indent=2)
print('Promoted exact validated selective-range artifact',digest('dist/bot.py'))
