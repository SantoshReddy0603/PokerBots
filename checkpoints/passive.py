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

def choose_action(state, req):
    return ("check" if "check" in req["legal_actions"] else "call",)

def choose_discard(state, req, hole):
    return min(hole)

if __name__ == "__main__":
    main()
