"""Opening opportunities and minimum-size reraises use public context."""
import runpy
import sys

b = runpy.run_path(sys.argv[1])
m = b["Frequencies"]()
m.observe([dict(street="preflop", actor="me", action="call", amount=2),
           dict(street="preflop", actor="opp", action="check")], "button")
assert m.cells[("preflop", "isolate")] == (0, 1)
assert ("preflop", "open") not in m.cells
m.observe([dict(street="preflop", actor="opp", action="raise", amount=5)], "big_blind")
assert m.cells[("preflop", "open")] == (1, 1)

history = [dict(street="preflop", actor="me", action="raise", amount=4),
           dict(street="preflop", actor="opp", action="raise", amount=6)]
event = b["range_events"](history, "button")[0]
assert event.reraise and abs(event[3] - 1 / 3) < 1e-12
assert len(event) == 6
seen = []
class Spy(b["Frequencies"]):
    def rate(self, key, prior, mass=16):
        seen.append(key)
        return super().rate(key, prior, mass)
b["vector_estimate"]((48, 45, 38), (0, 5, 10), (), [event], Spy(), 64)
assert ("preflop", "reraise") in seen and ("preflop", "open") not in seen
print("Separate open/isolate opportunities and minimum-reraise dispatch passed")
