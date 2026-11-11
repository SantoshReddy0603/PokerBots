# Independently implemented bot upgrade — 9 November 2026

Historical strategy upgrade. The current submission adds a verified calculation
optimization; see `LOSS_REVIEW.md` for the new artifact hash and loss analysis.

The current submission is `dist/bot.py`, rebuilt from the project's own source.
The previous release is backed up unchanged in `checkpoints/pre-friend-review.py`.
New evaluator, learning and strategy code was implemented independently. No code
from the teammate archive is embedded or imported by the submission. That archive
is used only as an external source of test opponents.

## Changes now in the current bot

- Match-local public-action learning. `src/learning.py` counts opening, reraising,
  betting, overbetting and folds to different bet sizes, with prior smoothing.
  Completed authoritative hands update the model once. Duplicate results cannot
  update it twice. Counts reset with the bot process; private cards are not stored
  in the model and no information is carried between matches.
- An original base-15 NumPy histogram evaluator in `src/vector_equity.py`, checked
  against the existing scalar evaluator. This uses a different implementation and
  score representation from the teammate's evaluator. Flop and turn decisions
  normally use 512 common-runout samples. The river enumerates all 903 compatible
  opponent pairs when both discards are known.
- Action-conditioned opponent ranges. Betting frequencies are calibrated against
  weighted public hand-strength percentiles. Ordinary bets, reraises and overbets
  have separate estimates. Equal-strength hands receive the same percentile.
  Discard decisions use only the flop, including inside simulated deals.
- Revised preflop defense and reraising using this project's existing equity
  table, with conservative large-commitment rules until enough aggression is seen.
- Expected-value comparisons of checking, calling, folding and several legal bet
  sizes in `src/learning_policy.py`. Bet estimates account for which opponent
  holdings are likely to continue, rather than treating all hands as callers.
- Exact alternating-blind reserves. Full capped scores are protected when they
  can be guaranteed. In the final 10% of hands, a guaranteed positive score can
  be protected because match points are the primary scoring criterion.
- A low-bank standard-library fallback and separate action/simulation randomness.
  Neither NumPy installation nor file/network access occurs at runtime.

Default builds now use this strategy. `tools/release_manifest.py` records its
source hashes and the exact tested artifact, with the prior release as fallback.
The earlier `--friend-review` build remains an archived isolated experiment.

## Validation and reproducibility

Tests passed on Linux CPython 3.11.9 with NumPy 2.2.6:

- 15,000 vector/scalar ranking comparisons across five-, six- and seven-card hands.
- 2,000 vector/scalar flop feature comparisons, an independent exact river oracle,
  suit-rotation invariance, board-playing ties and future-board isolation.
- Duplicate-result learning, fresh-model resets and late positive-score protection.
- Existing protocol, selection, 24,000 evaluator-oracle comparisons, decision,
  public-history range, score-lock and matrix-validation fixtures.
- The NumPy-unavailable path was exercised with Python's `-S` option.
- Static submission checks found only `sys`, `json`, `time`, `random`, `itertools`
  and optional `numpy` imports, with no file/network/process access.

One-CPU, 1 GiB constrained Linux matches of the exact released bytes completed
400 and 1,000 hands with full capped wins (+400 / +1,292), no bot diagnostics,
corrections or forfeits. Charged banks were 15.64 / 51.85 seconds out of 60 / 150;
p99 replies 61.37 / 55.86 ms, maximum replies 99.66 / 96.65 ms. Maximum RSS for
the timed command was 40,332 KiB. Log audits verified full-cap protection from
hands 228 / 612. These are local WSL measurements under host load, not organizer
hardware measurements. Reports: `experiments/learning-v5-stress.jsonl` and
`experiments/learning-v5-stress-time.txt`.

The 35-opponent coverage run completed 34 full 400-hand wins. One supplied
`aggro_3bet.py` opponent crashed by reading a missing `max_raise` field when raising
was unavailable. That forfeit is excluded from the 34 completed wins. Its unchanged
source and the captured traceback are retained; no candidate protocol failure
occurred. This run uses one seed and one assignment per opponent, so it is a
coverage diagnostic rather than a paired estimate of playing strength.

The pilot, screen and confirmation seed blocks were declared in
`experiments/learning-seeds.json` before strategy development. Early candidates
v1 and v2 lost the pilot and were rejected. Intermediate v3 won the four pilot
games. v4 and the selected v5 have separate archived reports; none were deleted.
The final v5 code was frozen before the confirmation block was evaluated.

## Measured results against the teammate

| Block | Match length | Updated bot W/D/L | Previous release W/D/L |
|---|---:|---:|---:|
| Development screen, two seeds | 400 | 4/0/0 | 0/0/4 |
| Development screen, two seeds | 1,000 | 3/0/1 | 0/0/4 |
| Fresh confirmation, four seeds | 400 | 5/0/3 | 0/0/8 |
| Fresh confirmation, four seeds | 1,000 | 6/0/2 | 0/0/8 |

The fresh confirmation therefore improved from **0/16 to 11/16 wins**. The
matched comparison validates the complete matrices, bot hashes and identical
test configuration before calculating differences. Reports:
`experiments/learning-v5-confirmation.jsonl`,
`experiments/learning-incumbent-confirmation-matched.jsonl` and
`experiments/learning-confirmation-comparison.txt`. Screening is development
evidence, rather than additional held-out confirmation.

The completed wider development matrix won **47/48** games: 8/8 each against
the previous release, tight-shove, range, polarized and pressure opponents, and
7/8 against the trap/check-raise opponent. Both assignments, both match lengths
and two seed blocks were used. There were no candidate notices, forfeits or
diagnostic output. Maximum charged banks were 33.64 / 69.67 seconds by stage.
The trap loss was -337 chips at 400 hands; the incumbent won its corresponding
trap screen. This is a remaining matchup weakness despite the overall improvement.
The full report is `experiments/learning-v5-field.jsonl`.

For reproducible matrix comparisons, use the matching `.meta.json` sidecars.
The broad incumbent screen used three concurrent matches and the final v5 screen
used two, so they should not be pooled into a strict paired confidence interval.
The separately rerun confirmation reference uses the same concurrency as the
selected bot. Opponent families and seed counts remain limited.

## Using the submission

Submit `dist/bot.py` as the top-level `bot.py` requested by the supplied protocol.
It is a single file, 76,045 bytes, SHA-256
`5f6746cae189f2b94e16c06dae8834383179d12e92f0d139ed1c32edb1817a5e`.
The optional NumPy path requires only the competition-provided library.

```powershell
python tools/build_submission.py
python tests/learning.py dist/bot.py
python tests/protocol.py dist/bot.py
python tools/check_score_lock.py learning-v5-stress --alternating-blinds --late-win
```

Winning every game or the hackathon cannot be established from local testing.
These range and continuing-range models remain approximations; a finite opponent
pool cannot represent every tournament entrant. No submission upload, organizer
contact or external publication was performed.
