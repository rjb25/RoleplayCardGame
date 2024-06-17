from collections import Counter
from collections import OrderedDict
from mergedeep import merge, Strategy
import random

board = {"hey":1,"hy":3}
me = {"board":board}
you = {"board":board}
me["board"]["hey"]=2
you["board"]["hooo"]=2
print(board)
print(me)
print(you)


#for each card you have
#"target" returns a list of cards, "function" will receive all those cards along side an "argument"
#What about draw? Well it calls draw passing it the player card/cards and arguments
#Draw should target the deck
#Money targets the player
{
"aggression":
    {
    "actions":
        [
            {
                "name": "Enemy discard 2",
                "traits":["board","instant"],
                "percent":100,
                "rate": 0,
                "functions": [{"function":"progress","targets":[""], "arguments":{"trait":"expire", "percent": 200}}]
            },
            {
                "traits":["board","duration"],
                "percent":0,
                "rate": 40,
                "functions": [{"function":"progress","targets":["enemy"],"arguments":{"percent":-100}}]
            },
            {
                "traits":["board","exit"],
                "percent":0,
                "rate": 10,
                "functions": [{"function":"kill","targets":["enemy"],"arguments":{"percent":10}},{"function":"expire", "targets": ["self"]}]
            },
            {
                "traits":["board","death"],
                "percent":0,
                "rate": 0,
                "resist": 3,
                "functions": [{"function":"move", "targets": ["self"], "arguments":{"to":"discard"}}]
            },
            {
                "traits":["hand","shop"],
                "percent":0,
                "rate": 10,
                "functions": [{"function":"expire", "targets": ["self"]}]
            },
            {
                "traits":["buy"],
                "percent":0,
                "rate": 0,
                "resist": 15,
                "functions": [{"function":"purchase", "targets": ["self"]}]
            },
            {
                "traits":["draw"],
                "percent":0,
                "rate": 0,
                "functions": [{"function":"draw", "targets": ["self"]}]
            }
        ]
    }
}
