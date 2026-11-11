"""Generate fixed, independently configured opponents for local evaluation."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
base = "\n\n".join((root / "src" / (part + ".py")).read_text(encoding="utf-8-sig")
                  for part in ("protocol", "poker"))
strategy = r'''
RNG = Random(STYLE_SEED)

def choose_discard(state, req, hole):
    flop = tuple(CARD_ID[c] for c in req["board"])
    return hole[pick(hole, flop, DISCARD)]

def choose_action(state, req):
    hole = state.hole
    board = tuple(CARD_ID[c] for c in req["board"])
    call, pot = req["to_call"], req["pot"]
    legal = req["legal_actions"]
    if not board:
        ranks = sorted((c // 4 for c in hole), reverse=True)
        strength = .29 + .016 * ranks[0] + .007 * ranks[1] + .003 * ranks[2]
        if len(set(ranks)) < 3:
            strength += .22
        if len(set(ranks)) == 1:
            strength += .14
    elif len(hole) == 3:
        strength = max(flop_score(tuple(hole[j] for j in pair), board) for pair in PAIRS)
    elif STYLE == "equity":
        values = simulate(hole, board, state.dead, 76, perf_counter() + .008, RNG)
        strength = values[0] if values else .45
    else:
        made = rank(hole + board)
        strength = (.21, .52, .73, .84, .92, .95, .98, .99, 1)[made[0]]
        strength += .005 * (made[1] - 6)
        if len(board) == 5 and made == rank(board):
            strength -= .24
        elif len(board) == 4 and any(sum(c % 4 == s for c in hole + board) == 4 for s in range(4)):
            strength += .10
    odds = call / (pot + call)
    roll = RNG.random()
    if STYLE == "shove" and "raise" in legal and (strength >= .65 or roll < .12):
        return ("raise", req["max_raise"])
    fold_cut, raise_cut, bluff, size = PARAMS
    if call and strength < max(fold_cut, odds + .04) and roll > (0.72 if STYLE == "station" else .03):
        return ("fold",)
    if "raise" in legal and (strength >= raise_cut + (.10 if call > 2 else 0) or roll < bluff):
        return ("raise", req["opp_bet"] + round(size * (pot + call)))
    return ("call" if call else "check",)
'''
styles = {
    "tag": (.50, .69, .05, .72),
    "loose": (.30, .84, .02, .57),
    "station": (.21, .91, .004, .65),
    "overfold": (.62, .75, .04, .74),
    "aggro": (.34, .63, .23, 1.39),
    "shove": (.48, .78, .03, .82),
    "equity": (.35, .65, .05, .71),
    "final_tag": (.47, .64, .08, .54),
    "final_aggro": (.39, .71, .19, 1.68),
    "final_station": (.24, .83, .01, .36),
    "final_shove": (.40, .71, .11, 1.04),
    "final_equity": (.37, .69, .12, .84),
}
for i, (name, params) in enumerate(styles.items()):
    style = name.removeprefix("final_")
    config = f"STYLE = {style!r}\nSTYLE_SEED = {735 + i}\nDISCARD = {i % 3}\nPARAMS = {params!r}\n"
    (root / "opponents" / (name + ".py")).write_text(
        base + "\n" + config + strategy + "\nif __name__ == '__main__':\n    main()\n", encoding="utf-8")

