#TODO TODONE
#Make refresh work
#Add images
#Make it so you can play against yourself
#Make drag and drop work
#inspect to see information
#Restructure cards so enter progress and exit are inside a trigger dict
#Change the python and javascript to match the new structure
#How to get divs on an image
#Progress bars of different thickness to represent number, and color to represent function. Yellow for gold, teal for cards, blue for shield, green for heal. etc. Overlay them thinly on the bottom of the card
#Image and number for coins
#Refactor cardButton updates.
#Refactor for sending complete states to client instead of the client never seeing that something is dead or progress complete. Just the reset to 0 state
#fix shield
#make an exit trigger
#refactor targetting
#Add to inspect
#Make a max money
#Make a way to see team info
#Add skull image on death
#bot removal
#Red text if you don't have the money
#Fix higher cost for cards
#rounded slots
#TODO 
#Make more triggers and actions
#Make a discard pile
#Bots play to random open slot instead of 12345
#Make a team health bar near you and on their side for them
#Make you money bar closer to you
#TODO maybe
#Create random cards and allow them to be saved off if good
#TODO SCENARIOS / Bot loadouts. Tutorial bot. Bots sequence on defeat, checks player list for name+1 also contains message relevant to bot
#Intro, bots have lower draw speed and income
#Scenario 1.  Daggers from the bot. You have to place your bombs where the daggers are not.
#Scenario 2.  Daggers and shields from the bot. You have daggers and bombs now
#Scenario 3.  Daggers and shields from the bot and bombs. You have daggers and bombs and shields.
#Standard campaign starts with an even fight.
#Then you have 3 cards to choose from selected from a pool
#Pool: income draw slow enemy income, slow enemy draw, protect neighbor cards, better versions of bomb cards. Combined cards, like spike shield. or Spiky bomb. Guardian that adds armor to neighbor cards. Card that increases tick rate of neighbor cards.
#TODO TRIGGERS
#On target action - When a target takes and action.... Specify name of action or category. Handled in trigger function.
#On target trigger - When a target trigger occurs... Specify name of trigger
#On draw triggers so when you draw the card you get money or something. Or you take damage when you draw the card.
#TODO Actions
#Mirror requres action to mirror as argument and does so. Basically trigger handles action
#TODO CARD IDEAS
#Card that reflects destabilize back at attacker
#Card that deals more damage when hurt
#Start using images on cards
#Hot potato or cooked grenade cards that start their countdown while in your hand.
#They cannot select target while in play

#DON'T USE ORDERED DICT SINCE YOU CAN'T CHOOSE INSERTION POINT. JUST USE A LIST WITH REFERENCES TO A MEGA DICT
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
#ACTIONS
def destabilize_action(card, arguments):
    target = arguments["target"]
    amount = arguments["amount"]
    if target:
        target["stability"] -= amount

def finish_action(card, arguments):
    move(card,"discard")

def money_action(card, arguments):
    target = arguments["target"]
    amount = arguments["amount"]
    income(amount,target)

def draw_action(card, arguments):
    target = arguments["target"]
    amount = arguments["amount"]
    draw(amount,target)

def time_action(card, arguments):
    target = arguments["target"]
    amount = arguments["amount"]
    teams_table[target]["time"] += amount

def damage_action(card, arguments):
    target = arguments["target"]
    amount = arguments["amount"]
    apply_damage(target,amount)

def protect_action(card, arguments):
    target = arguments["target"]
    amount = arguments["amount"]
    teams_table[target]["armor"] += amount

#TRIGGERS
#Could make this a general progress trigger that gets passed an amount eventually
def timer_trigger(card,timer):
    seconds_passed = timer.get("progress")
    if timer["progress"] >= timer["goal"]:
        timer["progress"] -= timer["goal"]
        for action in timer["actions"]:
            call_actions(card,action)
    #The change comes after so the client gets a chance to see the progress
    timer["progress"] += tick_rate()

def standard_trigger(card,event):
    for action in event["actions"]:
        call_actions(card,action)

#CORE
def call_actions(card,action):
    function_name = action["action"]+"_action"
    arguments = resolve_argument_aliases(card,action)
    print(function_name, action)
    globals()[function_name](card, arguments)

def call_triggers(card,event_type):
    events = card["triggers"].get(event_type)
    if events:
        for event in events:
            function_name = event_type + "_trigger";
            if function_name in globals():
                globals()[function_name](card, event)
            else:
                standard_trigger(card, event)

def resolve_argument_aliases(card,argus):
    #TODO need a copy function here so UI isn't messed up
    arguments = copy.deepcopy(argus)
    owner = card["owner"]
    arguments["owner"] = owner
    team = card["team"]
    enemy_team = get_enemy_team(team)
    arguments["team"] = card["team"]
    target = arguments["target"]
    enemy_board = teams_table[enemy_team]["board"]
    my_board = teams_table[team]["board"]
    if target == "self":
        arguments["target"] = owner
    elif target == "team":
        arguments["target"] = team
    elif target == "enemy_team":
        arguments["target"] = enemy_team
    elif target == "random":
        arguments["target"] = random.choice(enemy_board)
    elif target == "across":
        arguments["target"] = enemy_board[card["index"]]
    return arguments

#Maybe make this an action?
def kill_card(card):
    move(card,"discard")


#JSON
def load(a):
    with open(a["file"]) as f:
            return json.load(f)

#This is kind of a joke, but I want to see it play out so I can understand what I'm really doing system wise. How hard is it for a new person to make a card? Protect is confusing as is was a realization.
#Make a version of this that allows the user to create a card from lists. Then randomization is simply choosing random options. Asks if you want to continue.
#All options are integer based
#Random card just chooses random integers and maybe continues, maybe does not.
#If Auto random, else promptgg
def random_card():
    card = {}
    card["stability"] = random.randint(1,9)
    card["cost"] = random.randint(1,9)
    random_table
    return

#adventure_table = load({"file":"json/adventure.json"})
random_table = load({"file":"json/decks.json"})
decks_table = load({"file":"json/decks.json"})
cards_table = load({"file":"json/cards.json"})
players_default = load({"file":"json/players.json"})
team_default = load({"file":"json/teams.json"})
teams_table = {}
teams_list = ["good","evil"]
game_table = {"tick_duration":0.5,"tick_value":1,"running":0, "loser":""}
players_table = {}
local_players_table = {}
#COMMUNICATIONS
#adventure = "intro"
current_id = 1
message_queue = {}
loser = ""
log_message = {}
player_percents = []

def log(action):
    target = action["owner"]
    amount = int(action["amount"])
    action = action["action"]
    log = {target:Counter({action:amount})}
    merge(log_message, log, strategy=Strategy.ADDITIVE)

def saveBattle():
        with open('json/decks.json', 'w') as f:
            json.dump(decks_table,f)



def remove_broken_cards(team_data):
    cards = team_data["board"]
    for card in cards:
        if card:
            if card["stability"] <= 0:
                kill_card(card)



def get_card_index(board):
    for index, card in enumerate(board):
        if card:
            return index
    return None

def get_empty_index(board):
    for index, card in enumerate(board):
        if not card:
            return index
    return None

#Flow hand to board
def play_card(card,card_index):
    username = card["owner"]
    if players_table[username]["gold"] >= card["cost"]:
        game_table["running"] = 1
        players_table[username]["gold"] -= card["cost"]
        #TODO replace with index targetting
        #TODO make index targetting smart to go to an opening after you play a card or go to index 1 if all full. This way targetting is clear and can be manual if you want
        move(card,"board",card_index)
        #Team set here so you can play against yourself
        call_triggers(card, "enter")

#Flow deck to hand
#Flow of discard to deck
def deal(username):
    player_data = players_table[username]
    deck = player_data["deck"]
    player_discard = player_data["discard"]
    hand = player_data["hand"]
    if len(deck) <= 0:
        for card in player_discard:
            move(card,"deck")
        random.shuffle(deck)
    empty_hand_index = get_empty_index(hand)
    if len(deck) > 0 and empty_hand_index is not None:
        card = deck[-1]
        move(card,"hand",empty_hand_index)

def discard(username):
    player_data = players_table[username]
    hand = player_data["hand"]
    card_index = get_card_index(hand)
    if card_index is not None:
        card = hand[card_index]
        move(card,"discard")

def draw(count, target):
    usernames = get_targets(target)
    for username in usernames:
        for i in range(abs(count)):
            if count < 0:
                discard(username)
            else:
                deal(username)

#Back bone of flow
def move(card, to, index = -1):
    card_owner = card["owner"]
    card_location = card["location"]
    player_data = players_table.get(card_owner)
    if to == "board":
        card["team"] = get_team(card_owner)
        teams_table[card["team"]][to][index] = card
    elif to == "hand":
        if player_data:
            player_data[to][index] = card
    else:
        if player_data:
            player_data[to].append(card)

    if card_location == "board":
        call_triggers(card,"exit")
        teams_table[card["team"]][card_location][card["index"]] = 0
    elif card_location == "hand":
        if player_data:
            player_data[card_location][card["index"]] = 0
    else:
        if player_data:
            if card in player_data[card_location]:
                player_data[card_location].remove(card)
            else:
                print("SOMETHING ELSE MOVED THE CARD SOMEHOW")
                print(card)
                print(to)
                print(index)

    card["location"] = to
    card["index"] = index

    if to == "discard":
        refresh_card(card)

def board_tick():
    for team, team_data in teams_table.items():
        for card in team_data["board"]:
            if card:
                call_triggers(card,"timer")

async def tick():
    while True:
        await asyncio.sleep(game_table["tick_duration"])
        if game_table.get("reset"):
            game_table["reset"] = 0
            await update_state()
        if game_table["running"]:
            for player in list(players_table):
                if players_table.get(player).get("quit"):
                    del players_table[player]
            board_tick()
            team_tick()
            ai_tick()
            await update_state()
            #Done here so that the client gets full states
            for team, team_data in teams_table.items():
                remove_broken_cards(team_data)
def remove_quit_players(team_data):
            del players_table[player]

def tick_rate():
    return game_table["tick_duration"]*game_table["tick_value"]

def safe_get(l, idx, default=0): 
    try: 
        return l[idx] 
    except IndexError: 
        return default

def ai_tick():
    for player, player_data in players_table.items():
        if player_data["ai"]:
            hand = player_data["hand"]
            card_from_index = get_card_index(hand)
            card_to_index = get_empty_index(get_board(player))
            if card_from_index is not None and card_to_index is not None:
                card = hand[card_from_index]
                play_card(card,card_to_index)

def team_tick():
    for team, team_data in teams_table.items():
        team_data["income_timer"] += tick_rate()
        team_data["draw_timer"] += tick_rate()
        #overdraw needed for if the timer loops
        if team_data["draw_timer"] >= team_data["draw_seconds"]:
            team_data["draw_timer"] -= team_data["draw_seconds"]
            draw(1,team)
        if team_data["income_timer"] >= team_data["income_seconds"]:
            team_data["income_timer"] -= team_data["income_seconds"]
            income(1,team)


def reset_teams():
    for team in list(teams_table.keys()):
        initialize_team(team)

def initialize_team(team):
    teams_table[team] = copy.deepcopy(team_default)
    team_data = teams_table[team]
    team_data["income_timer"] = 0
    team_data["draw_timer"] = 0

def initialize_teams(teams):
    for team in teams:
        initialize_team(team)

def reset_state():
    global loser
    reset_teams()
    for username in list(players_table.keys()):
        load_deck(username)
        draw(3,username)

    teams_table[loser]["text"] = "Defeat... &#x2639;"
    teams_table[get_enemy_team(loser)]["text"] = "Victory! &#128512;"

    loser = ""
    game_table["reset"] = 1

def get_unique_id():
    global current_id
    current_id += 1
    return current_id

def refresh_card(card):
    baby_card = copy.deepcopy(cards_table[card["name"]])
    card["triggers"] = baby_card["triggers"]
    card["max_stability"] = baby_card["stability"]
    card["stability"] = baby_card["stability"]

def initialize_card(card_name,username,random=""):
    baby_card = {}
    if random:
        baby_card = random_card()
        card_name = get_unique_id()
    baby_card = copy.deepcopy(cards_table[card_name])
    if not("title" in baby_card.keys()):
        baby_card["title"] = card_name
    baby_card["name"] = card_name
    baby_card["owner"] = username
    baby_card["id"] = get_unique_id()
    baby_card["location"] = "deck"
    refresh_card(baby_card)
    return baby_card
#Need an add card
def load_deck(username,deck_type="beginner"):
    players_table[username].update(copy.deepcopy(players_default))
    deck_to_load = decks_table[deck_type]
    random.shuffle(deck_to_load)
    deck = []
    for card_name in deck_to_load:
        baby_card = initialize_card(card_name, username)
        deck.append(baby_card)
    players_table[username]["deck"] = deck
    players_table[username]["discard"] = []

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
        players_table[username]["gold"] = max(0, players_table[username]["gold"])
        players_table[username]["gold"] = min(players_table[username]["gold_limit"], players_table[username]["gold"])

def apply_damage(team, damage):
    teams_table[team]["health"] -= max(damage - teams_table[team]["armor"], 0)
    global loser
    if teams_table[team]["health"] <= 0 and (not loser):
        #Make this a lose game function
        loser = team
        reset_state()

async def release_message():
    global message_queue
    for username in list(message_queue.keys()):
        if local_players_table.get(username):
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

def get_board(username):
    return teams_table[players_table[username]["team"]]["board"]

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
    queue_message({"game_table":game_table},targets)
    queue_message({"teams_table":teams_table},targets)
    queue_message({"evil":teams_table["evil"]["board"]},targets)
    queue_message({"good":teams_table["good"]["board"]},targets)
    target_list = get_targets(targets)
    for player in target_list:
        queue_message({"player_state":players_table[player]},player)
        queue_message({"hand":players_table[player]["hand"]},player)
    await release_message()

def card_from(card_id, cards):
    for card in cards:
        if card and card_id == card["id"]:
            return card
    return {}

async def new_client_connected(client_socket, path):
    username = add_player("good", 0)
    local_players_table[username] = {"socket":client_socket}
    await update_state(username)

    try:
        while True:
            card_json_message = await client_socket.recv()
            card_json = json.loads(card_json_message)
            print("Client sent:", card_json)
            if ("id" in card_json.keys()):
                await handle_play(username,card_json)
            if (card_json.get("command")):
                globals()[card_json["command"]](username)
                if card_json.get("command") == "quit":
                    break;

    except Exception as e:
        print("Client quit:", username)
        print(e)
        del local_players_table[username]
        del players_table[username]

def pause(username):
    print(username + " paused")
    if game_table["running"]:
        game_table["running"] = 0
    else:
        game_table["running"] = 1


def join_evil(username):
    print(username + " joined evil")
    players_table[username]["team"] = "evil"

def join_good(username):
    print(username + " joined good")
    players_table[username]["team"] = "good"

def reset_game(username):
    global loser
    loser = "good"
    reset_state()

def add_ai_evil(username):
    add_player("evil",1)

def add_ai_good(username):
    add_player("good",1)

def quit(username):
    players_table[username]["quit"] = 1

def remove_ai(username):
    #Needs to mark for removal then remove after tick to avoid issues
    for player, player_data in players_table.items():
        if player_data["ai"]:
            player_data["quit"] = 1

def add_player(team,ai):
    username = "player" + str(get_unique_id())
    print("Player Added: "+username)
    players_table[username] = {"team":team,"ai":ai}
    load_deck(username)
    draw(3,username)
    return username

async def handle_play(username,card_json):
    team = get_team(username)
    card_id = int(card_json["id"])
    card_index = int(card_json["index"])
    #Get card from id
    card = card_from(card_id, players_table[username]["hand"])
    print(card_json)
    if card:
        play_card(card,card_index)

    await update_state()

async def start_server():
    print("Server started!")
    initialize_time()
    initialize_teams(teams_list)
    await websockets.serve(new_client_connected, "localhost", 12345)

if __name__ == '__main__':
    event_loop = asyncio.get_event_loop()
    event_loop.run_until_complete(start_server())
    event_loop.run_forever()
