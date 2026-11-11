import json
import sys

CARDS = tuple(r + s for r in "23456789TJQKA" for s in "shdc")
CARD_ID = {card: i for i, card in enumerate(CARDS)}

class State:
    def __init__(self):
        self.total = 400
        self.reply_ms = 5000
        self.errors = 0
        self.reset({})

    def reset(self, msg):
        self.hand = msg.get("hand_id", 0)
        self.seat = msg.get("seat")
        self.hole = tuple(CARD_ID[c] for c in msg.get("hole_cards", ()))
        self.dead = ()
        self.history = []
        self.pending = None

    def observe(self, msg, kind):
        if kind == "new_hand":
            self.reset(msg)
        elif kind == "init":
            self.total = msg["total_hands"]
            self.reply_ms = msg["per_response_ms"]
        elif kind == "discard_result":
            self.hole = tuple(CARD_ID[c] for c in msg["hole_cards"])
            self.dead = (CARD_ID[msg["my_discard"]], CARD_ID[msg["opp_discard"]])
        elif kind == "notice" and self.pending is not None:
            applied = msg.get("applied")
            if self.pending["type"] == "discard" and applied in CARD_ID:
                self.pending = {"type": "discard", "card": applied}
            elif applied in ("fold", "check"):
                self.pending = {"type": "action", "action": applied}
        elif kind == "hand_result":
            self.reset({})

def normalize(req, action, amount=None):
    legal = req["legal_actions"]
    if action == "raise" and action in legal and type(amount) is int:
        return {"type": "action", "action": "raise",
                "amount": max(req["min_raise"], min(req["max_raise"], amount))}
    if action == "raise" or action not in legal:
        action = "check" if "check" in legal else "fold"
    return {"type": "action", "action": action}

def main():
    state = State()
    for line in sys.stdin:
        try:
            req = json.loads(line)
        except ValueError:
            continue
        if not isinstance(req, dict):
            continue
        kind = req.get("type")
        if kind == "match_end":
            return
        reply = None
        try:
            if kind == "action_request":
                state.history = req["history"]
                reply = normalize(req, *choose_action(state, req))
            elif kind == "discard_request":
                hole = tuple(CARD_ID[c] for c in req["hole_cards"])
                card = choose_discard(state, req, hole)
                reply = {"type": "discard", "card": CARDS[card if card in hole else min(hole)]}
            else:
                state.observe(req, kind)
        except Exception as exc:
            state.errors += 1
            if state.errors <= 8:
                print(f"fallback {kind}: {type(exc).__name__}: {exc}", file=sys.stderr)
            if kind == "action_request":
                reply = normalize(req, None)
            elif kind == "discard_request":
                reply = {"type": "discard", "card": min(req["hole_cards"], key=CARD_ID.__getitem__)}
        if reply is not None:
            state.pending = reply
            print(json.dumps(reply, separators=(",", ":")), flush=True)

from itertools import combinations
from random import Random
from time import perf_counter

DECK = tuple(range(52))
PAIRS = ((1, 2), (0, 2), (0, 1))
WINDOWS = tuple((31 << (hi - 4), hi) for hi in range(12, 3, -1)) + ((4111, 3),)

def straight(mask):
    for pattern, high in WINDOWS:
        if mask & pattern == pattern:
            return high
    return -1

STRAIGHTS = tuple(straight(mask) for mask in range(8192))

def rank(cards):
    counts = [0] * 13
    suits = [0] * 4
    mask = 0
    for card in cards:
        value, suit = divmod(card, 4)
        counts[value] += 1
        bit = 1 << value
        suits[suit] |= bit
        mask |= bit
    values = [v for v in range(12, -1, -1) if counts[v]]
    flush = next((s for s in suits if s.bit_count() >= 5), 0)
    if flush and STRAIGHTS[flush] >= 0:
        return (8, STRAIGHTS[flush])
    groups = sorted(((counts[v], v) for v in values), reverse=True)
    count, top = groups[0]
    if count == 4:
        return (7, top, next(v for v in values if v != top))
    if count == 3 and groups[1][0] >= 2:
        return (6, top, groups[1][1])
    if flush:
        return (5, *[v for v in values if flush & (1 << v)][:5])
    if STRAIGHTS[mask] >= 0:
        return (4, STRAIGHTS[mask])
    others = [v for v in values if v != top]
    if count == 3:
        return (3, top, *others[:2])
    if count == 2:
        if groups[1][0] == 2:
            second = groups[1][1]
            return (2, top, second, next(v for v in others if v != second))
        return (1, top, *others[:3])
    return (0, *values[:5])

def flop_score(pair, flop, draws=True):
    cards = pair + flop
    made = rank(cards)
    scores = (0.08, .43, .69, .79, .87, .92, .97, .99, 1)
    high, low = sorted((c // 4 for c in pair), reverse=True)
    value = scores[made[0]] + (.005 * high + .002 * low)
    if made[0] == 1:
        value += .012 * (made[1] - 6)
        if made[1] not in (high, low):
            value -= .27
    if made[0] == 2 and len({c // 4 for c in flop}) == 2 and high != low:
        value -= .10
    if draws and made[0] < 4:
        suits = [c % 4 for c in cards]
        if any(suits.count(s) == 4 for s in set(suits)):
            value += .33
        mask = sum(1 << v for v in {c // 4 for c in cards})
        outs = 0
        for window, _ in WINDOWS:
            missing = window & ~mask
            if missing.bit_count() == 1:
                outs |= missing
        value += .104 * min(outs.bit_count(), 3)
    return value

def pick(hole, flop, mode=2):
    if mode == 0:
        return hole.index(min(hole))
    if mode == 1:
        return max(range(3), key=lambda i: rank(tuple(hole[j] for j in PAIRS[i]) + flop))
    return max(range(3), key=lambda i: flop_score(tuple(hole[j] for j in PAIRS[i]), flop))

def compare(a, b):
    return 1.0 if a > b else .5 if a == b else 0.0

def budget(state, req):
    bank = req["time_left_ms"]
    remaining = max(1, state.total - req["hand_id"] + 1)
    return max(0, min(.018, state.reply_ms * .00025, bank * .000001, bank / remaining * .00014))

def simulate(hole, board, dead, samples, deadline, rng, evidence=0., discard_mix=None):
    """Mean equities of each possible retention, with common samples on the flop."""
    unseen = [c for c in DECK if c not in hole + board + dead]
    sums = [0.] * (3 if len(hole) == 3 and board else 1)
    mass = 0.
    missing = 5 - len(board)
    opp_count = 2 if dead else 3
    for n in range(samples):
        if n % 4 == 0 and perf_counter() >= deadline:
            break
        deal = tuple(rng.sample(unseen, missing + opp_count))
        opp = deal[:opp_count]
        full = board + deal[opp_count:]
        flop = full[:3]
        weight = 1.
        if not dead:
            mode = rng.choices((0, 1, 2), discard_mix)[0] if discard_mix else (0, 2, 2, 1)[n % 4]
            i = pick(opp, flop, mode)
            opp = tuple(opp[j] for j in PAIRS[i])
        else:
            triple = opp + (dead[1],)
            predicted = pick(triple, flop)
            weight = 1. if predicted == 2 else .29
        if evidence:
            strength = flop_score(opp, flop)
            weight *= max(.10, 1 + evidence * (strength - .46))
        score = rank(opp + full)
        if len(hole) == 2:
            sums[0] += weight * compare(rank(hole + full), score)
        elif not board:
            i = pick(hole, flop)
            pair = tuple(hole[j] for j in PAIRS[i])
            sums[0] += weight * compare(rank(pair + full), score)
        else:
            for i, (a, b) in enumerate(PAIRS):
                sums[i] += weight * compare(rank((hole[a], hole[b]) + full), score)
        mass += weight
    return tuple(x / mass for x in sums) if mass else None

DISCARD_MODE = "equity"
BETTING = False
ADAPT = False
RNG = Random(739483)

def choose_discard(state, req, hole):
    flop = tuple(CARD_ID[c] for c in req["board"])
    if DISCARD_MODE == "rank":
        return min(hole)
    if DISCARD_MODE == "made":
        return hole[pick(hole, flop, 1)]
    deadline = perf_counter() + budget(state, req)
    values = simulate(hole, flop, (), 128, deadline, RNG, pressure(state, "flop"))
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
    return ("check" if "check" in req["legal_actions"] else "call",)

if __name__ == "__main__":
    main()
