class Frequencies:
    """Match-local public-action counts; no retained cards or cross-match state."""
    def __init__(self):
        self.cells = {}

    def add(self, key, yes):
        wins, count = self.cells.get(key, (0, 0))
        self.cells[key] = (wins + bool(yes), count + 1)

    def rate(self, key, prior, mass=16):
        wins, count = self.cells.get(key, (0, 0))
        return (wins + mass * prior) / (count + mass)

    def observe(self, history, seat):
        totals = [1, 2] if seat == "button" else [2, 1]
        street, last = "preflop", None
        opened = False
        pot = 3
        last_ratio = 0.
        last_bucket = "fold_small"
        for event in history:
            if event["street"] != street:
                street, totals, last = event["street"], [0, 0], None
            who = event["actor"] == "opp"
            action = event["action"]
            owed = max(0, totals[1 - who] - totals[who])
            faced = owed > 0
            old_total = totals[who]
            addition = max(0, event.get("amount", old_total) - old_total)
            if who:
                group = "preflop" if street == "preflop" else "postflop"
                if street == "preflop":
                    context = ("reraise" if totals[1 - who] > 2 else
                               ("open" if seat == "big_blind" else "isolate"))
                    self.add(("preflop", "shove_" + context), action == "raise" and event.get("amount", 0) == 200)
                self.add((group, "raise"), action == "raise")
                if group == "postflop":
                    self.add((group, "large"), action == "raise" and addition > 1.5 * pot)
                    if faced:
                        self.add((group, "reraise"), action == "raise")
                elif faced and totals[1 - who] > 2:
                    self.add((group, "reraise"), action == "raise")
                if not faced:
                    self.add((group, "bet"), action == "raise")
                if street == "preflop" and not opened:
                    # Opponent button opens and BB isolations have different opportunities.
                    key = "open" if not FIX_OPENINGS or seat == "big_blind" else "isolate"
                    self.add(("preflop", key), action == "raise")
                if last and last["actor"] == "me" and last["action"] == "raise":
                    self.add((group, "fold"), action == "fold")
                    self.add((group, last_bucket), action == "fold")
            if action == "raise":
                opened = True
                last_ratio = (raise_size_features(pot, owed, addition)[0]
                              if FIX_BET_SIZES else addition / max(1, pot))
                last_bucket = (raise_size_features(pot, owed, addition)[1] if FIX_BET_SIZES else
                               ("fold_small" if last_ratio < .6 else "fold_large"))
            if action in ("call", "raise"):
                totals[who] = event.get("amount", totals[1 - who])
                pot += totals[who] - old_total
            last = event
