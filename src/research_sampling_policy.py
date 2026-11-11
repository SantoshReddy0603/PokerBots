DISCARD_MODE = "equity"
BETTING = True
ADAPT = False
RNG = Random(739483)
ACTION_RNG = Random(817263)


def estimate(state, req, hole, board, dead, samples):
    events = range_events(state.history, state.seat)
    state.posterior = None
    if np is not None and req["time_left_ms"] > max(2000, 12 * (state.total - req["hand_id"] + 1)):
        started = perf_counter()
        remaining = max(1, state.total - req["hand_id"] + 1)
        allowance = min(.075, state.reply_ms / 10000,
                        req["time_left_ms"] / 1000 / remaining * .5)
        values, weights, outcomes, strengths, particles = vector_estimate(
            hole, board, dead, events, state.model, samples, True, return_particles=True)
        elapsed = perf_counter() - started
        best = max(range(len(values)), key=values.__getitem__)
        error = float(np.sqrt(np.dot(weights ** 2, (outcomes[best] - values[best]) ** 2)) / weights.sum())
        cost = req.get("to_call", 0)
        realization = 1. if req.get("opp_stack") == 0 else (.94 if state.seat == "button" else .89)
        threshold = cost / max(1, (req.get("pot", 0) + cost) * realization)
        close = cost >= .25 * max(1, req.get("pot", 0)) and abs(values[best] - threshold) < 2 * error
        if req.get("type") == "discard_request":
            order = sorted(range(len(values)), key=values.__getitem__, reverse=True)
            gap = outcomes[order[0]] - outcomes[order[1]]
            mean_gap = values[order[0]] - values[order[1]]
            gap_error = float(np.sqrt(np.dot(weights ** 2, (gap - mean_gap) ** 2)) / weights.sum())
            close = mean_gap < 2 * gap_error
        # One additional batch at most; reweight the pooled particles together.
        # Predict its cost conservatively before launching non-preemptible NumPy work.
        if len(board) < 5 and close and perf_counter() + 2.5 * elapsed < started + allowance:
            values, weights, outcomes, strengths = vector_estimate(
                hole, board, dead, events, state.model, samples, True, particles=particles)
        state.sample_stats = dict(rows=len(weights), ess=float(weights.sum() ** 2 / np.dot(weights, weights)),
                                  seconds=perf_counter() - started)
        state.posterior = weights, outcomes[max(range(len(values)), key=values.__getitem__)], strengths
        return values
    return modeled_equity(hole, board, dead, events, 144, perf_counter() + budget(state, req), RNG)

def choose_discard(state, req, hole):
    flop = tuple(CARD_ID[c] for c in req["board"])
    if DISCARD_MODE == "rank":
        return min(hole)
    if DISCARD_MODE == "made":
        return hole[pick(hole, flop, 1)]
    values = estimate(state, req, hole, flop, (), 512)
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
        # Keep the tested thresholds for non-trip holdings. Unknown shove
        # ranges can be much tighter than the table's premium-heavy prior.
        trips = len({card // 4 for card in state.hole}) == 1
        uniform, premium = (x / 1000 for x in PREFLOP_EQUITY[preflop_key(state.hole)])
        aggression = state.model.rate(("preflop", "raise"), .30)
        equity = uniform + min(.8, max(0., .65 - aggression)) * (premium - uniform)
        if call >= 20:
            conservative = calibrated_preflop(state.hole, req["opp_bet"]) if trips else preflop(state.hole)
            threshold = max(odds + .09, .57 + .00065 * call)
            if (equity < odds + .055 if aggression > .45 else conservative < threshold):
                return ("fold",)
            if "raise" in legal and equity > .76:
                return ("raise", req["max_raise"])
            return ("call",)
        if "raise" in legal:
            if req["opp_bet"] <= 2 and equity >= (.42 if button else .58):
                return ("raise", 5 if button else 7)
            if req["opp_bet"] > 2 and equity >= .60 + .001 * call:
                return ("raise", max(3 * req["opp_bet"], 12))
        if call and equity < odds + (.10 if button else .14):
            return ("fold",)
        return ("call" if call else "check",)

    board = tuple(CARD_ID[c] for c in req["board"])
    values = estimate(state, req, state.hole, board, state.dead, 512)
    if not values:
        return ("check" if not call else "fold",)
    equity = max(values)
    river = street == "river"
    if getattr(state, "posterior", None) is not None:
        return posterior_action(state, req, equity)
    if call:
        if river or req["opp_stack"] == 0:
            if not terminal_call(equity, pot, call):
                return ("fold",)
        else:
            threshold = max(odds + .035, .27 + .10 * min(1., call / pot))
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
            fold_rate = state.model.rate(("postflop", "fold"), .35)
            if button and equity < .37 and ACTION_RNG.random() < max(.03, min(.35, fold_rate - .22)):
                return ("raise", max(2, round(pot * .47)))
    return ("call" if call else "check",)


def posterior_action(state, req, equity):
    """Compare incremental chip EV using a soft continuing-range model."""
    pot, call, mine, other = req["pot"], req["to_call"], req["my_bet"], req["opp_bet"]
    legal = req["legal_actions"]
    terminal = req["street"] == "river" or req["opp_stack"] == 0
    realize = 1. if terminal else (.94 if state.seat == "button" else .89)
    choices = {}
    if "fold" in legal:
        choices[("fold",)] = 0.
    if "check" in legal:
        choices[("check",)] = realize * equity * pot
    if "call" in legal:
        choices[("call",)] = realize * equity * (pot + call) - call
    if "raise" in legal:
        weights, outcomes, strength = state.posterior
        percentile = weighted_position(strength, weights)
        targets = {max(req["min_raise"], min(req["max_raise"], other + round((pot + call) * fraction)))
                   for fraction in (.35, .70, 1.10)}
        if equity > .75 and min(req["my_stack"], req["opp_stack"] + call) < 2 * (pot + call):
            targets.add(req["max_raise"])
        base_fold = state.model.rate(("postflop", "fold"), .40)
        for target in targets:
            cost = target - mine
            reply = min(req["opp_stack"], target - other)
            ratio, size_bucket = raise_size_features(pot, call, cost)
            prior = float(np.clip(base_fold + .15 * (ratio - .5), .06, .85))
            fold = state.model.rate(("postflop", size_bucket), prior)
            if call:
                fold *= .55
            willingness = .10 + .90 * np.clip((percentile - fold) / .25 + .5, 0., 1.)
            continuing = weights * willingness
            fold = 1 - continuing.sum() / weights.sum()
            showdown = float(np.dot(continuing, outcomes) / continuing.sum())
            ev = fold * pot + (1 - fold) * (realize * showdown * (pot + cost + reply) - cost)
            # A nonterminal bet can be raised by a more selective range.
            if target < req["max_raise"] and req["opp_stack"] > reply:
                ev -= .035 * cost * (1 - equity)
            choices[("raise", int(target))] = float(ev)
    return max(choices, key=choices.get)






