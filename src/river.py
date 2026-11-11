ACTION_RNG = Random(614375)

def river_distribution(hole, board, dead, events, deadline, rng, boundary=None):
    """Uniformly order compatible holdings and evaluate a bounded prefix."""
    unseen = [c for c in DECK if c not in hole + board + dead]
    holdings = list(combinations(unseen, 2))
    rng.shuffle(holdings)
    mine = rank(hole + board)
    board_rank = rank(board)
    rows = []
    total = square = wins = 0.
    for index, pair in enumerate(holdings):
        if index % 16 == 0:
            if perf_counter() >= deadline:
                break
            if boundary is not None and index >= 96:
                equity = wins / total
                ess = total * total / square
                margin = 1.8 * (max(.05, equity * (1 - equity)) / ess) ** .5
                if min(abs(equity - point) for point in boundary) > margin:
                    break
        made = rank(pair + board)
        weight = discard_weight(pair, dead[1], board[:3])
        weight *= range_weight(pair + (dead[1],), pair, board, events, made, board_rank)
        result = compare(mine, made)
        strength = street_strength(pair, board, made, board_rank)
        rows.append((weight, result, strength))
        total += weight
        square += weight * weight
        wins += weight * result
    if not rows:
        return None
    return wins / total, total * total / square, rows, len(rows) == len(holdings)

def response_probabilities(strength, fraction):
    # Broad priors with nonzero calling and raising tails.
    center = min(.77, .38 + .21 * fraction)
    call = .08 + .87 * max(0., min(1., .52 + 3.2 * (strength - center)))
    raise_risk = min(.22, max(0., (strength - .75) * .68))
    return 1 - call, call * (1 - raise_risk), call * raise_risk

def river_bet_ev(rows, pot, contribution, extra, may_reraise):
    mass = value = 0.
    fraction = extra / max(1, pot)
    for weight, result, strength in rows:
        fold, call, raise_risk = response_probabilities(strength, fraction)
        showdown = result * (pot + contribution + extra) - contribution
        # A strong hand continues at the raise node. The marginal risk
        # discount prevents valuing every high-strength response as a flat call.
        raised = showdown - min(2 * extra, pot) * (1 - result)
        value += weight * (fold * pot + call * showdown +
                           raise_risk * (raised if may_reraise else showdown))
        mass += weight
    return value / mass

def river_action(req, distribution):
    equity, ess, rows, exact = distribution
    call, pot = req["to_call"], req["pot"]
    action = "call" if call else "check"
    baseline = equity * (pot + call) - call
    if call and baseline < 0:
        baseline, action = 0., "fold"
    best = (action,)
    if "raise" not in req["legal_actions"]:
        return best
    # Require a margin for the response model and any remaining sampling error.
    margin = pot * (.045 if exact else .055 + .24 / ess ** .5)
    sizes = {max(req["min_raise"], min(req["max_raise"], req["opp_bet"] + round((pot + call) * size)))
             for size in (.29, .60, .96, 1.45)}
    if equity > .9 and req["max_raise"] - req["my_bet"] <= 2.2 * (pot + call):
        sizes.add(req["max_raise"])
    best_value = baseline + margin
    for target in sorted(sizes):
        contribution = target - req["my_bet"]
        extra = target - req["opp_bet"]
        ev = river_bet_ev(rows, pot, contribution, extra,
                          req["raises_left"] > 1 and target < req["max_raise"])
        if ev > best_value:
            best_value, best = ev, ("raise", target)
    return best

