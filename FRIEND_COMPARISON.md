# Teammate comparison — 9 November 2026

Historical initial comparison. The subsequent independently implemented strategy
and updated submission are documented in `STRENGTHENING_REPORT.md`.

Your teammate's bot is a stronger direct opponent in this local comparison.
Both your existing release and the new candidate lost all eight Linux matches
against it. Two useful engineering improvements have been implemented in a
separate candidate; they do not establish a stronger tournament strategy.
`dist/bot.py` and its release manifest remain the previously validated release.

## What was compared

- Input: `pokerbots-discard-holdem-main (1).zip`, SHA-256
  `f8868144daefe721681fd87219f4bd69a5930bf99ba7723859253b3ee291fd80`.
- Teammate bot: SHA-256 `0016b0f931f16c3cb414696cd90861d1c1673ef4dde66de4c02b33b071846886`.
  Extracted unchanged under `experiments/friend-review/pokerbots-discard-holdem-main/`.
  That extraction and its smoke-match logs are ignored by Git; retain the zip to reproduce it.
- Your previous release: `checkpoints/pre-friend-review.py`, an exact backup of
  `dist/bot.py`, SHA-256 `d679d00967b25c56db9c9b1889732823496f0cf017977f3d5e9fdfa4a0b73e3c`.
- Candidate: `checkpoints/friend-review.py`, SHA-256
  `3021a3c4e6e5784b69aa65a5679a0a5bd5d8097834a8b5251b84b793db34ad5b`.

The comparison uses our unchanged organizer engine, not the engine supplied
inside the friend's archive. No organizer files were modified.

## Relevant differences

| Area | Your release | Teammate's version | Decision |
|---|---|---|---|
| Preflop | Conservative heuristic; calibrated table for trips | Embedded equity estimates against several range widths; learned raise frequencies | Keep current policy in the candidate; test any replacement separately |
| Opponent model | Fixed likelihoods conditioned on public actions and discards | Match-local fold, aggression, raise-size, showdown and discard statistics with priors | Promising next strategy experiment; no broad adaptation copied |
| Equity engine | Standard-library sampled weighted equity | NumPy batch evaluation, broader flop sampling, turn pair enumeration and exact river pair enumeration | Borrow invariant river caching; keep existing range model and sampling |
| Bet sizing | Tested threshold and pot-fraction rules | Compares several sizes using fold probability, continuing ranges and reraise risk | Requires separate validation; earlier local EV-sizing experiment also failed its gate |
| Match protection | Full capped lead minus two blinds per remaining hand | Exact alternating blinds; also protects a smaller positive lead late in a match | Use exact blinds in the candidate; retain the full-cap target |

These are source-level differences. The matches do not isolate which mechanisms
caused the friend's advantage. Its larger adaptation and NumPy changes are
substantial architectural changes, rather than safe parameter substitutions.

## Implemented candidate improvements

1. `src/friend_score_protocol.py`: exact future blind cost. For `n` remaining
   hands, reserve `3 * (n // 2)` plus the current blind when `n` is odd. For
   example, five hands starting on the button cost at most seven chips, versus
   the previous ten-chip reserve. Lock only after consecutive authoritative
   results and only when the full capped score remains guaranteed. Unknown
   seats retain the old conservative bound. This uses the organizer's alternating
   seats, never duplicate cards, hidden cards or future boards.
2. `src/friend_ranges.py`: rank the fixed river board and hero hand once per
   decision instead of once per sampled opponent holding. At 144 samples this
   avoids 286 redundant rank calls. Same samples produce exactly the same
   equity; production deadlines can permit different sample counts.

The local river timing check used 40 fixed holdings, 144 samples, public betting
evidence and five repetitions: median **14.71 → 12.86 ms** per decision, about
**13% less time**. This is a local microbenchmark under host load, not a
whole-match speed or win-rate claim. Raw timings are in
`experiments/friend-review-river-timing.json`.

## Match evidence

Linux CPython 3.11.9, NumPy 2.2.6 installed for the teammate bot. Your release and
candidate continue to use only the standard library. Both assignments of two
existing seed blocks were played at both match lengths, with production clocks.

| Your bot vs teammate | 400-hand W/D/L | Raw chips/hand | 1,000-hand W/D/L | Raw chips/hand |
|---|---:|---:|---:|---:|
| Existing release | 0/0/4 | -1.309 | 0/0/4 | -1.089 |
| Candidate | 0/0/4 | -1.143 | 0/0/4 | -1.110 |

All capped results were -1 chip/hand. No forfeits, notices or diagnostic output
occurred in either matrix. Reports and hash/interpreter/seed metadata are in
`experiments/friend-review-linux-{baseline,candidate}.jsonl` and corresponding
`.meta.json` files. The preliminary Python 3.12 Windows matrix is archived as
`experiments/friend-review-baseline.jsonl`; it is not pooled with these results.
Only two seed blocks were used, and the candidate's production sampling is
time-dependent. No statistically established improvement or tournament forecast
follows from these numbers.

The additional regression screen (`experiments/friend-review-regression.jsonl`)
used one seed block and both assignments: the candidate split 1–1 against the
incumbent at each stage and won 2–0 against the tight-shove opponent at each
stage, with no protocol or resource failures. This is insufficient evidence to
promote a replacement under the repository's existing selection rule.

Constrained candidate validation shared one CPU and inherited a 1 GiB address-space
limit. The 400-hand pressure and 1,000-hand range matches won +513 and +1,382
chips with full caps, no corrections, forfeits or diagnostic output. Charged
banks were 3.70 / 18.25 seconds; maximum replies 19.02 / 19.55 ms. Maximum RSS
for the timed command was 23,060 KiB. Full logs confirm protection began at
hands 137 / 542 and preserved each capped lead. Reports:
`experiments/friend-review-stress.jsonl` and `friend-review-stress-time.txt`.

## Reproduce and use

From the repository root with Python 3.11:

```powershell
python tools/build_submission.py --friend-review --output checkpoints/friend-review.py
python tests/friend_review.py checkpoints/friend-review.py
python tests/protocol.py checkpoints/friend-review.py
python tests/selection.py checkpoints/friend-review.py
python tests/evaluator.py checkpoints/friend-review.py
python tests/review_decisions.py checkpoints/friend-review.py
python tests/review_ranges.py checkpoints/friend-review.py
python tests/review_lock.py checkpoints/friend-review.py
python tools/check_score_lock.py friend-review-stress --alternating-blinds
```

The new regression test checks 2,800 seat/remaining-hand boundaries, explicit
fold-out guarantees, 100 identical fixed-sample river results and rank-call
counts. Existing tests also passed, including 24,000 evaluator oracle comparisons.
Independent default and candidate rebuilds matched their respective hashes.

For the direct matchup, after extracting the archive and installing NumPy in the
local test interpreter:

```powershell
python tools/evaluate.py checkpoints/friend-review.py experiments/friend-review/pokerbots-discard-holdem-main/bot.py --manifest experiments/review-reserved-seeds.json --split screen --count 2 --jobs 2 --out experiments/NEW-REPORT.jsonl
```

The build flag requires an output outside `dist/`. Normal builds still reproduce
the incumbent release. The best next isolated strategy experiment is opponent
frequency calibration with shrinkage and held-out opponents, followed by a
separate NumPy river-enumeration experiment. Neither is presented as validated
or included in this candidate.
