def preflop_key(hole):
    """Canonicalize all permutations within equal rank groups and relabel suits."""
    high, middle, low = sorted(hole, reverse=True)
    ordered = [(high, middle, low)]
    if high // 4 == middle // 4:
        ordered.append((middle, high, low))
    if middle // 4 == low // 4:
        ordered.append((high, low, middle))
    keys = []
    for cards in ordered:
        suits = {}
        key = 0
        for card in cards:
            suit = card % 4
            key = key * 52 + 4 * (card // 4) + suits.setdefault(suit, len(suits))
        keys.append(key)
    return min(keys)

def premium_weight(hole):
    high, mid, low = sorted((card // 4 for card in hole), reverse=True)
    pair = high == mid or mid == low
    return .08 + .62 * (pair and mid >= 6) + .75 * (mid >= 9) + .16 * (high == 12)

