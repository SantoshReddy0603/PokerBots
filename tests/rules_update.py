"""Updated leg lifecycle, score scope, legal actions and fixed-draw equivalence."""
import argparse
import contextlib
import copy
import io
import json
from pathlib import Path
import runpy
import sys

sys.path.insert(0, str(Path("tools").resolve()))
sys.path.insert(0, str(Path("tests").resolve()))
from benchmark_legs import engine
from matrix import validate
from protocol import run

candidate = sys.argv[1] if len(sys.argv) > 1 else "checkpoints/rules-1110.py"
new = runpy.run_path(candidate)
old = runpy.run_path("checkpoints/pre-rules-1110.py")
for hands, bank in ((200, 30000), (500, 75000), (400, 30000)):
    init = dict(type="init", protocol_version="1.0", total_hands=hands,
                starting_stack=200, small_blind=1, big_blind=2,
                time_bank_ms=bank, per_response_ms=5000)
    state = new["State"]()
    state.observe(init, "init")
    assert state.score_scope == "leg" and state.cap is None
    state.match_net, state.scored_hands = 10000, hands - 1
    hand = dict(type="new_hand", hand_id=hands, seat="button", hole_cards=["As", "Ah", "Kd"])
    state.observe(hand, "new_hand")
    assert not state.locked
    state.model.observe([dict(street="preflop", actor="opp", action="raise", amount=6)], "button")
    assert state.model.cells
    state.observe(init, "init")
    assert state.model.cells == {} and state.match_net == state.scored_hands == 0
    assert not state.hole and not state.dead and not state.history and state.pending is None
    state.observe(hand, "new_hand")
    request = dict(type="action_request", hand_id=hands, street="preflop", board=[],
                   pot=3, my_bet=1, opp_bet=2, to_call=1, my_stack=199, opp_stack=198,
                   legal_actions=["fold", "call", "raise"], min_raise=4, max_raise=200,
                   raises_left=3, history=[], time_left_ms=bank)
    assert new["choose_action"](state, request)[0] == "raise"
    # Fresh process per invocation; no output after match_end. Legal_actions
    # remains authoritative even when raises_left is positive versus an all-in.
    messages = [init, hand, request, dict(type="match_end"), request]
    import protocol
    protocol.ARTIFACT = candidate
    assert len(run(messages)) == 1
    blocked = dict(request, pot=202, to_call=199, opp_bet=200, opp_stack=0,
                   legal_actions=["fold", "call"])
    assert run([init, hand, blocked])[0]["action"] in ("fold", "call")

# Identical current-format decisions before/after the lifecycle hardening.
# These inputs test public states only and never enter the submitted policy.
rng = new["Random"](111010)
for i in range(60):
    cards = tuple(rng.sample(range(52), 10))
    length = (0, 3, 4, 5)[i % 4]
    hole = cards[:3] if length < 4 else cards[:2]
    board = cards[3:3 + length]
    request = dict(street="preflop" if not length else {3:"flop",4:"turn",5:"river"}[length],
                   board=[new["CARDS"][c] for c in board], hand_id=20, pot=40,
                   my_bet=0, opp_bet=10, to_call=10, my_stack=180, opp_stack=170,
                   legal_actions=["fold", "call", "raise"], min_raise=20,
                   max_raise=180, raises_left=3, history=[], time_left_ms=25000)
    actions = []
    for scope in (old, new):
        state = scope["State"]()
        state.observe(dict(total_hands=200, per_response_ms=5000), "init")
        state.hole, state.dead, state.seat = hole, (() if length < 4 else cards[8:10]), "button"
        g = scope["choose_action"].__globals__
        g["VECTOR_RNG"] = scope["np"].random.default_rng(i)
        g["ACTION_RNG"].seed(i)
        actions.append(scope["choose_action"](state, request))
    assert actions[0] == actions[1], (i, actions)

# Drive the actual organizer control flow with independent, disposable bot
# objects. This verifies deal/seat swaps offline, never inside the playing bot.
instances = []
class FakeBot:
    fail_leg = None
    def __init__(self, name, path, python, log_dir, bank, per_reply, log_name):
        self.name, self.label = name, path
        self.time_used_s = self.notices = 0
        self.messages = []
        self.closed = False
        instances.append(self)
    def send(self, message):
        self.messages.append(copy.deepcopy(message))
    def begin(self, message):
        self.send(message)
    def wait_reply(self, deadline):
        if self.name == "A" and instances.index(self) // 2 + 1 == self.fail_leg:
            return None, "fixture forfeit"
        req = self.messages[-1]
        if req["type"] == "discard_request":
            reply = dict(type="discard", card=req["hole_cards"][0])
        else:
            reply = dict(type="action", action="check" if "check" in req["legal_actions"] else "call")
        return json.dumps(reply), None
    def close(self):
        self.closed = True

original = engine.Bot
engine.Bot = FakeBot
try:
    args = argparse.Namespace(bot_a=candidate, bot_b=candidate, python=sys.executable, hands=4,
                              stage=1, seed="lifecycle-fixture", verbose=False, log_dir="", no_time_limits=False)
    with contextlib.redirect_stdout(io.StringIO()):
        game = engine.Match(args)
        game.run()
    assert len(instances) == 4 and all(b.closed for b in instances)
    for bot in instances:
        assert bot.messages[0]["total_hands"] == 2 and bot.messages[0]["time_bank_ms"] == 30000
        assert bot.messages[-1] == dict(type="match_end", reason="complete")
        assert [m["hand_id"] for m in bot.messages if m["type"] == "new_hand"] == [1, 2]
    for index in range(2):
        first = [m for m in instances[index].messages if m["type"] == "new_hand"]
        second = [m for m in instances[3-index].messages if m["type"] == "new_hand"]
        assert [(m["seat"],m["hole_cards"]) for m in first] == [(m["seat"],m["hole_cards"]) for m in second]
    class CaptureMatch(engine.Match):
        def summary(self, totals, played, forfeits, where):
            self.captured = played, forfeits, where
    for leg in (1, 2):
        instances.clear()
        FakeBot.fail_leg = leg
        game = CaptureMatch(args)
        game.run()
        played, failed, where = game.captured
        assert len(instances) == 2 * leg and all(b.closed for b in instances)
        assert failed[0][0].name == "A" and where == (leg, 1)
        assert played == 2 * (leg - 1)
        assert instances[-2].messages[-1]["reason"] == "forfeit"
        assert instances[-1].messages[-1]["reason"] == "opp_forfeit"
finally:
    engine.Bot = original

print("Leg resets, local-score protection disabled, exit/all-in legality, 60 unchanged decisions, and organizer two-leg lifecycle passed")
