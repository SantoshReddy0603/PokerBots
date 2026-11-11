from pathlib import Path
import runpy

paths = list(Path("opponents/league/development-v2").glob("*.py"))
paths += list(Path("opponents/league/confirmation").glob("*.py"))
assert len(paths) == 18
for path in paths:
    bot = runpy.run_path(str(path))
    state = bot["State"]()
    state.seat = "button"
    cards = bot["CARD_ID"]
    state.hole = tuple(cards[c] for c in ("As", "2h", "7d"))
    base = dict(legal_actions=["check", "raise"], to_call=0, pot=12,
                min_raise=2, max_raise=194, opp_bet=0, my_bet=0)
    for street, board in (("preflop", []), ("flop", ["3s", "4s", "Kh"]),
                          ("turn", ["3s", "4s", "Kh", "8h"]),
                          ("river", ["3s", "4s", "Kh", "8h", "2s"])):
        if street == "turn":
            state.dead = (state.hole[-1], cards["Qc"])
            state.hole = state.hole[:2]
        req = dict(base, street=street, board=board)
        action = bot["normalize"](req, *bot["choose_action"](state, req))
        assert action["action"] in req["legal_actions"]
print("18 independent league artifacts exercised on all streets")

