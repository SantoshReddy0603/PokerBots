# Single message loop release

`src/main_loop.py` reads each message once. `State` follows the match score, the
opponent frequency model and the protected-lead lock; `MatchState` follows the
range model and the clock. Preflop uses the equity table; with NumPy the discard
and the later streets use the vectorised range model (`src/range_engine.py`).
Without NumPy the list-based estimate plays every decision.

Changes from the previous release (`checkpoints/pre-release-1115.py`): one plain
source file instead of separately compressed modules, the protected-lead lock
applies on every street, and `tests/` run against the submission itself.

All matches use the official two-leg engine at production clocks with both seats
played. Paired rows share (opponent, stage, seed, seat).

## New opponents (previous release, seeds 44000-44005)

| Opponent | Stage 1 | Stage 2 |
|---|---|---|
| vinayreddy1008/pokerbots-2026-backup (Peak_06) | 12/12 | 12/12 |
| SantoshReddy0603/pokerbots-final | 12/12 | 12/12 |

Peak_06 forfeited 17 of these on its own time bank under local load.

## Against the previous release, same seeds (45000-45003)

| Opponent | Stage 1 | Stage 2 |
|---|---|---|
| range-model-bot | 4/8 vs 4/8 | 8/8 vs 2/8 |
| varun | 7/8 vs 8/8 | 8/8 vs 7/8 |
| Peak_06 | 8/8 vs 8/8 | 8/8 vs 8/8 |

Total 43/48 against 37/48. Stage 1 -4.2 [-16.7, +8.3] points, Stage 2 +29.2
[+20.8, +33.3] (95% seed-block bootstrap).

Head to head against the previous release (seeds 46000-46007 and 47000-47007): 27 of
64 matches, within noise of even for two builds that make the same decisions.

## Further check (seeds 48000-48001)

32 of 32: agri, amogh, nitish and SantoshReddy0603 each 4/4 in both stages.

## Resources

No forfeits or notices from this build in any match. Slowest reply 201 ms on a
loaded machine. With both bots on one core: Stage 1 17 s of bank over both legs
(30 s per leg), Stage 2 53 s over both legs (75 s per leg), slowest reply 221 ms,
startup 0.9 s. With NumPy blocked the file plays the list-based path and completes
full matches. `tests/protocol.py`, `leg_compatibility.py`, `learning.py`,
`selection.py`, `evaluator.py` and `python -S tests/protocol.py` pass on the
submission.

## Files

- `merged-field-45000.jsonl`, `release-field-45000.jsonl`: paired field runs
- `head-to-head.jsonl`: this build against the previous release
- `merged-field-48000.jsonl`, `release-new-opponents-44000.jsonl`
