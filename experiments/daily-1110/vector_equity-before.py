try:
    import numpy as np
except ImportError:
    np = None


def batch_rank(cards):
    """Original histogram evaluator: base-15 category and five rank digits."""
    cards = np.asarray(cards, dtype=np.int16)
    values, suits = cards // 4, cards % 4
    ranks = np.arange(13)
    counts = (values[:, :, None] == ranks).sum(axis=1)
    present = counts > 0
    order = np.argsort(counts * 16 + ranks, axis=1)[:, ::-1]
    rows = np.arange(len(cards))
    top, second = order[:, 0], order[:, 1]
    digits = np.sort(np.where(present, ranks + 1, 0), axis=1)[:, -5:][:, ::-1]
    category = np.zeros(len(cards), dtype=np.int64)

    def high_without(excluded, number):
        available = present.copy()
        for value in excluded:
            available[rows, value] = False
        return np.sort(np.where(available, ranks + 1, 0), axis=1)[:, -number:][:, ::-1]

    def put(mask, kind, components):
        category[mask] = kind
        digits[mask] = 0
        for column, component in enumerate(components):
            digits[mask, column] = component[mask]

    pair = counts[rows, top] == 2
    kick = high_without([top], 3)
    put(pair, 1, [top + 1, *kick.T])
    two = pair & (counts[rows, second] == 2)
    put(two, 2, [top + 1, second + 1, high_without([top, second], 1)[:, 0]])
    trips = counts[rows, top] == 3
    put(trips, 3, [top + 1, *high_without([top], 2).T])

    def straight_high(bits):
        result = np.full(len(cards), -1)
        result[bits[:, [12, 0, 1, 2, 3]].all(axis=1)] = 3
        for high in range(4, 13):
            result[bits[:, high - 4:high + 1].all(axis=1)] = high
        return result

    run = straight_high(present)
    put(run >= 0, 4, [run + 1])
    flush_bits = np.zeros_like(present)
    for suit in range(4):
        belongs = suits == suit
        mask = belongs.sum(axis=1) >= 5
        bits = ((values[:, :, None] == ranks) & belongs[:, :, None]).any(axis=1)
        flush_bits[mask] = bits[mask]
    flush = flush_bits.any(axis=1)
    flush_digits = np.sort(np.where(flush_bits, ranks + 1, 0), axis=1)[:, -5:][:, ::-1]
    put(flush, 5, list(flush_digits.T))
    put(trips & (counts[rows, second] >= 2), 6, [top + 1, second + 1])
    put(counts[rows, top] == 4, 7, [top + 1, high_without([top], 1)[:, 0]])
    flush_run = straight_high(flush_bits)
    put(flush_run >= 0, 8, [flush_run + 1])
    return category * 15 ** 5 + digits @ (15 ** np.arange(4, -1, -1))


def batch_flop(pairs, flop):
    board = np.broadcast_to(flop, (len(pairs), 3))
    cards = np.concatenate((pairs, board), axis=1)
    score = batch_rank(cards)
    category = score // 15 ** 5
    high = score // 15 ** 4 % 15 - 1
    private = pairs // 4
    hi, lo = private.max(axis=1), private.min(axis=1)
    strength = np.asarray((.08, .43, .69, .79, .87, .92, .97, .99, 1.))[category]
    strength += .005 * hi + .002 * lo
    strength += np.where(category == 1, .012 * (high - 6), 0)
    strength -= .27 * ((category == 1) & ~(private == high[:, None]).any(axis=1))
    if len(set(int(c) // 4 for c in flop)) == 2:
        strength -= .10 * ((category == 2) & (hi != lo))
    ranks = np.arange(13)
    bits = (cards[:, :, None] // 4 == ranks).any(axis=1)
    draw = np.zeros(len(pairs), dtype=bool)
    for suit in range(4):
        draw |= (cards % 4 == suit).sum(axis=1) == 4
    outs = np.zeros_like(bits)
    for pattern, _ in WINDOWS:
        included = np.array([bool(pattern & (1 << r)) for r in range(13)])
        missing = included & ~bits
        outs |= missing & (missing.sum(axis=1) == 1)[:, None]
    strength += (category < 4) * (.33 * draw + .104 * np.minimum(outs.sum(axis=1), 3))
    return strength


def vector_strength(pair, board, made=None):
    if len(board) == 3:
        return np.clip(batch_flop(pair, board), .02, .99)
    score = made if made is not None else batch_rank(np.concatenate((pair, np.broadcast_to(board, (len(pair), len(board)))), axis=1))
    category = score // 15 ** 5
    high = score // 15 ** 4 % 15 - 1
    strength = np.asarray((.14, .47, .65, .77, .86, .91, .97, .99, 1.))[category]
    strength += np.where(category <= 2, .012 * (high - 6), 0)
    strength -= .12 * ((category <= 2) & ~(pair // 4 == high[:, None]).any(axis=1))
    if len(board) == 4:
        all_cards = np.concatenate((pair, np.broadcast_to(board, (len(pair), 4))), axis=1)
        draw = np.zeros(len(pair), dtype=bool)
        for suit in range(4):
            draw |= (all_cards % 4 == suit).sum(axis=1) == 4
        strength += .13 * ((category < 4) & draw)
    if len(board) == 5:
        strength = np.where(score == batch_rank(np.asarray([board]))[0], .15, strength)
    return np.clip(strength, .02, 1.)


_DENSE_PREFLOP = None


def weighted_position(strength, weights):
    """Equal public hand strengths share a percentile, including board ties."""
    _, groups = np.unique(strength, return_inverse=True)
    masses = np.bincount(groups, weights=weights)
    return ((np.cumsum(masses) - .5 * masses) / masses.sum())[groups]


def batch_preflop(triples):
    global _DENSE_PREFLOP
    if _DENSE_PREFLOP is None:
        _DENSE_PREFLOP = np.zeros((52, 52, 52), dtype=float)
        for triple in combinations(range(52), 3):
            _DENSE_PREFLOP[triple] = PREFLOP_EQUITY[preflop_key(triple)][0] / 1000
    ordered = np.sort(triples, axis=1)
    return _DENSE_PREFLOP[ordered[:, 0], ordered[:, 1], ordered[:, 2]]


def vector_estimate(hole, board, dead, events, model, samples=512, details=False):
    """Common-runout estimates; exact compatible pair enumeration on the river."""
    unseen = np.asarray([c for c in DECK if c not in hole + board + dead])
    if len(board) == 5 and dead:
        indices = np.triu_indices(len(unseen), 1)
        pairs = np.column_stack((unseen[indices[0]], unseen[indices[1]]))
        triple = np.column_stack((pairs, np.full(len(pairs), dead[1])))
        full = np.broadcast_to(board, (len(pairs), 5))
    else:
        count = (2 if dead else 3) + 5 - len(board)
        selected = np.argpartition(VECTOR_RNG.random((samples, len(unseen))), count - 1, axis=1)[:, :count]
        draw = unseen[selected]
        # argpartition selects an unordered uniform subset; randomize its roles.
        draw = np.take_along_axis(draw, np.argsort(VECTOR_RNG.random(draw.shape), axis=1), axis=1)
        own = 2 if dead else 3
        full = np.concatenate((np.broadcast_to(board, (samples, len(board))), draw[:, own:]), axis=1)
        if dead:
            pairs = draw[:, :2]
            triple = np.column_stack((pairs, np.full(samples, dead[1])))
        else:
            triple = draw[:, :3]
            possibilities = [triple[:, pair] for pair in PAIRS]
            choices = np.column_stack([batch_flop(pair, board[:3]) for pair in possibilities])
            # Mixture allows uncertainty in the opponent's flop-only discard.
            best = np.argmax(choices + VECTOR_RNG.gumbel(0, .09, choices.shape), axis=1)
            pairs = np.stack(possibilities, axis=1)[np.arange(samples), best]
    n = len(pairs)
    river_scores = batch_rank(np.concatenate((pairs, full), axis=1)) if len(board) == 5 else None
    weights = np.ones(n)
    if dead:
        alternatives = np.column_stack([batch_flop(triple[:, pair], board[:3]) for pair in PAIRS])
        preferences = np.exp((alternatives - alternatives.max(axis=1)[:, None]) / .12)
        weights *= .15 + .85 * preferences[:, 2] / preferences.sum(axis=1)
    cache = {}
    for size, action, bet, faced, commitment, position in events:
        if action == "fold" or size > len(board):
            continue
        if size not in cache:
            cache[size] = batch_preflop(triple) if size == 0 else vector_strength(
                pairs, board[:size], river_scores if size == 5 else None)
        strength = cache[size]
        group = "preflop" if size == 0 else "postflop"
        percentile = weighted_position(strength, weights)
        if action == "raise":
            if size == 0:
                key, prior = ("reraise", .13) if faced > .34 else ("open", .65)
            elif bet > 1.5:
                key, prior = "large", .10
            else:
                key, prior = ("reraise", .18) if faced > 0 else ("bet", .50)
            frequency = model.rate((group, key), prior)
            likelihood = .08 + .92 / (1 + np.exp(-13 * (percentile - (1 - frequency))))
        elif action == "call":
            cutoff = (.20 if size == 0 else
                      np.clip(model.rate((group, "fold"), .40) + .15 * (faced - .5), .10, .80))
            likelihood = .15 + .85 / (1 + np.exp(-11 * (percentile - cutoff)))
        else:
            frequency = model.rate((group, "bet"), .45)
            likelihood = .20 + .80 / (1 + np.exp(9 * (percentile - (1 - frequency))))
        weights *= likelihood ** .65
    theirs = river_scores if river_scores is not None else batch_rank(np.concatenate((pairs, full), axis=1))
    heroes = (hole,) if dead else tuple((hole[a], hole[b]) for a, b in PAIRS)
    values = []
    results = []
    for hero in heroes:
        if len(board) == 5:
            # All rows have the same visible board: rank hero once, exactly.
            score = rank(hero + board)
            mine = score[0] * 15 ** 5 + sum((value + 1) * 15 ** (4 - i)
                                           for i, value in enumerate(score[1:]))
        else:
            mine = batch_rank(np.concatenate((np.broadcast_to(hero, (n, 2)), full), axis=1))
        outcomes = (mine > theirs) + .5 * (mine == theirs)
        results.append(outcomes)
        values.append(float(outcomes[0]) if (outcomes == outcomes[0]).all() else
                      float(np.dot(weights, outcomes) / weights.sum()))
    if details:
        if len(board) not in cache:
            cache[len(board)] = vector_strength(pairs, board, river_scores)
        return tuple(values), weights, results, cache[len(board)]
    return tuple(values)


VECTOR_RNG = np.random.default_rng(6183902) if np is not None else None
