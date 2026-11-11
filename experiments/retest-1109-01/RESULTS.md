# Current bot retest — 9 November 2026

Retested the unchanged current submission on the same four seed blocks, four opponents, both bot assignments and both competition stages. All 64 matches completed (44,800 hands).

| Result | Earlier run | Retest |
|---|---:|---:|
| Overall wins | 56/64 | 56/64 |
| Wins against friend | 10/16 | 10/16 |

Friend breakdown: 400 hands **5 wins, 3 losses**; 1,000 hands **5 wins, 3 losses**. The friend matches are included in the 64 overall.

| Opponent | Wins | Draws | Losses |
|---|---:|---:|---:|
| Trap/check-raise | 14 | 0 | 2 |
| Tight-reraise | 16 | 0 | 0 |
| Pressure | 16 | 0 | 0 |
| Friend | 10 | 0 | 6 |

Forfeits: 0; candidate corrections: 0; candidate diagnostic bytes: 0.

The aggregate counts repeated, but the friend stage split changed from 4/8 + 6/8 to 5/8 + 5/8. Bots use time-adaptive simulations, so identical deal seeds need not reproduce every action or outcome. This is a same-seed repeat, not new independent tournament evidence. No bot code was changed.

The original study ran two matrices concurrently; this retest ran one matrix with two concurrent matches. Host load and actual simulation work can differ.

SHA-256: `44b011220dce58a5a9ce0c8352c66a1f3c5054ef791c1669a1a3cfb2a68abe46`. Interpreter, seeds, opponent/harness hashes and concurrency are in `results.meta.json`; exact command in `command.json`; raw results in `results.jsonl`; validated paired comparison in `comparison.txt`.
