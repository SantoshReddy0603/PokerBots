# PokerBots

Self-contained Python 3.11 Discard Hold'em bot. The selected submission is `dist/bot.py`.
The current policy learns public-action frequencies within each leg, uses an original
NumPy histogram evaluator with exact river enumeration, and compares legal bet sizes
against estimated continuing ranges. A standard-library fallback is included.

The selected release now uses `src/selective_equity.py` to model rare postflop
reraises and large bets more selectively. Loss diagnosis and validation are in
`experiments/loss-improvement-1110/RESULTS.md`. Fresh paired confirmation:
86/96 wins versus the prior bot's 76/96; against the tested friend snapshot,
9/16 versus 0/16. All four other confirmation profiles remained 16/16, and the
archived friend result improved 12/16 to 13/16. Separate pressure, switching-style
and previous-champion checks were 24/24. No observed matchup regression passed
the selection process; finite local tests cannot guarantee no true regression.
The previous exact release and manifest are in `checkpoints/pre-selective-1110.py`
and `checkpoints/pre-selective-1110.release.json`. Default builds reproduce the
new tested artifact; the experimental response-tree model is excluded.
The pre-update release is frozen in `checkpoints/pre-rules-1110.py`; an older
release is in `checkpoints/learning-v5.py`. The earlier
baseline is in `checkpoints/pre-friend-review.py`, and the original
11,875-byte champion is in `checkpoints/betting.py`. Keep original organizer files
under `pokerbots_1/` and `vendor/` unchanged.

The earlier calculation optimization, five-loss analysis and strategy selection
are documented in `LOSS_REVIEW.md`. Those results used the previous match format.
The 10 November rule update changes matches to two independently launched legs;
see `RULES.md` and `experiments/rules-update-1110/`. The exact prior release and
manifest are frozen at `checkpoints/pre-rules-1110.py` and
`checkpoints/pre-rules-1110.release.json`. The preceding strategy upgrade and measured
limits are in `STRENGTHENING_REPORT.md`. The earlier
comparison is archived in `FRIEND_COMPARISON.md`. The friend's code is used only
as a test opponent; no module from its archive is included in the submission.

The earlier review implementation is in `REVIEW_FIXES_2026-11-09.md`: the
optimization CLI is repaired; model-correction candidates are tested separately.
The opening/isolation finalist scored 53/64 versus the release's 56/64 in fresh
confirmation, so the submission at that time was retained.

The subsequent daily review is in `experiments/daily-1110/RESULTS.md`. It fetched
the teammate's current private-repository bot through the connected GitHub account,
and promoted a calculation-only histogram improvement. Fixed-draw posterior
outputs are unchanged; local warm equity calculations were 4.8–6.8% faster.
The exact new artifact split four current-format matches against that updated
opponent, so it does not establish a stronger win rate. The prior exact release
and manifest are preserved in `checkpoints/pre-daily-1110.py` and its
`.release.json` companion. That calculation-only release is now the fallback
for the subsequent selective-range improvement described above.

The separate river-order candidate failed its fresh 32-match screen (24 wins
versus 25 for the frozen pre-optimization release) and remains experimental.
All 24 synthetic-family matches were wins for each artifact; the updated
teammate won 7/8 and 8/8 respectively. The exact optimized release's separate
2/4 teammate result uses different seeds and is not a paired improvement.

The subsequent user-requested field test is recorded in
`experiments/requested-field-test-1110/RESULTS.md`: the then-current release
completed 96 fresh-seed current-format matches, with 82 wins and 14 losses.
Against the updated teammate it went 2/16 (400-hand 2/8, 1,000-hand 0/8);
trap, pressure, tight-shove, range-aware and polarized synthetic opponents were
16/16 each. No forfeits, corrections or diagnostic output occurred. These
local synthetic-family wins do not establish broad tournament strength.

## Local commands

From the repository root in PowerShell:

```powershell
$py = "$env:USERPROFILE/.cache/pokerbots-python311/python.exe"
& $py tools/build_submission.py --output checkpoints/rebuild.py
& $py tests/protocol.py
& $py tests/selection.py
& $py tests/evaluator.py
& $py tests/learning.py
& $py tests/optimization.py
& $py tests/selective_response.py
& $py tests/review_matrix.py
```

The default build writes `dist/bot.py`. Use `--output checkpoints/NAME.py` during development. Candidate source files are combined with `--protocol`, `--policy`, and repeated `--extra` arguments.

Current matches use `vendor/Starter_Kit_2026_11_10/engine.py`, kept byte-for-byte
as supplied. `tools/evaluate.py` and `tools/validate_release.py` default to
two-leg matches with separate process launches, per-leg banks, and combined
whole-match scoring. Pass `--engine-format legacy` only for archived experiments.
`tools/benchmark.py` remains the legacy runner; use `tools/benchmark_legs.py` for
an individual current-format match. Reports retain each leg's runtime and notices.
The selected bot's existing 200/500-hand handling does not lock on a local leg
lead. An explicit reset/score-scope candidate is retained separately at
`src/leg_protocol.py` and `checkpoints/rules-1110.py`; its fresh comparison did
not justify replacing the current submission. Rebuild it with the source
overrides recorded in `experiments/rules-update-1110/commands.json`.

On the provisioned Ubuntu WSL runtime:

```powershell
wsl -d Ubuntu -- /home/miyyapuram_saivarun/pokerbots-runtime/Python-3.11.9/python -B tools/build_league.py
wsl -d Ubuntu -- /home/miyyapuram_saivarun/pokerbots-runtime/Python-3.11.9/python -B tools/evaluate.py checkpoints/betting.py opponents/league/development-v2/range.py --manifest experiments/review-seeds.json --split screen --count 4 --jobs 4 --out experiments/example-matrix.jsonl
```

Use distinct output paths for each candidate. Match matrices include both assignments and both stage lengths. The metadata sidecar records interpreter, concurrency, seed manifest, harness and bot hashes. Compare matrices with `tools/compare.py A.jsonl B.jsonl`. Legacy reports predate strict metadata. `tools/field.py` models a toy field for sensitivity checks.

## Promotion

Use fresh seed blocks and the stronger league. Require no new protocol or resource failures, a positive paired match-point result with convincing block-level support, and no severe unexplained matchup regression. Use capped chips as the tie-break and raw chips as a diagnostic. Retain the tested champion when evidence is inconclusive. Validate the exact prospective release in constrained Linux CPython 3.11 before replacing `dist/bot.py`. Keep confirmation seeds untouched until candidate selection. See `PROGRESS.md` for completed matrices, sampled opponents and limits.
