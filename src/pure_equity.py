from math import exp, log

PURE_RNG = Random(5172093)
FLOP_SCALE = (.08, .43, .69, .79, .87, .92, .97, .99, 1.)
LATER_SCALE = (.14, .47, .65, .77, .86, .91, .97, .99, 1.)


def plain_flop(pair, flop):
    return max(.02, min(.99, flop_score(pair, flop)))


def plain_strength(pair, board, made, board_rank):
    """Scalar form of vector_strength for turn and river boards."""
    if len(board) == 3:
        return plain_flop(pair, board)
    if board_rank is not None and made == board_rank:
        return .15
    category, high = made[0], made[1]
    strength = LATER_SCALE[category]
    if category <= 2:
        strength += .012 * (high - 6)
        if pair[0] // 4 != high and pair[1] // 4 != high:
            strength -= .12
    if len(board) == 4 and category < 4:
        suits = [c % 4 for c in pair + board]
        if any(suits.count(s) == 4 for s in set(suits)):
            strength += .13
    return min(1., max(.02, strength))


def plain_position(strength, weights):
    """Equal public strengths share a weighted percentile."""
    masses = {}
    for s, w in zip(strength, weights):
        masses[s] = masses.get(s, 0.) + w
    total = sum(masses.values()) or 1.
    below, mids = 0., {}
    for s in sorted(masses):
        mids[s] = (below + .5 * masses[s]) / total
        below += masses[s]
    return [mids[s] for s in strength]


def logistic(x):
    if x < -60:
        return 0.
    if x > 60:
        return 1.
    return 1. / (1. + exp(-x))


def pure_estimate(hole, board, dead, events, model, samples):
    """Pure-Python version of vector_estimate with sampled opponent holdings."""
    rng = PURE_RNG
    unseen = [c for c in DECK if c not in hole + board + dead]
    flop = board[:3]
    count = (2 if dead else 3) + 5 - len(board)
    own = 2 if dead else 3
    river = len(board) == 5
    board_rank = rank(board) if river else None
    pairs, triples, fulls, weights = [], [], [], []
    for _ in range(samples):
        draw = rng.sample(unseen, count)
        full = board + tuple(draw[own:])
        if dead:
            pair = (draw[0], draw[1])
            triple = pair + (dead[1],)
            alt = [plain_flop((triple[a], triple[b]), flop) for a, b in PAIRS]
            top = max(alt)
            pref = [exp((x - top) / .12) for x in alt]
            weight = .15 + .85 * pref[2] / sum(pref)
        else:
            triple = tuple(draw[:3])
            best, choice = -1e9, 0
            for i, (a, b) in enumerate(PAIRS):
                u = rng.random() or 1e-12
                value = plain_flop((triple[a], triple[b]), flop) - .09 * log(-log(u) or 1e-12)
                if value > best:
                    best, choice = value, i
            a, b = PAIRS[choice]
            pair = (triple[a], triple[b])
            weight = 1.
        pairs.append(pair)
        triples.append(triple)
        fulls.append(full)
        weights.append(weight)
    theirs = [rank(p + f) for p, f in zip(pairs, fulls)]
    cache = {}

    def strengths(size):
        if size not in cache:
            if size == 0:
                cache[size] = [PREFLOP_EQUITY[preflop_key(t)][0] / 1000 for t in triples]
            elif size == 3:
                cache[size] = [plain_flop(p, board[:3]) for p in pairs]
            else:
                sub = board[:size]
                cache[size] = [plain_strength(p, sub, theirs[i] if size == 5 else rank(p + sub),
                                              board_rank if size == 5 else None)
                               for i, p in enumerate(pairs)]
        return cache[size]

    for size, action, bet, faced, commitment, position in events:
        if action == "fold" or size > len(board):
            continue
        strength = strengths(size)
        group = "preflop" if size == 0 else "postflop"
        percentile = plain_position(strength, weights)
        if action == "raise":
            if size == 0:
                key, prior = ("reraise", .13) if faced > .34 else ("open", .65)
            elif bet > 1.5:
                key, prior = "large", .10
            else:
                key, prior = ("reraise", .18) if faced > 0 else ("bet", .50)
            frequency = model.rate((group, key), prior)
            floor = min(.08, max(.01, .20 * frequency)) if size > 0 and (faced > 0 or bet > 1.5) else .08
            cut = 1 - frequency
            factors = [floor + (1 - floor) * logistic(13 * (p - cut)) for p in percentile]
        elif action == "call":
            cutoff = (.20 if size == 0 else
                      min(.80, max(.10, model.rate((group, "fold"), .40) + .15 * (faced - .5))))
            factors = [.15 + .85 * logistic(11 * (p - cutoff)) for p in percentile]
        else:
            cut = 1 - model.rate((group, "bet"), .45)
            factors = [.20 + .80 * logistic(-9 * (p - cut)) for p in percentile]
        weights = [w * f ** .65 for w, f in zip(weights, factors)]
    heroes = (hole,) if dead else tuple((hole[a], hole[b]) for a, b in PAIRS)
    total = sum(weights) or 1.
    values, results = [], []
    for hero in heroes:
        if river:
            mine = rank(hero + board)
            outcomes = [1. if mine > t else .5 if mine == t else 0. for t in theirs]
        else:
            outcomes = []
            for f, t in zip(fulls, theirs):
                mine = rank(hero + f)
                outcomes.append(1. if mine > t else .5 if mine == t else 0.)
        results.append(outcomes)
        values.append(sum(w * o for w, o in zip(weights, outcomes)) / total)
    return tuple(values), weights, results, strengths(len(board))
