import asyncio
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

#EFFECTS
def destabilize_effect(action):
    team = get_team(action["owner"])
    target = action["target"]
    amount = action["amount"]
    enemy_team = get_enemy_team(team)
    if target == "random":
        plans = teams_table[enemy_team]["plans"]
        if plans:
            plan = random.choice(plans)
            card = random.choice(plan)
            card["stability"] -= amount
            if card["stability"] < 0:
                plan.remove(card)
                if len(plan) == 0:
                    plans.remove(plan)

def money_effect(action):
    target = action["target"]
    amount = action["amount"]
    #Need a function to discard gold
    print("amount" + str(amount))
    deal_gold(amount,target)

def draw_effect(action):
    target = action["target"]
    amount = action["amount"]
    #Need a function for discard TODO will need to handle negative
    deal_cards(amount,target)

def time_effect(action):
    target = action["target"]
    amount = action["amount"]
    teams_table[target]["time"] += amount
    #Handle negative TODO

def health_effect(action):
    target = action["target"]
    amount = action["amount"]
    teams_table[target]["health"] += amount

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
players_table = {}
local_players_table = {}
#COMMUNICATIONS
#adventure = "intro"
current_id = -1 
default_time = 120
message_queue = {}

def saveBattle():
        with open('json/decks.json', 'w') as f:
            json.dump(decks_table,f)

#CORE
def all_ready():
    ready_count = 0
    for team, team_data in teams_table.items():
        ready_count += team_data["planned"]
    return (ready_count == len(teams_table.items()))

def call_function(function, args):
    #handle target interpretation here
    owner = args["owner"]
    target = args["target"]
    if target == "self":
        args["target"] = owner
    elif target == "team":
        args["target"] = get_team(owner)
    elif target == "enemy_team":
        args["target"] = get_enemy_team(get_team(owner))
    globals()[function](args)

def end_round():
    #Enter
    for team, team_data in teams_table.items():
        cards_played = team_data["cards_played"]
        team_data["plans"].insert(0,copy.deepcopy(cards_played))
        cards_played.clear()
        team_data["planned"] = 0
        for card in team_data["plans"][0]:
            for action in card["enter"]:
                action["owner"] = card["owner"]
                call_function(action["function"]+"_effect",action)
    #Progress
    teams = list(teams_table.keys())
    queue_length = 0
    for team, team_data in teams_table.items():
        queue_length += team_data["queue_length"] -2
    for i in range(queue_length):
        index = i + 2
        team_i = i % 2
        team = teams[team_i]
        plan_i = index // 2
        plans = teams_table[team]["plans"]
        if plan_i < len(plans):
            for card in plans[plan_i]:
                for action in card["progress"]:
                    print("Progressing")
                    print(action)
                    action["owner"] = card["owner"]
                    call_function(action["function"]+"_effect",action)
                    #TODO need the ability to test exit which means I need the ability to play sham
    #Exit
    for team, team_data in teams_table.items():
        if len(team_data["plans"]) > team_data["queue_length"]:
            exit_plan = team_data["plans"].pop()
            for card in exit_plan:
                for action in card["exit"]:
                    action["owner"] = card["owner"]
                    call_function(action["function"]+"_effect",action)

    #Cleanup
    for team, team_data in teams_table.items():
        teams_table[team]["running"] = 1

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
        baby_card = copy.deepcopy(cards_table[card])
        if not("title" in baby_card.keys()):
            baby_card["title"] = card
        baby_card["owner"] = username
        baby_card["id"] = get_unique_id()
        deck_dict[baby_card["id"]] = baby_card
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

def share(count,team,category):
    targets = get_targets(team)
    length = len(targets)
    share_dict = {}
    #main
    all_get = (count // length) 
    #if targetting all
    target_all = not team
    if target_all:
        all_get = count

    for target in targets:
        share_dict[target] = all_get

    if is_team(team):
        #to_next
        first_index = teams_table[team][category+"_to_next"]
        shifted_targets = targets[first_index:] + targets[:first_index]
        leftovers = count % length
        to_next_i_shifted = (leftovers+1) % len(shifted_targets)
        to_next = shifted_targets[to_next_i_shifted]
        to_next_i = targets.index(to_next)
        teams_table[team][category+"_to_next"] = to_next_i
        #leftovers
        remaining_targets = shifted_targets[:leftovers]
        for target in remaining_targets:
            share_dict[target] += 1

    return share_dict

def deal_gold(count, target):
    share_dict = share(count,target,"pay")
    for username, amount in share_dict.items():
        players_table[username]["gold"] += amount

def deal(username):
    player_data = players_table[username]
    deck = player_data["deck"]
    deck_dict = player_data["deck_dict"]
    discard = player_data["discard"]
    hand = player_data["hand"]
    if len(deck) <= 0:
        deck.extend(discard)
        random.shuffle(deck)
        discard.clear() 
    if len(deck) > 0:
        card_id = deck.pop(0)
        card = deck_dict[card_id]
        hand.append(card_id)

def deal_cards(count, target):
    usernames = get_targets(target)
    message_result = {}
    share_dict = share(count,target,"deal")
    for username, amount in share_dict.items():
        for i in range(amount):
            deal(username)

async def release_message():
    global message_queue
    for username in list(message_queue.keys()):
        await local_players_table[username]["socket"].send(str(message_queue[username]))
    message_queue = {}

#queue_message({"cards":[{"id":card_id, "card":card}]}, username, Strategy.ADDITIVE )
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

#def game_finished():
#    for team, team_data in teams_table.items():
#        if team_data["victory"] > 4:
#            queue_message({"text":"You win!"},team)
#            reset_state()
#            return True
#    return False

def play_card(username,choice):
    team = get_team(username)
    card = players_table[username]["deck_dict"][choice]
    discard = players_table[username]["discard"]
    cards_played = teams_table[team]["cards_played"]
    #send a message saying "valid move if < their limit and they are allowed to play. This would then tell the client to remove the card.
    if not teams_table[team]["planned"]:
        teams_table[team]["running"] = 1
        discard.append(choice)
        players_table[username]["hand"].remove(choice)
        cards_played.append(card)
        #cards_left
        #if len players_table
        queue_message({"played":choice},username)

    if len(cards_played) == 3:
        teams_table[team]["planned"] = 1
        teams_table[team]["running"] = 0

    if all_ready():
        end_round()

#Add _card to all the card functions so card strings don't clash

def initialize_time():
    timer = asyncio.create_task(tick())
    
async def time_up(team):
    #health function
    losing_team = team
    winning_team = get_enemy_team(team)
    teams_table[losing_team]["text"] = "You lose! Neener!"
    teams_table[winning_team]["text"] = "You win! Yay!"
    reset_state()
    update_state()
    await release_message()

async def tick():
    while True:
        await asyncio.sleep(1)
        for team, team_data in teams_table.items():
            if team_data["running"]:
                team_data["time"] = max(team_data["time"]-1, 0)
                if team_data["time"] <=0:
                    await time_up(team)

def update_state(targets = ""):
    #No stripping needed at the moment
    #strip_team_keys = [""]
    #copied_teams_table = copy.deepcopy(teams_table)
    #for key in strip_teams_keys:
    queue_message({"teams_table":teams_table},targets)

    copied_players_table = copy.deepcopy(players_table)
    for player, player_data in copied_players_table.items():
        full_hand = []
        for ID in player_data["hand"]:
            full_hand.append(player_data["deck_dict"][ID])
        player_data["hand"] = full_hand

    strip_player_keys = ["deck_dict","deck","discard","socket","team"]
    for key in strip_player_keys:
        for player, player_data in copied_players_table.items():
            player_data.pop(key, None)
    
    for player, player_data in copied_players_table.items():
        queue_message({"player_table":player_data},player)

async def new_client_connected(client_socket, path):
    paths = path.split('/')
    username = paths[1]
    team = paths[2]
    if not(username in list(players_table.keys())):
        print("New client connected!")
        print("User: "+username)
        local_players_table[username] = {"socket":client_socket}
        players_table[username] = {"team":team}
        load_deck(username)
        deal_cards(6,username)
        deal_gold(6,username)
    else:
        local_players_table[username]["socket"] = client_socket
        #This is just numbers. Needs content. Why does deck dict exist again?
        hand = players_table[username]["hand"]
        cards = []
        for card in hand:
            cards.append({"id":card, "card":players_table[username]["deck_dict"][card]})

    update_state(username)
    await release_message()

    while True:
        card_id = await client_socket.recv()
        print("Client sent:", card_id)
        
        choice = int(card_id)
        play_card(username,choice)
        #This shouldn't need to be here. I'm missing something
        update_state()
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
#Create decals for cards and cards in plans
#Implement sham cards
#
#General purpose display cards that looks nice
