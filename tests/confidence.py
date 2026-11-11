"""Avoid uncertain marginal stack-offs without rejecting cheap or strong calls."""
import runpy
import sys

b = runpy.run_path(sys.argv[1])
np = b["np"]
state = b["State"]()
state.seat = "button"
outcomes = np.asarray([1.] * 52 + [0.] * 48)
state.posterior = np.ones(100), outcomes, np.zeros(100)
req = dict(street="flop", pot=202, to_call=198, my_bet=2, opp_bet=200,
           my_stack=198, opp_stack=0, legal_actions=["fold", "call"])
assert b["posterior_action"](state, req, .52) == ("fold",)
assert b["posterior_action"](state, dict(req, pot=100, to_call=1), .52) == ("call",)
assert b["posterior_action"](state, dict(req, street="river"), .52) == ("call",)
state.posterior = np.ones(10000), np.tile(outcomes, 100), np.zeros(10000)
assert b["posterior_action"](state, req, .52) == ("call",)
state.posterior = np.ones(100), np.asarray([1.] * 80 + [0.] * 20), np.zeros(100)
assert b["posterior_action"](state, req, .80) == ("call",)
print("Marginal, cheap, strong, exact-river and increasing-sample call checks passed")
