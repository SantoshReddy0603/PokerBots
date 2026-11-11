# Implementation of the 9 November project review

## Decision

Retain the exact tested submission: `dist/bot.py`, 76,699 bytes, SHA-256
`44b011220dce58a5a9ce0c8352c66a1f3c5054ef791c1669a1a3cfb2a68abe46`.
The opening/isolation candidate tied the screen but lost the fresh confirmation
56–53 against the release. The other isolated fixes and their combination also
failed to improve the screen. No candidate was promoted and the release manifest
remains unchanged. This protects the current version; it does not claim the
current model is free of the reviewed limitations.

The CLI regression is fixed in place. All three model corrections are implemented
in candidate source modules, tested independently and together, and retained
outside `dist/`. They are **not fixes deployed in the selected submission**.
Semantic correctness and improved playing strength are separate requirements.

## Preservation and provenance

Read README, RULES, PROGRESS, LOSS_REVIEW, release manifest and project review,
and inspected the dirty/untracked working tree before editing. The initial
assessment was given before changes: the CLI repair cannot change play; the
model repairs are worthwhile but cannot guarantee stronger match results.

- Exact fallback: `checkpoints/review-1109-fallback.py` and
  `checkpoints/review-1109-fallback.release.json`.
- Pre-edit source archive: `experiments/review-fixes-1109/source-before.zip`.
- Post-change source and compact evidence archive:
  `experiments/review-fixes-1109/source-after.zip`.
- Inventory of 462 pre-existing file hashes:
  `experiments/review-fixes-1109/workspace-before.json`.
- Reproducible candidate source recipes and hashes: the study's `recipes/` directory.
- Original organizer files, frozen opponents, historical checkpoints, supplied zip
  and pre-existing experiment results were preserved. No league/opponent generator
  was rerun. The new tight-reraise diagnostic was built once at a new study path.
- No staging, reset, commit, upload or external contact was performed. Source
  archives preserve the work without changing the user's Git index.

## Confirmed bugs and implementations

1. **Optimization CLI shadowing.** `tests/optimization.py` now uses `cli_args`
   for argparse and `case_args` for holding tuples and loops. Both the default
   command and the fresh `--timing-out` command exited zero and completed all 60
   posterior-equivalence cases. Earlier successful assertion output was not enough
   to establish a successful process exit; this run records both.
2. **Bet-size bucket mismatch.** `src/bet_features.py` defines the shared ratio:
   incremental raise contribution / (pre-action pot + outstanding call). The
   contribution includes the call and equals raise-to minus the raiser's prior
   street total. The small/large boundary is exactly 3/5, with equality large.
   Prediction and observation use the same helper and bucket. The size prior and
   existing prediction convention are preserved; observation is corrected.
3. **Minimum preflop reraises.** `src/review_ranges.py` carries an explicit flag
   derived from public street totals. With the reraise fix enabled,
   `src/review_equity.py` uses this flag, not the faced-fraction heuristic. The
   legal raise-to-4 / minimum-reraise-to-6 fixture queries `preflop/reraise`.
4. **Opening versus isolation opportunities.** `src/review_learning.py` counts
   opponent button opens separately from big-blind isolation opportunities, and
   `src/review_equity.py` selects the matching key/prior. A BB check after a limp
   increments `isolate`, not a failed `open`.

The review learner/policy/equity modules provide explicit ablation flags for
isolating the three fixes; disabled flags retain legacy behavior intentionally.
`src/review_policy.py` contains no confidence penalty. The existing experimental
`context_learning.py`, `context_vector_equity.py` and `uncertainty_policy.py`
were also corrected for the shared bucket/context conventions. Their helper is
bundled by `tools/build_submission.py`; default release builds are unchanged.
The older frozen v9 artifact is preserved, not automatically selected.

Focused tests evaluate the same legal raise through actual policy prediction
and public-history observation, including 18 fold/call/reraise responses,
existing contributions, and targets immediately below/at/above the 0.6 boundary.
They test opening counters and their inference lookups, not only counter names.
A control profile with all fixes disabled matches release learned counts and
complete posterior arrays exactly on 40 real-history cases.

## Paired full-match evidence, including unfavorable results

All matrices used Linux CPython 3.11.9, NumPy 2.2.6, clocks enabled, both bot
assignments and both competition stages (400/1,000 hands). Opponents: frozen
confirmation trap/check-raise, frozen confirmation pressure, a new synthetic
tight-reraise diagnostic and the unchanged external comparison bot. The synthetic
profile is style coverage, not an independently established strong entrant.

Fresh screen: two seed blocks, four opponents, 32 matches per artifact.

| Artifact | Wins / matches | Decision |
|---|---:|---|
| Exact release | 30/32 | Reference |
| Bet-size correction | 29/32 | Not advanced |
| Reraise classification | 26/32 | Not advanced |
| Open/isolation correction | 30/32 | Advanced to untouched confirmation |
| All three corrections | 27/32 | Not advanced |

Four-seed confirmation was declared before screening and consumed only after
selecting the opening candidate. It used 64 matches per artifact:

| Stage | Exact release W/D/L | Opening candidate W/D/L | Paired point difference |
|---|---:|---:|---:|
| 400 hands | 26/0/6 | 26/0/6 | 0.0000 |
| 1,000 hands | 30/0/2 | 27/0/5 | -0.09375 |
| Total | 56/0/8 | 53/0/11 | No promotion |

The 1,000-hand four-block bootstrap interval for paired points was
[-0.2188, +0.0625], and for capped chips/hand [-0.1903, +0.0050]. The interval
does not establish universal harm, but provides no convincing improvement and
includes a substantial observed regression. The external opponent produced the
three additional losses. The other three opponent families tied on match points.
Do not pool the inspected screen with held-out confirmation as fresh evidence.

Complete reports, source/bot/opponent hashes, harness hashes, interpreter,
concurrency and seed manifests are under `experiments/review-fixes-1109/`.
`tools/review_report.py` validated complete matrices before running the strict
paired comparison tool. Per-stage/opponent results, runtime maxima and failures
are in each phase's `*-summary.json`; uncertainty and leave-one-opponent-out
results are in `*-comparison.txt`.

## Resource and correctness validation

The combined candidate passed four focused invocations plus all seven applicable
bot tests and two matrix/league tests (13 invocations). The opening finalist also
passed its seven applicable bot tests. Additional checks cover the ablation
control, both CLI forms, corrected experimental context/confidence source,
research invariants, and a NumPy-unavailable subprocess fallback.

Combined and opening candidates each completed full 400/1,000-hand stress games
on one shared CPU with an inherited 1 GiB address-space limit:

| Candidate | Stage 1/2 chips | Stage 1/2 charged bank | Largest reply | Command max RSS |
|---|---|---|---:|---:|
| Combined | +621 / +1,406 | 17.20 / 10.86 s | 88.02 ms | 40,268 KiB |
| Open/isolation | +487 / +1,294 | 18.51 / 19.40 s | 94.69 ms | 40,524 KiB |

Score-protection log audits passed. There were zero forfeits, corrections or
diagnostic output in all 336 controlled paired-matrix matches and all four
constrained stress matches. These are local WSL results, not organizer hardware
measurements. Ordinary paired matrices used two concurrent matches per artifact;
multiple artifacts/phases overlapped under host load. Affinity/resource limits
apply to the separate constrained runs. Environment details are recorded.

## Further experiments and assessment

Both experiments use the corrected combined profile, without the old confidence
penalty, and have their own artifacts/source hashes:

- **Action-specific preflop ranges:** separate opening, isolation, reraise and
  shove-context evidence; 768 simulated preflop deals weighted by the inferred
  range, choosing both discards from the flop only. This removes the aggregate
  0.45-aggression switching rule in that experiment. Variable-flop features match
  the scalar reference and action-key/no-discontinuity tests pass. Range priors
  and likelihood floors remain uncalibrated approximations.
- **Close expensive sampling:** start at 512 rows, use weighted sampling error
  to identify close calls/discards, and optionally add one batch. Pooled particles
  are reweighted together. A time/work guard bounds launches, and exact river
  enumeration never resamples. Budget/exact-river/pooled-sample tests pass.

Separate fresh research block: combined reference 13/16, sampling experiment
13/16, action-range experiment 12/16. One block cannot support a meaningful
bootstrap interval; neither experiment is promoted. In 30 offline expensive-call
probes, mean effective sample size was about 138, no extra batch was observed,
and both methods had the same mean absolute error, 0.01993, against an independent
4,096-sample model reference. Not every probe was close to a boundary; time and
closeness guards both govern extra work. This is inconclusive, not evidence of
an accuracy gain or true opponent equity. One initialization took 119 ms; the
75 ms internal allocation is a launch estimate, not a preemptive hard timeout.

An additional public-history diagnostic on 3,200 earlier instrumented replay
hands found zero reraise-classifier disagreements among 1,187 opponent preflop
raises, 39 bucket disagreements among 1,555 own postflop raises, and 187 BB checks
after limps. This explains why the legal minimum-reraise regression can be real
yet latent under the current opening policy. These old traces are diagnostic,
not the new selection matrices. Timing-dependent opponent sampling means score
differences alone do not prove which individual fix caused a loss.

Remaining weaknesses: the retained release still has the reviewed model
conventions, heuristic range/continuation likelihoods and the aggregate preflop
large-commitment rule. The next highest-value step is to calibrate action-specific
range/response models under the corrected public features, with original live
diagnostic traces and new holdouts. More samples cannot repair biased ranges;
the sampling experiment also needs a useful measured time allocation before
claiming a benefit.

## Reproduce without overwriting evidence

From this workspace in PowerShell:

```powershell
$wsl = "$env:WINDIR/System32/wsl.exe"
$py = "/home/miyyapuram_saivarun/pokerbots-runtime/Python-3.11.9/python"
& $wsl -d Ubuntu -- $py -B tests/optimization.py
& $wsl -d Ubuntu -- $py -B tests/optimization.py --timing-out experiments/NEW-timing.json
& $wsl -d Ubuntu -- $py -B tests/review_findings.py checkpoints/review-1109-combined.py
& $wsl -d Ubuntu -- $py -B tests/review_control.py
& $wsl -d Ubuntu -- $py -B tests/review_research.py
```

The actual study commands were:

```powershell
& $wsl -d Ubuntu -- $py -B tools/review_fixes.py build
& $wsl -d Ubuntu -- $py -B tools/review_fixes.py run
& $wsl -d Ubuntu -- $py -B tools/review_research.py
& $wsl -d Ubuntu -- $py -B tools/review_fixes.py run --phase research --candidates combined sampling-exp ranges-exp --count 1 --parallel 2
& $wsl -d Ubuntu -- $py -B tools/review_fixes.py run --phase confirmation --candidates baseline openings --count 4 --parallel 2
& $wsl -d Ubuntu -- $py -B tools/review_report.py screen
& $wsl -d Ubuntu -- $py -B tools/review_report.py research
& $wsl -d Ubuntu -- $py -B tools/review_report.py confirmation
```

Study builders/reporters intentionally reject existing outputs. Do not rerun them
over this evidence. To rebuild a candidate at a fresh path:

```powershell
& $wsl -d Ubuntu -- $py -B tools/build_submission.py --protocol src/learning_protocol.py --policy src/review_policy.py --extra src/preflop_key.py --extra src/preflop_table.py --extra src/bet_features.py --extra experiments/review-fixes-1109/recipes/combined.py --extra src/review_ranges.py --extra src/review_learning.py --extra src/review_equity.py --output checkpoints/NEW-combined.py
& $wsl -d Ubuntu -- $py -B tools/evaluate.py checkpoints/NEW-combined.py opponents/league/confirmation/trap.py experiments/review-fixes-1109/tight_reraise.py opponents/league/confirmation/pressure.py experiments/friend-review/pokerbots-discard-holdem-main/bot.py --manifest experiments/review-fixes-1109/seeds.json --split screen --count 2 --jobs 2 --out experiments/NEW-screen.jsonl
```

The already inspected study seeds reproduce tests; future promotion requires
new untouched blocks. No submission was uploaded and nobody was contacted.
