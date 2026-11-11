"""Check the selected artifact against official two-leg init and request fields."""
from pathlib import Path
import runpy
import sys

sys.path.insert(0, str(Path("tests").resolve()))
import protocol

artifact = sys.argv[1] if len(sys.argv) > 1 else "dist/bot.py"
protocol.ARTIFACT = artifact
scope = runpy.run_path(artifact)
for total, bank in ((200, 30000), (500, 75000)):
    init = dict(type="init", protocol_version="1.0", total_hands=total,
                starting_stack=200, small_blind=1, big_blind=2,
                time_bank_ms=bank, per_response_ms=5000)
    hand = dict(type="new_hand", hand_id=1, seat="button", hole_cards=["As", "Ah", "Kd"])
    req = dict(type="action_request", hand_id=1, street="preflop", board=[], pot=3,
               my_bet=1, opp_bet=2, to_call=1, my_stack=199, opp_stack=198,
               legal_actions=["fold", "call", "raise"], min_raise=4, max_raise=200,
               raises_left=3, history=[], time_left_ms=bank)
    first = protocol.run([init, hand, req, dict(type="match_end"), req])
    assert len(first) == 1 and first[0]["action"] == "raise"
    # Each fresh process must begin from the same public state, without any
    # match/leg identity or private duplicate information supplied to the bot.
    assert first == protocol.run([init, hand, req, dict(type="match_end")])
    state = scope["State"]()
    state.observe(init, "init")
    assert state.total == total and state.cap is None
    state.match_net, state.scored_hands = 10000, total - 1
    state.observe(dict(hand, hand_id=total), "new_hand")
    assert not state.locked
    assert scope["choose_action"](state, dict(req, hand_id=total))[0] == "raise"
    all_in = dict(req, pot=202, to_call=199, opp_bet=200, opp_stack=0,
                  legal_actions=["fold", "call"])
    assert protocol.run([init, hand, all_in])[0]["action"] in all_in["legal_actions"]
    discard = dict(type="discard_request", hand_id=1, hole_cards=hand["hole_cards"],
                   board=["2s", "3c", "4d"], pot=400, my_stack=0, opp_stack=0, time_left_ms=100)
    reply = protocol.run([init, hand, discard])[0]
    assert reply["type"] == "discard" and reply["card"] in hand["hole_cards"]
print("Selected release: both official leg lengths, fresh processes, no local lead lock, legal all-in actions/discards, and exit passed")
