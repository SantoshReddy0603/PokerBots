# Fresh PokerBots field test — 10 November 2026

**82/0/14 wins/draws/losses across 96 full matches and 67,200 hands.**

The exact current release was tested against the current teammate bot and five local synthetic opponent families. No playing-policy changes were made during this test.

| Opponent | 400-hand W/D/L | 1,000-hand W/D/L | Overall W/D/L | Net chips / hand |
|---|---:|---:|---:|---:|
| Friend (current GitHub version) | 2/0/6 | 0/0/8 | 2/0/14 | -1.235 |
| Trap / check-raise | 8/0/0 | 8/0/0 | 16/0/0 | +3.126 |
| Pressure | 8/0/0 | 8/0/0 | 16/0/0 | +4.974 |
| Tight shove | 8/0/0 | 8/0/0 | 16/0/0 | +1.445 |
| Range-aware | 8/0/0 | 8/0/0 | 16/0/0 | +3.493 |
| Polarized betting | 8/0/0 | 8/0/0 | 16/0/0 | +4.739 |

**The main observed weakness is the updated teammate bot: 2 wins and 14 losses.** Wins against local synthetic profiles do not establish a consistent advantage against that opponent. The earlier 2/4 check used different seeds; these runs are not evidence that the unchanged policy became worse.

## What was run

- Four newly generated seed blocks, both assignments, both official stages: 16 matches per opponent.
- Each 400/1,000-hand match comprised two fresh-process 200/500-hand legs.
- Official 30/75-second per-leg time banks and response limits were enabled.
- Linux CPython 3.11.9, NumPy 2.2.6; four concurrent matches; BLAS thread limits set to one.
- This broad run did not impose CPU affinity or an address-space limit. Separate constrained release validation is archived in the earlier daily review.
- The updated organizer engine and all frozen opponents were unchanged.

## Reliability and runtime

- Full matrix validation passed: 96/96 unique expected matches, both legs and artifact hashes checked.
- Match forfeits: 0.
- Our correction notices / diagnostic bytes: 0 / 0.
- All bots' correction notices / diagnostic bytes: 0 / 0.
- Stage 1: largest per-leg bank 13.62/30 s; largest response 64.14 ms.
- Stage 2: largest per-leg bank 35.87/75 s; largest response 95.44 ms.

## Interpretation

These results measure this declared local pool, not a tournament-wide win probability. The five synthetic families share project infrastructure and are not five independently established strong entrants. Four seed blocks are limited evidence; assignment results within a seed are related. Opponent sampling is time-adaptive, so scheduling and host load can change action paths. Do not pool these fresh results with earlier inspected seeds as if they were a single untouched confirmation study.

## Exact artifact and reproduction

- Current bot SHA-256: `bb86e3e7dafd4019157bf9f24cee640e4c9dfbb276883dd92fee1585a03a1990`.
- Friend Git blob, checked again through the connected GitHub account before the run: `a5c8b01162763bb9c67051a5a625eb06607baf5a`.
- Project: `C:\Users\varun\OneDrive\Documents\ChatGPT\PokerBots`.
- Evidence directory: `experiments/requested-field-test-1110/`.
- `plan.json`, `seeds.json`, `command.json`, `results.meta.json`, `results.jsonl`, `summary.json` and the frozen bot files preserve the exact setup and results.
- Run the argument array in `command.json` from the project root, changing `--out` to a new path. Existing reports must not be overwritten.
- Reusing these seeds is reproduction, not new holdout evidence.

No submission upload, Git push or strategy promotion was performed by this test.
