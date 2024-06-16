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
#todo change value next to values
#green or red +- next to number with diff
#one of each type in starting hand
#empty the hearts when they go down
#EFFECTS
def destabilize_effect(action):
    #good destabilize is the only one with an initial damage
    team = get_team(action["owner"])
    target = action["target"]
    amount = action["amount"]
    enemy_team = get_enemy_team(team)
    if target == "random":
        board = teams_table[enemy_team]["board"][1:]
        card = random.choice(board)
        if card:
            card["stability"] -= amount

def money_effect(action):
    target = action["target"]
    amount = action["amount"]
    income_team(amount,target)

def draw_effect(action):
    target = action["target"]
    amount = action["amount"]
    draw_team(amount,target)

def time_effect(action):
    target = action["target"]
    amount = action["amount"]
    teams_table[target]["time"] += amount

def damage_effect(action):
    target = action["target"]
    amount = action["amount"]
    apply_damage(target,amount)

#JSON
def load(a):
    with open(a["file"]) as f:
            return json.load(f)

#adventure_table = load({"file":"json/adventure.json"})
decks_table = load({"file":"json/decks.json"})
cards_table = load({"file":"json/cards.json"})
players_default = load({"file":"json/players.json"})
team_default = load({"file":"json/teams.json"})
teams_table = {"evil":{},"good":{}}
game_table = {"tick_duration":0.5,"tick_value":1,"running":0, "loser":""}
players_table = {}
local_players_table = {}
#COMMUNICATIONS
#adventure = "intro"
current_id = -1 
message_queue = {}
loser = ""
tick_rate = 5
log_message = {}
board_percents = ["exit","kill","progress"]
hand_percents = ["expire"]
team_percents = ["income","draw"]
player_percents = []

def log(action):
    target = action["owner"]
    amount = int(action["amount"])
    function = action["function"]
    log = {target:Counter({function:amount})}
    merge(log_message, log, strategy=Strategy.ADDITIVE)

def saveBattle():
        with open('json/decks.json', 'w') as f:
            json.dump(decks_table,f)

#CORE
def call_functions(card, step):
    for action in card[step]:
        function = action["function"]+"_effect"
        #handles target interpretation 
        owner = card["owner"]
        action["owner"] = owner
        target = action["target"]
        if target == "self":
            action["target"] = owner
        elif target == "team":
            action["target"] = get_team(owner)
        elif target == "enemy_team":
            action["target"] = get_enemy_team(get_team(owner))
        globals()[function](card, action)

def remove_broken_cards(team_data):
    cards = team_data["board"]
    for index, card in enumerate(cards):
        if card:
            if card["stability"] < 0:
                kill_card(card)

def get_next_field(board):
    for index, card in enumerate(board):
        if not card:
            return index
    return -1 

def refresh_card(card):
    card["exit_percent"] = 0
    card["progress_percent"] = 0
    card["expire_percent"] = 0
    card["death_percent"] = 0

#Flow of hand to discard
def expire_card(card):
    move(card,"discard")

#Flow of board to discard
def kill_card(card):
    move(card,"discard")

def progress_card(card):
    call_functions(card,"progress")
    
def exit_card(card):
    call_functions(card, "exit")
    move(card,"discard")

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
def draw(card):
    username = card["owner"]
    player_data = players_table[username]
    deck = player_data["deck"]
    player_discard = player_data["discard"]
    hand = player_data["hand"]
    if len(deck) <= 0:
        for card in player_discard:
            move(card,"deck")
            random.shuffle(deck)
    if len(deck) > 0:
        card = deck[-1]
        move(card,"hand")

def discard(username):
    player_data = players_table[username]
    hand = player_data["hand"]
    if hand:
        card = hand[-1]
        expire_card(card)

def draw(count, target):
    usernames = get_targets(target)
    for username in usernames:
        for i in range(abs(count)):
            if count < 0:
                discard(username)
            else:
                deal(username)

#Back bone of flow
def move(card, to, index = 0):
    card_owner = card["owner"]
    card_location = card["location"]
    card_target = card["location"]
    player_data = players_table[card_owner]
    team_data = teams_table[player_data["team"]]
    if to == "board":
        team_data[to][index] = card
        card["location"] = to
    else:
        player_data[to].append(card)
        card["location"] = to

    if card_location == "board":
        team_data[card_location].remove(card)
    else:
        player_data[card_location].remove(card)

    if to == "discard":
        refresh_card(card)

#You can eventually handle health and all things about a card through here
#You can add the fields with just a word too and it will add bonus, multiplier, all that good stuff
def update_card_percent(card,field):
    card[field+"_percent"] += tick_rate() * card[field+"_rate"]
    if card[field+"_percent"] >= 100:
        function = field+"_card"
        globals()[function](card)

def update_team_percent(team,field):
    team[field+"_percent"] += tick_rate() * team[field+"_rate"]
    if team[field+"_percent"] >= 100:
        function = field+"_team"
        globals()[function](team)

async def tick():
    while True:
        await asyncio.sleep(game_table["tick_duration"])
        if game_table["running"]:
            #for team, team_data in teams_table.items():
                #team_data["time"] = max(team_data["time"]-tick_rate, 0)
            card_tick()
            team_tick()
            #A dict/list of data to tick
            hand_tick()
            for team, team_data in teams_table.items():
                remove_broken_cards(team_data)
            await update_state()
def tick_rate():
    return game_table["tick_duration"]*game_table["tick_value"]


def hand_tick():
    for player, player_data in players_table.items():
        for card in player_data["hand"]:
            if card:
                for field in hand_percents:
                    update_card_percent(card,field)

def team_tick():
    for team, team_data in teams_table.items():

        team_data["income_percent"] += tick_rate()*team_data["income_rate"]
        team_data["draw_percent"] += tick_rate()*team_data["draw_rate"]
        if team_data["draw_percent"] >= 100:
            team_data["draw_percent"] -= 100
            draw_team(1,team)
        if team_data["income_percent"] >= 100:
            team_data["income_percent"] -= 100
            income_team(1,team)

def card_tick():
    for team, team_data in teams_table.items():
        for card in team_data["board"]:
            if card:
                for field in board_percents:
                    update_card_percent(card,field)

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
    baby_card["expire_rate"] = 10
    baby_card["expire_percent"] = 0
    baby_card["progress_rate"] = 40
    baby_card["progress_percent"] = 0
    baby_card["exit_rate"] = 10 
    baby_card["exit_percent"] = 0
    
    baby_card["max_stability"] = baby_card["stability"]
    baby_card["location"] = "deck"
    return baby_card


def load_deck(username):
    players_table[username].update(copy.deepcopy(players_default))
    deck_to_load = decks_table[username]
    random.shuffle(deck_to_load)
    deck = []
    for card_name in deck_to_load:
        baby_card = initialize_card(card_name, username)
        deck.append(baby_card)
    players_table[username]["deck"] = deck
    players_table[username]["discard"] = []
    players_table[username]["hand"] = []

def get_targets(target = ""):
    if isinstance(target, list):
        return target
    target_list = []
    #Target team
    if is_team(target):
        for player in list(players_table.keys()):
            if target == get_team(player):
                target_list.append(player)
    #target player
    elif target in list(players_table.keys()):
        target_list.append(target)
    #target everyone
    else:
        for player in list(players_table.keys()):
            target_list.append(player)
    return target_list

def is_team(target = ""):
    if target in list(teams_table.keys()):
        return True

def income(count, target):
    usernames = get_targets(target)
    for username in usernames:
        players_table[username]["gold"] += count

def apply_damage(team, damage):
    teams_table[team]["health"] -= damage
    global loser
    if teams_table[team]["health"] <= 0 and (not loser):
        #Make this a lose game function
        loser = team
        reset_state()

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

    if not (username in list(decks_table.keys())):
        print("Invalid username")
        return ""
        
    if not(username in list(players_table.keys())):
        print("New client connected!")
        print("User: "+username)
        local_players_table[username] = {"socket":client_socket}
        players_table[username] = {"team":team}
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
