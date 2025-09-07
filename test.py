from collections import Counter
from collections import OrderedDict
import random
import copy
dict1 = {"triggers":{"timer":
    [{
        "goal":"y"
        }]
    }}
dict1["triggers"]["timer"].append({"swag":"iguess"})
print(dict1)
