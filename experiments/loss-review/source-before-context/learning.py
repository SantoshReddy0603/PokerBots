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
        for event in history:
            if event["street"] != street:
                street, totals, last = event["street"], [0, 0], None
            who = event["actor"] == "opp"
            action = event["action"]
            faced = totals[1 - who] > totals[who]
            old_total = totals[who]
            addition = max(0, event.get("amount", old_total) - old_total)
            if who:
                group = "preflop" if street == "preflop" else "postflop"
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
                    self.add(("preflop", "open"), action == "raise")
                if last and last["actor"] == "me" and last["action"] == "raise":
                    self.add((group, "fold"), action == "fold")
                    self.add((group, "fold_small" if last_ratio < .6 else "fold_large"), action == "fold")
            if action == "raise":
                opened = True
                last_ratio = addition / max(1, pot)
            if action in ("call", "raise"):
                totals[who] = event.get("amount", totals[1 - who])
                pot += totals[who] - old_total
            last = event
