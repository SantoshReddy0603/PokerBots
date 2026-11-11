# PokerBots loss analysis and improvement — 10 November 2026

**Promoted the validated selective-aggression range update.** The previous champion is preserved byte-for-byte.

## What the loss investigation found

The original field test had 14 losses against the friend snapshot. It retained match summaries, not every action. All 16 friend matchups—including the two wins—were rerun with development-only request/decision logging. The bot and opponent work depend on timing, so these are diagnostic replays, not exact reconstructions of the original action sequences. Original results were preserved. The replay analysis covers 11,200 hands.

| Replay cohort | Hands | Net chips |
|---|---:|---:|
| Ended before showdown | 9,178 | +374 |
| Showdowns | 2,022 | -13,381 |
| Our preflop street contribution at least 20 | 8 | +0 |
| First voluntary all-in decision on flop | 250 | -8,516 |
| First voluntary all-in decision on turn | 351 | -3,691 |
| First voluntary all-in decision on river | 311 | +10,753 |

Cohorts overlap and must not be added together. Decision-level summaries can repeat a hand’s final net; they are not a causal accounting of each action.

The main observed leak was expensive postflop continuation against strong hands. In 185 terminal turn calls, mean estimated equity was 53.0%; exact future runouts against the subsequently shown holding averaged 31.7%. Against those actual holdings, 109 calls had negative incremental call EV; 20 other calls lost despite nonnegative conditional EV. These are selected called/showdown hands, not an unbiased calibration of every opponent action. Knowing the shown hand retrospectively does not prove a call was wrong against the full range.

For example, one replay called 158 chips on the turn with Ad Ah on 3s Ks 4d 7s. The estimate was about 51%, but the later-shown As 5s already made a flush; conditional equity against that hand was zero. Other losses were ordinary unfavorable runouts. No shown/hidden opponent cards enter the submitted strategy.

## Implemented change

`src/selective_equity.py` lowers the weak-hand likelihood floor for postflop reraises and large bets when their learned frequency is low. The floor is `min(0.08, max(0.01, 0.20 * frequency))` in those contexts. Ordinary bets and frequent aggression retain the prior broad floor. This stops rare strong actions from leaving as much weight on weak holdings. The rule uses public history and shrunk within-leg action frequencies, not opponent identity, test seeds or revealed cards.

The preflop decision code, hand evaluator, sample counts, discard scoring code and standard-library fallback were retained. Posterior equities and therefore actions/discards can intentionally change after selective aggression. The existing histogram calculation optimization is retained.

A separate explicit reraise-response model was implemented in `src/response_policy.py` and tested alone and combined. Its effective-stack-shove assumption did not win selection; it is excluded from the selected build.

## Fresh screening — complete results

Two fresh seed blocks, four opponents, both assignments and both stages: 32 matches per artifact, 128 total. No partial score was used to select a candidate.

| Artifact | W/D/L |
|---|---:|
| baseline | 17/0/15 |
| selective | 29/0/3 |
| response | 21/0/11 |
| combined | 26/0/6 |

Range-only was advanced because it had the highest eligible match points, gained at both stages, and had no observed matchup regression. The current friend subset was 6/8 versus baseline 0/8. Screening scores are selection evidence, not fresh confirmation.

## Untouched confirmation

Four reserved fresh blocks, six opponent snapshots, both assignments/stages: 96 matches per artifact. All matrices and paired configurations passed strict validation before comparison.

| Opponent | Previous champion W/D/L | Range candidate W/D/L |
|---|---:|---:|
| Friend snapshot from the 96-match test | 0/0/16 | 9/0/7 |
| Archived friend bot | 12/0/4 | 13/0/3 |
| Trap / check-raise | 16/0/0 | 16/0/0 |
| Tight shove | 16/0/0 | 16/0/0 |
| Range-aware | 16/0/0 | 16/0/0 |
| Polarized betting | 16/0/0 | 16/0/0 |
| **Total** | **76/0/20** | **86/0/10** |

| Stage | Previous champion W/D/L | Range candidate W/D/L |
|---|---:|---:|
| 400 hands | 38/0/10 | 43/0/5 |
| 1000 hands | 38/0/10 | 43/0/5 |

Paired match-point difference: +0.1042 per match; four-block bootstrap 95% interval [0.08333333333333333, 0.14583333333333331]. Individual block differences: [0.08333333333333333, 0.08333333333333333, 0.08333333333333333, 0.16666666666666666]. Four blocks provide limited uncertainty information; this conditional local interval is not a tournament-wide forecast.

## Additional regression and resource checks

Fresh pressure/switch/champion study: candidate 24/0/0, previous champion 14/8/2. Candidate won all eight against each opponent, including the previous champion. The baseline-versus-itself games were eight draws; do not present those as losses.

Exact candidate bytes also passed full official-format matches sharing one CPU and inheriting a 1 GiB address-space limit. The resource test includes an unfavorable result:

| Stage / opponent | Net chips | Worst per-leg bank | Official bank |
|---|---:|---:|---:|
| 1 / friend test snapshot | -339 | 11.49 s | 30 s |
| 2 / archived friend | +3,407 | 30.36 s | 75 s |

Largest response 90.94 ms; timed-command maximum RSS 43,784 KiB. All 20 initial correctness invocations passed, including 15,000 scalar/vector rank checks per candidate, range isolation, loose-opponent controls, protocol, decision and official-leg fixtures. Selected-byte static audit and no-NumPy official-leg checks also passed. Screen, confirmation, regression and resource reports recorded 0 match forfeits; the tested artifacts had 0 correction notices and 0 diagnostic bytes.

## Release decision and reproducibility

- Decision: promote selective range update; precise Boolean gate results are in `decision.json`.
- Current artifact SHA-256: `c264cb8a9e914a210be622d39751aa9ef45e9b9b717b1ef9281e069438e3a39a`.
- Project: `C:\Users\varun\OneDrive\Documents\ChatGPT\PokerBots`.
- Evidence: `experiments/loss-improvement-1110/`, including traces, original/replay comparisons, all three candidates, source hashes, seed manifests, matrix metadata, raw results and strict comparisons. Existing reports are never overwritten.
- Reproduction uses the frozen recipe/seed files. Reusing inspected seeds is reproduction, not new holdout evidence. Opponent sampling depends on time, so repeated runs can differ.
- The synthetic families share project infrastructure; the two friend snapshots also share their author and architecture. They do not represent every strong entrant or independent family.
- Finite tests cannot guarantee no true regression, or wins against every opponent. The previous exact bot remains available as a fallback. No commit, push, upload or external contact was performed.

Default `tools/build_submission.py` reproduces the selected tested bytes. The active vector module is now `src/selective_equity.py`; `src/vector_equity.py` preserves the previous model. The optimization-equivalence test keeps its equality assertions and targets the preserved calculation-only checkpoint by default; the new range weights are checked by separate isolation/model fixtures and fresh games. `dist/release.json` and the manifest-generator defaults reference the correct new source/report hashes. Fallback: `checkpoints/pre-selective-1110.py` and its `.release.json` companion.
