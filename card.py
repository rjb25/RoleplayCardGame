#DON't use ordered dict since you can't choose insertion point. Just use a list with references to a mega dict
import asyncio
from collections import Counter
import websockets
from mergedeep import merge, Strategy
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
#Green screen when playing again
#TODO end of game stats
#TODO all cards need to execute
#TODO debug log of all actions
#TODO round summary, what you gained and lost each round
#TODO deal specific card
#TODO show round summary and opponent health and information
#TODO simplify
#TODO Visual bars  for numbers
#Enemy hand size and +-
#Information round?
#TODO if another card goes over 100% during a cards turn make sure it gets ticked after instead of instant.
#todo change value next to values
#green or red +- next to number with diff
#one of each type in starting hand
#empty the hearts when they go down
#EFFECTS

#JSON
def load(a):
    with open(a["file"]) as f:
            return json.load(f)

#adventure_table = load({"file":"json/adventure.json"})
decks_table = load({"file":"json/decks.json"})
cards_table = load({"file":"json/cards.json"})
team_default = load({"file":"json/teams.json"})
teams_table = {"evil":{},"good":{}}
game_table = {"tick_duration":0.5,"tick_value":1,"running":0, "loser":""}
players_table = {}
boards = {}
local_players_table = {}
#COMMUNICATIONS
#adventure = "intro"
current_id = -1 
message_queue = {}
loser = ""
tick_rate = 5
log_message = {}
player_percents = []

def saveBattle():
        with open('json/decks.json', 'w') as f:
            json.dump(decks_table,f)

def get_next_field(board):
    for index, card in enumerate(board):
        if not card:
            return index
    return -1 

def refresh_card(card):
    actions = find_actions_without_trait(card,"persist")
    instant_actions = find_actions_with_trait(card,"instant")
    for action in actions:
        action["percent"] = 0
    for action in instant_actions:
        action["percent"] = 100

#Flow hand to board
def play_card(card):
    username = card["owner"]
    if players_table[username]["gold"] >= card["cost"]:
        players_table[username]["gold"] -= card["cost"]
        #TODO replace with slot targetting
        #TODO make slot targetting smart to go to an opening after you play a card or go to slot 1 if all full. This way targetting is clear and can be manual if you want
        move(card,"board",0)
        call_functions(card, "enter")

#Flow deck to hand
#Flow of discard to deck

#Back bone of flow
def move(card, arguments, index = 0):
    to = arguments["to"]
    card_owner = card["owner"]
    card_location = card["location"]
    card_target = card["location"]
    player_data = players_table[card_owner]
    if to == "board":
        player_data[to][index] = card
        card["location"] = to
        card["index"] = index
    else:
        player_data[to].append(card)
        card["location"] = to

    if card_location == "board":
        player_data[card_location].remove(card)

    if to == "discard":
        refresh_card(card)

def find_actions_with_trait(card,trait):
    actions = card["actions"]
    actions_list = []
    for action in actions:

def update_team_percent(team,field):
    team[field+"_percent"] += tick_rate() * team[field+"_rate"]
    if team[field+"_percent"] >= 100:
        function = field+"_team"
        globals()[function](team)
        if trait in action["traits"]:
            actions_list.append(action)
    return actions_list

def find_actions_without_trait(card,trait):
    actions = card["actions"]
    actions_list = []
    for action in actions:
        if trait not in action["traits"]:
            actions_list.append(action)
    return actions_list

def card_targets(card,targets):
    target_cards = []
    for target in targets:
        if target == "self":
            target_cards.append(card)
        if target == "team":
            card["owner"]

def action_times(action):
    times = 0
    if "overkill" in action["traits"]:
        times = round(action["percent"]/100)
        action["percent"] = action["percent"] % 100
    else:
        action["percent"] = 0
        times = 1
        return times

def execute_functions(card,action,arguments)
    for function in action["functions"]:
        targets = action["targets"]
        args = action["arguments"]
        for target_card in card_targets(card,targets):
            globals()[function](target_card,arguments)
    
def progress(card,arguments):
    trait = arguments["trait"]
    percent = arguments["percent"]
    actions = find_actions_with_trait(card,trait)
    for action in actions:
        action["percent"] += percent/action["resist"]
        if action["percent"] >= 100 && action.get("functions") != None:
            for x in range(action_times(action))
                execute_functions(card,action,arguments)

async def tick():
    while True:
        await asyncio.sleep(game_table["tick_duration"])
        if game_table["running"]:
            hand_tick()
            board_tick()
            player_tick()
            await update_state()

def tick_rate():
    return game_table["tick_duration"]*game_table["tick_value"]

def tick_progress():
    for player, player_data in players_table.items():


def initialize_teams():
    for team in list(teams_table.keys()):
        teams_table[team] = copy.deepcopy(team_default)

def reset_state():
    global loser
    initialize_teams()
    for username in list(players_table.keys()):
        load_deck(username)
        deal_cards(3,username)

    teams_table[loser]["text"] = "Defeat... &#x2639;"
    teams_table[get_enemy_team(loser)]["text"] = "Victory! &#128512;"

    loser = ""

def get_unique_id():
    global current_id
    current_id += 1
    return current_id

def initialize_card(card_name,username):
    baby_card = copy.deepcopy(cards_table[card_name])
    if not("title" in baby_card.keys()):
        baby_card["title"] = card_name
    baby_card["owner"] = username
    baby_card["id"] = get_unique_id()
    baby_card["location"] = "deck"
    return baby_card


def load_deck(username):
    deck_to_load = decks_table[username]
    random.shuffle(deck_to_load)
    deck = []
    for card_name in deck_to_load:
        baby_card = initialize_card(card_name, username)
        deck.append(baby_card)
    players_table[username]["deck"] = deck
    players_table[username]["discard"] = []
    players_table[username]["hand"] = []


def is_team(target = ""):
    if target in list(teams_table.keys()):
        return True

async def release_message():
    global message_queue
    for username in list(message_queue.keys()):
        await local_players_table[username]["socket"].send(str(message_queue[username]))
    message_queue = {}

def queue_message(message, target = "", method = Strategy.REPLACE):
    global message_queue
    target_list = get_targets(target)
    for player in target_list:
        message_queue.setdefault(player,{})
        merge(message_queue[player], message, strategy = method)

def get_team(username):
    return players_table[username]["team"]

def get_enemy_team(team): 
    if team == "evil":
        return "good"
    else: 
        return "evil"

def initialize_time():
    timer_handle = asyncio.create_task(tick())
    
def strip_keys_copy(keys, table):
    copied_table = copy.deepcopy(table)
    for key in keys:
        copied_table.pop(key, None)

#If an action has a name then client renders the progress. Otherwise no
async def update_state(targets = ""):
    strip = ["deck","discard","socket","team"]
    strip_keys_copy(strip, players_table)
    queue_message({"teams_table":teams_table},targets)
    target_list = get_targets(targets)
    for player in target_list:
        queue_message({"player_state":players_table[player]},player)
    await release_message()

def card_from(card_id, cards):
    for card in cards:
        if card_id == card["id"]:
            return card
    return {}

async def new_client_connected(client_socket, path):
    paths = path.split('/')
    username = paths[1]
    team = paths[2]

    if username not in list(decks_table.keys()):
        print("Invalid username")
        return ""

    if team not in list(boards.keys()):
        boards[team] = [0,0,0,0,0]
        
    if username not in list(players_table.keys()):
        print("New client connected!")
        print("User: "+username)
        local_players_table[username] = {"socket":client_socket}
        players_table[username] = {"team":team}
        players_table["board"] = boards[team]
        load_deck(username)
        deal_cards(3,username)
    else:
        #If the player that just connected already connected before just update their socket
        local_players_table[username]["socket"] = client_socket

    await update_state(username)

    while True:
        card_json_message = await client_socket.recv()
        print("Client sent:", card_json_message)
        card_json = json.loads(card_json_message)
        card_id = int(card_json["id"])
        card_owner = card_json["owner"]
        #Get card from id
        card = card_from(card_id, players_table[username]["hand"])
        if card:
            play_card(card)
        else:
            teams_table[team]["text"] = "That card was yeeted... Oops"

        teams_table[team]["text"] = "Playing!"
        await update_state()

async def start_server():
    print("Server started!")
    initialize_teams()
    initialize_time()
    await websockets.serve(new_client_connected, "localhost", 12345)

if __name__ == '__main__':
    event_loop = asyncio.get_event_loop()
    event_loop.run_until_complete(start_server())
    event_loop.run_forever()
#CARD IDEAS
#Start using images on cards
#They cannot select target while in play
