"""Message loop.

State follows the match score, the opponent frequency model and the protected-lead
lock; MatchState follows the same messages for the range model and the clock.
Preflop uses the equity table. With NumPy the discard and the later streets use
the range model; without it the list-based estimate plays every decision.
"""


def range_feed(req, kind):
    method = {"action_request": STATE.observe, "discard_request": STATE.observe,
              "init": STATE.configure, "new_hand": STATE.new_hand,
              "discard_result": STATE.discard_result, "hand_result": STATE.hand_result}.get(kind)
    if method is not None:
        try:
            method(req)
        except Exception as exc:
            range_log("state error", repr(exc))


def range_reply(req):
    try:
        return legalize(range_action(req), req)
    except Exception as exc:
        range_log("action error", repr(exc))
        return legalize(fallback_action(req), req)


def range_discard_card(req):
    cards = [c for c in req["hole_cards"] if isinstance(c, str)]
    try:
        card = range_discard(req)
    except Exception as exc:
        range_log("discard error", repr(exc))
        card = None
    if card not in cards:
        card = fallback_discard(req)
    return card if card in cards else None


def main():
    state = State()
    vector = HAVE_NP
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
        if vector:
            range_feed(req, kind)
        reply = None
        try:
            if kind == "action_request":
                state.history = req["history"]
                if state.locked:
                    reply = normalize(req, None)
                elif vector and req.get("street") != "preflop":
                    reply = range_reply(req)
                else:
                    reply = normalize(req, *choose_action(state, req))
            elif kind == "discard_request":
                hole = tuple(CARD_ID[c] for c in req["hole_cards"])
                card = range_discard_card(req) if vector else None
                if card is None:
                    pick = min(hole) if state.locked else choose_discard(state, req, hole)
                    card = CARDS[pick if pick in hole else min(hole)]
                reply = {"type": "discard", "card": card}
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
