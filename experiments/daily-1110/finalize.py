from pathlib import Path
import hashlib
import json
import subprocess
import sys

root = Path('experiments/daily-1110')
digest = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
subprocess.run([sys.executable, '-B', 'tools/build_submission.py', '--output', str(root / 'final-rebuild.py')], check=True)
assert (root / 'final-rebuild.py').read_bytes() == Path('dist/bot.py').read_bytes() == (root / 'histogram.py').read_bytes()
subprocess.run([sys.executable, '-B', 'tools/release_manifest.py', '--output', str(root / 'manifest-rebuild.json')], check=True)
assert (root / 'manifest-rebuild.json').read_bytes() == Path('dist/release.json').read_bytes()
manifest = json.loads(Path('dist/release.json').read_text())
assert digest('dist/bot.py') == manifest['sha256']
assert all(digest(p) == expected for p, expected in manifest['source_sha256'].items())
assert digest('vendor/Starter_Kit_2026_11_10/engine.py') == manifest['organizer_engine_sha256']
assert digest(root / 'baseline.py') == digest('checkpoints/pre-daily-1110.py')
workspace_check = subprocess.run(['git', 'diff', '--check'], capture_output=True, text=True)
git_check = subprocess.run(['git', 'diff', '--check', '--', 'src/vector_equity.py',
                            'tools/release_manifest.py', 'dist/bot.py', 'dist/release.json', 'README.md'],
                           capture_output=True, text=True)
assert git_check.returncode == 0, git_check.stdout + git_check.stderr
state = dict(artifact_sha256=digest('dist/bot.py'), artifact_bytes=Path('dist/bot.py').stat().st_size,
             manifest_sha256=digest('dist/release.json'), source_sha256=manifest['source_sha256'],
             release_rebuild_identical=True, manifest_rebuild_identical=True, scoped_git_diff_check=0,
             workspace_diff_check=dict(exit=workspace_check.returncode, output=workspace_check.stdout,
                                       note='Pre-existing rule-update PROGRESS lines contain trailing whitespace; preserved.'),
             strategy_candidate_promoted=False, confirmation_blocks_used=0)
with (root / 'final-state.json').open('x') as f:
    json.dump(state, f, indent=2)
print(json.dumps(state, indent=2))
