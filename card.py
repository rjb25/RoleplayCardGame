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

def money_effect(action):
    target = action["target"]
    amount = action["amount"]
    deal_gold(amount,target)

def draw_effect(action):
    target = action["target"]
    amount = action["amount"]
    deal_cards(amount,target)

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
players_table = {}
local_players_table = {}
#COMMUNICATIONS
#adventure = "intro"
current_id = -1 
default_time = 120
message_queue = {}
loser = ""

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
    #handles target interpretation 
    owner = args["owner"]
    target = args["target"]
    if target == "self":
        args["target"] = owner
    elif target == "team":
        args["target"] = get_team(owner)
    elif target == "enemy_team":
        args["target"] = get_enemy_team(get_team(owner))
    globals()[function](args)

def remove_broken_plans(team_data):
    plans = team_data["plans"]
    for plan in plans:
        plan[:] = [card for card in plan if card["stability"] > 0]
    plans[:] = [plan for plan in plans if len(plan) > 0]

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
                if(card["stability"]>0):
                    for action in card["progress"]:
                        action["owner"] = card["owner"]
                        call_function(action["function"]+"_effect",action)
    #Exit
    for team, team_data in teams_table.items():
        if len(team_data["plans"]) > team_data["queue_length"]:
            exit_plan = team_data["plans"].pop()
            for card in exit_plan:
                if(card["stability"]>0):
                    for action in card["exit"]:
                        action["owner"] = card["owner"]
                        call_function(action["function"]+"_effect",action)

    #Cleanup
    for team, team_data in teams_table.items():
        teams_table[team]["running"] = 1
        #Removes cards lacking stability
        remove_broken_plans(team_data)

def initialize_teams():
    for team in list(teams_table.keys()):
        teams_table[team] = copy.deepcopy(team_default)

def reset_state():
    global default_time
    global loser
    initialize_teams()
    for username in list(players_table.keys()):
        load_deck(username)
        deal_cards(6,username)
    global current_id
    current_id = 0

    teams_table[loser]["text"] = "Defeat..."
    teams_table[get_enemy_team(loser)]["text"] = "Victory!"

    loser = ""
    queue_message({"reset": 1})
    #Don't need to remove cards anymore
    queue_message({"played":[]})

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
    return baby_card


def load_deck(username):
    loaded_deck = {} 
    deck_to_load = decks_table[username]
    random.shuffle(deck_to_load)
    deck_dict = {}
    for card_name in deck_to_load:
        baby_card = initialize_card(card_name, username)
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

def share(cnt,team,category):
    count = abs(cnt)
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

def get_sign(number):
    if number < 0:
        return -1
    return 1

def deal_gold(count, target):
    sign = get_sign(count)
    share_dict = share(count,target,"pay")
    for username, amount in share_dict.items():
        players_table[username]["gold"] += amount * sign
        if players_table[username]["gold"] < 0:
            apply_damage(get_team(username), abs(players_table[username]["gold"]))
            players_table[username]["gold"] = 0

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

def discard(username):
    player_data = players_table[username]
    discard = player_data["discard"]
    hand = player_data["hand"]
    if len(hand) > 0:
        card_id = hand.pop()
        discard.append(card_id)
        queue_message({"played":[card_id]},username,Strategy.ADDITIVE)
    else:
        apply_damage(get_team(username), 1)

def apply_damage(team, damage):
    teams_table[team]["health"] -= damage
    global loser
    if teams_table[team]["health"] <= 0 and (not loser):
        loser = team

def deal_cards(count, target):
    usernames = get_targets(target)
    message_result = {}
    share_dict = share(count,target,"deal")
    for username, amount in share_dict.items():
        for i in range(amount):
            if count < 0:
                discard(username)
            else:
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

def check_no_cards():
    found_no_cards = 0
    for team, team_data in teams_table.items():
        if not team_data["planned"]:
            cards_left = 0
            a_player = ""
            for player, player_data in players_table.items():
                if team == player_data["team"]:
                    cards_left += len(player_data["hand"])
                    a_player = player
            if not cards_left and a_player:
                found_no_cards += 1
                limit = team_data["limit"]
                count_played = len(team_data["cards_played"])
                remaining = limit - count_played
                for i in range(remaining):
                    baby_card = initialize_card("uhh",a_player)
                    play_card(a_player,baby_card)
    return found_no_cards

def play_card(username,card,choice=-1):
    team = get_team(username)
    discard = players_table[username]["discard"]
    cards_played = teams_table[team]["cards_played"]
    limit = teams_table[team]["limit"]
    if not teams_table[team]["planned"]:
        #if choice is not -1
        if choice + 1:
            teams_table[team]["running"] = 1
            discard.append(choice)
            players_table[username]["hand"].remove(choice)
            #Don't send message if the game is over
            queue_message({"played":[choice]},username,Strategy.ADDITIVE)
        if players_table[username]["gold"] >= card["cost"]:
            players_table[username]["gold"] -= card["cost"]
            cards_played.append(card)
        else:
            baby_card = initialize_card("umm",username)
            cards_played.append(baby_card)

    if len(cards_played) == limit:
        teams_table[team]["planned"] = 1
        teams_table[team]["running"] = 0

    if all_ready():
        end_round()

def initialize_time():
    timer = asyncio.create_task(tick())
    
async def time_up(team):
    #health function
    teams_table[team]["time"] += 60
    apply_damage(team,10)
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
    global loser
    if loser:
        reset_state()

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
    else:
        local_players_table[username]["socket"] = client_socket
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
        card = players_table[username]["deck_dict"][choice]
        play_card(username,card,choice)
        teams_table[team]["text"] = "Playing!"
        #I see timer problems I'm concerned it's not running
        while check_no_cards():
            print("NONE!")
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
#Start using images on cards
