"""Drive the generated bot as an isolated subprocess."""
import json
from pathlib import Path
import shutil
import runpy
import subprocess
import sys
import tempfile

ARTIFACT = sys.argv[1] if len(sys.argv) > 1 else "dist/bot.py"

def run(messages):
    with tempfile.TemporaryDirectory() as folder:
        bot = Path(folder) / "bot.py"
        shutil.copyfile(ARTIFACT, bot)
        completed = subprocess.run(
            [sys.executable, str(bot)], cwd=folder, text=True,
            input="\n".join(map(json.dumps, messages)) + "\n",
            capture_output=True, timeout=5, check=True,
        )
        assert not completed.stderr, completed.stderr
        return [json.loads(line) for line in completed.stdout.splitlines()]

def main():
    cards = ["7d", "7s", "Ac"]
    init = dict(type="init", total_hands=400, time_bank_ms=60000, per_response_ms=5000)
    hand = dict(type="new_hand", hand_id=1, seat="big_blind", hole_cards=cards)
    base = dict(type="action_request", hand_id=1, street="preflop", board=[],
                pot=4, my_bet=2, opp_bet=2, to_call=0, my_stack=198, opp_stack=198,
                raises_left=3, history=[], time_left_ms=50000, extra=True)
    check = dict(base, legal_actions=["check"])
    cap = dict(base, legal_actions=["fold", "call"], to_call=20, opp_bet=22, raises_left=0)
    short = dict(base, legal_actions=["check", "raise"], min_raise=3, max_raise=3)
    discard = dict(type="discard_request", hand_id=1, board=["5c", "9c", "Kh"],
                   hole_cards=cards, my_stack=0, opp_stack=0, pot=400, time_left_ms=100)
    result = dict(type="discard_result", my_discard="7s", opp_discard="Ts", hole_cards=["7d", "Ac"])
    messages = [init, hand, {"type": "future_message"}, check, cap, short, discard,
                dict(type="notice", code="illegal_discard", applied="7s"), result,
                dict(type="hand_result", result="showdown", net=0, history=[]),
                dict(type="match_end"), check]
    replies = run(messages)
    assert len(replies) == 4, replies
    for reply, request in zip(replies, [check, cap, short]):
        assert reply["type"] == "action" and reply["action"] in request["legal_actions"]
        if reply["action"] == "raise":
            assert type(reply["amount"]) is int and reply["amount"] == 3
    assert replies[-1]["type"] == "discard" and replies[-1]["card"] in cards
    assert run([init, hand, check]) == [replies[0]]
    fold = dict(cap, to_call=198, opp_bet=200, my_bet=2, pot=202,
                opp_stack=0, time_left_ms=41000)
    weak = dict(hand, hole_cards=["2s", "3h", "7c"])
    ended = dict(type="hand_result", hand_id=1, result="fold", net=-2, history=[])
    limp = dict(short, history=[dict(street="preflop", actor="opp", action="call", amount=2)])
    assert run([init, weak, fold, ended, dict(hand, hand_id=2), limp])[0]["action"] == "fold"
    bot = runpy.run_path(ARTIFACT)
    normalize = bot["normalize"]
    assert normalize(short, "raise", True)["action"] == "check"
    assert normalize(short, "raise", 99)["amount"] == 3
    assert normalize(cap, "raise", 99)["action"] == "fold"
    state = bot["State"]()
    state.observe(hand, "new_hand")
    state.pending = {"type": "discard", "card": "7d"}
    state.observe(dict(type="notice", code="illegal_discard", applied="7s"), "notice")
    assert state.pending["card"] == "7s"
    state.observe(result, "discard_result")
    assert state.hole == tuple(bot["CARD_ID"][c] for c in ("7d", "Ac"))
    assert state.dead == tuple(bot["CARD_ID"][c] for c in ("7s", "Ts"))
    state.observe(ended, "hand_result")
    assert not (state.hole or state.dead or state.history or state.pending)
    print("protocol subprocess fixtures passed")

if __name__ == "__main__":
    main()
