import itertools
import runpy
import sys

scope = runpy.run_path(sys.argv[1])
g = scope["betting_action"].__globals__
terminal = scope["terminal_call"]
assert terminal(.25, 100, 10)
assert not terminal(.05, 100, 10)
assert terminal(.5, 200, 200)
assert not terminal(.49, 200, 200)
assert terminal(.34, 200, 100)
assert not terminal(.24, 200, 100)
assert not terminal(0, 200, 1)
assert all(not terminal(.12, 100, c) or terminal(.12, 200, c) for c in range(1, 201))

encode = lambda cards: tuple(scope["CARD_ID"][c] for c in cards.split())
key = scope["preflop_key"]
table = scope["PREFLOP_EQUITY"]
assert set(map(key, itertools.combinations(range(52), 3))) == table.keys()
for cards in ("2s 2h 2d", "As Ah Kd", "As Kh Qd", "As Ks 5s", "Ks Kh 2s"):
    hole = encode(cards)
    assert all(key(tuple(4 * (c // 4) + suits[c % 4] for c in hole)) == key(hole)
               for suits in itertools.permutations(range(4)))
    ref = scope["simulate"](hole, (), (), 4000, float("inf"), scope["Random"](981))[0]
    assert abs(table[key(hole)][0] / 1000 - ref) < .09, (cards, ref, table[key(hole)])
    print(cards, "uniform independent", round(ref, 4), "table", table[key(hole)])
state = scope["State"]()
state.hole = encode("2s 2h 2d")
state.seat = "big_blind"
request = dict(street="preflop", pot=202, to_call=198, my_stack=198, opp_stack=0,
               legal_actions=["fold", "call"], opp_bet=200)
assert scope["betting_action"](state, request) == ("fold",)
state.hole = encode("As Ah Kd")
assert scope["betting_action"](state, request) == ("call",)
state.hole = encode("As Kd")
state.dead = encode("6s 7s")
g["simulate"] = lambda *args: (.25,)
if "modeled_equity" in g:
    g["modeled_equity"] = lambda *args: (.25,)
if "estimate" in g:
    g["estimate"] = lambda *args: (.25,)
request.update(street="river", board="2c 3h 9d Jc Qd".split(), pot=100, to_call=10,
               opp_stack=100, time_left_ms=20000, hand_id=1)
assert scope["betting_action"](state, request) == ("call",)
request.update(street="turn", board=request["board"][:4], opp_stack=0)
assert scope["betting_action"](state, request) == ("call",)

if "protected_lead" in scope:
    lock = scope["protected_lead"]
    assert lock(410, 400, 396, 395, 400)
    assert not lock(409, 400, 396, 395, 400)
    assert not lock(1000, 400, 396, 394, 400)
    assert not lock(1000, 400, 396, 395, None)
    state.observe(dict(protocol_version="1.0", small_blind=1, big_blind=2,
                       total_hands=400, per_response_ms=5000), "init")
    for hand, net in enumerate([50, -17, 0, 20], 1):
        state.observe(dict(hand_id=hand), "new_hand")
        state.observe(dict(hand_id=hand, net=net), "hand_result")
        state.observe(dict(hand_id=hand, net=net), "hand_result")
    assert (state.match_net, state.scored_hands) == (53, 4)
print("review decision fixtures passed")
