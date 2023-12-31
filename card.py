import asyncio
import websockets
import sys
import requests
import functools
import json
from fractions import Fraction
from operator import itemgetter
import math
import random
import traceback
from functools import reduce
from operator import getitem
from collections import defaultdict
import pprint
import tkinter as tk
import argparse
import re
import shlex
import copy
from itertools import takewhile


def geti(list, index, default_value):
    try:
        return list[index]
    except:
        return default_value
#ddel(battleInfo,["groups",group])
def ddel(context,path):
    deep = pathing(path[:-1],context)
    if isinstance(deep, list):
        deep.pop(int(path[-1]))
    else:
        deep.pop(path[-1],None)

def dset(context, path, value):
    if not isinstance(path,list):
        path = [path]
    for key in path[:-1]:
        context = context.setdefault(key, {})
    context[path[-1]] = value

def dmod(context, path, value):
    if not isinstance(path,list):
        path = [path]
    for key in path[:-1]:
        context = context.setdefault(key, {})
    if dget(context,path[-1],None) == None:
        context[path[-1]] = int(value)
    else:
        context[path[-1]] = context[path[-1]] + int(value)

def dget(context, path, default=None):
    try:
        if not isinstance(path,list):
            path = [path]
        internal_dict_value = context
        for k in path:
            if isinstance(internal_dict_value,list):
                internal_dict_value = geti(context, int(k), default)
            else:
                internal_dict_value = internal_dict_value.get(k, default)
            if internal_dict_value is default:
                return default
        return internal_dict_value
    except:
        return default
                
def load(a):
    with open(a["file"]) as f:
            return json.load(f)

decks_table = load({"file":"json/decks.json"})
state_table = load({"file":"json/state.json"})
adventure_table = load({"file":"json/adventure.json"})
cards_table = load({"file":"json/cards.json"})
situations_table = load({"file":"json/situations.json"})

def saveBattle():
        with open('json/state.json', 'w') as f:
            json.dump(state_table,f)
        with open('json/decks.json', 'w') as f:
            json.dump(state_table,f)

def add_dicts2(di1,di2):
    return {i: di1.get(i, 0) + di2.get(i, 0)for i in set(di1).union(di2)}

def add_dicts(dicts):
    return functools.reduce(add_dicts2, dicts)

def sub_dicts2(di1,di2):
    return {i: di1.get(i, 0) - di2.get(i, 0)for i in set(di1).union(di2)}

def sub_dicts(dicts):
    return functools.reduce(sub_dicts2, dicts)

def remaining_situation(situation):
    for element,value in situation.items():
        if value < 0:
            situation[element] = value*-1;
        if value > 0:
            situation[element] = 0;
    return situation

def situation_handled(situation):
    for element,value in situation.items():
        if value < 0:
            return False
    return True

#CARDS
def attack():
    state_table["force"] = state_table["force"] +1;

#SITUATIONS

#COMMUNICATIONS
all_clients = [] 
cards_played = []
adventure = "intro"
def add_situation():
    situation_deck = decks_table[adventure]
    random.shuffle(situation_deck)
    situation = add_dicts([situations_table[situation_deck[0]], situations_table[situation_deck[1]]])
    state_table["situations"].append(situation)

def run_situation(situations, plans):
    situation = situations.pop(0)
    while plans:
        print(plans)
        plan = plans.pop(0)
        print(plans)
        print(plan)
        print(bool(plans))
        print(situation)
        result = sub_dicts([plan,situation])
        handled = situation_handled(result)
        if handled:
            plans.insert(0,result)
            return 1
        else:
            situation = remaining_situation(result)
    return -1

def reset_state():
    state_table["situations"] = []
    state_table["plans"] = []
    state_table["victory"] = 0
 

async def send_message(message: str):
    for client in all_clients:
        await client.send(message)

async def new_client_connected(client_socket, path):
    #if messages = allclients.length: globals()["situation_name"]()
    print("New client connected!")
    username = path[1:]
    print("User: "+username)
    all_clients.append(client_socket)

    #Card management
    deck = decks_table[username]
    random.shuffle(deck)
    hand = deck[:5]
    deck = deck[5:]
    discard = []

    await send_message(str({"state":state_table,"hand":hand,"text":"Welcome!"}))
    while True:
        message = await client_socket.recv()
        print("Client sent:", message)

        choice = int(message)
        card = hand.pop(choice)
        discard.append(card)

        #Use discard if deck empty
        if len(deck) <= 0:
            deck = discard.copy()
            random.shuffle(deck)
            discard = []
        if len(deck) > 0:
            hand.insert(choice,deck.pop(0))

        cards_played.append(card)
        if len(cards_played) == 3:
            plan = add_dicts([cards_table[cards_played[0]], cards_table[cards_played[1]], cards_table[cards_played[2]]])
            state_table["plans"].append(plan)
            cards_played.clear()
            state_table["victory"] += run_situation(state_table["situations"],state_table["plans"])
            if state_table["victory"] > 4:
                await send_message(str({"text":"You win!"}))
                reset_state()
            if state_table["victory"] < -4:
                await send_message(str({"text":"You lose! Neener!"}))
                reset_state()
            add_situation()
            await send_message(str({"state":state_table,"hand":hand,"text":"Turn executed!"}))

async def start_server():
    print("Server started!")
    add_situation()
    await websockets.serve(new_client_connected, "localhost", 12345)

if __name__ == '__main__':
    event_loop = asyncio.get_event_loop()
    event_loop.run_until_complete(start_server())
    event_loop.run_forever()
