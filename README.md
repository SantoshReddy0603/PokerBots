# Discard Hold'em bot

Our entry for the 2026 PokerBots Discard Hold'em competition. The bot is the single
file [`bot.py`](bot.py). It runs on Python 3.11 and needs nothing apart from NumPy,
and it still plays correctly if NumPy is missing.

## How it plays

Each player gets three hole cards and throws one away after the flop, so most of the
work goes into estimating what the opponent could hold.

**Preflop.** We look up the hand's equity in a precomputed table of three-card
starting hands and compare it with opening and defending thresholds. Against big
raises the table is mixed with a stronger range, because that is what people raise
with.

**Discard.** We try every pair we could keep, run each against sampled flops and
the opponent's likely holdings, and keep the pair that does best.

**After the flop.** The opponent's range is updated after every action and every
showdown, including the card they threw away. A vectorised hand evaluator scores
our hand against that range. Fold, call and several raise sizes are then compared
by expected chips, using how often each bet size is likely to get a fold.

**Opponent model.** During a leg we count what the opponent does (how often they
raise, bet big, re-raise and fold to small or large bets) and adjust to it. Nothing
carries over between legs, as the rules require.

**Protecting a lead.** When we are ahead by more than the opponent can win back
from the blinds left, the bot just checks and folds out the leg.

**Without NumPy.** The same range model runs on plain Python lists, with fewer
samples when the time bank is low.

## Rules check

| Rule | bot.py |
|---|---|
| Python 3.11, standard library plus NumPy/SciPy | Standard library, NumPy optional |
| Top-level `bot.py` or ZIP up to 5 MB | Single 192 KB file |
| No file writes, network, subprocesses or state between legs | None; everything resets on `init` |
| 5 s per reply, 30 s / 75 s bank per leg, 1 CPU, 1 GB | Slowest reply about 0.2 s, roughly a third of the bank used, about 50 MB of memory |
| Protocol 1.0 JSON lines | Tested with both leg lengths on the official engine |

## Building and testing

`bot.py` is generated from the modules in `src/`:

```bash
python3.11 tools/build_submission.py      # writes bot.py
python3.11 tests/protocol.py              # message protocol
python3.11 tests/leg_compatibility.py     # 200 and 500 hand legs
python3.11 tests/learning.py              # evaluator and opponent model
python3.11 tests/selection.py             # hand ranking and discards
python3.11 -S tests/protocol.py           # same checks without NumPy
```

## Files

| Path | What it is |
|---|---|
| `bot.py` | The submission |
| `src/learning_protocol.py` | Match state and the lead check |
| `src/poker.py` | Hand evaluator and card helpers |
| `src/preflop_key.py`, `src/preflop_table.py` | Preflop equity table |
| `src/event_ranges.py` | Replays hand events into an opponent range |
| `src/learning.py` | Opponent action counts |
| `src/selective_equity.py`, `src/pure_equity.py` | Range equity without NumPy |
| `src/learning_policy.py` | Betting and discard decisions without NumPy |
| `src/range_engine.py` | NumPy evaluator, range model, discard search and betting |
| `src/main_loop.py` | Reads the engine's messages and replies |
| `tools/build_submission.py` | Builds `bot.py` from `src/` |
| `tests/` | Protocol and decision tests |
