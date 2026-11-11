import json
import sys

CARDS = tuple(r + s for r in "23456789TJQKA" for s in "shdc")
CARD_ID = {card: i for i, card in enumerate(CARDS)}

def protected_lead(net, total, hand, scored, cap, seat=None):
    # At hand start only blinds are committed. Seats alternate in protocol 1.0,
    # so folding out costs 1+2 per pair, plus the current blind for odd counts.
    # Retain the conservative bound if the current seat is unavailable.
    remaining = total - scored
    cost = 2 * remaining
    if seat in ("button", "big_blind"):
        cost = 3 * (remaining // 2) + (remaining % 2) * (1 if seat == "button" else 2)
    return cap is not None and 1 <= hand <= total and scored == hand - 1 and net - cost >= cap

class State:
    def __init__(self):
        self.total = 400
        self.reply_ms = 5000
        self.errors = 0
        self.match_net = 0
        self.scored_hands = 0
        self.cap = None
        self.score_scope = "leg"
        self.locked = False
        self.model = Frequencies()
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
            # Only this leg's score is visible. Neither a positive leg score
            # nor the whole-match cap can certify a win across both legs.
            self.locked = False
        elif kind == "init":
            # A new init owns a fresh leg. Never reuse observations or a score
            # from another leg, even when driven by an in-process test harness.
            self.__init__()
            self.total = msg["total_hands"]
            self.reply_ms = msg["per_response_ms"]
            # Do not infer a full match from total_hands. It is a leg length,
            # including when a local runner uses a nonstandard --hands value.
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
            if msg.get("hand_id") == self.hand == self.scored_hands + 1:
                self.model.observe(msg.get("history", []), self.seat)
                self.match_net += msg["net"]
                self.scored_hands += 1
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
                reply = normalize(req, None) if state.locked else normalize(req, *choose_action(state, req))
            elif kind == "discard_request":
                hole = tuple(CARD_ID[c] for c in req["hole_cards"])
                card = min(hole) if state.locked else choose_discard(state, req, hole)
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


