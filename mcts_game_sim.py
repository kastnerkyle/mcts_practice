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
    
    def legal(self, order):	# order has the same structure and keys as units
	
	legal_maxbuild = all(order[unit] <= unit.maxbuild for unit in order)
	legal_resource = (
	    self.resource > sum(order[unit] * unit.cost for unit in order))
	return legal_resource and legal_maxbuild

    def add_units(self, order):

	if self.legal(order):
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

def run():
	    
    farmer = Unit('farmer', cost = 6, value = 3, speedup = 3, maxbuild = 10)
    soldier = Unit('soldier', cost = 10, value = 10, speedup = 0, maxbuild = 20)
    hero = Unit('hero', cost = 100, value = 150, speedup = 0, maxbuild = 1)
    init_unit = {farmer: 0, soldier: 0, hero: 0}
	
    server = Server(init_unit, resource=30, addup=5)
	
    max_round = 10
    for r in range(0, max_round):
	server.random_play()
	server.describe()
	
if __name__ == '__main__':
    run()