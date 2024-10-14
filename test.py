from collections import Counter
from collections import OrderedDict
import random
import copy
dict1 = {"value_world":2}
slot1 = [dict1]
slot2 = []
list1 = [[],[]]
list1[0] = slot1
list1[1] = slot2
print(list1)
list1[1] = slot1
print(list1)
list1[0] = slot2
dict1["h"] = 3
print(list1)
