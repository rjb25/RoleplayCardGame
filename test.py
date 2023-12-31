import functools
def add_dicts2(di1,di2):
    return {i: di1.get(i, 0) + di2.get(i, 0)for i in set(di1).union(di2)}

def add_dicts(dicts):
    return functools.reduce(add_dicts2, dicts)

def sub_dicts2(di1,di2):
    return {i: di1.get(i, 0) - di2.get(i, 0)for i in set(di1).union(di2)}

def sub_dicts(dicts):
    return functools.reduce(sub_dicts2, dicts)

def situation_handled(situation):
    for element,value in situation.items():
        if value > 0:
            return False
    return True
plan = {"you":2,"hey":3,"yolo":3}
situation = {"yolo":3}
print(sub_dicts([situation,plan]))
print(situation_handled(sub_dicts([situation,plan])))


plan = {"situations":[{"bad":3,"good":4}],"hey":3,"yolo":3}
print(plan)
situations = plan["situations"]
situations.pop(0)
print(plan)

for i in [{},{}]:
    print("hey")
