"""Independent synthetic tight-reraise diagnostic; public information only."""
RNG = Random(526019)


def choose_discard(state, req, hole):
    board = tuple(CARD_ID[c] for c in req["board"])
    values = simulate(hole, board, (), 80, perf_counter() + .006, RNG)
    return hole[max(range(3), key=values.__getitem__)] if values else hole[pick(hole, board)]


def choose_action(state, req):
    legal, call, pot = req["legal_actions"], req["to_call"], req["pot"]
    if req["street"] == "preflop":
        equity = PREFLOP_EQUITY[preflop_key(state.hole)][0] / 1000
        if "raise" in legal:
            if req["opp_bet"] <= 2 and equity > .48:
                return ("raise", 6)
            if req["opp_bet"] > 2 and equity > .69:
                return ("raise", 3 * req["opp_bet"])
        threshold = .36 if call <= 3 else (.53 if call <= 16 else .71)
        return ("fold",) if call and equity < threshold else ("call" if call else "check",)
    board = tuple(CARD_ID[c] for c in req["board"])
    values = simulate(state.hole, board, state.dead, 80, perf_counter() + .006, RNG)
    equity = max(values) if values else .4
    if call and equity < call / (pot + call) + (.07 if req["street"] != "river" else .02):
        return ("fold",)
    if "raise" in legal and equity > (.78 if call else .61):
        return ("raise", req["opp_bet"] + round(.85 * (pot + call)))
    return ("call" if call else "check",)
