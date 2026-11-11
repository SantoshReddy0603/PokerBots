# Loss review and optimization — 9 November 2026

Follow-up: `REVIEW_FIXES_2026-11-09.md` records repairs to the optimization CLI
and separate model-correction experiments. The current submission is retained.
Editable experimental context/confidence modules now include shared bet-size
consistency and explicit context corrections; they no longer reproduce the older
frozen v9 byte-for-byte. That checkpoint is unchanged, and its pre-edit sources
are preserved in `experiments/review-fixes-1109/source-before.zip`.

This review examines the five losses from the previous 16-match confirmation.
The previous submission is preserved at `checkpoints/learning-v5.py`.

## What the five losses tell us

| Original case | Original net | Logged replay net |
|---|---:|---:|
| 400 hands, c0, assignment 0 | -454 | +425 |
| 400 hands, c0, assignment 1 | -477 | -547 |
| 400 hands, c2, assignment 1 | -1 | -565 |
| 1,000 hands, c2, assignment 0 | -36 | +423 |
| 1,000 hands, c2, assignment 1 | -156 | +534 |

Original matches retained summary scores, not complete decision logs. These new
replays use the same deal seeds and both exact original bot files, but add
development-only tracing. Simulation work in the opponent depends on elapsed
time, and instrumentation also changes scheduling. Consequently the action
paths and outcomes can change. These are diagnostic replays, not exact
reconstructions of the original five action sequences. No original result was
overwritten or reclassified as a win.

The recurring risk is large pots: in one losing replay, six 200-chip losses
against two 200-chip wins produced -882 showdown chips despite +335 chips from
non-showdown hands. Some commitments were made with estimated equities close
enough to a decision threshold for simulation noise to matter. Other losses
followed substantial estimates against a range that did not match the strong
holding ultimately shown. Seeing a strong holding once does not prove the
range estimate or call was wrong before the cards were revealed.

There were also ordinary bad beats. In a replay, retained AA lost to a club
flush after the turn; against that particular shown hand it was still a 69%
favorite before the river. Offline exhaustive runouts illustrate both cases:

| Hero | Shown opponent | Visible board | Equity against that known holding |
|---|---|---|---:|
| AK hearts | A-diamonds, 2-clubs | A-spades, Q-spades, 2-hearts | 34.77% |
| K-diamonds, J-hearts | Pocket fives | J-clubs, 5-diamonds, 9-diamonds | 7.75% |
| Pocket aces | 6-clubs, 2-clubs | 9-diamonds, K-clubs, 2-hearts, 7-clubs | 69.05% |

These hindsight calculations are confined to the analysis tools. The submitted
bot cannot see hidden opponent cards and does not use these examples as rules.
The first two rows illustrate model risk; the third illustrates runout variance.
They are not a causal accounting of every chip lost in the original matches.

## Verified calculation optimization

`checkpoints/learning-v6-optimized.py` removes redundant work without changing
the fixed-draw calculation: river hero ranks are computed once, compatible river
opponent scores are reused, and current-street strength arrays are reused when
already available. Sixty tests compared complete equities, weights, outcomes
and strength arrays with v5, requiring exact equality.

Local median times at 512 samples / full river enumeration, 20 holdings per
street and three repetitions:

| Street | Previous | Optimized | Reduction |
|---|---:|---:|---:|
| Flop | 29.46 ms | 26.11 ms | 11% |
| Turn | 25.03 ms | 21.21 ms | 15% |
| River | 35.38 ms | 23.99 ms | 32% |

These are local microbenchmarks under load, not whole-match speed guarantees.
Raw timings: `experiments/optimization-timing.json`; check:
`python tests/optimization.py checkpoints/learning-v6-optimized.py`.

## Independently implemented strategy experiments

- A commitment-scaled sampling margin. Large uncertain calls/raises subtract a
  weighted Monte Carlo standard error; cheap calls are affected much less. Full
  river enumeration receives no sampling penalty. This measures sampling noise,
  not the unknown error in the opponent model.
- Correct opportunity counts: button openings and big-blind isolations are counted
  separately. A big-blind check after a limp must not lower the estimated button
  opening rate.
- Explicit public preflop context: a minimum reraise can face the same pot fraction
  as an initial blind decision. The new event representation records whether the
  opponent faced an existing raise using street totals, instead of guessing from
  a numerical pot-fraction threshold. It preserves the existing six public features.

New context and confidence fixtures cover minimum reraises, opportunity counts,
marginal/cheap/strong calls, exact river calls and increasing sample counts.
Existing evaluator, suit/future-board isolation, protocol and decision tests also
pass on the combined candidate.

The pilot used two newly declared seeds, both assignments and both match lengths
against the teammate and trap/check-raise opponent:

| Candidate | Teammate wins | Trap wins | Total wins |
|---|---:|---:|---:|
| Calculation optimization only | 5/8 | 8/8 | 13/16 |
| Sampling margin only, plus optimization | 7/8 | 8/8 | 15/16 |
| Public-context correction only, plus optimization | 6/8 | 8/8 | 14/16 |
| Combined changes, plus optimization | 8/8 | 8/8 | 16/16 |

Pilot selection does not establish generalization. A separate four-seed
confirmation compares the frozen combined candidate with the actual previous
release under identical test configuration. All pilot reports and rejected
candidates are retained, including unfavorable results.

## Fresh comparison and release decision

| Four-seed confirmation | Previous strategy | Combined candidate |
|---|---:|---:|
| Teammate, 400 hands | 7/8 | 6/8 |
| Teammate, 1,000 hands | 6/8 | 8/8 |
| Trap, 400 hands | 5/8 | 5/8 |
| Trap, 1,000 hands | 8/8 | 8/8 |
| Total | 26/32 | 27/32 |

The pilot's 16/16 result did not establish a consistent strategic improvement.
The paired 400-hand point difference was -0.0625 with a four-block bootstrap
interval crossing zero; 1,000-hand difference +0.125 had an interval reaching
zero. Short-match performance against the teammate regressed. The separate
candidate field check won all 16 matches against v5, tightjam, range and pressure,
but used only one seed block. The evidence is insufficient to replace the tested
strategy. The confidence/context changes remain experimental rather than being
selected on attractive pilot scores or the known five losing seeds.

**The actual submission now uses the calculation optimization only.**
`dist/bot.py` matches `checkpoints/learning-v6-optimized.py`, 76,699 bytes,
SHA-256 `44b011220dce58a5a9ce0c8352c66a1f3c5054ef791c1669a1a3cfb2a68abe46`.
This improves calculation efficiency; no stronger win rate is claimed for it.
The full strategy experiment remains available at
`checkpoints/learning-v9-context-confidence.py` with editable experimental sources
`src/context_learning.py`, `src/context_ranges.py`, `src/context_vector_equity.py`
and `src/uncertainty_policy.py`.

The exact optimized release passed one-CPU, 1 GiB Linux CPython 3.11 validation:
full 400- and 1,000-hand wins, +529 / +1,320 chips, no notices, diagnostics or
forfeits; charged banks 6.79 / 33.10 seconds, maximum replies 87.25 / 98.30 ms.
Maximum RSS for the timed command was 40,492 KiB. These whole-match timings use
different deals from earlier stress runs and do not measure the optimization's
isolated speedup; use the controlled microbenchmark above for that comparison.
The original strategy is backed up at `checkpoints/learning-v5.py`.

Reports: `experiments/loss-review-confirmation-comparison.txt`,
`experiments/loss-review-{selected,prior}-confirmation.jsonl`,
`experiments/loss-review-selected-field.jsonl` and
`experiments/loss-review-optimized-stress.jsonl`. Every complete controlled matrix
has a hash/configuration sidecar. The release manifest records the deployed
artifact and its actual validation reports.

## Hardcoding, provenance and legal information

The static audit found only approved imports, no direct file/network/process
access, no opponent-name or opponent-ID field lookup, no test-seed/deal-ID lookup,
and no embedded experiment paths or known test-seed strings. The original
preflop table covers all 22,100 three-card holdings via 1,755 suit classes; it is
a general equity estimate table, not answers for recorded matches.

Normal strategy priors, numeric thresholds and fixed simulation RNG seeds remain.
Those are policy parameters and reproducibility choices, not access to the match
deal seed. Runtime decisions use own cards, visible board, public history, legal
bounds, remaining clocks and accumulated public-action counts. Cards reset at
hand boundaries; no model state is carried between match processes.

The new code was written independently on this project's existing implementation.
No teammate module is imported or bundled in the submission. The static syntax
comparison found zero exact shared top-level function bodies with the teammate's
main bot. That limited comparison is not, by itself, proof of authorship or a
complete security proof. Source and runtime tests provide complementary evidence.

Audit reports are in `experiments/loss-review/*-audit.json`. Replay traces,
unchanged original scores, derived summaries and hindsight examples are in
`experiments/loss-review/`. Tracing wrappers are development tools and are never
included by the submission builder. No upload or organizer contact was performed.

## Reproduce the deployed build and checks

```powershell
python tools/build_submission.py
python tests/learning.py dist/bot.py
python tests/optimization.py dist/bot.py
python tools/audit_submission.py dist/bot.py --out experiments/new-release-audit.json
```

To rebuild the retained combined experiment, use the experimental context modules:

```powershell
python tools/build_submission.py --protocol src/learning_protocol.py --policy src/uncertainty_policy.py --extra src/preflop_key.py --extra src/preflop_table.py --extra src/context_ranges.py --extra src/context_learning.py --extra src/context_vector_equity.py --output checkpoints/rebuilt-context-confidence.py
```
