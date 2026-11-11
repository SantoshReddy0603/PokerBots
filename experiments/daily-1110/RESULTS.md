# PokerBots daily review — 10 November 2026

The selected bot now computes the same equities faster. The new river strategy
did not improve the full-match screen and was excluded. The updated teammate
remains a difficult opponent; these results do not establish that our bot beats
it consistently or wins against every entrant.

## Selected artifact

- Project: `C:\Users\varun\OneDrive\Documents\ChatGPT\PokerBots`.
- Submission: `dist/bot.py`, SHA-256
  `bb86e3e7dafd4019157bf9f24cee640e4c9dfbb276883dd92fee1585a03a1990`.
- Exact tested checkpoint: `checkpoints/daily-1110-histogram.py`.
- Previous submission and manifest: `checkpoints/pre-daily-1110.py` and
  `checkpoints/pre-daily-1110.release.json`.
- Default build reproduces the tested bytes. `dist/release.json` references
  the exact artifact, source hashes, current-format resource reports and current
  teammate validation. The manifest generator's defaults match this release.

The only deployed calculation change replaces a temporary row/card/rank
comparison tensor with direct row/rank histogram bins in `src/vector_equity.py`.
It preserves the evaluator, policy, learned statistics, sample counts and random
draws. No teammate source was copied into the submission.

## Updated teammate comparison

The public page returned 404, but the connected GitHub account could read the
private repository. The [current bot](https://github.com/sricharanreddycheruku/pokerbots-discard-holdem/blob/main/bot.py)
was fetched and preserved unchanged as `friend-current.py` in this study.
Its Git blob is `a5c8b01162763bb9c67051a5a625eb06607baf5a`, verified independently
with `git hash-object`; SHA-256 is
`89ca146619df53be4179b77be94dd0da6ca7262e57e76033fa7b117050c55cd0`.
This differs from the teammate ZIP used in earlier project reports.

| Area | Our selected bot | Updated teammate |
|---|---|---|
| Public adaptation | Shrunk action frequencies; aggregate large-preflop-commitment rule | More separate preflop contexts, including context-specific jam rates |
| Equity computation | Independent histogram evaluator; sampled flop/turn, exact compatible river pairs | Packed-count evaluator, preflop lookup cache, turn hero-runout cache and exact river pairs |
| Betting | Candidate sizes scored against a heuristic continuing range | Size-aware continuation estimates, restricted deep-stack shoves and a large-call discount |
| Current rules | Fresh processes per leg; no lead lock on official 200/500-hand leg inputs | Updated leg clock defaults; old local lead protection removed |

These source differences suggest hypotheses, not causal explanations of the
match results. The optimization uses NumPy's direct histogram primitive; it does
not import the teammate's packed-count evaluator or parameter settings.

## Calculation equivalence and timing

All 16,536 rank rows in the isolated probe agreed exactly. Sixty complete
fixed-draw posterior cases, across all three postflop streets, had identical
equities, weights, outcomes and strength arrays. The existing learning suite
also passed its 15,000 independent scalar/vector rank checks.

Paired warm estimates used 20 cases per street, five repetitions and alternating
execution order on one Linux CPU, with 512 samples or full river enumeration:

| Street | Prior median | Selected median | Reduction |
|---|---:|---:|---:|
| Flop | 28.00 ms | 26.10 ms | 6.8% |
| Turn | 24.44 ms | 23.27 ms | 4.8% |
| River | 27.24 ms | 25.63 ms | 5.9% |

These are local calculation timings under host load. They are not whole-match
speedups or win-rate improvements. Exact comparisons and raw alternating timings
are in `histogram-probe.json` and `histogram-timing.json`.

## Playing-strength experiment and unfavorable evidence

An isolated candidate uses complete showdown rank, including kickers and ties,
when ordering river opponent holdings for range inference and continuation.
It corrects demonstrable inversions in the old heuristic. It passed 86,480
compatible pair-order checks, 10,000 independent scalar rank checks, 60 isolation
cases and suit/tie fixtures. Semantic correctness did not translate into a
validated strength improvement.

Both artifacts completed 32 clocked matches against the **updated** teammate,
trap/check-raise, pressure and tight-reraise families. Two fresh seed blocks,
both assignments and both official stages were included; each match had two
independently launched legs.

| Artifact | Teammate W/D/L | Other families W/D/L | Total W/D/L |
|---|---:|---:|---:|
| Frozen release before histogram optimization | 1/0/7 | 24/0/0 | 25/0/7 |
| River-order strategy candidate | 0/0/8 | 24/0/0 | 24/0/8 |

Strict matrix/configuration comparison passed. Stage 1 paired match points tied;
Stage 2 candidate-minus-baseline points averaged -0.0625. Two-block uncertainty
is weak, and time-adaptive opponent sampling can change paths under host load.
Nevertheless, the candidate failed the declared positive-points gate. It was
not promoted and the four reserved confirmation blocks remain unused. Higher
raw chip means against this sampled pool did not override worse match points.

The exact selected histogram artifact separately played **four fresh matches**
against the updated teammate: Stage 1 2 wins/0 losses; Stage 2 0 wins/2 losses.
This is a different seed block from the screen and is not a paired comparison
with the 1/8 baseline result. It does not demonstrate an improvement from 1/8
to 2/4. All 68 matrix matches had zero forfeits, corrections or diagnostics.

## Exact-release resource and protocol checks

Linux CPython 3.11.9, NumPy 2.2.6, one shared CPU and inherited 1 GiB address-space
limit; unchanged updated organizer engine:

| Stage / opponent | Hands | Net chips | Largest per-leg bank | Allowed per-leg bank |
|---|---:|---:|---:|---:|
| Stage 1 / pressure | 400 | +4,332 | 9.97 s | 30 s |
| Stage 2 / trap | 1,000 | +3,238 | 32.76 s | 75 s |

Both complete two-leg matches passed. Largest response was 45.09 ms; command
maximum RSS was 40,484 KiB. Zero corrections, diagnostics or forfeits. The eight
recorded check invocations passed: protocol, selection, evaluator, learning,
review decisions, official-leg compatibility, protocol without site packages
and static submission audit. A separate official-leg compatibility run without
site packages also passed. Static audit found no opponent/seed lookup or direct
file/network/process access in our artifact; syntactic checks are not proof of
authorship. See `histogram-checks.jsonl`, `histogram-audit.json`,
`histogram-no-site-legs.txt`, `histogram-stress.jsonl` and its GNU time log.

## Reproduction and next priority

From the project root with the provisioned Linux Python:

```text
python3.11 -B tools/build_submission.py --output checkpoints/NEW-rebuild.py
python3.11 -B tests/learning.py dist/bot.py
python3.11 -B tools/compare.py experiments/daily-1110/screen-river-order.jsonl experiments/daily-1110/screen-baseline.jsonl
python3.11 -B tools/release_manifest.py --output experiments/NEW-release.json
```

Study builders, runners and reporters preserve their existing outputs. Use new
paths and genuinely untouched seed blocks for new studies; rerunning these
inspected blocks is reproduction, not fresh confirmation.

The next strategic priority is public-history diagnostics and calibration of
large commitments and responses to raises across several independent strong
opponent styles. The new teammate's advantage warrants investigation, while
the weaker synthetic families need stronger challengers. Additional samples
alone cannot correct a biased opponent model. No upload, push, commit or message
to another person was performed. Original organizer files and prior working-tree
changes were preserved.
