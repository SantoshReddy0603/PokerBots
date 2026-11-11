# Field comparison, 11 November 2026

Champion: dist/bot.py (sha256 c264cb8a...). Official two-leg engine (tools/benchmark_legs.py), both stages, both seat assignments, production clocks, Linux Python 3.12.

| Subject (vs champion) | Seeds | Matches | Subject W/L | Subject chips/match |
|---|---|---|---|---|
| Varun576253/PokerBots main 6dcdf4d (bot 0aa59a5f) | 9100-9123 | 96 | 40/56 | -80 |
| Teammate pokerbots-discard-holdem e1a8c54 | 9200-9211 | 48 | 15/33 | -563 |

Teammate by stage: stage 1 10/14, stage 2 5/19. No forfeits. Finite samples; no regression-free guarantee.
Teammate source is a local-only test opponent and is not stored here.
Reproduce: python3 h2h.py <subject> <champion> out.jsonl <seed0> <n_seeds> <jobs>

## Candidate search and promotion (same day)

Candidates are one-line edits to src/learning_policy.py; subjects play the teammate bot and Varun576253 main (both stages, both seats). Prior release = `base`.

| Round | Arm | Matches | Match points | Paired chip delta vs base (95% block bootstrap) |
|---|---|---|---|---|
| c1 seeds 9500-9529 | base | 240 | 57.5% | |
| | pfwide | 240 | 68.8% | +135 [14, 253] |
| | pw_disc | 240 | 69.6% | +166 [30, 305] |
| | disc | 240 | 62.3% | +46 [-71, 171] |
| | pf3bet | 240 | 63.7% | +54 [-56, 161] |
| | combo | 240 | 59.2% | +58 [-52, 173] |
| c2 held-out seeds 9600-9639 | base | 320 | 48.1% | |
| | pfwide | 320 | 66.2% | +234 [115, 346] |
| | pw_disc | 320 | 67.5% | +246 [139, 355] |
| c3 six synthetic profiles, seeds 9700-9704 | base / pfwide / pw_disc | 120 each | 100% | 0 |

Promoted: pfwide (button open threshold .42 -> .38, big blind isolation .58 -> .55), the single simpler change. Fallback: checkpoints/pre-pfwide-1111.py. Local full match timing unchanged (max leg banks about 12 s / 27 s). Round-one selection was among six arms; round c2 used unseen seeds.
Reproduce: pool.py SUBJECT OUT SEED0 NSEEDS JOBS OPP... (see h2h harness), variants built by one-line substitutions.
