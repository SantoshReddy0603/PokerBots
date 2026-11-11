"""Offline timing/ESS probe with independent high-budget model references."""
import json
from pathlib import Path
from random import Random
import runpy
from statistics import mean

base = runpy.run_path("checkpoints/review-1109-combined.py")
adaptive = runpy.run_path("checkpoints/review-1109-sampling-exp.py")
rng = Random(681034)
history = [dict(street="preflop", actor="opp", action="raise", amount=5),
           dict(street="preflop", actor="me", action="call", amount=5),
           dict(street="flop", actor="me", action="check"),
           dict(street="flop", actor="opp", action="raise", amount=4),
           dict(street="flop", actor="me", action="call", amount=4),
           dict(street="turn", actor="me", action="check"),
           dict(street="turn", actor="opp", action="raise", amount=191)]
rows = []
for i in range(30):
    cards = tuple(rng.sample(range(52), 8))
    hole, board, dead = cards[:2], cards[2:6], cards[6:]
    req = dict(type="action_request", hand_id=1, pot=209, to_call=191, time_left_ms=60000,
               opp_stack=0, my_stack=191, my_bet=0, opp_bet=191, street="turn", legal_actions=["fold", "call"])
    values = []
    for scope in (base, adaptive):
        state = scope["State"]()
        state.seat, state.history = "big_blind", history
        scope["vector_estimate"].__globals__["VECTOR_RNG"] = scope["np"].random.default_rng(900 + i)
        values.append(scope["estimate"](state, req, hole, board, dead, 512)[0])
        if scope is adaptive:
            stats = state.sample_stats
    base["vector_estimate"].__globals__["VECTOR_RNG"] = base["np"].random.default_rng(6000 + i)
    reference = base["vector_estimate"](hole, board, dead, base["range_events"](history, "big_blind"),
                                       base["Frequencies"](), 4096)[0]
    rows.append(dict(case=i, fixed=values[0], adaptive=values[1], reference=reference, **stats))
summary = dict(cases=len(rows), resampled=sum(r["rows"] > 512 for r in rows),
               mean_ess=mean(r["ess"] for r in rows), max_ms=1000 * max(r["seconds"] for r in rows),
               fixed_mean_absolute_model_reference_error=mean(abs(r["fixed"] - r["reference"]) for r in rows),
               adaptive_mean_absolute_model_reference_error=mean(abs(r["adaptive"] - r["reference"]) for r in rows),
               caveat="4096-sample reference shares the heuristic range model; not true equity against an actual opponent.")
with Path("experiments/review-fixes-1109/sampling-probe.json").open("x") as file:
    json.dump(dict(summary=summary, rows=rows), file, indent=2)
print(json.dumps(summary, indent=2))
