STREET_CARDS = {"preflop": 0, "flop": 3, "turn": 4, "river": 5}

def range_events(history, seat):
    """Replay public street totals into the pot and pressure at each action."""
    totals = [1, 2] if seat == "button" else [2, 1]
    pot, street = 3, "preflop"
    events = []
    for event in history:
        current = event["street"]
        if current != street:
            totals = [0, 0]
            street = current
        actor = int(event["actor"] == "opp")
        action = event["action"]
        amount = event.get("amount", totals[actor])
        addition = max(0, amount - totals[actor])
        faced = max(0, totals[1 - actor] - totals[actor])
        if actor:
            events.append((STREET_CARDS[street], action, addition / max(1, pot),
                           faced / max(1, pot), min(1., addition / max(1, 200 - (pot - faced) / 2)),
                           seat != "button"))
        pot += addition
        totals[actor] += addition
    return events

def street_strength(pair, board, made=None, board_rank=None):
    if len(board) == 3:
        return min(.99, flop_score(pair, board))
    if made is None:
        made = rank(pair + board)
    if board_rank is not None and made == board_rank:
        return .15
    category, high = made[:2]
    strength = (.14, .47, .65, .77, .86, .91, .97, .99, 1.)[category]
    if category <= 2:
        strength += .012 * (high - 6)
        if all(c // 4 != high for c in pair):
            strength -= .12
    if len(board) == 4 and category < 4:
        if any(sum(c % 4 == suit for c in pair + board) == 4 for suit in {c % 4 for c in pair}):
            strength += .13
    return min(1., max(.02, strength))

def action_likelihood(strength, action, size, faced, commitment, in_position):
    if action == "raise":
        threshold = min(.83, .49 + .20 * size + .10 * min(1., faced) +
                        .08 * commitment - (.035 if in_position else 0))
        value = max(0., min(1., .45 + 3.5 * (strength - threshold)))
        bluff = .14 + .17 * max(0., .40 - strength)
        return bluff + (1 - bluff) * value
    if action == "call":
        threshold = .29 + .22 * min(1., faced)
        willingness = max(0., min(1., .50 + 3.1 * (strength - threshold)))
        return .22 + .73 * willingness - .14 * max(0., strength - .73)
    if action == "check":
        return .68 + .27 * min(1., max(0., (.70 - strength) * 2))
    return 1.

def discard_weight(pair, exposed, flop):
    triple = pair + (exposed,)
    selected = pick(triple, flop, 2)
    # Agreement with several plausible flop-only discard rules.
    return (.16 + .57 * (selected == 2) + .15 * (pick(triple, flop, 0) == 2)
            + .12 * (pick(triple, flop, 1) == 2))

def range_weight(triple, pair, board, events, made=None, board_rank=None):
    weight = 1.
    strengths = {}
    for size, action, bet, faced, commitment, in_position in events:
        if size > len(board):
            continue
        if size not in strengths:
            strengths[size] = (PREFLOP_EQUITY[preflop_key(triple)][0] / 1000 if size == 0 else
                               street_strength(pair, board[:size], made if size == len(board) else None,
                                               board_rank if size == 5 else None))
        likelihood = action_likelihood(strengths[size], action, bet, faced, commitment, in_position)
        # Soften product weights so one unexpected event does not erase a hand.
        weight *= .18 + .82 * likelihood
    return weight

def modeled_equity(hole, board, dead, events, samples, deadline, rng):
    unseen = [c for c in DECK if c not in hole + board + dead]
    flop = board[:3]
    mass = 0.
    sums = [0.] * (3 if not dead else 1)
    hero_pairs = (hole,) if dead else tuple((hole[a], hole[b]) for a, b in PAIRS)
    for n in range(samples):
        if n % 4 == 0 and perf_counter() >= deadline:
            break
        draw = tuple(rng.sample(unseen, 5 - len(board) + (2 if dead else 3)))
        if dead:
            pair, full = draw[:2], board + draw[2:]
            triple = pair + (dead[1],)
            weight = discard_weight(pair, dead[1], flop)
        else:
            triple, full = draw[:3], board + draw[3:]
            i, j = PAIRS[pick(triple, flop, (0, 2, 2, 1)[n % 4])]
            pair = (triple[i], triple[j])
            weight = 1.
        score = rank(pair + full)
        weight *= range_weight(triple, pair, board, events, score if len(board) == 5 else None,
                               rank(board) if len(board) == 5 else None)
        for i, hero in enumerate(hero_pairs):
            sums[i] += weight * compare(rank(hero + full), score)
        mass += weight
    return tuple(x / mass for x in sums) if mass else None

