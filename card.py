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
#Hard refactor targetting so that Name = actual card
#refactor data so all I need to push is game state
#Add zones for tent and base so cards can target them just like they would other cards
#Update javascript to match new zones
#Make the team a card, but in another sector
#TODO 
#Fix effects
#Make while triggers, maybe they add something something in a pre tick. The "effect" section is then wiped on tick cleanup
#Change protect to add temporary health on a timer. Maybe a blue line below healthbar
#Then a grey bar for flat armor below that?
#Make a way to create cards from terminal
#Make add random card a player menu function
#Make more triggers and actions
#Make a discard pile
#prevent replace card so players don't step on toes
#Bots play to random open slot instead of 12345
#Make a team health bar near you and on their side for them
#Make you money bar closer to you on the player icon
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
import tkinter as tk
import argparse
import re
import shlex
import copy
import time
from itertools import takewhile
def log(*words):
    for word in words:
        print(word)

def play_action(target,action,card=0):
    username = target["owner"]
    owner = owner_card(username)
    if owner["gold"] >= target["cost"]:
        game_table["running"] = 1
        owner["gold"] -= target["cost"]
        move(target,"board",action["to"])
        call_triggers(target, "enter")

def discard_action(target, action = 0, card = 0):
    move(target,"discard")

def income_action(target, action, card = 0):
    target["gold"] += action["amount"]
    target["gold"] = max(0, target["gold"])
    target["gold"] = min(target["gold_limit"], target["gold"])

def draw_action(target, action = 0, card = 0):
    player_data = players_table[target["owner"]]
    deck = player_data["deck"]
    player_discard = player_data["discard"]
    hand = player_data["hand"]
    empty_hand_index = get_empty_index(hand)
    if not (empty_hand_index is None):
        move(target,"hand",empty_hand_index)
    #Reshuffle if deck empty
    if len(deck) <= 0:
        for discarded in player_discard:
            move(discarded,"deck")
        random.shuffle(deck)

def damage_action(target, action, card = 0):
    damage = action["amount"] 
    try:
        damage = max(0, damage - target["effects"]["armor"])
    except KeyError:
        print("no armor")
        pass
    target["health"] -= damage

def protect_action(target, action, card = 0):
    if target["effects"].get("armor"):
        target["effects"]["armor"] += action["amount"]
    else:
        target["effects"]["armor"] = action["amount"]

def find_triggers_with_action_name(card, action):
    triggers = []
    for trigger in card["triggers"]:
        for action in trigger["actions"]:
            if "action_name" == action["action"]:
                triggers.append(trigger)
                continue

#TRIGGERS
#Could make this a general progress trigger that gets passed an amount eventually
def timer_trigger(card, timer):
    seconds_passed = timer.get("progress")
    if timer["progress"] >= timer["goal"]:
        timer["progress"] -= timer["goal"]
        for action in timer["actions"]:
            call_action(action, card)
    #The change comes after so the client gets a chance to see the progress
    timer["progress"] += tick_rate()

def standard_trigger(card, event):
    for action in event["actions"]:
        call_action(action, card)

#CORE
def call_action(action, card = 0):
    function_name = action["action"]+"_action"
    targets = targetting(action["target"], card)
    for target in targets:
        globals()[function_name](target, action, card)

def call_triggers(card, event_type):
    events = card["triggers"].get(event_type)
    if events:
        for event in events:
            function_name = event_type + "_trigger";
            if function_name in globals():
                globals()[function_name](card, event)
            else:
                standard_trigger(card, event)

#Kind of messy, but it at least puts all the messy in one place
def targetting(target, card = 0):
    if not isinstance(target, list):
        target_aliases = [target]
    else:
        target_aliases = target

    paths = []
    for target_alias in target_aliases:
        if target_alias == "self":
            who = ""
            if card["location"] in ["base","board"]:
                who = card["team"]
            else:
                who = card["owner"]
            paths.append({"location":card["location"],"who":who,"index":card["index"]})

        elif target_alias == "allies":
            for player, player_data in players_table.items():
                if player_data["team"] == card["team"]:
                    paths.append({"location":"tent","who":player})

        elif target_alias == "enemies":
            for player in players_table.keys():
                if player_data["team"] != card["team"]:
                    paths.append({"location":"tent","who":player})

        elif target_alias == "ally_base":
            for team in teams_table.keys():
                if team == card["team"]:
                    paths.append({"location":"base","who":team})

        elif target_alias == "enemy_base":
            for team in teams_table.keys():
                if team != card["team"]:
                    paths.append({"location":"base","who":team})

        elif target_alias == "team_decks":
            for player, player_data in players_table.items():
                if player_data["team"] == card["team"]:
                    paths.append({"location":"deck","who":player,"index":-1})

        elif target_alias == "my_deck":
            paths.append({"location":"deck","who":card["owner"],"index":-1})

        elif target_alias == "my_deck3":
            paths.append({"location":"deck","who":card["owner"],"index":[-1,-2,-3]})

        elif target_alias == "random":
            for team in teams_table.keys():
                if team != card["team"]:
                    paths.append({"location":"board","who":team})

        elif target_alias == "across":
            for team in teams_table.keys():
                if team != card["team"]:
                    paths.append({"location":card["location"],"who":team,"index":card["index"]})

    for path in paths:
        if path["location"] in ["board","base"]:
            path["region"] = "teams"
        else:
            path["region"] = "players"

    targets = []
    for path in paths:
        try:
            if "index" in path:
                indices = []
                #If index is not a list make it a list
                if not isinstance(path["index"], list):
                    indices = [path["index"]]
                else:
                    indices = path["index"]
                for index in indices:
                    target = game_table[path["region"]][path["who"]][path["location"]][index]
                    if target:
                        targets.append(target)
            else:
                target = random.choice(game_table[path["region"]][path["who"]][path["location"]])
                if target:
                    targets.append(target)
        except KeyError:
            print("KEY ERROR")
            print(path)
            print(target)
            print(card)
            pass
        except IndexError:
            print("INDEX ERROR")
            print(path)
            print(target)
            print(card)
            pass
    return targets

#Ultimately this is a card in spot simulator. location, who, index. All have their aliases.
#These aliases could  have selection logic and multiples
#This reaches full code level complexity don't make me put this in the data
#So targetting for team draw 2 is {"location":"deck","who":{},"index":{"count":"random3","insert":"random"}}
#But this is good.
#So Aliases generate a list
#Random all would be. Well you really wouldn't do random location. so it would be random person and random index at worst
#This selection logic and multiples leads to a list of [{"location":"hand","who":"jason","index":2}]
#So do we need 2 functions? Or just one. I think just one. Just pass the alias all the way down?
#Each section has an alias which is resolved when retrieved.
#Ultimately what I need is a list of endpoints
#Problem is it could have randomization or multiple
#target list is the result
#resolved during call_actions

#Maybe make this an action?
def kill_card(card):
    move(card,"discard")

#JSON
def load(a):
    with open(a["file"]) as f:
            return json.load(f)

#Make a version of this that allows the user to create a card from lists. Then randomization is simply choosing random options. Asks if you want to continue.
#All options are integer based
#Random card just chooses random integers and maybe continues, maybe does not.
#If Auto random, else promptgg
def create_random_card(card_name):
    cards_table[card_name] = {}
    card = cards_table[card_name]
    card["health"] = random.randint(1,9)
    card["cost"] = random.randint(1,9)
    card["triggers"] = {}
    for x in range(random.randint(1,9)):
        trigger, triggerData = random.choice(list(random_table["triggers"].items()))
        card["triggers"][trigger] = create_random_trigger(triggerData)
    return card

def create_random_trigger(trigger):
    if "goal" in trigger:
        trigger["goal"] = random.randint(1,9)
    if "progress" in trigger:
        trigger["progress"] = random.randint(1,9)

def create_random_action(action):
    return "hey"

#GLOBALS
random_table = load({"file":"json/random.json"})
decks_table = load({"file":"json/decks.json"})
cards_table = load({"file":"json/cards.json"})
players_default = load({"file":"json/players.json"})
team_default = load({"file":"json/teams.json"})
teams_list = ["good","evil"]
game_table = load({"file":"json/game.json"})
teams_table = game_table["teams"]
players_table = game_table["players"]
local_players_table = {}
current_id = 1

def saveBattle():
        with open('json/decks.json', 'w') as f:
            json.dump(decks_table,f)

def apply_damage(team, damage):
    teams_table[team]["health"] -= max(damage - teams_table[team]["armor"], 0)
    if teams_table[team]["health"] <= 0 and (not loser):
        #Make this a lose game function
        game_table["loser"] = team
        reset_state()

def remove_broken_cards(cards):
    for card in cards:
        if card:
            card["effects"] = {}
            if card["health"] <= 0:
                loser = game_table["loser"]
                if card["location"] == "base" and (not loser):
                    game_table["loser"] = card["team"]
                    reset_state()
                else:
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
                log("SOMETHING ELSE MOVED THE CARD SOMEHOW")
                log(card)
                log(to)
                log(index)

    card["location"] = to
    card["index"] = index

    if to == "discard":
        refresh_card(card)

def location_tick():
    for team, team_data in teams_table.items():
        for location, location_data in team_data.items():
            for card in location_data:
                if card:
                    call_triggers(card,"timer")

def effect_tick():
    for team, team_data in teams_table.items():
        for location, location_data in team_data.items():
            for card in location_data:
                if card:
                    call_triggers(card,"effect")

async def tick():
    while True:
        await asyncio.sleep(game_table["tick_duration"])
        if game_table.get("reset"):
            game_table["reset"] = 0
            await update_state(local_players_table.keys())
        if game_table["running"]:
            for player in list(players_table):
                if players_table.get(player).get("quit"):
                    del players_table[player]
            effect_tick()
            location_tick()
            ai_tick()
            await update_state(local_players_table.keys())
            #Done here so that the client gets full states
            for team, team_data in teams_table.items():
                for location, cards in team_data.items():
                    remove_broken_cards(cards)

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
                play_action(card, {"to":card_to_index})

def reset_teams():
    for team in list(teams_table.keys()):
        initialize_team(team)

def initialize_team(team):
    game_table["teams"][team] = copy.deepcopy(team_default)
    #Need to add a card to base
    game_table["teams"][team]["base"][0] = initialize_card(team, "", "base",team)

def initialize_teams(teams):
    for team in teams:
        initialize_team(team)

def reset_state():
    reset_teams()
    for username in list(players_table.keys()):
        load_deck(username)
        call_action({"action":"draw", "target":"my_deck3"},{"owner":username})
    loser = game_table["loser"]
    game_table["text"][loser] = "Defeat... &#x2639;"
    game_table["text"][get_enemy_team(loser)] = "Victory! &#128512;"
    game_table["loser"] = ""

    game_table["reset"] = 1

def get_unique_id():
    global current_id
    current_id += 1
    return current_id

def get_unique_name():
    cards_table["current_name"] += 1
    return cards_table["current_name"]

def refresh_card(card):
    try:
        baby_card = copy.deepcopy(cards_table[card["name"]])
        card["triggers"] = baby_card["triggers"]
        card["effects"] = {}
        card["max_health"] = baby_card["health"]
        card["health"] = baby_card["health"]
    except KeyError:
        pass

def initialize_card(card_name,username="",location="deck",team=""):
    baby_card = {}
    baby_card = copy.deepcopy(cards_table[card_name])
    if not("title" in baby_card.keys()):
        baby_card["title"] = card_name
    baby_card["name"] = card_name
    if username:
        baby_card["owner"] = username
    baby_card["id"] = get_unique_id()
    baby_card["location"] = location
    if team:
        baby_card["team"] = team
    else:
        baby_card["team"] = get_team(username)
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
    players_table[username]["tent"][0] = initialize_card("player", username, "tent")


def is_team(target = ""):
    if target in list(teams_table.keys()):
        return True

async def update_state(players):
    for player in players:
        if player in local_players_table:
            await local_players_table[player]["socket"].send(str({"game_table":game_table,"me":player}))

def strip_keys_copy(keys, table):
    copied_table = copy.deepcopy(table)
    for key in keys:
        copied_table.pop(key, None)

#ACTIONS
def owner_card(owner):
    return game_table["players"][owner]["tent"][0]

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

def card_from(card_id, cards):
    for card in cards:
        if card and card_id == card["id"]:
            return card
    return {}

async def new_client_connected(client_socket, path):
    username = add_player("good", 0)
    local_players_table[username] = {"socket":client_socket}
    await update_state([username])

    #try:
    while True:
        card_json_message = await client_socket.recv()
        card_json = json.loads(card_json_message)
        log("Client sent:", card_json)
        if ("id" in card_json.keys()):
            await handle_play(username,card_json)
        if (card_json.get("command")):
            globals()[card_json["command"]](username)
            if card_json.get("command") == "quit":
                break;
            await update_state(local_players_table.keys())

    #except Exception as e:
    #    log("Client quit:", username)
    #    log(e)
    #    del local_players_table[username]
    #    del players_table[username]

def pause(username):
    log(username + " paused")
    if game_table["running"]:
        game_table["running"] = 0
    else:
        game_table["running"] = 1
def add_random_card(username):
    card_name = get_unique_name()
    baby_card = create_random_card(card_name)
    baby_card = initialize_card(card_name, username)
    players_table[username]["deck"].append(baby_card)

def save_random_cards(username):
    with open('json/cards.json', 'w') as f:
        json.dump(cards_table,f)

def join_evil(username):
    log(username + " joined evil")
    players_table[username]["team"] = "evil"

def join_good(username):
    log(username + " joined good")
    players_table[username]["team"] = "good"

def reset_game(username):
    game_table["loser"] = "good"
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
    log("Player Added: "+username)
    players_table[username] = {"team":team,"ai":ai}
    load_deck(username)
    call_action({"action":"draw", "target":"my_deck3"},{"owner":username})
    return username

async def handle_play(username,card_json):
    team = get_team(username)
    card_id = int(card_json["id"])
    card_index = int(card_json["index"])
    card = card_from(card_id, players_table[username]["hand"])
    if card:
        play_action(card,{"to":card_index})

    await update_state(local_players_table.keys())

async def start_server():
    log("Server started!")
    initialize_teams(teams_list)
    initialize_time()
    await websockets.serve(new_client_connected, "localhost", 12345)

if __name__ == '__main__':
    event_loop = asyncio.get_event_loop()
    event_loop.run_until_complete(start_server())
    event_loop.run_forever()
