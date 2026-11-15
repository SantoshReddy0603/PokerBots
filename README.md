# PokerBots: Discard Hold'em bot

A self-contained Python 3.11 bot for the 2026 Discard Hold'em competition.

**Submission file: [`dist/bot.py`](dist/bot.py)** (192 KB, a single file with no
other files needed), built from `src/` by `tools/build_submission.py`.

- **Preflop:** precomputed three-card equity table, blended against heavy raises.
- **Discard and postflop (NumPy):** vectorised hand evaluator, an opponent range
  model updated from every action and showdown, discard search over sampled flops,
  and a betting policy that weighs fold, call and raise sizes against that range.
- **Match control:** frequency model of the opponent's actions and a protected-lead
  lock that checks or folds once the remaining blinds cannot erase a winning lead.
- **Without NumPy:** a list-based range-weighted estimate plays every decision.

## How the list-based path plays

- **Preflop:** opening and defending thresholds use a precomputed three-card equity
  table (`src/preflop_table.py`). Against heavy raises, the table blends a broad
  range with a premium-heavy one.
- **Opponent model:** each leg keeps counts of the opponent's public actions
  (raise, bet, large bet, reraise, fold to small or large bets). These are used as
  shrunk frequencies. Nothing is carried between legs or matches.
- **Range-weighted equity:** after the flop, opponent holdings are sampled and
  weighted by how likely each one is to have taken the observed actions. The model
  also covers the opponent's own flop discard and the card they exposed. On the
  river, every remaining opponent pair is enumerated exactly.
- **Bet selection:** fold, check or call and three raise sizes are compared by
  expected chips. Each raise uses an estimated fold rate and the equity against the
  range that continues.
- **Discard:** keeps the pair with the best range-weighted equity, with a small
  bonus for playability.
- **Without NumPy:** `src/pure_equity.py` runs the same range model on plain lists.
  The number of samples adapts to the time bank, so a slow machine stays well inside
  the limits.

## Rules compliance

| Requirement | Status |
|---|---|
| Python 3.11, standard library plus NumPy/SciPy | Standard library only; NumPy optional |
| Top-level `bot.py` or ZIP no larger than 5 MB | `dist/bot.py`, 192 KB |
| No file writes, network, subprocesses or state between legs | None used; learned state resets at each `init` |
| 5 s per response, 30 s / 75 s bank per leg, 1 CPU | With both bots sharing one core: slowest reply 221 ms, startup 0.9 s, bank about 9 s of 30 s and 27 s of 75 s per leg; slowest reply on a loaded machine 201 ms |
| Protocol 1.0 JSON lines, two-leg matches | Full matches on the official engine with no forfeits or notices; `tests/` pass on `dist/bot.py` |

The full rules summary is in [`RULES.md`](RULES.md).

## Results

All results below use the official two-leg engine
(`vendor/Starter_Kit_2026_11_10/engine.py`) at production clocks, on fresh seeds
with both seats played.

**The submitted file** (`experiments/release-1115/`), paired with the previous
release on the same seeds (45000-45003). Each cell is the submitted file first:

| Opponent | Stage 1 | Stage 2 |
|---|---|---|
| strongest public range-model bot | 4/8 vs 4/8 | 8/8 vs 2/8 |
| varun | 7/8 vs 8/8 | 8/8 vs 7/8 |
| vinayreddy1008 Peak_06 | 8/8 vs 8/8 | 8/8 vs 8/8 |

Total: 43 of 48 against 37 of 48 (Stage 2 +29.2 points, 95% interval +20.8 to
+33.3). Head to head against the previous release it won 27 of 64. On seeds
48000-48001 it won 32 of 32 against agri, amogh, nitish and SantoshReddy0603. No
match had a forfeit or protocol notice from our bot.

**How decisions were assigned:** preflop, discard, turn and river were each tested
with the table and with the range model. The table helped only preflop. Seven
settings changes to the range model (sizes, sample counts, exact turn equity) did
not beat the current one.

**Earlier testing of the list-based path:** it won 77% of 3,202 matches against public
GitHub bots: nitish 100%, agri 95%, amogh 92%, the range-model bot 56% and varun 50%. It won
all 684 matches against 19 synthetic exploit styles.

These are finite local samples, and the results against other entrants may differ.

## Build and test

```bash
python3.11 tools/build_submission.py                 # dist/bot.py
python3.11 tests/protocol.py                         # wire protocol fixtures
python3.11 tests/leg_compatibility.py                # both official leg lengths
python3.11 tests/learning.py dist/bot.py             # evaluator and model invariants
python3.11 tests/selection.py dist/bot.py            # rank and discard cases
python3.11 tests/evaluator.py dist/bot.py            # hand evaluator oracle
python3.11 -S tests/protocol.py                      # same fixtures without site-packages
```

[`dist/release.json`](dist/release.json) records the SHA-256 of the submission and
of every source. The previous release is kept exactly as
`checkpoints/pre-release-1115.py`. To play a single match, use
`tools/benchmark_legs.py`.

## Repository layout

| Path | Contents |
|---|---|
| `dist/` | Submission file and release manifest |
| `src/` | Bot sources, concatenated by `tools/build_submission.py` |
| `tests/` | Protocol, evaluator, model and decision tests |
| `tools/` | Build, match runner, evaluation and comparison tools |
| `opponents/` | Synthetic opponents used for testing |
| `checkpoints/` | The previous submission, kept exactly (`pre-release-1115.py`) |
| `experiments/` | Compact match evidence for each promotion |
| `vendor/`, `pokerbots_1/` | Organizer engine and starter kit, unchanged |

Source files in build order: `learning_protocol.py` (match state),
`poker.py` (evaluator and helpers), `preflop_key.py` and `preflop_table.py`,
`event_ranges.py` (event replay and the fallback model), `learning.py`
(frequency model), `selective_equity.py` and `pure_equity.py` (range estimates),
`learning_policy.py` (list-based decisions), `range_engine.py` (vectorised
postflop) and `main_loop.py` (message loop).
