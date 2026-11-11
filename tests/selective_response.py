"""Range isolation and response-tree accounting against independent fixtures."""
from pathlib import Path
import math
import runpy

root = Path('experiments/loss-improvement-1110')
old = runpy.run_path(str(root/'baseline.py'))
new = runpy.run_path(str(root/'selective.py'))
risk = runpy.run_path(str(root/'response.py'))
np = old['np']
hole, board = (48,45,38), (0,17,30)
def output(bot,events,model):
    bot['vector_estimate'].__globals__['VECTOR_RNG'] = np.random.default_rng(1101026)
    return bot['vector_estimate'](hole,board,(),events,model,512,True)
for events in ([],[(0,'raise',1.,.33,.02,True)],[(3,'raise',.7,0.,.1,True)],[(3,'call',.4,.4,.1,True)]):
    a,b = [output(bot,events,bot['Frequencies']()) for bot in (old,new)]
    assert a[0]==b[0] and np.array_equal(a[1],b[1])
    assert all(np.array_equal(x,y) for x,y in zip(a[2],b[2]))
events = [(3,'raise',.7,.4,.1,True)]
a,b = [output(bot,events,bot['Frequencies']()) for bot in (old,new)]
assert not np.array_equal(a[1],b[1])
assert np.dot(b[1],b[3])/b[1].sum() > np.dot(a[1],a[3])/a[1].sum()
for bot in (old,new):
    model = bot['Frequencies']()
    model.cells[('postflop','reraise')] = (1000,1000)
    result = output(bot,events,model)
    if bot is old:
        reference = result
    else:
        assert reference[0]==result[0] and np.array_equal(reference[1],result[1])

state = risk['State']()
req = dict(pot=40,my_bet=4,opp_bet=10,max_raise=100)
weights = np.array([1.,2.,3.])
continuing = np.array([.2,1.,2.8])
position = np.array([.1,.4,.9])
cost,reply = 26,20
fold = 1-continuing.sum()/weights.sum()
# With no winning runout, raising then folding/calling can only lose the
# initial contribution. It must never charge that contribution twice.
ev = risk['response_tree_ev'](state,req,weights,np.zeros(3),position,continuing,cost,reply,1.)
assert abs(ev-(fold*40-(1-fold)*cost))<1e-12
# With guaranteed wins every response branch returns pot plus opponent chips.
raise_mass = sum(float(c)*(.03+.97/(1+math.exp(-14*(float(p)-(1-.18)))))
                 for c,p in zip(continuing,position))/weights.sum()
call_mass = 1-fold-raise_mass
ev = risk['response_tree_ev'](state,req,weights,np.ones(3),position,continuing,cost,reply,1.)
assert abs(ev-(fold*40+call_mass*(40+reply)+raise_mass*(40+90)))<1e-10

for street,raises_left in (('river',3),('turn',1),('flop',0)):
    req = dict(street=street,raises_left=raises_left,pot=40,to_call=6,my_bet=4,opp_bet=10,
               min_raise=16,max_raise=100,my_stack=96,opp_stack=90,
               legal_actions=['fold','call','raise'])
    results = []
    for bot in (old,risk):
        state = bot['State']()
        state.seat = 'button'
        state.posterior = (weights,np.array([1.,.5,0.]),position)
        results.append(bot['posterior_action'](state,req,.4))
    assert results[0]==results[1]
print('Range isolation, selective/loose action distinction, response mass/EV accounting and river/final-raise controls passed')
