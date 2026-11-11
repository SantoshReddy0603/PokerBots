# Current teammate head-to-head: 10 November 2026

Frozen repository commit: `8549810994f2189bb74b456d4c515db065a8d363`.
Our SHA-256: `bb86e3e7dafd4019157bf9f24cee640e4c9dfbb276883dd92fee1585a03a1990`.
Teammate SHA-256: `1ce00b601ebdebb5d03ae1e307fdccbcd3c5d65ac90724e63599faa47a393ec0`.

Both updated competition stages, two fresh-process legs per match, four fresh seed blocks and both assignments. Linux CPython 3.11.9, jobs=2, BLAS threads=1. Official time banks/startup grace enabled; no hard CPU/RAM sandbox in this matrix. No playing code changed.

| Stage | Our wins | Draws | Teammate wins | Our net chips |
|---|---:|---:|---:|---:|
| 1 (400 hands) | 4 | 0 | 4 | -704 |
| 2 (1000 hands) | 2 | 0 | 6 | -6,269 |
| **Total** | **6** | **0** | **10** | **-6,973** |

## Match results

| Stage | Seed | Assignment reversed | Our net chips | Our match points | Forfeit |
|---|---|---|---:|---:|---|
| 1 | teammate-1110-19878924f663e1b432832a1e | False | +1954 | 1 | {} |
| 1 | teammate-1110-19878924f663e1b432832a1e | True | +190 | 1 | {} |
| 1 | teammate-1110-79bdcd8c639cb3a5e6423945 | False | +1505 | 1 | {} |
| 1 | teammate-1110-79bdcd8c639cb3a5e6423945 | True | +13 | 1 | {} |
| 1 | teammate-1110-deb79239da21946792ee702e | False | -652 | 0 | {} |
| 1 | teammate-1110-deb79239da21946792ee702e | True | -1576 | 0 | {} |
| 1 | teammate-1110-dfc8340819347aadd95343e8 | False | -1047 | 0 | {} |
| 1 | teammate-1110-dfc8340819347aadd95343e8 | True | -1091 | 0 | {} |
| 2 | teammate-1110-19878924f663e1b432832a1e | False | +561 | 1 | {} |
| 2 | teammate-1110-19878924f663e1b432832a1e | True | +1337 | 1 | {} |
| 2 | teammate-1110-79bdcd8c639cb3a5e6423945 | False | -1174 | 0 | {} |
| 2 | teammate-1110-79bdcd8c639cb3a5e6423945 | True | -463 | 0 | {} |
| 2 | teammate-1110-deb79239da21946792ee702e | False | -752 | 0 | {} |
| 2 | teammate-1110-deb79239da21946792ee702e | True | -1757 | 0 | {} |
| 2 | teammate-1110-dfc8340819347aadd95343e8 | False | -2558 | 0 | {} |
| 2 | teammate-1110-dfc8340819347aadd95343e8 | True | -1463 | 0 | {} |

## Runtime, failures and uncertainty

```json
{
  "provenance": {
    "repository": "https://github.com/sricharanreddycheruku/pokerbots-discard-holdem",
    "commit": "8549810994f2189bb74b456d4c515db065a8d363",
    "teammate_sha256": "1ce00b601ebdebb5d03ae1e307fdccbcd3c5d65ac90724e63599faa47a393ec0",
    "ours_sha256": "bb86e3e7dafd4019157bf9f24cee640e4c9dfbb276883dd92fee1585a03a1990",
    "fetched_utc": "2026-11-10T15:53:48.924630+00:00"
  },
  "overall": {
    "matches": 16,
    "wins": 6,
    "draws": 0,
    "losses": 10,
    "net_chips": -6973,
    "capped_chips": -4251,
    "forfeits": 0
  },
  "stages": {
    "1": {
      "matches": 8,
      "wins": 4,
      "draws": 0,
      "losses": 4,
      "net_chips": -704,
      "capped_chips": -597,
      "forfeits": 0,
      "ours_resources": {
        "max_leg_bank_s": 9.093438190000008,
        "max_reply_ms": 65.60201499999607,
        "notices": 0,
        "diagnostics": 0
      },
      "teammate_resources": {
        "max_leg_bank_s": 6.944732432000038,
        "max_reply_ms": 50.315122000000656,
        "notices": 0,
        "diagnostics": 0
      }
    },
    "2": {
      "matches": 8,
      "wins": 2,
      "draws": 0,
      "losses": 6,
      "net_chips": -6269,
      "capped_chips": -3654,
      "forfeits": 0,
      "ours_resources": {
        "max_leg_bank_s": 28.67700907800048,
        "max_reply_ms": 98.36913499998445,
        "notices": 0,
        "diagnostics": 0
      },
      "teammate_resources": {
        "max_leg_bank_s": 20.766791137998894,
        "max_reply_ms": 60.224615999970865,
        "notices": 0,
        "diagnostics": 0
      }
    }
  },
  "seed_blocks": 4,
  "summed_match_wall_s": 977.3084977899998,
  "points_per_seed_block": [
    0,
    1,
    0.5,
    0
  ],
  "conditional_seed_bootstrap_95": [
    0,
    0.75
  ],
  "warning": "Four independent seed blocks, one opponent and time-adaptive play; this is not a hackathon win-probability estimate. Matrix used official clocks but no hard CPU/RAM sandbox."
}
```

Complete matrix validation passed. Exact command: command.json. Immutable bot/harness hashes and configuration: results.meta.json. Raw per-leg metrics and outcomes: results.jsonl. Use a new output directory to repeat; existing results are never overwritten.

Four independent seed blocks, one opponent and time-adaptive play; this is not a hackathon win-probability estimate. Matrix used official clocks but no hard CPU/RAM sandbox.

Version note after completion: another task changed dist/bot.py during this test. Its current manifest/hash is c264cb8a9e914a210be622d39751aa9ef45e9b9b717b1ef9281e069438e3a39a. This study deliberately kept ours.py frozen at the start-of-test bb86e3e7... artifact throughout; the 6/16 result does NOT describe the newer c264cb8a... release. No change from the other task was reverted.
