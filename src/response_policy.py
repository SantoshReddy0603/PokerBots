"""Experimental nonterminal raise response tree; bundle after learning_policy.

The old calculation treats a continuing opponent as a caller and subtracts a
small flat risk charge. This experiment splits continuing mass into calls and
reraises using public action frequencies. A reraise is approximated as an
effective-stack shove, against which the bot may fold or call. This is a model
assumption to validate, not a claim to solve future betting.
"""
_flat_response_action = posterior_action


def response_tree_ev(state, req, weights, outcomes, percentile, continuing, cost, reply, realize):
    total = float(weights.sum())
    fold_mass = 1 - float(continuing.sum()) / total
    frequency = state.model.rate(("postflop", "reraise"), .18)
    reraising = continuing * (.03 + .97 / (1 + np.exp(-14 * (percentile - (1 - frequency)))))
    calling = continuing - reraising
    call_mass, raise_mass = float(calling.sum()) / total, float(reraising.sum()) / total
    call_equity = float(np.dot(calling, outcomes) / calling.sum()) if call_mass > 0 else 0.
    raise_equity = float(np.dot(reraising, outcomes) / reraising.sum()) if raise_mass > 0 else 0.
    full_cost = req["max_raise"] - req["my_bet"]
    full_reply = req["max_raise"] - req["opp_bet"]
    call_ev = realize * call_equity * (req["pot"] + cost + reply) - cost
    # Initial raise cost is sunk only inside this prospective response branch.
    # At the current decision all values are measured relative to folding now.
    raise_ev = max(-cost, raise_equity * (req["pot"] + full_cost + full_reply) - full_cost)
    return fold_mass * req["pot"] + call_mass * call_ev + raise_mass * raise_ev


def posterior_action(state, req, equity):
    # Keep the already profitable river model and final-raise cases isolated.
    if req["street"] == "river" or req.get("raises_left", 1) <= 1 or "raise" not in req["legal_actions"]:
        return _flat_response_action(state, req, equity)
    pot, call, mine, other = req["pot"], req["to_call"], req["my_bet"], req["opp_bet"]
    legal = req["legal_actions"]
    terminal = req["opp_stack"] == 0
    realize = 1. if terminal else (.94 if state.seat == "button" else .89)
    choices = {}
    if "fold" in legal:
        choices[("fold",)] = 0.
    if "check" in legal:
        choices[("check",)] = realize * equity * pot
    if "call" in legal:
        choices[("call",)] = realize * equity * (pot + call) - call
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
        ratio = cost / max(1, pot + call)
        prior = float(np.clip(base_fold + .15 * (ratio - .5), .06, .85))
        fold = state.model.rate(("postflop", "fold_small" if ratio < .6 else "fold_large"), prior)
        if call:
            fold *= .55
        willingness = .10 + .90 * np.clip((percentile - fold) / .25 + .5, 0., 1.)
        continuing = weights * willingness
        if target < req["max_raise"] and req["opp_stack"] > reply:
            ev = response_tree_ev(state, req, weights, outcomes, percentile, continuing, cost, reply, realize)
        else:
            fold = 1 - continuing.sum() / weights.sum()
            showdown = float(np.dot(continuing, outcomes) / continuing.sum())
            ev = fold * pot + (1 - fold) * (realize * showdown * (pot + cost + reply) - cost)
        choices[("raise", int(target))] = float(ev)
    return max(choices, key=choices.get)
