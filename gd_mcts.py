import copy
import time
from random import choice, shuffle
from math import log, sqrt

class Unit(object):

    def __init__(self, name_s, **kwargs):

	self.name = name_s
	self.cost = int(kwargs.get('cost', 1))
	self.value = int(kwargs.get('value', 1))
	self.speedup = int(kwargs.get('speedup', 2))
	self.maxbuild = int(kwargs.get('maxbuild', 5))


class Server(object):

    def __init__(self, unit_s, **kwargs):

	self.resource = int(kwargs.get('resource', 0))
	self.addup = int(kwargs.get('addup', 0))
	self.units = unit_s	# units is a dict: {unit_ref: unit_count}
	self.ucount = len(self.units.items())
    
    def update(self):

	self.resource += self.addup + sum(
	    self.units[unit] * unit.speedup for unit in self.units)
	# self.describe()
    
    def legal(self, order):	# order has the same structure and keys as units
	
	if not order:
	    return 1
	legal_maxbuild = all(order[unit] <= unit.maxbuild for unit in order)
	legal_resource = (
	    self.resource > sum(order[unit] * unit.cost for unit in order))
	return legal_resource and legal_maxbuild

    def add_units(self, order):

	if self.legal(order):
	    if order:
		for unit in order:
		    self.resource -= unit.cost * order[unit]
		    self.units[unit] += order[unit]
		    self.update()

    def describe(self):
	
	for unit in self.units:
	    print(unit.name + ': ' + str(self.units[unit]))
	print('Resource Status: ' + str(self.resource))
    
    def deployable(self, unit):

	return min(self.resource / unit.cost, unit.maxbuild)
  
    def random_deploy(self, unit):
	
	if self.deployable(unit):
	    deploy = choice(range(0, self.deployable(unit)))
	else:
	    deploy = 0
	return deploy
    
    def random_play(self):
	
	temp_order = {}
	for unit in self.units:
	    temp_order[unit] = self.random_deploy(unit)
	    
	while not self.legal(temp_order):
	    for unit in self.units:
		temp_order[unit] = self.random_deploy(unit)
	self.add_units(temp_order)

class MCTS(object):

    def __init__(self, server, op_server, max_actions = 100):
	
	self.confident = 1.414
	self.actions = 0
	self.max_actions = max_actions

	self.server = server
	self.op = op_server
	self.uclass = self.server.units.keys()
	self.forest_visit = {}
	self.forest_win = {}
	self.max_depth = 0
	self.t1_order = {}
	self.exhaust = {}   # {unit: {iteration: exhaust_u}}
	self.path = []	# [(unit, iteration, order_count)]
	self.backup_unit = {}
	self.backup_resource = self.server.resource

	# Initial the subtrees and the root
	# Inside the MCTS AI, 
	# the tree represents available orders to give to the server
	for unit in self.uclass:
	    # init forest, inner dict structure: 
	    # {iteration: {order_count: visit_times}}
	    self.forest_visit[unit] = {}
	    self.forest_win[unit] = {}
	    self.exhaust[unit] = {}
	    # assign root value, inner dict structure: 
	    # {iteration: {order_count: visit_times}}
	    self.forest_visit[unit][0] ={0: 1}
	    self.forest_win[unit][0] = {0: 0}
	    self.exhaust[unit][0] = 1
	for unit in self.uclass:
	    self.path.append((unit, 0, 0))
	    pass
	for unit in self.uclass:
	    self.backup_unit[unit] = self.server.units[unit]
	    
    def selection(self, iteration, sel_server, available_visit, available_win): 
    #	iteration is an integer
    #	add visit filter for available_visit & available_win? 
	
	order_uct = []		# [({unit: order_count}, uct_value)]	
	
	try:
	    for unit in self.forest_visit:
		available_visit[unit] = self.forest_visit[unit][iteration + 1]	
	    for unit in self.forest_win:
		available_win[unit] = self.forest_win[unit][iteration + 1]
	except KeyError:
	    print(iteration)
	
	if iteration == 0:
	    sel_server.resource = self.backup_resource
	    for unit in self.uclass:
		sel_server.units[unit] = self.backup_unit[unit]
	
	# UCT value maximization
	avail = recursive_combine(
	    available_visit, self.server.units.keys(), [{}])
		   
	for order in avail:
	    
	    uct = 0
	    win_t = 0
	    visit_t = 0
	    
	    for unit in self.uclass:  # Let each unit pop a deploy count.
		visit = available_visit[unit][order[unit]]
		visit_t += visit
		win = available_win[unit][order[unit]]
		win_t += win
		t = sum(available_visit[unit].values())
		uct += self.confident * sqrt(log(t) / visit)
	    uct += win_t / visit_t
	    order_uct.append((order, uct))

	if order_uct:
	    uct_max, order_fin = max( (o[1], o[0] ) for o in order_uct)
	else:
	    order_fin = {}
	
	while not sel_server.legal(order_fin):
	    order_uct.remove((order_fin, uct_max))
	    if order_uct == []:
		order_fin = {}
		break
	    else:
		uct_max, order_fin = max( (o[1], o[0]) for o in order_uct)
	
	for unit in order_fin:
	    self.path.append((unit, iteration + 1, order_fin[unit]))
	
	if iteration == 0:
	    self.t1_order = order_fin
		
	if iteration + 1 < self.max_depth and order_fin:
	    sel_server.add_units(order_fin)
	    return self.selection(
	        iteration + 1, sel_server, available_visit, available_win)
	else:
	    self.expansion(sel_server)
	    if self.actions < self.max_actions:
		return self.selection(
		    0, sel_server, available_visit, available_win)
	    else:
		return self.t1_order

    def expansion(self, exp_server):
	
	try:
	    if all(self.exhaust[unit][self.max_depth] for unit in exp_server.units):	
		self.max_depth += 1
		for unit in self.forest_visit:
		    self.exhaust[unit][self.max_depth] = 0
		    self.forest_visit[unit][self.max_depth] = (
			{exp_server.deployable(unit): 1})
		    self.forest_win[unit][self.max_depth] = (
			{exp_server.deployable(unit): 0})		
		    self.simulation(self.max_depth, exp_server)
	    else:
		for unit in self.forest_visit:
		    if self.exhaust[unit][self.max_depth] == 0:
			cursor = exp_server.deployable(unit)
			while cursor in self.forest_visit[unit][self.max_depth]:
			    cursor -= 1
			if cursor > 0:
			    self.forest_visit[unit][self.max_depth].update({cursor: 1})
			    self.forest_win[unit][self.max_depth].update({cursor: 0})
			    self.simulation(self.max_depth, exp_server)
			if cursor <= 0:
			    self.exhaust[unit][self.max_depth] = 1
		    else:
			pass
	    
	    self.actions += 1
	except KeyError:
	    print(str(self.max_depth) + 'level reached')

    def simulation(self, iteration, sim_server):
	
	max_sim = iteration
	if max_sim == 0:
	    return 1
	
	op = copy.deepcopy(self.op)
	unit_ref_copy(sim_server, op)
	for it in range(1, max_sim):
	    op.random_play()
		
	result = sum(unit.value * sim_server.units[unit] for unit in sim_server.units) > (
	    sum(unit.value * op.units[unit] for unit in op.units))
	self.backpropagation(result)

    def backpropagation(self, result):    
	  
	for brac in self.path:	# brac: (unit, iteration, order_count)
	    self.forest_visit[brac[0]][brac[1]][brac[2]] += 1
	    self.forest_win[brac[0]][brac[1]][brac[2]] += result
	 
	self.path = []
	for unit in self.uclass:
	    self.path.append((unit, 0, 0))
  
    def get_action(self):
	
	server_copy = copy.deepcopy(self.server)
	
	visit = {}	# {unit: {order_count: visit_times}}
	win = {}	# {unit: {order_count: win_times}}
	
	unit_ref_copy(self.server, server_copy)
	self.expansion(server_copy)
	return self.selection(0, server_copy, visit, win)

def recursive_combine(visit, units, container):    
# units: list of Unit objects
# container: list of possible orders
    
    if units:
	merge = []
	unit = units.pop()
	dict_list = []
	for count in visit[unit]:
	    dict_list.append({unit: count})
	# merge = []
	for item in dict_list:
	    for content in container:
		temp = {}
		for key in content:
		    temp[key] = content[key]
		temp.update(item)
		merge.append(temp)
		pass
	container = merge
	return recursive_combine(visit, units, container)
    else:
	return container
	    

def unit_ref_copy(ref_server, copy_server):
	
    name_dict = {}
    for runit in ref_server.units:
	name_dict[runit.name] = runit
    for cunit in copy_server.units:
	copy_server.units.update(
	    {name_dict[cunit.name]: copy_server.units.pop(cunit)})

def run():
    
    farmer = Unit('farmer', cost = 6, value = 3, speedup = 3, maxbuild = 10)
    soldier = Unit('soldier', cost = 10, value = 10, speedup = 0, maxbuild = 20)
    hero = Unit('hero', cost = 100, value = 150, speedup = 0, maxbuild = 1)
    init_unit = {farmer: 0, soldier: 0, hero: 0}

    server = Server(init_unit, resource=30, addup=10)
    opponent = copy.deepcopy(server)
    unit_ref_copy(server, opponent)

    max_round = 10
    for r in range(0, max_round):
	AI = MCTS(server, opponent)
	act = AI.get_action()
	if server.legal(act):
	    server.add_units(act)
	    server.describe()

if __name__ == '__main__':
    run()