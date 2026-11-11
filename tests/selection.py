"""Explicit ranking and discard cases that are rare in randomized checks."""
import runpy
import sys

bot = runpy.run_path(sys.argv[1] if len(sys.argv) > 1 else "dist/bot.py")
cards = bot["CARD_ID"]
rank = bot["rank"]
pick = bot["pick"]
encode = lambda text: tuple(cards[c] for c in text.split())

assert rank(encode("As 2d 3h 4c 5s Kd Qd")) == (4, 3)
assert rank(encode("As Ah Ad Ks Kh Kd Qs")) == (6, 12, 11)
assert rank(encode("As Ah Ad Ac Ks Kh Kd")) == (7, 12, 11)
assert rank(encode("As Ks Qs Js Ts 2c 3d")) == (8, 12)
assert rank(encode("As Ah Kd Qc 8s 5d 2h")) > rank(encode("Ad Ah Kd Jc 8s 5d 2h"))
for hole_text, flop_text, discard in [
    ("9s 9h Kc", "9d 7d 2s", "Kc"),
    ("7s 8s Ac", "9s Ts 2d", "Ac"),
    ("4s 5d Kc", "6d 7h 2d", "Kc"),
    ("As Qh 3c", "Ah 7d 2s", "3c"),
]:
    hole, flop = encode(hole_text), encode(flop_text)
    values = bot["simulate"](hole, flop, (), 512, float("inf"), bot["Random"](739483))
    assert hole[max(range(3), key=values.__getitem__)] == cards[discard], (hole_text, values)
print("targeted rank and discard cases passed")
