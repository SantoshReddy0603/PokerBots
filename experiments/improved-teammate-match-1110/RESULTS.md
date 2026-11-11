# Improved bot versus latest teammate: 10 November 2026

Frozen repository commit: `8549810994f2189bb74b456d4c515db065a8d363`.
Our SHA-256: `c264cb8a9e914a210be622d39751aa9ef45e9b9b717b1ef9281e069438e3a39a`.
Teammate SHA-256: `35046e2fc6b3e4f52d9356779ca15db8bcd6cfd39b7e799978bac3163c260e64`.

Both updated competition stages, two fresh-process legs per match, four fresh seed blocks and both assignments. Linux CPython 3.11.9, jobs=2, BLAS threads=1. Official time banks/startup grace enabled; no hard CPU/RAM sandbox in this matrix. No playing code changed.

| Stage | Our wins | Draws | Teammate wins | Our net chips |
|---|---:|---:|---:|---:|
| 1 (400 hands) | 4 | 0 | 4 | -989 |
| 2 (1000 hands) | 5 | 0 | 3 | +4,488 |
| **Total** | **9** | **0** | **7** | **+3,499** |

## Match results

| Stage | Seed | Assignment reversed | Our net chips | Our match points | Forfeit |
|---|---|---|---:|---:|---|
| 1 | improved-peer-1110-0bdc9de50120b194b68e3c6d | False | -233 | 0 | {} |
| 1 | improved-peer-1110-0bdc9de50120b194b68e3c6d | True | +77 | 1 | {} |
| 1 | improved-peer-1110-1c51e7c6535a50a32af7dd5c | False | +101 | 1 | {} |
| 1 | improved-peer-1110-1c51e7c6535a50a32af7dd5c | True | +538 | 1 | {} |
| 1 | improved-peer-1110-1ded74dee7b8c053bdc79b18 | False | -438 | 0 | {} |
| 1 | improved-peer-1110-1ded74dee7b8c053bdc79b18 | True | +1129 | 1 | {} |
| 1 | improved-peer-1110-8b493c68481225534a0aa89d | False | -1351 | 0 | {} |
| 1 | improved-peer-1110-8b493c68481225534a0aa89d | True | -812 | 0 | {} |
| 2 | improved-peer-1110-0bdc9de50120b194b68e3c6d | False | -1999 | 0 | {} |
| 2 | improved-peer-1110-0bdc9de50120b194b68e3c6d | True | -1820 | 0 | {} |
| 2 | improved-peer-1110-1c51e7c6535a50a32af7dd5c | False | +785 | 1 | {} |
| 2 | improved-peer-1110-1c51e7c6535a50a32af7dd5c | True | +2275 | 1 | {} |
| 2 | improved-peer-1110-1ded74dee7b8c053bdc79b18 | False | +3358 | 1 | {} |
| 2 | improved-peer-1110-1ded74dee7b8c053bdc79b18 | True | +2638 | 1 | {} |
| 2 | improved-peer-1110-8b493c68481225534a0aa89d | False | +219 | 1 | {} |
| 2 | improved-peer-1110-8b493c68481225534a0aa89d | True | -968 | 0 | {} |

## Runtime, failures and uncertainty

```json
{
  "provenance": {
    "repository": "https://github.com/sricharanreddycheruku/pokerbots-discard-holdem",
    "commit": "8549810994f2189bb74b456d4c515db065a8d363",
    "ours_sha256": "c264cb8a9e914a210be622d39751aa9ef45e9b9b717b1ef9281e069438e3a39a",
    "teammate_sha256": "35046e2fc6b3e4f52d9356779ca15db8bcd6cfd39b7e799978bac3163c260e64",
    "fetched_utc": "2026-11-10T16:09:58.936647+00:00"
  },
  "overall": {
    "matches": 16,
    "wins": 9,
    "draws": 0,
    "losses": 7,
    "net_chips": 3499,
    "capped_chips": 581,
    "forfeits": 0
  },
  "stages": {
    "1": {
      "matches": 8,
      "wins": 4,
      "draws": 0,
      "losses": 4,
      "net_chips": -989,
      "capped_chips": -455,
      "forfeits": 0,
      "ours_resources": {
        "max_leg_bank_s": 9.70904005299986,
        "max_reply_ms": 52.04061799997817,
        "notices": 0,
        "diagnostics": 0
      },
      "teammate_resources": {
        "max_leg_bank_s": 7.02167291800005,
        "max_reply_ms": 53.8365619999972,
        "notices": 0,
        "diagnostics": 0
      }
    },
    "2": {
      "matches": 8,
      "wins": 5,
      "draws": 0,
      "losses": 3,
      "net_chips": 4488,
      "capped_chips": 1036,
      "forfeits": 0,
      "ours_resources": {
        "max_leg_bank_s": 26.637835235999347,
        "max_reply_ms": 87.36431699998093,
        "notices": 0,
        "diagnostics": 0
      },
      "teammate_resources": {
        "max_leg_bank_s": 19.566456563999907,
        "max_reply_ms": 61.48970300000656,
        "notices": 0,
        "diagnostics": 0
      }
    }
  },
  "seed_blocks": 4,
  "summed_match_wall_s": 975.7209465480003,
  "points_per_seed_block": [
    1,
    0.75,
    0.25,
    0.25
  ],
  "conditional_seed_bootstrap_95": [
    0.25,
    0.875
  ],
  "warning": "Four independent seed blocks, one opponent and time-adaptive play; this is not a hackathon win-probability estimate. Matrix used official clocks but no hard CPU/RAM sandbox."
}
```

Complete matrix validation passed. Exact command: command.json. Immutable bot/harness hashes and configuration: results.meta.json. Raw per-leg metrics and outcomes: results.jsonl. Use a new output directory to repeat; existing results are never overwritten.

Four independent seed blocks, one opponent and time-adaptive play; this is not a hackathon win-probability estimate. Matrix used official clocks but no hard CPU/RAM sandbox.
