# Pokerbots progress and handoff

Updated 9 November 2026 (IST), project calendar.

## Project-review findings implemented and tested

See `REVIEW_FIXES_2026-11-09.md` for implementation, uncertainty and commands.
Read the requested documents and dirty tree first, then assessed the fixes before
editing: the CLI repair cannot affect play; model corrections can change match
results and require validation. Preserved 462 pre-existing hashes and a source
archive under `experiments/review-fixes-1109/`. Exact fallback is
`checkpoints/review-1109-fallback.py` plus its saved release manifest. No Git reset,
staging, commit, historical-result overwrite or frozen-opponent rebuild occurred.

Fixed `tests/optimization.py` CLI namespace shadowing (`cli_args` vs `case_args`).
Both default and `--timing-out` forms exited zero with all 60 assertions passed.
Implemented shared raise-size features, explicit public preflop reraise flags,
and matching open/isolation counters/lookups in isolated review candidates.
Updated corresponding experimental context/confidence modules consistently;
none were automatically promoted. A disabled-fix control preserves release counts
and full posteriors exactly in 40 public-history cases. Focused regressions cover
18 legal raise-response paths, calls, reraises, the exact 0.6 boundary and the
raise-to-4/minimum-reraise-to-6 case, independently of confidence penalties.

Fresh paired screen, both assignments and 400/1,000 hands, four styles, two seeds:
baseline 30/32; bet-size 29/32; reraise 26/32; opening/isolation 30/32; combined
27/32. The opening candidate advanced unchanged to four untouched confirmation
blocks: baseline 56/64 versus candidate 53/64. At Stage 1 both won 26/32; Stage 2
baseline won 30/32 versus 27/32. Paired Stage 2 points -0.09375, four-block 95%
bootstrap [-0.2188, +0.0625]. No convincing improvement; retain the tested release.

Separate research block: corrected combined 13/16; extra sampling 13/16;
action-specific preflop range simulation 12/16. Neither is promoted. Sampling
probe: mean ESS 138 across 30 expensive-call states; no second batch observed and
no accuracy gain against a model-conditioned 4,096-row reference. This does not
establish true opponent equity. Prior replay public-history diagnostic: 0/1,187
reraise-classifier disagreements, 39/1,555 raise bucket disagreements, and 187 BB
checks after limps. This is diagnostic evidence, not new selection data.

All 336 full matches in controlled matrices had zero failures, notices and
diagnostic output. All matrices include hashes/configuration, timings and complete
assignment/stage coverage; paired comparisons preserve whole seed blocks.
Combined passed four focused + seven applicable bot + two matrix/league checks;
opening finalist also passed all seven applicable bot tests. Research/control
fixtures, experimental context/confidence checks and no-NumPy fallback passed.

Constrained Linux CPython 3.11 (one CPU, 1 GiB) full-stage checks passed for both
combined and opening candidates, with score-lock audits. Combined chips +621/+1,406,
banks 17.20/10.86 s, max reply 88.02 ms, command RSS 40,268 KiB. Opening chips
+487/+1,294, banks 18.51/19.40 s, max reply 94.69 ms, RSS 40,524 KiB. These
stress games use separate deals and are resource checks, not paired speed gains.

Actual reproduction commands (PowerShell; study outputs are write-protected,
so use fresh output paths/prefixes when repeating):

```powershell
$wsl = "$env:WINDIR/System32/wsl.exe"
$py = "/home/miyyapuram_saivarun/pokerbots-runtime/Python-3.11.9/python"
& $wsl -d Ubuntu -- $py -B tests/optimization.py
& $wsl -d Ubuntu -- $py -B tests/optimization.py --timing-out experiments/NEW-timing.json
& $wsl -d Ubuntu -- $py -B tests/review_findings.py checkpoints/review-1109-combined.py
& $wsl -d Ubuntu -- $py -B tests/review_control.py
& $wsl -d Ubuntu -- $py -B tests/review_research.py
& $wsl -d Ubuntu -- $py -B tools/review_fixes.py run --phase screen --count 2
& $wsl -d Ubuntu -- $py -B tools/review_fixes.py run --phase confirmation --candidates baseline openings --count 4 --parallel 2
& $wsl -d Ubuntu -- /usr/bin/time -v taskset -c 0 prlimit --as=1073741824 -- $py -B tools/validate_release.py --bot checkpoints/review-1109-combined.py --opponents opponents/league/confirmation/trap.py experiments/review-fixes-1109/tight_reraise.py --prefix NEW-combined-stress
```

The study's `recipes/`, summaries, comparison files, CLI/test logs and stress
reports preserve actual commands, hashes and unfavorable results. The new report
includes fresh-path build/evaluation commands and all remaining model weaknesses.
Selected submission stays `dist/bot.py`, 76,699 bytes, SHA-256
`44b011220dce58a5a9ce0c8352c66a1f3c5054ef791c1669a1a3cfb2a68abe46`;
its manifest and default-source rebuild remain unchanged. The three model bugs
are repaired in candidates, not deployed in this retained release. Next priority:
calibrate action-specific range/response models under consistent features before
spending more computation or changing production policy. No upload or contact.

## Current optimized release and five-loss analysis

Reviewed all five previous confirmation losses using new decision traces. Exact
original paths cannot be reconstructed from score-only reports: timed opponent
simulation and instrumentation changed replay results, which remain separate.
Documented full-stack exposure, range-estimation risk and ordinary bad beats in
`LOSS_REVIEW.md`, with offline-only hindsight examples and all original scores.

Deployed only calculation caching: river hero ranks once, reused river opponent
scores and reused current-street strengths. Sixty complete fixed-draw posterior
comparisons matched v5 exactly. Local microbenchmarks improved flop/turn/river
times by about 11/15/32 percent. Current `dist/bot.py` equals
`checkpoints/learning-v6-optimized.py`, 76,699 bytes, SHA-256
`44b011220dce58a5a9ce0c8352c66a1f3c5054ef791c1669a1a3cfb2a68abe46`.
Previous strategy remains at `checkpoints/learning-v5.py`.

Independently implemented sampling-error and explicit preflop-context candidates.
Combined won 16/16 pilot matches, then 27/32 fresh confirmation versus v5's 26/32,
including a 400-hand regression. A one-seed wider field check won 16/16. Evidence
was inconclusive, so strategy changes remain experimental. Their context modules
and confidence policy are preserved outside the default build. No test-seed,
opponent-name or recorded-deal lookup was found; the equity table covers all
22,100 holdings and no exact teammate function bodies match. Audit scope limits
are documented rather than presenting syntax comparison as proof of authorship.

Exact optimized artifact passed constrained Linux CPython 3.11, 1 CPU, 1 GiB:
full-cap wins +529/+1,320, banks 6.79/33.10 s, maximum replies 87.25/98.30 ms,
maximum RSS 40,492 KiB, no bot notices/diagnostics/forfeits. Manifest and default
build select this artifact, with v5 as fallback. All experimental reports are kept.

## Previous independently implemented strategy release

After the follow-up request, implemented a match-local public frequency model,
original base-15 NumPy histogram evaluator, 512-sample flop/turn estimates, exact
river enumeration, frequency-conditioned ranges, preflop defense and continuing-range
bet-size EV. Added exact blind reserves and late guaranteed-positive-score protection.
Default builds and `dist/bot.py` now select `checkpoints/learning-v5.py` exactly:
76,045 bytes, SHA-256 `5f6746cae189f2b94e16c06dae8834383179d12e92f0d139ed1c32edb1817a5e`.
The previous release remains at `checkpoints/pre-friend-review.py`. No teammate
source was included in the new implementation; it is used only as a test opponent.

Fresh confirmation against the teammate: selected 5/8 wins at 400 hands and 6/8
at 1,000; incumbent 0/8 at both lengths on the same configuration. Strict paired
comparisons are in `experiments/learning-confirmation-comparison.txt`. There were
four independent seed blocks, both assignments, production clocks and no bot
failures/notices/diagnostics. This is a local improvement, not a tournament guarantee.
The separate 35-opponent coverage run yielded 34 completed wins and one excluded
opponent crash (`aggro_3bet.py`, missing `max_raise`); no candidate failures.
The completed wider matrix won 47/48: all eight against the incumbent and each
of four other league styles, and seven of eight against trap/check-raise. That
trap loss is retained as a remaining weakness. Across the teammate development
screen and this field matrix, selected won 54/56, without claiming a pooled
confidence interval across the differently configured reference screen.

New vector/learning, existing protocol/selection/evaluator/decision/range/lock/matrix
tests, scalar fallback and static submission checks passed. Constrained Linux
CPython 3.11.9 (one CPU, 1 GiB) completed full-cap wins at both lengths. Charged
banks 15.64 / 51.85 s, maximum replies 99.66 / 96.65 ms, maximum RSS 40,332 KiB.
The exact bytes and source hashes are recorded in `dist/release.json`. All recorded
organizer source hashes remain unchanged. See `STRENGTHENING_REPORT.md` for methods,
additional matrices, limitations and build commands. No upload or external contact.

## Teammate archive comparison, 9 November

Historical first-pass result, superseded by the current release above.

See `FRIEND_COMPARISON.md` for the source comparison, exact hashes, commands and
results. Added isolated candidate sources `src/friend_score_protocol.py` and
`src/friend_ranges.py`: exact alternating-blind capped-lead protection and cached
river hero/board ranks. Build with `--friend-review --output checkpoints/friend-review.py`.
Boundary, fixed-sample equivalence and existing regression tests passed. Linux
CPython 3.11 constrained full matches passed at 400/1000 hands with full capped
wins and zero protocol/resource failures. River microbenchmark was about 13%
faster. Both incumbent and candidate lost all eight matches against the teammate's
NumPy-enabled bot; the candidate split four matches against the incumbent and won
four against tightjam. No demonstrated match-point improvement, so no promotion.
Default builds, `dist/bot.py` and `dist/release.json` retain the prior release;
`checkpoints/pre-friend-review.py` is its exact backup. Original organizer files
and the supplied zip are unchanged.

Review update, 4 November: see `REVIEW_AND_IMPROVEMENT_PLAN.md` and `experiments/review-2026-11-04.json`. All three existing tests passed again under WSL Python 3.11.9; source/input hashes and release reproducibility checked. Read-only probes identified a terminal-call threshold problem and preflop low-trip overvaluation. The 40-match final pool uses only two deal seeds and a shared opponent template. A matching public event listing was found, but official amendments remain unverified. This review changes documentation only, adds an audit result, and does not change the selected bot or claim new full-match results.

M0 through M7 local release preparation complete. The selected file is dist/bot.py, byte-identical to checkpoints/betting.py. Team eligibility, organizer amendments and upload are team-side items. See milestone records for reproducibility and limits.
## M0 complete

Extracted the six inspected ZIP entries with `Expand-Archive -LiteralPath (Get-ChildItem pokerbots_1/*.zip).FullName -DestinationPath vendor`. Original files untouched. Hashes in experiments/sources.csv, rules in RULES.md. Frozen splits in experiments/seeds.json, report fields in experiments/schema.json, subprocess fixtures in tests/protocol.py for M1.

Provisioned official Windows embeddable Python 3.11.9 amd64 at C:/Users/varun/AppData/Local/PokerBots/python311/python.exe with Invoke-WebRequest https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip followed by Expand-Archive. Archive SHA-256 009D6BF7E3B2DDCA3D784FA09F90FE54336D5B60F0E0F305C37F400BF83CFD3B. `-VV` reported de54cf5, MSC v.1938. All subsequent commands use this interpreter.

- `python vendor/Starter_Kit/engine.py vendor/Starter_Kit/bot.py vendor/Starter_Kit/example_bots/random_bot.py --stage 1 --seed baseline-s1 --log-dir experiments/baseline-s1`: 400/400, starter -24, no notices/forfeits, 1.44 s command elapsed.
- `python vendor/Starter_Kit/engine.py vendor/Starter_Kit/bot.py vendor/Starter_Kit/example_bots/random_bot.py --stage 2 --seed baseline-s2 --log-dir experiments/baseline-s2`: 1000/1000, starter +740, no notices/forfeits, 2.54 s command elapsed.

Clocks enabled. Reported bank usage 0.00 s because both matches fell within the runner's startup grace. The random opponent uses an unseeded policy RNG, so the fixed seeds reproduce deals, while exact random actions vary. One match per stage provides no useful estimate of win rate. Memory unmeasured. Next: M1 package and time the generated bot using a separate harness.

## M1 complete

Generated standard-library dist/bot.py with state, authoritative history, corrections and bounded exception handling. Archived passive checkpoint dist/m1_bot.py. Ran `python tools/build_submission.py`, `python tests/protocol.py` (isolated cwd fixture passed) and `python tools/benchmark.py dist/bot.py vendor/Starter_Kit/example_bots/random_bot.py --stage S --seed smoke-sS --log-dir experiments/m1-sS` for S=1,2. Full matches +410 and +408, zero notices, forfeits and stderr. Charged 0.186/0.185 s, max 16 ms; Windows monotonic timer quantization explains reported zero p99. Memory not measured. SHA-256 0ec95b182835f48c81409e91b770e06a63b76122517083270aee3ffa8c2bb46b. Separate harness preserves organizer engine and charges from reply two. Next M2 oracle and equity validation.

## M2 complete

`python tools/build_submission.py; python tests/evaluator.py`: 24,000 exact seven-card tuple comparisons against unchanged organizer evaluator and suit-rotation invariance, deterministic fixed-seed equity and board-playing tie assertions passed. 161,975 ranks/s in this run. Simulations exclude known dead cards, choose both simulated discards from the flop only, use common runouts for all three candidates, and stop in batches at the deadline. No equity policy timing gate inferred from evaluator throughput. Next M3 paired discard comparisons and clock checks.

## M3 complete

`python tools/discards.py` ran 1,400 paired scenarios (350 each on validation-0 through validation-3) across rank, made, draw and rollout opponent discard styles. Equity discard gains in showdown points ranged +0.047 to +0.070 vs rank and +0.009 to +0.026 vs made. Per-seed normal 95% half-widths in experiments/m3-pairs.txt. `python tools/evaluate.py checkpoints/discard.py checkpoints/passive.py opponents/made_passive.py --split validation --count 2 --out experiments/m3-matches.jsonl` ran 16 full clocked matches using both assignments. Rank-only: 4–0 at each stage, +0.185/+0.231 chips per hand. Made-only: three wins and one draw at Stage 1, four wins at Stage 2, +0.018/+0.049 chips per hand. Two independent deal seeds per stage limits generalization. No notices/forfeits. Candidate bank max 3.52/8.78 s. Frozen discard checkpoint SHA-256 e0d5119c012471f872f9be5acf03a829124170624ca4e556067422322ee0811f. Next M4 betting versus diverse styles.


## M4 complete

`python tools/build_submission.py; python tests/protocol.py; python tests/selection.py; python tools/build_opponents.py`. Added three-card preflop features, pot-odds thresholds, position and opponent raise evidence, bounded postflop rollouts and pot-relative value/bluff sizing. Frozen checkpoint SHA-256 404af500d979b827d40bd34ff2aecb3c2545d203dd9c94ddc0be53a685c9e171.

`python tools/evaluate.py checkpoints/betting.py opponents/tag.py opponents/loose.py opponents/station.py opponents/overfold.py opponents/aggro.py opponents/shove.py opponents/equity.py --split training --count 1 --jobs 6 --out experiments/m4.jsonl`: both assignments per stage, 28 wins in 28 matches. No notices or forfeits. One independent seed per opponent and stage, correlated assignments, no generalization claim. Over-folder produced the narrowest wins, +474 to +1510 chips. Match report retains every score and clock reading. Corrected threaded stdout capture and added higher-resolution timing and stderr counts for later runs. Next M5 test smoothed action and discard adaptation against frozen betting.

## M5 complete

Added shrinkage-smoothed aggression and fold rates, showdown-informed discard mixture, and bounded response adjustments in checkpoints/adaptive.py (SHA-256 f76d089985bb2de81ed41ed3cdcde45ca056009bdabc0f42a9957a913876e700). Only aggregate actions and legal showdown observations enter the model, once per completed hand. No lookahead solver added.

`python tools/evaluate.py checkpoints/adaptive.py checkpoints/betting.py opponents/overfold.py opponents/aggro.py opponents/equity.py --split validation --count 1 --jobs 8 --out experiments/m5-adaptive.jsonl` and `python tools/evaluate.py checkpoints/betting.py opponents/overfold.py opponents/aggro.py opponents/equity.py --split validation --count 1 --jobs 5 --out experiments/m5-base.jsonl`. Base won all four head-to-head matches. Both went 12/12 versus shared opponents. Adaptive minus base averaged about -0.69/-0.17 chips per hand at stages 1/2 across those styles, with only one seed block per stage. Max adaptive bank 18.70/43.48 s. No corrections, forfeits or stderr. Adaptation gate failed; retain betting checkpoint for final confirmation. Next M6 frozen comparisons on sealed seeds and separately configured opponents.


## M6 complete

Linux CPython 3.11.9 was built in Ubuntu WSL from https://www.python.org/ftp/python/3.11.9/Python-3.11.9.tgz with `./configure; make -j4`. Source archive SHA-256 e7de3240a8bc2b1e1ba5c81bf943f06861ff494b69fda990ce2722a504c6153d. Interpreter /home/miyyapuram_saivarun/pokerbots-runtime/Python-3.11.9/python, GCC 11.4.0.

`python tools/evaluate.py checkpoints/C.py opponents/final_tag.py opponents/final_aggro.py opponents/final_station.py opponents/final_shove.py opponents/final_equity.py --split final --count 2 --jobs 6 --out experiments/m6-C.jsonl` for C=betting and adaptive. Used sealed-0 and sealed-1, both assignments, 400 and 1000 hands, clocks enabled. Both candidates won all 40 matches and had zero corrections, forfeits or stderr. Fixed betting averaged +9.709/+8.618 raw chips/hand and +1.0/+1.0 capped chips/hand. Weakest average matchup was tight-aggressive at +5.096/+5.446. Max bank 21.93/54.17 s, worst match p99 26.14/27.56 ms, max reply 37.77/53.64 ms. Retained fixed betting based on the validation head-to-head, more raw chips per hand on sealed opponents, and lower worst bank usage. Bootstrap results from `python tools/compare.py experiments/m6-adaptive.jsonl experiments/m6-betting.jsonl` are conditional on only two seed blocks. The observed win rate does not establish out-of-pool odds.

`python tools/peer_matches.py opponents/final_tag.py opponents/final_aggro.py opponents/final_station.py opponents/final_shove.py opponents/final_equity.py --jobs 3 --out experiments/m6-peers.jsonl` ran 40 peer matches for a seven-player field exercise. `python tools/field.py experiments/m5-head-to-head.jsonl experiments/m6-betting.jsonl experiments/m6-adaptive.jsonl experiments/m6-peers.jsonl` resampled the local edge results in 2,000 Swiss and round-robin trials. The betting-vs-adaptive edge comes from M5. Standings sensitivity is in experiments/m6-field.txt and describes this local field only. Aggregate metrics are in experiments/m6-summary.jsonl. Next M7 validate the exact bytes under constrained Linux and generate local release metadata.


## M7 local release complete

`wsl -d Ubuntu -- /usr/bin/time -v taskset -c 0 prlimit --as=1073741824 -- /home/miyyapuram_saivarun/pokerbots-runtime/Python-3.11.9/python -B tools/validate_release.py`. Both bots and the runner shared one logical CPU. Each inherited the 1 GiB address-space limit. Clocked full matches of the exact file completed at 400 and 1,000 hands. Wins were +4,647 versus final_aggro and +5,398 versus final_equity. Zero corrections, forfeits or stderr. Bot response bank charged 10.386/29.426 s out of 60/150 s, p99 15.94/15.53 ms, max 21.04/28.53 ms, launch to first reply 82.66/99.35 ms, wall 11.27/37.76 s. GNU time reported maximum RSS 15,804 KiB for the timed command and 52.17 s total elapsed. Local WSL results do not measure organizer hardware. Raw release results and GNU time output are in experiments/release-linux.jsonl and experiments/release-linux-time.txt.

`python tools/release_manifest.py` generated dist/release.json. Rebuilt with `python tools/build_submission.py` and verified the bytes against the tested hash. Then ran `python tests/protocol.py`, `python tests/selection.py` and `python tests/evaluator.py` successfully, including clean-directory launch, raise type and bounds, correction/reset, fold and all-in fixtures, explicit card cases and 24,000 oracle comparisons. Original and extracted reference source hashes were rechecked against experiments/sources.csv and matched. Strategy is frozen for local release on 4 November IST. The early freeze follows the request to finish local preparation in this run.

- Submission file dist/bot.py, 11,875 bytes. SHA-256 404af500d979b827d40bd34ff2aecb3c2545d203dd9c94ddc0be53a685c9e171.
- Low-compute fallback checkpoints/discard.py, tested in M3. If needed, use its exact contents as bot.py.
- Public searches for the supplied title and deadline found no event-specific announcement. Team needs to confirm current limits and AI-assistance guidance, eligibility and verified registration, then handle upload and platform confirmation. Supplied deadline 15 November 2026, 23:59 IST. No upload or contact performed.

## Review implementation, development checkpoints

The original champion stays at dist/bot.py and checkpoints/betting.py (404af500d979b827d40bd34ff2aecb3c2545d203dd9c94ddc0be53a685c9e171). Candidate builds use separate paths.

- Evaluation. Added strict match-matrix metadata and validation, stage-specific paired point/cap/chip comparisons and leave-one-opponent-out sensitivity. Fixed wall clock endpoints. Froze pilot, screen, confirmation and stress splits in experiments/review-seeds.json. Built distinct league policies with `python tools/build_league.py` and `python tools/build_league.py --variant confirmation`. Independent here means distinct betting decisions sharing the verified protocol/evaluator. The confirmation generator changes policy RNG seeds and is not a holdout of entirely independent opponent families. `python tests/review_matrix.py` passed.
- Adversary pilot. `python tools/evaluate.py checkpoints/betting.py checkpoints/adaptive.py opponents/league/development/adversary.py opponents/league/development/adversary_wide.py opponents/league/development/adversary_tight.py --manifest experiments/review-seeds.json --split pilot --count 1 --jobs 8 --out experiments/review-adversary.jsonl` completed 16 clocked matches. The tight parameter trial conceded the fewest raw chips among the three (11,679 vs 14,631 and 15,017 over four matches each), although all three lost every match. This is a weak adversary search, not evidence that the selected profile is strong.
- Decision repairs. `python tools/train_preflop.py --samples 512 --jobs 8` generated embedded uniform and premium-weighted estimates for all suit classes. `python tools/build_submission.py --policy src/candidate_policy.py --extra src/preflop_key.py --extra src/preflop_table.py --output checkpoints/review-calls.py`. Terminal calls use incremental EV; normal preflop uses a blend and trips use calibrated estimates. A 4,000-rollout independent reference estimated three deuces at .3345 vs the .322 uniform table entry. AAK and AKQ references .8041/.6410 vs .829/.622. These are model-conditioned estimates, with a much smaller effective sample for premium ranges.
- Score protection. Added `--protocol src/score_protocol.py` to build checkpoints/review-lock.py from the calls recipe. Count consecutive authoritative results; protect only a full capped lead after subtracting two blinds per remaining hand. `python tests/review_decisions.py checkpoints/review-lock.py` passed cheap call, all-in, calibration, suit equivalence, score accounting and exact-lock boundary checks. Lock does not chase losses.
- Ranges. Build review-ranges.py with `--protocol src/score_protocol.py --policy src/range_policy.py --extra src/preflop_key.py --extra src/preflop_table.py --extra src/ranges.py`. Replay public pot and street totals; weight hypothetical compatible holdings by action type, size, pressure, board prefix and a soft flop-only discard likelihood. Discard request uses the history already received, without guessing a missing action.
- River. Build review-river.py with the ranges recipe, `--policy src/river_policy.py --extra src/river.py`. Shuffle compatible pairs without replacement; return exact weighted equity if all 903 are evaluated. Allocate more samples around decision boundaries and track effective sample size. Separate action RNG. Compare several legal sizes using a simplified continuing-range/raise-risk model. `python tests/review_ranges.py checkpoints/review-river.py` passed street replay, future-board isolation, late improvement, deadline, full enumeration and representative response-EV fixtures.

All commands above used CPython 3.11.9 under WSL unless noted. Full matched screens and ablations are running; no candidate has been promoted.

### Review ablations and opponent correction

- The first league range opponent had a flop dispatch bug. It produced 680 diagnostic bytes per affected match. Those rows stay in the archived matrices, and comparisons explicitly exclude that opponent after validating the complete reports. The corrected development-v2 and confirmation artifacts pass `python tests/review_league.py` for all four streets. No candidate fallback was seen in the affected rows.
- Pilot commands: `python tools/evaluate.py checkpoints/review-C.py opponents/league/development/polar.py opponents/league/development/jam.py --manifest experiments/review-seeds.json --split pilot --count 1 --jobs 2 --out experiments/review-pilot-C.jsonl` for C=calls, lock, ranges, river. Eight full matches per candidate. The score lock retained all wins and all capped scores vs calls and cut maximum bank 21.131 to 10.978 s at Stage 1, 53.386 to 22.873 s at Stage 2. Range-only kept the same points and cap against these two profiles. The EV sizing candidate lost one Stage 1 match vs polar and cost more clock at both lengths.
- Isolated river enumeration from EV sizing in checkpoints/review-exact.py by building the same range/river modules with `--policy src/exact_policy.py`. Ran `python tools/evaluate.py checkpoints/review-C.py opponents/league/development-v2/polar.py --manifest experiments/review-seeds.json --split screen --count 1 --jobs 2 --out experiments/OUT.jsonl` for C=ranges and exact with OUT=review-exact-ablation-base and review-exact-ablation. Four matches per bot. Tied on points and cap, exact minus ranges -0.0825/-0.1725 raw chips per hand, bank maxima 21.807/68.495 s versus 20.581/48.152 s. No promotion.
- Built a lock-only ablation with `python tools/build_submission.py --protocol src/score_protocol.py --output checkpoints/review-lock-only.py`. The isolated `python tests/review_lock.py checkpoints/review-lock-only.py` transcript verified check, fold and mandatory discard after a protected lead. Deterministic sample-count builds are supported outside dist for development while match clocks remain on. The running comparisons use production deadlines, so scheduling can vary effective sample counts.


### Completed broad screens and constrained checks

The broad screen ran 64 matches each for checkpoints/betting.py and checkpoints/review-calls.py. Command shape: `python tools/evaluate.py BOT opponents/league/development/range.py opponents/league/development/polar.py opponents/league/development/pressure.py opponents/league/development/trap.py opponents/league/development/jam.py opponents/league/development/adversary.py checkpoints/betting.py checkpoints/adaptive.py --manifest experiments/review-seeds.json --split screen --count 2 --jobs 7 --out experiments/OUT.jsonl` with OUT review-base and review-calls. After explicit removal of the faulty opponent, calls won 23/28 and 26/28 versus the base's 24/28 and 24/28. Paired points -0.0357/+0.0714 and capped chips/hand +0.0484/+0.2011. The Stage 2 improvement was not enough to offset the 400-hand and tight-shove risks. No valid rows had forfeits, corrections or diagnostic output.

The challenge ran 16 matches each with `python tools/evaluate.py BOT opponents/league/development/range.py checkpoints/betting.py --manifest experiments/review-seeds.json --split screen --count 2 --jobs 3 --out experiments/review-challenge-NAME.jsonl` for base, lock, ranges and river. Ignore the faulty opponent. Ranges won 8/8 head-to-head versus the original frozen champion. River sizing won 4/8. The corrected development matrix used `opponents/league/development-v2/range.py opponents/league/development-v2/trap.py` with otherwise identical screen options and `review-fixed-NAME.jsonl`. Ranges won 8/8 per stage vs the base's 7/8 and 6/8. Gains were concentrated in the range matchup.

Confirmation used `python tools/evaluate.py BOT opponents/league/confirmation/tightjam.py opponents/league/confirmation/switch.py --manifest experiments/review-seeds.json --split confirmation --count 4 --jobs 4 --out experiments/review-confirm-NAME.jsonl` for base, lock-only and ranges. Base and lock-only went 32/32 each. The lock-only capped score differences were +0.0322/+0.0067 chips/hand with intervals crossing zero. Ranges went 15/16 and 13/16, with all four losses against tightjam. The broad preflop calibration remained experimental. The range model and score protection had enough signal to test with the champion's original non-trip preflop policy.

Built checkpoints/review-conservative.py with the range recipe and `--policy src/conservative_range_policy.py`. This keeps original non-trip preflop thresholds, uses the table for trips, and keeps terminal postflop EV, weighted ranges and capped-lead protection. `python tests/review_decisions.py checkpoints/review-conservative.py`, protocol, selection, evaluator (24,000 oracle/suit checks), range and isolated lock fixtures passed.

Constrained check command for the conservative build: `wsl -d Ubuntu -- /usr/bin/time -v taskset -c 13 prlimit --as=1073741824 -- /home/miyyapuram_saivarun/pokerbots-runtime/Python-3.11.9/python -B tools/validate_release.py --bot checkpoints/review-conservative.py --opponents opponents/league/development-v2/pressure.py opponents/league/development-v2/range.py --prefix review-stress-conservative --seeds review-stress-510 review-stress-511`. Full 400 and 1,000 hands. Wins +460/+1,466 with zero notices, diagnostics or forfeits. Bot bank 12.284/25.810 s, p99 23.43/21.85 ms, max 31.61/32.22 ms. Maximum RSS for the timed command 23,032 KiB. `python tools/check_score_lock.py review-stress-conservative` verified locks from hands 284/586 and no post-lock loss beyond blinds or voluntary contributions. Lock-only and broader ranges also passed constrained checks with the same opponents/seeds, their respective bot paths and report prefixes, and CPUs 15/14. These were local Linux runs under varying host load.


### Review release decision

Promoted checkpoints/review-conservative.py to dist/bot.py. Default `python tools/build_submission.py` independently rebuilt the stress-tested bytes. Artifact is 60,515 bytes, SHA-256 d679d00967b25c56db9c9b1889732823496f0cf017977f3d5e9fdfa4a0b73e3c. Original 404af500... champion remains byte-for-byte at checkpoints/betting.py. The release manifest points to the exact duel and stress reports.

- Fresh duel: `python tools/evaluate.py checkpoints/review-conservative.py checkpoints/review-lock-only.py --manifest experiments/review-final-duel-seeds.json --split confirmation --count 4 --jobs 6 --out experiments/review-final-duel.jsonl`. The selected bot won 8/8 at each stage, both assignments on each of four fresh seeds. Capped chips per hand +0.8141/+0.9624, raw +0.9163/+1.0808, worst bank 24.810/57.308 s. Zero notices, forfeits or stderr. `python tools/duel.py experiments/review-final-duel.jsonl` validated and summarized the full matrix. Four seed blocks and one opponent make the conditional all-win bootstrap interval unsuitable as a tournament-wide forecast.
- Reserved mixed pool: `python tools/evaluate.py BOT opponents/league/confirmation/tightjam.py checkpoints/betting.py --manifest experiments/review-reserved-seeds.json --split screen --count 2 --jobs 4 --out experiments/review-reserved-NAME.jsonl` for conservative and lock-only. Selected won 8/8 and 7/8 versus reference 7/8 at both stages. Selected capped differences +0.3862/+0.3175 chips/hand. It won all eight tight-shove matches and capped all eight.
- Corrected range/trap screen: same review-fixed command above for conservative and lock-only. Selected won 8/8 at each stage versus reference 7/8 and 8/8. Paired capped gains +0.1378/+0.1216 chips/hand. Gains were concentrated against the range-aware opponent. Zero new protocol failures. Comparisons are in experiments/review-fixed-conservative-comparison.txt and experiments/review-reserved-comparison.txt.
- Revalidated the shipped file using `python tests/{protocol,selection,evaluator,review_decisions,review_ranges,review_lock}.py dist/bot.py` as separate invocations. The release-manifest command used `--selected checkpoints/review-conservative.py --fallback checkpoints/betting.py --fallback-report experiments/m6-betting.jsonl --report experiments/review-stress-conservative.jsonl --final-report experiments/review-final-duel.jsonl --sources src/score_protocol.py src/poker.py src/preflop_key.py src/preflop_table.py src/ranges.py src/conservative_range_policy.py`. Verified the original rule and engine hashes.

Promotion covers score protection, weighted public-history ranges, terminal postflop call EV and calibrated trips with conservative non-trip preflop thresholds. Broad preflop all-in recalibration, adaptive exact river sampling and EV sizing were kept in experimental checkpoints. The river sizing gate did not pass, so no new adaptation or solver experiment was run. The selected likelihood model is heuristic and the production sample count depends on clock and host load. The review's 128/640-match targets were not reached per candidate. The declared matrices are complete, and the comparisons support a local selection against a limited set of opponent families. No upload or organizer contact performed.


## Same-seed current-release retest

Retested unchanged dist/bot.py (44b011220dce58a5a9ce0c8352c66a1f3c5054ef791c1669a1a3cfb2a68abe46) against the same four opponents/four confirmation seeds, both assignments and both stages. All 64 full matches completed: 56 wins, 0 draws, 8 losses; friend subset 10 wins, 0 draws, 6 losses. Friend stage split 5/8 and 5/8 versus the earlier 4/8 and 6/8. Trap 14/16, tight-reraise 16/16, pressure 16/16. Zero forfeits, corrections or diagnostics. Complete matrix validation and strict configuration comparison passed. No bot changes; repeated seeds are not fresh holdout evidence.

Reports and exact command: experiments/retest-1109-01/{RESULTS.md,summary.json,results.jsonl,results.meta.json,command.json,comparison.txt}. Reproduction: run command.json argv from the project root with a new --out path. Clocks remain enabled; timing-adaptive opponent work and host load can alter individual results.

## 10 November rule update (implementation and validation in progress)

Reviewed all three updated PDFs and compared the new starter kit with the frozen old organizer files. Main change: two fresh-process legs, 200/500 hands and 30/75 s bank per leg, combined match scoring, no state transfer. Submission-local reads are permitted; no runtime IO was added. Updated originals and hashes are under vendor/Starter_Kit_2026_11_10 and experiments/rules-update-1110/sources.json. PDF differences and relevant page renders are saved with the experiment.

Preserved exact prior release/manifest at checkpoints/pre-rules-1110.py and checkpoints/pre-rules-1110.release.json (bot SHA-256 44b011220dce58a5a9ce0c8352c66a1f3c5054ef791c1669a1a3cfb2a68abe46). Candidate checkpoints/rules-1110.py is SHA-256 4bee6c3e30a87610f60768f3b30af13d995fcf10ce66a63fe7c13848bc042cd3. dist is still the previous release while validation runs.

Candidate resets all state at init and explicitly disables local-score match locking, including custom leg lengths. Existing release already disabled locking for official 200/500-hand init values, so this is lifecycle hardening, not a claim of strategic gain. 60 fixed-draw current-format decisions agree with the old release. Core gameplay/equity/range modules and experimental strategic candidates were not changed. Both organizer versions remain byte-for-byte untouched.

Added tools/benchmark_legs.py; evaluate.py and validate_release.py default to updated legs, with --engine-format legacy for historical reproduction. Per-leg metrics are retained, clocks keep the official startup grace, and matrix checks validate leg totals, hashes, completion, resource limits and whole-match forfeit denominator.

Passed 13 Linux checks (all exit 0): rules_update, protocol, selection, evaluator, learning, review_decisions, optimization both default and --timing-out, rules_matrix, review_findings, review_research, review_control, and protocol without site packages (-S). Reproduction: WSL CPython 3.11 python -B experiments/rules-update-1110/run_checks.py; it refuses to overwrite checks.jsonl and optimization-timing.json, so use a new experiment directory for another run. Exact commands/output/runtime in checks.jsonl. The lifecycle fixture also covers forfeits in either leg.

A Windows Stage 1 full two-leg smoke match vs trap completed 400 hands, +2429 chips, zero notices/diagnostics/forfeits. Candidate banks 8.109/8.927 s per leg (30 s limit); this smoke is not a constrained Linux check.

RUNNING: two Linux paired matrices, candidate.jsonl and baseline.jsonl, each 16 matches (4 opponents x 2 stages x 2 assignments x 1 fresh seed block). Opponents: confirmation/trap.py, review-fixes-1109/tight_reraise.py, confirmation/pressure.py, and the existing external friend-review bot. Command shape: python -B tools/evaluate.py BOT OPPONENTS --engine-format legs --manifest experiments/rules-update-1110/seeds.json --split confirmation --count 1 --jobs 2 --out experiments/rules-update-1110/NAME.jsonl. Each matrix uses jobs=2 and both run concurrently. Configuration/hashes are saved in each .meta.json; stderr/stdout are separate. One block cannot establish a strategic strength improvement.

NEXT: collect both matrices, strict paired comparison, constrained Linux validation (both stages, both legs), and artifact audit; then choose release/update manifest and document unfavorable results. Do not promote a strategic experiment. A one-time continuation was scheduled in this chat for 04:45 IST on 10 November (automation continue-pokerbots-rule-update); check saved progress before resuming work.

### Rule-update selection checkpoint

Both Linux matrices completed and validated: existing release 15/16 (Stage 1 8/8, Stage 2 7/8), candidate 13/16 (6/8, 7/8). Friend subset existing 3/4 vs candidate 1/4; trap, tight-reraise and pressure 4/4 each for both. No forfeits, notices or diagnostics in either matrix. Strict comparison passed; one block gives no meaningful block-level uncertainty interval. It does not establish a causal regression: the selected policy is identical on official leg inputs, while the external opponent and sampled work are time-adaptive. It also does not justify replacing the current release.

RETAINED dist/bot.py byte-for-byte. Preserved the candidate protocol as src/leg_protocol.py, and restored src/learning_protocol.py byte-for-byte to the existing manifest hash. Default build to checkpoints/rules-1110-retained-rebuild.py reproduces 44b01122... exactly. Explicit candidate rebuild to checkpoints/rules-1110-rebuild.py reproduces 4bee6c3e... exactly using --protocol src/leg_protocol.py --policy src/learning_policy.py and --extra for preflop_key, preflop_table, friend_ranges, learning, vector_equity (all under src, .py).

Candidate constrained Linux checks passed both full stages at 1 CPU/1 GiB address-space limit. Per-leg bank maxima 8.360/30 s and 36.400/75 s, max reply 84.004 ms, maximum RSS for the timed command 40,404 KiB; zero corrections/diagnostics/forfeits. Reports stress.jsonl and stress-time.txt. Exact selected release is now being rechecked under the same constraints, seeds and opponents with prefix retained-stress. Selected release additionally passed official 200/500-hand leg protocol fixtures with and without site packages plus the learning suite (3/3; retained-checks.jsonl).

NEXT: finish retained-stress, refresh only release metadata to reference the current-format validation, write RESULTS.md and final summary. Do not change/promote the playing policy. No submission upload or Git push is authorized for this rule-update task.

## Daily automated comparison — 10 November, calculation-only promotion

Subsequent to the rule-update validation, fetched the current teammate bot from the private GitHub repository via the connected account. Exact Git blob a5c8b01162763bb9c67051a5a625eb06607baf5a, SHA-256 89ca146619df53be4179b77be94dd0da6ca7262e57e76033fa7b117050c55cd0; preserved separately at experiments/daily-1110/friend-current.py. It differs from the old ZIP opponent; all old evidence remains unchanged.

Promoted a calculation-only direct histogram optimization in src/vector_equity.py, with identical rank counts, fixed-draw equities and complete posterior arrays. New dist/bot.py SHA-256 bb86e3e7dafd4019157bf9f24cee640e4c9dfbb276883dd92fee1585a03a1990. Default build reproduces the exact constrained-tested artifact. Previous dist and manifest are backed up at checkpoints/pre-daily-1110.py and checkpoints/pre-daily-1110.release.json. Do not restore the old rule-update bytes over this subsequent promotion. Playing policy, protocol and sampling count are unchanged.

Validation: 16,536 rank rows and 60 posterior-equivalence cases; eight existing check invocations plus a separate no-site-packages official-leg fixture passed. Single-CPU alternating warm median estimates improved 6.8% flop, 4.8% turn and 5.9% river. Exact artifact passed full two-leg 400/1,000-hand Linux CPython 3.11 matches with one CPU/1 GiB. The exact-artifact current-teammate check split 2 wins/2 losses (Stage 1 2/2; Stage 2 0/2), with no corrections, diagnostics or forfeits. One block is insufficient to establish strength; no increased win rate is claimed.

A separate strategy candidate uses complete showdown rank for river range/continuation ordering. It passed 86,480 compatible pair-order checks, 10,000 independent scalar ranks and 60 isolation cases. Both its 32-match screen and the frozen old baseline screen are still running against current teammate, trap, pressure and tight-reraise families, using two fresh blocks and both assignments/stages. Candidate remains outside dist; do not infer a playing-strength gain from semantic correctness alone. Fresh four-block confirmation seeds are reserved if the screen supports advancing it. Final results will be recorded at experiments/daily-1110/RESULTS.md. No push or upload performed.

### Daily comparison complete

Both 32-match screens completed and passed strict matrix/configuration validation. Frozen pre-optimization release: 25 wins/7 losses, including 1/8 against the freshly fetched teammate. River-order candidate: 24 wins/8 losses, including 0/8 against the teammate. All three other families were 8/8 for both. Stage 1 match points tied; Stage 2 paired points -0.0625. Candidate not advanced; four confirmation blocks remain untouched. All 64 screen matches had zero notices/diagnostics/forfeits. The independent exact selected-artifact teammate check was 2/4 on a different seed block and must not be presented as a paired improvement over 1/8.

Only the proven calculation optimization remains promoted. Exact artifact resource wins: +4,332 pressure and +3,238 trap; worst per-leg banks 9.97/30 s and 32.76/75 s, max reply 45.09 ms, command maximum RSS 40,484 KiB. Existing release metadata now reproduces the new artifact by default. Full evidence, source comparison, unfavorable results and reproduction are in experiments/daily-1110/RESULTS.md. This daily review is complete; consistent strength against the updated teammate and unseen strong entrants is not established.

### Rule-update work completed at the scheduled 04:45 IST continuation

Finished experiments/rules-update-1110/RESULTS.md and validated all historical evidence with summarize.py --validate-only (exit 0). This rule-update study completed 32 paired matrix matches, four constrained Linux matches and one Windows smoke match (37 full matches total). Retained artifact 44b01122... scored 15/16; lifecycle candidate 4bee6c3e... scored 13/16, including friend 3/4 versus 1/4. No result was excluded and there were zero corrections, diagnostics or forfeits. One seed block gives no useful block confidence interval. No strategic candidate was promoted.

The exact retained release additionally passed eight Linux checks and both full constrained stages; banks per leg peaked at 7.459/30 s and 31.990/75 s, maximum charged reply 65.118 ms, timed-command maximum RSS 40,492 KiB. Detailed retained-stress.jsonl and retained-stress-time.txt have all four legs. The rule-update release metadata was refreshed after those checks.

IMPORTANT chronology: while this chat awaited its scheduled continuation, the separate daily task promoted its validated calculation-only histogram optimization. Current dist/bot.py is bb86e3e7dafd4019157bf9f24cee640e4c9dfbb276883dd92fee1585a03a1990, not the 44b01122... artifact in this study. Preserved that subsequent work and did not modify its source, release or running experiments. The rule-update manifest is now independently frozen at experiments/rules-update-1110/retained.release.json and all eight historical sources at frozen-sources/. commands.json includes overrides to reproduce both historical artifacts without reverting the current tree. Current release authority remains dist/release.json. Do not attribute the old matrix scores to the new histogram artifact.

Rule-update implementation, integration, testing and reporting are complete. Updated organizer files are unchanged, old files and fallbacks remain preserved, and the current default source hashes match the later daily release. No upload, Git push or contact was performed by this task. The one-time continuation automation is being removed after completion. Further daily strategy experiments remain owned by that separate task; they are not automatically promoted by this review.

## Requested current-release field test — 10 November

Completed the user's request to run the game against the teammate and other bots. Fetched current GitHub main/bot.py again; blob a5c8b01162763bb9c67051a5a625eb06607baf5a is unchanged. Froze the exact bb86e3e7... release and six opponents under experiments/requested-field-test-1110. Declared four fresh random seed blocks, both assignments and both official stages before play: 96 matches, 192 independently launched legs, 67,200 hands. Linux CPython 3.11.9/NumPy 2.2.6; four concurrent clocked matches with BLAS threads limited to one. This broad test has no CPU affinity or memory cap; separate constrained validation remains archived.

Results: 82 wins, 0 draws, 14 losses. Updated teammate 2/0/14 (400 hands 2/0/6; 1,000 hands 0/0/8). Trap/check-raise, pressure, tight-shove, range-aware and polarized profiles each 16/0/0. All 96 rows passed strict complete-matrix, artifact-hash, two-leg and scoring validation. Zero forfeits, notices and diagnostic bytes for either side. Our maximum per-leg banks were 13.62/30 s and 35.87/75 s; largest response 95.44 ms. Dist bytes remained unchanged throughout the run.

Full report, summary, commands, seed manifest, frozen opponents and original results are in experiments/requested-field-test-1110/. The larger fresh test exposes a significant observed teammate weakness; it is not evidence of a policy regression relative to the earlier 2/4 check, which used other seeds. Five project-generated opponent families are limited field coverage, not independently established strong entrants. No playing code, release metadata, Git history or external submission was changed by this test; only test evidence and documentation were added.

## Requested current-teammate head-to-head — 10 November 2026

Fetched teammate repository https://github.com/sricharanreddycheruku/pokerbots-discard-holdem at commit 8549810994f2189bb74b456d4c515db065a8d363. Frozen bot SHA-256 1ce00b601ebdebb5d03ae1e307fdccbcd3c5d65ac90724e63599faa47a393ec0. This is newer than the previously fetched 89ca1466... teammate. Our frozen current submission SHA-256 bb86e3e7dafd4019157bf9f24cee640e4c9dfbb276883dd92fee1585a03a1990. No playing code was changed.

Completed and validated 16 full matches, four freshly generated seed blocks, both assignments, both updated competition stages and two fresh-process legs per match. Our result: 6 wins / 0 draws / 10 losses. Stage 1: 4/0/4, -704 raw chips; Stage 2: 2/0/6, -6,269 raw chips. Total -6,973 raw chips, -4,251 capped chips. Zero forfeits, corrections or diagnostics from either bot. Our max charged per-leg bank 9.093/30 s and 28.677/75 s; teammate 6.945/30 and 20.767/75 s. Maximum charged reply ours 98.37 ms; teammate 60.23 ms. All unfavorable results included.

Linux CPython 3.11.9, official two-leg clocks/startup grace, jobs=2, OPENBLAS_NUM_THREADS=OMP_NUM_THREADS=MKL_NUM_THREADS=1; matrix was not hard CPU/RAM sandboxed. Only four independent blocks: conditional seed-block bootstrap interval for match points [0, .75], too broad for a reliable long-run or tournament win forecast. Teammate performed better in this sample, especially Stage 2. No policy change, promotion, push or upload.

Reproduction: experiments/teammate-match-1110/command.json holds exact argv/cwd; use a fresh output directory. Frozen bot snapshots, fetched Git checkout, provenance.json, seeds.json, results.jsonl, results.meta.json and validated summary.json are preserved there. Full results: experiments/teammate-match-1110/RESULTS.md. summarize.py validates complete matrix, artifact/opponent/harness hashes and writes reports with exclusive creation.

Head-to-head version clarification: final hash verification found a concurrent task had replaced dist/bot.py with c264cb8a9e914a210be622d39751aa9ef45e9b9b717b1ef9281e069438e3a39a during the match run. The tested ours.py snapshot stayed bb86e3e7... and all 16 recorded hashes validate against it. Do not attribute 6/16 to the newer dist release. Preserved concurrent work without modification.

## Loss analysis and selective-range release complete - 10 November

Analyzed all 16 diagnostic friend replays (11,200 hands). Showdown net -13,381 vs nonshowdown +374. Selected called-turn holdings showed substantial equity overestimation; ordinary bad runouts were also identified. Hidden-card hindsight remains offline only. Three isolated candidates screened: baseline 17/32, selective range 29/32, response tree 21/32, combined 26/32. Advanced selective only.

Fresh four-block confirmation completed 96 matches per artifact: selected 86 wins/10 losses vs baseline 76/20. Both stages 43/48 vs 38/48. Tested friend snapshot 9/16 vs 0/16, archived friend 13/16 vs 12/16; trap/tightjam/range/polar each 16/16 for both. All four paired blocks positive; pooled match-point difference +0.10417, conditional block bootstrap interval [0.08333,0.14583]. Supplementary pressure/switch/champion selected 24/24 including champion 8/8. Every predeclared gate passed; finite tests cannot guarantee no true regression.

Promoted exact 77,217-byte artifact c264cb8a9e914a210be622d39751aa9ef45e9b9b717b1ef9281e069438e3a39a. Default build now uses src/selective_equity.py; original vector model preserved and response-tree excluded. Preserved previous release and manifest at checkpoints/pre-selective-1110.py and its .release.json companion. Updated manifest/defaults and reproduction checks passed. Optimization equality assertions retained against historical calculation-only checkpoint; selected range has independent fixtures. Twenty initial checks plus five post-promotion checks passed. One-CPU/1-GiB full matches passed resource checks, max leg banks 11.49/30 and 30.36/75 s; includes loss -339 vs friend and win +3407 vs archived friend. Max reply 90.94 ms, RSS 43,784 KiB. Zero study failures/notices/diagnostics. Full report and raw evidence: experiments/loss-improvement-1110/RESULTS.md. No upload, commit or push. Concurrent teammate-match evidence tests its frozen older snapshot, not this release.

## Improved bot versus latest teammate - 10 November

Fetched origin/main again for the user's requested head-to-head. Latest commit 8549810994f2189bb74b456d4c515db065a8d363; extracted exact Git bot.py bytes, SHA-256 35046e2fc6b3e4f52d9356779ca15db8bcd6cfd39b7e799978bac3163c260e64. Our frozen improved bot c264cb8a9e914a210be622d39751aa9ef45e9b9b717b1ef9281e069438e3a39a remained unchanged. Four fresh seed blocks, both assignments and both updated competition stages, two fresh-process legs each, production clocks, Linux Python 3.11.9/NumPy 2.2.6, two concurrent matches, BLAS threads one.

Complete 16-match matrix validated: 9 wins, 0 draws, 7 losses; 400 hands 4/0/4 net -989; 1,000 hands 5/0/3 net +4488; total +3499 raw chips (+581 capped). Zero forfeits/notices/diagnostic bytes for both bots. Our worst per-leg bank 9.71/30 and 26.64/75 s; max reply 87.36 ms. Four-block win-point bootstrap interval [.25,.875] is broad; no reliable dominance or tournament-win claim follows. Earlier 6/16 result tested old bb86... bot and different seeds, not a paired comparison. No playing code or release changes in this run. Evidence: experiments/improved-teammate-match-1110/{RESULTS.md,summary.json,results.jsonl,results.meta.json,provenance.json,seeds.json,command.json} and frozen bot files.
