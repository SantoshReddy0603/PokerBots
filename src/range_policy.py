DISCARD_MODE = "equity"
BETTING = True
ADAPT = False
RNG = Random(739483)

def choose_discard(state, req, hole):
    flop = tuple(CARD_ID[c] for c in req["board"])
    if DISCARD_MODE == "rank":
        return min(hole)
    if DISCARD_MODE == "made":
        return hole[pick(hole, flop, 1)]
    deadline = perf_counter() + budget(state, req)
    values = modeled_equity(hole, flop, (), range_events(state.history, state.seat), 128, deadline, RNG)
    if values:
        # Small prior favors better playability when rollout estimates are close.
        return hole[max(range(3), key=lambda i: values[i] + .05 *
                        flop_score(tuple(hole[j] for j in PAIRS[i]), flop))]
    return hole[pick(hole, flop)]

def pressure(state, street):
    return min(3., sum(.55 if event["street"] == "preflop" else .95
                       for event in state.history if event["actor"] == "opp"
                       and event["action"] == "raise"))

def choose_action(state, req):
    if BETTING:
        return betting_action(state, req)
    return ("check" if "check" in req["legal_actions"] else "call",)

def preflop(hole):
    high, middle, low = sorted((c // 4 for c in hole), reverse=True)
    strength = .34 + .011 * high + .008 * middle + .003 * low
    if high == low:
        return .71 + .009 * high
    if high == middle or middle == low:
        return strength + .10 + .006 * middle
    bonus = max((.045 if a % 4 == b % 4 else 0) +
                max(0, .033 - .008 * abs(a // 4 - b // 4))
                for a, b in combinations(hole, 2))
    return strength + bonus

def terminal_call(equity, pot, cost):
    return equity * (pot + cost) >= cost

def calibrated_preflop(hole, committed):
    uniform, premium = PREFLOP_EQUITY[preflop_key(hole)]
    # Large commitments are modeled as a mixture of broad and premium-heavy ranges.
    tight = min(.70, max(0., (committed - 5) / 95))
    return (uniform + tight * (premium - uniform)) / 1000

def betting_action(state, req):
    street = req["street"]
    pot, call = req["pot"], req["to_call"]
    behind = req["my_stack"]
    legal = req["legal_actions"]
    button = state.seat == "button"
    odds = call / (pot + call)
    if street == "preflop":
        calibrated = calibrated_preflop(state.hole, req["opp_bet"])
        if call and req["opp_stack"] == 0:
            return ("call" if terminal_call(calibrated, pot, call) else "fold",)
        values = {card // 4 for card in state.hole}
        equity = calibrated if len(values) == 1 else .80 * preflop(state.hole) + .20 * calibrated
        if call >= 20:
            threshold = max(odds + .09, .57 + .00065 * call)
            if equity < threshold:
                return ("fold",)
            if "raise" in legal and equity > .76:
                return ("raise", req["max_raise"])
            return ("call",)
        if "raise" in legal:
            if req["opp_bet"] <= 2 and equity >= (.473 if button else .546):
                return ("raise", 5 if button else 7)
            if req["opp_bet"] > 2 and equity >= .624 + .002 * call:
                return ("raise", max(3 * req["opp_bet"], 12))
        if call and (equity < .38 or (call > 3 and equity < .43 + .011 * call)):
            return ("fold",)
        return ("call" if call else "check",)

    board = tuple(CARD_ID[c] for c in req["board"])
    deadline = perf_counter() + budget(state, req)
    values = modeled_equity(state.hole, board, state.dead, range_events(state.history, state.seat), 144, deadline, RNG)
    if not values:
        return ("check" if not call else "fold",)
    equity = max(values)
    river = street == "river"
    if call:
        if river or req["opp_stack"] == 0:
            if not terminal_call(equity, pot, call):
                return ("fold",)
        else:
            threshold = max(odds + .045, .31 + .13 * min(1., call / pot))
            if not button:
                threshold += .023
            if equity < threshold:
                return ("fold",)
    if "raise" in legal:
        if call:
            if equity >= (.84 if river else .80) + .045 * min(1., call / pot):
                target = req["opp_bet"] + round(.66 * (pot + call))
                return ("raise", target)
        else:
            value_cut = .66 if river else .625
            if equity > value_cut:
                fraction = .82 if equity > .85 else .53
                if equity > .88 and behind <= 1.25 * pot:
                    fraction = 1.25
                return ("raise", max(2, round(pot * fraction)))
            if button and equity < .37 and RNG.random() < (.13 if river else .18):
                return ("raise", max(2, round(pot * .47)))
    return ("call" if call else "check",)




