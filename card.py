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

def load(a):
    with open(a["file"]) as f:
            return json.load(f)

#adventure_table = load({"file":"json/adventure.json"})
decks_table = load({"file":"json/decks.json"})
cards_table = load({"file":"json/cards.json"})
players_default = load({"file":"json/players.json"})
team_default = load({"file":"json/teams.json"})
teams_table = {"evil":{},"good":{}}
players_table = {}
#COMMUNICATIONS
#adventure = "intro"
current_id = -1 
default_time = 120
message_queue = {}

def saveBattle():
        with open('json/decks.json', 'w') as f:
            json.dump(decks_table,f)

def all_ready():
    ready_count = 0
    for team, team_data in teams_table.items():
        ready_count += team_data["planned"]
    return (ready_count == len(teams_table.items()))

def end_round():
    for team, team_data in teams_table.items():
        cards_played = team_data["cards_played"]
        team_data["plans"].append(copy.deepcopy(cards_played))
        cards_played.clear()
        team_data["planned"] = 0
        deal_cards(3,team)
    update_state()

#The references are the same here
def initialize_teams():
    for team in list(teams_table.keys()):
        teams_table[team].update(copy.deepcopy(team_default))

def reset_state():
    global default_time
    initialize_teams()
    for username in list(players_table.keys()):
        load_deck(username)
        deal_cards(6,username)
    global current_id
    current_id = 0

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
    players_table[username].update(copy.deepcopy(players_default))
    players_table[username]["deck"] = deck
    players_table[username]["deck_dict"] = deck_dict

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
    print(team)
    card = players_table[username]["deck_dict"][choice]["base"]
    discard = players_table[username]["discard"]
    cards_played = teams_table[team]["cards_played"]
    #send a message saying "valid move if < their limit and they are allowed to play. This would then tell the client to remove the card.
    if not teams_table[team]["planned"]:
        discard.append(choice)
        players_table[username]["hand"].remove(choice)
        print("call")
        cards_played.append(card)
        queue_message({"played":choice},username)

    if len(cards_played) == 3:
        teams_table[team]["planned"] = 1

    if all_ready():
        end_round()

def initialize_time():
    timer = asyncio.create_task(tick())
    
async def time_up(team):
    print("times up")
    losing_team = team
    winning_team = get_enemy_team(team)
    queue_message({"text":"You lose! Neener!"},losing_team)
    queue_message({"text":"You win! Yay!"},winning_team)
    reset_state()
    update_state()
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

def update_state(targets = ""):
    queue_message({"teams_table":teams_table},targets)

async def new_client_connected(client_socket, path):
    paths = path.split('/')
    username = paths[1]
    team = paths[2]
    if not(username in players_table.keys()):
        print("New client connected!")
        print("User: "+username)
        players_table[username] = {"socket":client_socket}

        #odd is good even is evil. Starting count at odd for first
        team_index = len(players_table.items())%2
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
        print(teams_table)
        await release_message()

async def start_server():
    print("Server started!")
    initialize_teams()
    initialize_time()
    await websockets.serve(new_client_connected, "localhost", 12345)

if __name__ == '__main__':
    event_loop = asyncio.get_event_loop()
    event_loop.run_until_complete(start_server())
    event_loop.run_forever()
#TODO
#Make a queue of plans with a size limit
#Add a 
#IDEAS
