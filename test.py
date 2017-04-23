import copy

def recursive_order(visit, units, container):    
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
	return recursive_order(visit, units, container)
    else:
	return container

if __name__ == '__main__':
    visit = {'a': {1:1, 2:2, 3:3}, 'b': {1:2, 2:3, 3:4}, 'c': {1:3, 2:4, 3:5}}
    win = {'a': {1:0, 2:1, 3:2}, 'b': {1:1, 2:2, 3:3}, 'c': {1:2, 2:3, 3:4}}
    units = ['a', 'b', 'c']
    m = [{}]
    c = recursive_order(visit, units, m)
    pass