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
import time
from itertools import takewhile

def deep_merge(base_dict,update_dict):
    base_dict.update(update_dict)

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
players_table = load({"file":"json/players.json"})

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

#COMMUNICATIONS
cards_played = []
adventure = "intro"
current_id = -1 
deal_to_next = 0
default_time = 120
time = default_time
running = False
message_queue = {}
def get_unique_id():
    global current_id
    current_id += 1
    return current_id

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
    cards_played = []
    state_table["situations"] = []
    state_table["plans"] = []
    state_table["victory"] = 0
    global default_time
    queue_message({"time": default_time, "reset": 1, "running":0})
    for username in list(players_table.keys()):
        players_table[username]["discard"] = []
        players_table[username]["hand"] = []
        players_table[username]["deck"] = list(players_table[username]["deck_dict"])
        deal_cards(6,username)
    global time
    time = default_time
    global running
    running = False

def load_deck(username):
    loaded_deck = {} 
    deck_to_load = decks_table[username]
    random.shuffle(deck_to_load)
    deck_dict = {}
    for card in deck_to_load:
        if not("title" in cards_table[card].keys()):
            cards_table[card]["title"] = card
        deck_dict[get_unique_id()] = cards_table[card]
    deck = list(deck_dict)
    players_table[username]["deck"] = deck
    players_table[username]["deck_dict"] = deck_dict
    players_table[username]["discard"] = []
    players_table[username]["hand"] = []

def deal_cards(count, player = ""):
    players = list(players_table.values())
    usernames = list(players_table.keys())
    message_result = {}
    global deal_to_next
    for i in range(count):
        #Handles spreading cards for non divisble amounts fairly
        if player:
            index = usernames.index(player)
        else:
            index = (i + deal_to_next) % len(players)
            if i == count -1:
                deal_to_next = (index + 1) % len(players)
        player_data = players[index]
        username = usernames[index]
        deck = player_data["deck"]
        deck_dict = player_data["deck_dict"]
        discard = player_data["discard"]
        hand = player_data["hand"]
        if len(deck) <= 0:
            #Lesson learned here is that 'dict[mylist] = list' works, and 'name = dict[mylist]; name.func(args)' works.
            #'name = newlist' fails
            deck.extend(discard)
            random.shuffle(deck)
            discard.clear() 
        if len(deck) > 0:
            card_id = deck.pop(0)
            card = deck_dict[card_id]
            hand.append(card_id)
            if not(username in message_result.keys()):
                message_result[username] = []
            message_result[username].append({"id":card_id, "card":card})
    for username, cards in message_result.items():
        queue_message({"cards":cards},username)

async def send_message(message,username = ""):
    if username:
        await players_table[username]["socket"].send(str(message))
    else:
        for player, player_data in players_table.items():
            await player_data["socket"].send(str(message))

async def release_message():
    global message_queue
    for username in list(message_queue.keys()):
        await players_table[username]["socket"].send(str(message_queue[username]))
    message_queue = {}

def queue_message(message,username = ""):
    global message_queue
    if username:
        message_queue.setdefault(username,{})
        deep_merge(message_queue[username], message)
    else:
        for username in list(players_table.keys()):
            message_queue.setdefault(username,{})
            deep_merge(message_queue[username], message)
def game_finished():
    if state_table["victory"] > 4:
        queue_message({"text":"You win!"})
        reset_state()
        return True
    if state_table["victory"] < -4:
        queue_message({"text":"You lose! Neener!"})
        reset_state()
        return True

def play_card(username,choice):
    players_table[username]["hand"].remove(choice)
    card = players_table[username]["deck_dict"][choice]["base"]
    discard = players_table[username]["discard"]
    discard.append(choice)
    cards_played.append(card)

    if len(cards_played) == 3:
        plan = add_dicts(cards_played)
        state_table["plans"].append(plan)
        cards_played.clear()
        state_table["victory"] += run_situation(state_table["situations"],state_table["plans"])
        if not(game_finished()):
            deal_cards(3)
        add_situation()
        queue_message({"state":state_table})

def initalize_time():
    timer = asyncio.create_task(tick())
    
async def time_up():
    print("times up")
    queue_message({"text":"You lose! Neener!"})
    reset_state()
    add_situation()
    queue_message({"state":state_table})
    await release_message()

async def tick():
    await asyncio.sleep(1)
    print("tick")
    global running
    if running:
        global time
        time = max(time-1, 0)
        if time <=0:
            await time_up()
    await tick()

async def new_client_connected(client_socket, path):
    username = path[1:]
    global time
    if not(username in players_table.keys()):
        print("New client connected!")
        print("User: "+username)
        players_table[username] = {"socket":client_socket}
        load_deck(username)
        queue_message({"time":time,"state":state_table, "text":"Welcome!"},username)
        deal_cards(6,username)
    else:
        players_table[username]["socket"] = client_socket
        hand = players_table[username]["hand"]
        cards = []
        for card in hand:
            cards.append({"id":card, "card":players_table[username]["deck_dict"][card]})
        queue_message({"time": time,"cards":cards,"text":"Welcome back!", "state":state_table},username)
    await release_message()

    while True:
        card_id = await client_socket.recv()
        print("Client sent:", card_id)
        global running
        running = True
        queue_message({"running":1})
        queue_message({"text":"Playing!"})
        
        choice = int(card_id)
        play_card(username,choice)
        await release_message()


async def start_server():
    print("Server started!")
    initalize_time()
    add_situation()
    await websockets.serve(new_client_connected, "localhost", 12345)

if __name__ == '__main__':
    event_loop = asyncio.get_event_loop()
    event_loop.run_until_complete(start_server())
    event_loop.run_forever()
#TODO
#discard cards
#Draw +2 card
#functions that can access the main data but are in another file/class
#aggragate messages and have anything that sends messages return as they add to make one message
#IDEAS
#situation queue
#Card that adds values based on plan, so for each time it gives another second, for each 3 force it adds 1 value to other categories for each 3 info it adds another card drawn for each stealth it increases the cards played for the next situation.
#Rogue Something like, defeat this situation, but it's effects get pushed to the next situation
#Rogue "end it", +1 card play blank plans for the rest of the plan. (if you cannot handle it and don't want to waste)
#Wizard Something like, return played cards to hands to restart a plan, see all players cards, redistribute cards, get cards for each info etc
#stealth targets future situations Rogue
#info targets more cards and team transparency Wizard
#time targets the timer Royalty
#force targets raw values for this turn Barbarian
#have it be time and need to handle all situations. Situations go back into the deck if they pass through. They also inflict a penalty when they pass
#Preparations phase where you can play 1 card each that adds a perk like seeing an extra situation ahead, drawing an extra card, relic type things, but only one
#let there be blood force x2
