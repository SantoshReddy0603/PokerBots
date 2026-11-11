"""Build isolated range/response ablations from exact current source hashes."""
from pathlib import Path
import hashlib
import json
import secrets

root = Path('experiments/loss-improvement-1110')
before = json.loads((root/'before.json').read_text())
digest = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
for p, expected in before['source_sha256'].items():
    assert digest(p)==expected, ('source drift',p)
source = Path('src/vector_equity.py').read_text()
needle = '            likelihood = .08 + .92 / (1 + np.exp(-13 * (percentile - (1 - frequency))))'
replacement = '''            # Rare large bets/reraises should not inherit the same weak-hand
            # likelihood floor as ordinary high-frequency bets. Frequent
            # aggression retains the broad prior; no opponent identity is used.
            floor = min(.08, max(.01, .20 * frequency)) if size > 0 and (faced > 0 or bet > 1.5) else .08
            likelihood = floor + (1 - floor) / (1 + np.exp(-13 * (percentile - (1 - frequency))))'''
assert source.count(needle)==1
with Path('src/selective_equity.py').open('x') as f:
    f.write(source.replace(needle,replacement))
sources = json.loads((root/'baseline.release.json').read_text())['sources']
recipes = {}
for name in ('selective','response','combined'):
    paths = ['src/selective_equity.py' if p=='src/vector_equity.py' and name in ('selective','combined') else p for p in sources]
    if name in ('response','combined'):
        paths.append('src/response_policy.py')
    body = '\n\n'.join(Path(p).read_text(encoding='utf-8-sig').strip() for p in paths)
    body += '\n\nif __name__ == "__main__":\n    main()\n'
    compile(body,name,'exec')
    with (root/(name+'.py')).open('xb') as f:
        f.write(body.encode())
    recipes[name] = dict(sources={p:digest(p) for p in paths},sha256=digest(root/(name+'.py')))
with (root/'recipes.json').open('x') as f:
    json.dump(recipes,f,indent=2)
with (root/'seeds.json').open('x') as f:
    json.dump({phase:['loss1110-'+phase+'-'+secrets.token_hex(10) for _ in range(n)]
               for phase,n in [('screen',2),('confirmation',4)]},f,indent=2)
with (root/'selection-plan.json').open('x') as f:
    json.dump(dict(screen_opponents=['current friend','old friend','trap','tightjam'],
                   screen_matches_per_artifact=32, screen_blocks=2,
                   candidates=['selective','response','combined'],
                   confirmation_blocks=4,
                   confirmation_opponents=['current friend','old friend','trap','tightjam','range','polar'],
                   confirmation_matches_per_artifact=96,
                   gate='Advance highest match points only if above baseline in screen and no severe matchup regression. Promote only with fresh positive paired confirmation points, convincing block support, no serious regression, correctness and constrained exact-byte validation. Otherwise retain baseline.',
                   note='Neither source correctness nor more raw chips overrides match-point evidence.'),f,indent=2)
print('Built three isolated ablations and froze fresh screen/confirmation plan')
