from collections import Counter
from collections import OrderedDict
from mergedeep import merge, Strategy
import random

mylist = [5,2,3,4]
mylist.remove(5)
print(mylist)

#for each card you have
{
    "aggression":{"stability":3,
        "cost":15,
        {"enter":
            {"start":
            "rate": 0,
            "actions": [{"function":"draw","target":"enemy_team", "percent": -200}]
            }
        ],
        "progress":[
            {"function":"money","target":"enemy_team","amount":-1}
        ],
        "exit":[
            {"function":"damage","target":"enemy_team","amount":10}
        ]},
