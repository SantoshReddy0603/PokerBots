# Project review - 9 November 2026

Reviewed the updated repository, active release sources, experimental variants, tests, evaluation tools, and recorded comparisons. This review leaves the user's source and submission unchanged. Fresh validation reports/logs are under `experiments/independent-review-1109*`.

## Assessment

The bot has advanced substantially since the first review. The active release now has within-match learning, a tested NumPy evaluator, exact river enumeration, continuing-range bet comparisons, and score protection. Release bytes reproduce from the recorded sources, all source hashes match the manifest, and 44 complete experiment matrices passed the current structural/hash/scoring validator.

Keep the current release as the baseline while correcting the specific issues below. The decision to retain the combined context/confidence experiment outside the release was reasonable: its four-seed confirmation was mixed and did not establish a consistent improvement. A broad rewrite or automatic promotion of v9 is not justified by that evidence.

Current release: `dist/bot.py`, 76,699 bytes, SHA-256 `44b011220dce58a5a9ce0c8352c66a1f3c5054ef791c1669a1a3cfb2a68abe46`.

## Confirmed findings

### 1. Fold observations and fold predictions use different bet-size buckets (P2)

Locations: `src/learning_policy.py:152-154`, `src/learning.py:43-46`.

The policy queries `fold_small` or `fold_large` using `cost / (pot + call)`. The learner records the response using `addition / pot` before the raise. These denominators differ when responding to a bet, so the model can learn from an observation in a bucket different from the one that predicted it.

Reproduced legal example:

- Preflop: button raises to 6, opponent reraises to 18, button raises to 40, opponent calls. Pot is 80.
- Flop: opponent bets 20. Pot is now 100, and the button owes 20.
- The policy's 35% target raises to 62. Its ratio is `62 / 120 = 0.517`, classified as small.
- If the opponent folds, the learner records `62 / 100 = 0.62`, classified as large.

Use one shared size definition for observing and predicting actions, replaying the same pre-action pot and call amount. Add a fixture that passes the same legal raise through prediction and observation and requires identical bucket keys. Apply this consistently to experimental learners/policies as well.

### 2. Minimum preflop reraises are classified as opens (P2)

Location: `src/vector_equity.py:178`.

`faced > .34` is used to choose the reraise frequency. After a button raise to 4 and a big-blind minimum reraise to 6, the faced ratio is `2 / 6 = 1/3`. The release therefore queries the opening model, with prior 0.65, instead of the reraise model, with prior 0.13. The resulting range can be much wider than intended.

Carry an explicit flag for facing an existing raise, derived from public street totals/history. The experimental `src/context_ranges.py` and `src/context_vector_equity.py` already implement this distinction, and `tests/context.py` covers the example. Test this correction independently from the confidence penalty before considering promotion.

### 3. Big-blind checks dilute button opening statistics (P2)

Location: `src/learning.py:39-40`.

When we limp on the button and the opponent checks in the big blind, the release records a failed `preflop/open` opportunity. That was an opportunity to isolate a limper, not an unopened button opportunity. Different actions with different baseline frequencies are pooled, affecting later range estimates.

A direct probe produced `('preflop', 'open'): (0, 1)` for this limp/check history. The experimental `src/context_learning.py` already separates `open` and `isolate`. Move the matching learner and inference changes together into an isolated candidate and test them on multiple opponent styles. Do not change the counters without changing the corresponding lookup keys.

### 4. The optimization test crashes before reporting completion (P2)

Location: `tests/optimization.py:29`, `:45`, `:50`.

The parsed argument namespace is stored as `args`, then overwritten with a hand tuple and reused as a loop variable. The documented command fails with:

```text
AttributeError: 'tuple' object has no attribute 'timing_out'
```

The 60 posterior-equivalence assertions were reached and passed in this execution; the failure occurs afterward. Thus this is a broken test/reporting entry point, not evidence of differing evaluator outputs. Rename the CLI namespace and case tuple variables, then run both the default command and the `--timing-out` form. A release checklist should require process exit status zero, not merely favorable output before a crash.

## Further changes worth testing

1. **Use action-specific preflop evidence for large commitments.** In `src/learning_policy.py:75-78`, most non-trip hands still use the old heuristic when aggregate aggression is at or below 0.45. Above that threshold, the policy switches to table equity with a different decision rule. A wide opener who reraises only strong holdings can be misrepresented by this aggregate. Test smooth, separately calibrated opening/reraise/shove ranges; compare against both wide and tight opponents. This is a strategic experiment, not a proven universal improvement.
2. **Resolve close expensive decisions with additional sampling.** The main NumPy path normally uses 512 samples regardless of decision difficulty. Measure effective sample size and allocate extra batches to close calls or discards, with an elapsed-time bound. Exact river enumeration needs no Monte Carlo penalty, but still has opponent-model uncertainty. Test this separately from the existing confidence-penalty candidate, whose broad promotion remains unsupported.
3. **Expand confirmation against strong styles.** The latest strategic confirmation contains four seeds and two opponents (teammate and trap). The optimized release itself has a 16-match pilot with two seeds; the stronger four-seed evidence belongs to the previous strategy and experimental combined candidate. Fixed-draw equivalence supports the optimization, but does not turn every previous score into a new test of the exact artifact. Add fresh paired blocks against independent aggressive, tight-reraise, check-raise, calling-station, and changing-style policies. Treat the 35-opponent single-assignment coverage run as coverage: one result was an opponent forfeit.
4. **Capture decision traces during selected original matches.** Replaying losses later changes time-dependent opponent actions, as the existing loss report correctly explains. Use a consistent tracing configuration for diagnostic comparisons and capture a compact set of original decisions/equities/weights. Keep traced diagnostics separate from production timing and strategy selection.
5. **Snapshot the working release in version control.** Several source files required by the default build are currently untracked, including the learning and vector-equity modules. The working folder rebuilds correctly, but the existing commit does not contain the complete current release sources. Preserve source, manifest, focused tests, and compact experiment evidence together. Archive duplicate experimental variants only after retaining reproducible build recipes.

## Verification performed now

Nine test scripts passed under WSL CPython 3.11.9:

- `tests/protocol.py`
- `tests/selection.py`
- `tests/evaluator.py` (24,000 oracle/suit cases)
- `tests/learning.py` (15,000 vector/scalar ranks, 2,000 flop features, river and information-boundary checks)
- `tests/review_decisions.py`
- `tests/review_ranges.py`
- `tests/review_lock.py`
- `tests/review_matrix.py`
- `tests/review_league.py`

`tests/optimization.py` failed as described above. A separate subprocess launched with `python -S` completed a legal postflop response without NumPy or diagnostics. This is fallback smoke coverage, not a full fallback tournament evaluation.

Fresh full matches used the exact submission and the confirmation trap opponent, on one shared CPU with a 1 GiB address-space limit:

| Stage | Hands | Net chips | Bank used | Maximum reply | Notices / diagnostics / forfeits |
|---|---:|---:|---:|---:|---|
| 1 | 400 | +546 | 14.453 s | 77.85 ms | 0 / 0 / 0 |
| 2 | 1,000 | +1,357 | 28.986 s | 76.27 ms | 0 / 0 / 0 |

Score-lock log checks passed: protection began at hands 217 and 422 respectively, preserving the full stage caps. These are two smoke/stress results, one assignment each, not a new win-rate estimate or evidence of a strategy improvement.

Command, from the project root:

```powershell
wsl -d Ubuntu -- taskset -c 0 prlimit --as=1073741824 -- /home/miyyapuram_saivarun/pokerbots-runtime/Python-3.11.9/python -B tools/validate_release.py --prefix independent-review-1109 --opponents opponents/league/confirmation/trap.py opponents/league/confirmation/trap.py
wsl -d Ubuntu -- /home/miyyapuram_saivarun/pokerbots-runtime/Python-3.11.9/python -B tools/check_score_lock.py independent-review-1109 --alternating-blinds --late-win
```

The output from the first command is saved in `experiments/independent-review-1109-stress.jsonl`; full match logs and stderr files are in the corresponding `-s1` and `-s2` directories. Use a new prefix to repeat without overwriting review evidence.

## Recommended next step

Fix the optimization runner, add a regression for the bet-size bucket mismatch, and build a candidate containing that learning fix. Separately test the existing context corrections without the confidence penalty. Compare both against the current release on fresh paired seeds before merging strategic changes. Keep the current tested artifact available throughout.
