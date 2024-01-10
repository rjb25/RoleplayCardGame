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

#adventure_table = load({"file":"json/adventure.json"})
decks_table = load({"file":"json/decks.json"})
cards_table = load({"file":"json/cards.json"})
players_table = load({"file":"json/players.json"})
teams_table = load({"file":"json/teams.json"})
#COMMUNICATIONS
#adventure = "intro"
current_id = -1 
default_time = 120
message_queue = {}
executing_team = "evil"

def saveBattle():
        with open('json/decks.json', 'w') as f:
            json.dump(decks_table,f)

def add_dicts2(di1,di2):
    return {i: di1.get(i, 0) + di2.get(i, 0)for i in set(di1).union(di2)}

def add_dicts(dicts):
    return functools.reduce(add_dicts2, dicts)

def sub_dicts2(di1,di2):
    return {i: di1.get(i, 0) - di2.get(i, 0)for i in set(di1).union(di2)}

def sub_dicts(dicts):
    return functools.reduce(sub_dicts2, dicts)

def remaining_execution(plan):
    for element,value in plan.items():
        if value < 0:
            plan[element] = value*-1;
        if value > 0:
            plan[element] = 0;
    return plan

def execution_handled(execution):
    for element,value in execution.items():
        if value < 0:
            return False
    return True

def execute():
    global executing_team
    reacting_team = get_enemy_team(executing_team)
    if teams_table[executing_team]["planned"] + teams_table[reacting_team]["planned"] == 2:

        execute_cards_played = teams_table[executing_team]["cards_played"]
        execute_plan = add_dicts(execute_cards_played)
        executions = teams_table[executing_team]["plans"]
        executions.append(execute_plan)
        teams_table[executing_team]["cards_played"].clear()
        teams_table[executing_team]["planned"] = 0

        react_cards_played = teams_table[reacting_team]["cards_played"]
        react_plan = add_dicts(react_cards_played)
        reactions = teams_table[reacting_team]["plans"]
        reactions.append(react_plan)
        teams_table[reacting_team]["cards_played"].clear()
        teams_table[reacting_team]["planned"] = 0

        execution = executions.pop(0)
        success = 1
        result = None
        while reactions:
            reaction = reactions.pop(0)
            result = sub_dicts([reaction,execution])
            handled = execution_handled(result)
            if handled:
                reactions.insert(0,result)
                success = 0
            else:
                execution = remaining_execution(result)
        executions.append(execution)
        teams_table[executing_team]["victory"] += success

        if not(game_finished()):
            deal_cards(3,executing_team)
            deal_cards(3,reacting_team)
        executing_team = reacting_team
        update_state()

#LAST TODO teams_table now replaces state_table
#How to have a bot player connect?
def reset_state():
    global default_time
    for team, data in teams_table.items():
        data["situations"] = []
        data["plans"] = []
        data["victory"] = 0
        data["deal_to_next"] = 0
        data["planned"] = 0
        data["running"] = 0
        data["time"] = default_time
    for username in list(players_table.keys()):
        players_table[username]["discard"] = []
        players_table[username]["hand"] = []
        players_table[username]["deck"] = list(players_table[username]["deck_dict"])
        deal_cards(6,username)

    update_state();
    queue_message({"reset": 1})

def get_unique_id():
    global current_id
    current_id += 1
    return current_id

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

def get_targets(target = ""):
    target_list = []
    if is_team(target):
        for player in list(players_table.keys()):
            if target == get_team(player):
                target_list.append(player)
    elif target in list(players_table.keys()):
        target_list.append(target)
    else:
        for player in list(players_table.keys()):
            target_list.append(player)
    return target_list

def is_team(target = ""):
    if target in list(teams_table.keys()):
        return True

def deal_cards(count, target):
    #This needs to be get targets, not players_table
    usernames = get_targets(target)
    message_result = {}
    deal_to_next = 0
    for i in range(count):
        #Handles spreading cards for non divisble amounts fairly
        index = 0
        if is_team(target):
            deal_to_next = teams_table[target]["deal_to_next"] 
            index = (i + deal_to_next) % len(get_targets(target))
            if i == count -1:
                teams_table[target]["deal_to_next"] = (index + 1) % len(get_targets(target))
        else:
            index = usernames.index(target)
        username = usernames[index]
        player_data = players_table[username]
        deck = player_data["deck"]
        deck_dict = player_data["deck_dict"]
        discard = player_data["discard"]
        hand = player_data["hand"]

        #Actual dealing
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

def get_team(username):
    return players_table[username]["team"]

def queue_message(message,target = ""):
    global message_queue
    target_list = get_targets(target)
    for player in target_list:
        message_queue.setdefault(player,{})
        deep_merge(message_queue[player], message)

def get_executing_team():
    global executing_team
    return executing_team

def get_enemy_team(team): 
    if team == "evil":
        return "good"
    else: 
        return "evil"

def game_finished():
    for team, team_data in teams_table.items():
        if team_data["victory"] > 4:
            queue_message({"text":"You win!"},team)
            reset_state()
            return True
    return False

def play_card(username,choice):
    team = get_team(username)
    card = players_table[username]["deck_dict"][choice]["base"]
    discard = players_table[username]["discard"]
    cards_played = teams_table[team]["cards_played"]
    #send a message saying "valid move if < their limit and they are allowed to play. This would then tell the client to remove the card.

    if not teams_table[team]["planned"]:
        discard.append(choice)
        players_table[username]["hand"].remove(choice)
        cards_played.append(card)
        queue_message({"played":choice},username)

    if len(cards_played) == 3:
        teams_table[team]["planned"] = 1
    
    execute()


def initalize_time():
    timer = asyncio.create_task(tick())
    
async def time_up(team):
    print("times up")
    losing_team = team
    winning_team = get_enemy_team(team)
    queue_message({"text":"You lose! Neener!"},losing_team)
    queue_message({"text":"You win! Yay!"},winning_team)
    reset_state()
    queue_message({"team_state":teams_table[winning_team]},winning_team)
    queue_message({"team_state":teams_table[losing_team]},losing_team)
    await release_message()

async def tick():
    await asyncio.sleep(1)
    #print("tick")
    for team, team_data in teams_table.items():
        if team_data["running"]:
            team_data["time"] = max(team_data["time"]-1, 0)
            if team_data["time"] <=0:
                await time_up(team)
    await tick()

def update_state(users = ""):
    targets = get_targets(users)
    for target in targets:
        team = get_team(target)
        enemy_team = get_enemy_team(get_team(target))
        queue_message({"team_state":teams_table[team], "enemy_plans":teams_table[enemy_team]["plans"]},target)

async def new_client_connected(client_socket, path):
    username = path[1:]
    team = ""
    if not(username in players_table.keys()):
        print("New client connected!")
        print("User: "+username)
        players_table[username] = {"socket":client_socket}

        #odd is good even is evil. Starting count at odd for first
        team_index = len(players_table.items())%2
        team = "good" if team_index else "evil"
        players_table[username]["team"] = team
        enemy_team = get_enemy_team(team)

        load_deck(username)
        update_state(username)
        deal_cards(6,username)
    else:
        players_table[username]["socket"] = client_socket
        hand = players_table[username]["hand"]
        cards = []
        for card in hand:
            cards.append({"id":card, "card":players_table[username]["deck_dict"][card]})
        queue_message({"cards":cards },username)
        update_state(username)
    await release_message()

    while True:
        card_id = await client_socket.recv()
        print("Client sent:", card_id)
        teams_table[team]["running"] = 1
        queue_message({"running":1})
        queue_message({"text":"Playing!"})
        
        choice = int(card_id)
        play_card(username,choice)
        await release_message()


async def start_server():
    print("Server started!")
    initalize_time()
    await websockets.serve(new_client_connected, "localhost", 12345)

if __name__ == '__main__':
    event_loop = asyncio.get_event_loop()
    event_loop.run_until_complete(start_server())
    event_loop.run_forever()
#TODO
#
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
