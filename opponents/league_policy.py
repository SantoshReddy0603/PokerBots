"""Independent league policies using the common card evaluator."""
RNG = Random(LEAGUE_SEED)

def choose_discard(state, req, hole):
    flop = tuple(CARD_ID[c] for c in req["board"])
    return hole[pick(hole, flop)]

def choose_action(state, req):
    legal = req["legal_actions"]
    call, pot = req["to_call"], req["pot"]
    board = tuple(CARD_ID[c] for c in req["board"])
    hole = state.hole
    style = STYLE
    if style == "switch":
        style = "pressure" if state.hand <= state.total / 2 else "trap"
    if style == "tightjam" and not board:
        high, middle, low = sorted((c // 4 for c in hole), reverse=True)
        if "raise" in legal and ((middle >= 8 and middle in (high, low)) or middle >= 11):
            return ("raise", req["max_raise"])
        if call > 2:
            return ("fold",)
        return ("call" if call else "check",)
    if style == "jam":
        return ("raise", req["max_raise"]) if "raise" in legal else ("call" if call else "check",)
    odds = call / (pot + call)
    if not board:
        hi, mid, low = sorted((c // 4 for c in hole), reverse=True)
        premium = (hi == mid and hi >= 7) or (mid == low and mid >= 7) or mid >= 10
        if "raise" in legal and (premium or (style == "pressure" and req["opp_bet"] == 2)):
            return ("raise", min(req["max_raise"], max(5, req["opp_bet"] * 3)))
        if call > 2 and not premium and (call > 13 or hi < 8):
            return ("fold",)
        return ("call" if call else "check",)
    if len(board) == 3:
        strength = max(flop_score(tuple(hole[i] for i in ids), board) for ids in PAIRS)
    else:
        score = rank(hole + board)
        strength = (.14, .40, .65, .80, .87, .92, .98, .99, 1)[score[0]]
        strength += .009 * (score[1] - 5)
        if len(board) == 5 and score == rank(board):
            strength = .11
    target = lambda fraction: ("raise", req["opp_bet"] + max(2, round(fraction * (pot + call))))
    can_raise = "raise" in legal
    if style == "range":
        if state.dead:
            values = simulate(hole, board, state.dead, 28, perf_counter() + .008, RNG,
                              1.8 if call > pot / 4 else .35)
            if values:
                strength = values[0]
        if can_raise and strength > (.80 if call else .64):
            return target(.62 if strength < .87 else 1.03)
        if call and strength < odds + (.02 if len(board) == 5 else .09):
            return ("fold",)
    elif style == "polar":
        if can_raise and len(board) == 5 and (strength > .78 or (not call and strength < .23 and RNG.random() < .52)):
            return target(1.38)
        if can_raise and not call and .58 < strength < .81 and len(board) < 5:
            return target(.47)
        if call and strength < max(.30, odds + .045):
            return ("fold",)
    elif style == "pressure":
        if can_raise and not call and (strength > .33 or RNG.random() < .64):
            return target(.24)
        if can_raise and call and strength > .79:
            return target(.61)
        if call and strength < max(.25, odds + .05):
            return ("fold",)
    elif style == "trap":
        if can_raise and call and strength > .75:
            return target(1.05)
        if can_raise and not call and state.seat == "button" and strength > .57:
            return target(.69)
        if call and strength < max(.33, odds + .06):
            return ("fold",)
    else:
        # Parameterized baseline used for the adversary search against frozen bots.
        value, fold, size, bluff = ADVERSARY
        if can_raise and (strength > value + (.13 if call else 0) or
                          (not call and RNG.random() < bluff)):
            return target(size)
        if call and strength < max(fold, odds + .035):
            return ("fold",)
    return ("call" if call else "check",)





