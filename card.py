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
#TODO WARN DEAR GOD DO NOT REFACTOR IN A WAY THAT IS NOT BITE SIZED EVER AGAIN
#TODO 
#Fix effects
#Have a random card shop as a rare reward. With end game cards expected to come from random draws.
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
        #Enemies alias is an issue since I cannot specify if it is grouped or not
    #We had [[self], [enemies]] and []
    #What I need is a list of entities each paired with a location. Or many paired to a single location.
    #                       split         joined
    #At this point we have [player1, [player3, player4]]
    #for each of the above I want you to grab all these things [[deck],[discard],[hand,board]]
    #This gives [[p1deck], [p1discard], [p1handboard], [p3deck p4deck], [p3discard p4discard], [p3handboard, p4handboard] ]
    #All these get passed to reduce to give
    # target1 [card card card card card card card] to action
    #For each of these individuals we need locations which can be parallel
    #We just need what to check from them. Reduce will have to deal with the many fors
    #Or we could fetch those locations from each section and combine them to make
    #[[deck],[discard],[hand,board]]
#TRIGGERS
#Could make this a general progress trigger that gets passed an amount eventually
def timer_trigger(timer, card):
    seconds_passed = timer.get("progress")
    print(timer)
    if timer["progress"] >= timer["goal"]:
        timer["progress"] -= timer["goal"]
        for action in timer["actions"]:
            call_action(action, card)
    #The change comes after so the client gets a chance to see the progress
    timer["progress"] += tick_rate()

def standard_trigger(event, card):
    for action in event["actions"]:
        call_action(action, card)

def play_action(action,card):
    #How do I handle default target here?
    targets = targetting(action, card)
    seek(preseek(
    for target in targets:
        username = target["owner"]
        owner = owner_card(username)
        if owner["gold"] >= target["cost"]:
            game_table["running"] = 1
            owner["gold"] -= target["cost"]
            #To should be second target here
            move(target,"board",action["to"])
            #This should really just be in move
            call_triggers(target, "enter")
            #This should really just be in move. Could have a trigger for purchase
            #This function is actually a combo ov value action, logic, and move action. As such it should call the other actions to keep code dry

def discard_action(action, card):
    targets = targetting(action, card)
    for target in targets:
        move(target,"discard")

def diskard_action(action, card):
    targets = targetting(action, card)
    for target in targets:
        move(target,"discard")

def income_action(action, card):
    targets = targetting(action, card)
    for target in targets:
        target["gold"] += action["amount"]
        target["gold"] = max(0, target["gold"])
        target["gold"] = min(target["gold_limit"], target["gold"])
#MAIN FUNCTIONS:
#Effect action, type as parameter, with duration amount etc as parameters
#Play action
#Move action
#Value action, with certain values having checks they run. Like if gold, check gold_limit. If health, check armor effect. Any value check resist effect. If any of these values apply this effect etc. One change function for math values.
#If a card spawns other cards, that is a different story
#Play action would call value action with the amount
#Play is really just play

def draw_action(action, card):
    #refactor this so it's actually targetting the top card
    #need a standard target
    #TAKE ADVANTAGE OF LAST MINUTE TARGETTING for default target
    #targets = targetting(action, card)
    #for target in targets:
    player_data = table("players")[card["owner"]]
    deck = player_data["deck"]
    player_discard = player_data["discard"]
    hand = player_data["hand"]
    for i in range(action["amount"]):
        targets = []
        if not action.get("target"):
        #Maybe have index be a reduce function.
        #Layered targetting. Target 1, target 2. Then defaults on those.
        #Whos
        #Locations
        #Indexes
        #For Whos a 
        #Damage function. Index "card" reduce.
        #draw function. Locations deck, discard
        #target 1. Locations deck, discard. Whos many players. index first 3 
        #What do you run the reduce on. All the players and locations squished. Like most expensive card play to field. Or play all most expensive cards to field. If you put ally-deck in location it puts all ally decks into a list. You could pull from this list the highest card. Or you could pull from
        #target 2. Index "empty" reduce.
        #Location can have
        #Do not do the whole alias thing, just write full targetting for every card then have defaults. Still do the whole alias thing. If you need to change it in the future it means less to change.
        #For draw
        #Ally-decks is a location that would populate
        #target1 {"who":["Nemesis,Friend"], "where":["deck"], "how", "which"}
        #Who returns a couple dicts based on an alias. Checking both teams and players.
        #Who [{[][][][]},{[][][][]},{[][][][]},{[][][][]}]
        #Where [{[]},{[]},{},{[],[]}]
        #How [[]]
        #Which [x,y]
        #Target runs who where how which on action and card. leaving input available to action if desired.
            #for section in how(where(who(targets))):
                #which(section)
                #Do not return a list of cards, return a list of how to find the cards.
                #Then run execute. You could run execute after if you wanted them to see the selected first.
                #Building a shopping list
        #Where returns all sections from all dicts if they contain that section.
        #Just have who and where be lists containing items or lists
        #That way the action knows to split if it wants. Call reduce on each generated list. That is a section of targetting. Removes the need for how.
        #Add handling for location list and who list, as well as nested lists. Add reduce instead of index. Reduce args.
        #This provides a target list or series of lists and items.
        #Do I actually need things like damage now? Since draw just turned into move
            action["target"] = {"location":"deck","who":"card","index":-1}            
        targets = targetting(action, card)
        for target in targets:
            empty_hand_index = get_empty_index(hand)
            if not (empty_hand_index is None):
                move(target,"hand",empty_hand_index)
            if len(deck) <= 0:
                for discarded in player_discard:
                    move(discarded,"deck")
                random.shuffle(deck)
            #Reshuffle if deck empty

def drew_action(action, card):
    targets = targetting(action, card)
    for target in targets:
        empty_hand_index = get_empty_index(hand)
        if not (empty_hand_index is None):
            move(target,"hand",empty_hand_index)

def damage_action(action, card):
    targets = targetting(action, card)[0]
    for target in targets:
        damage = action["amount"] 
        try:
            damage = max(0, damage - target["effects"]["armor"])
        except KeyError:
            print("no armor")
            pass
        target["health"] -= damage

def vampire_action(action, card):
    victims = targetting(action, card)
    monsters = targetting(action, card)
    for victim, monster in zip(victims,monsters):
        steal = action["amount"] 
        victim["health"] -= damage
        monster["health"] += damage
        #Modify value function for damage and health that checks max, checks alive and adds to a cleanup list.
        #Replace below with get effect which searches effect list
        try:
            damage = max(0, damage - target["effects"]["armor"])
        except KeyError:
            print("no armor")
            pass
        target["health"] -= damage

def protect_action(action, card):
    targets = targetting(action, card)[0]
    for target in targets:
        if target["effects"].get("armor"):
            target["effects"]["armor"] += action["amount"]
        else:
            target["effects"]["armor"] = action["amount"]

#TARGETS
#Targetting layers are functions that are named and accept parameters
#Functions like deck 3
#I need a standard target for each action
#Need multiple and nested methods of targetting.
#If you ever need to add args, just add them as a part of the action with the same name like allies_args. Then string fetch them.

#Layers of targetting. Action defaults like draw where 
#Make a dictionary of paths
#Action default location, who and index
#If you don't want default specify.

#May want to have access to all 3 of these steps in actions to optimize. Looking at draw, you could preseek once
def card_target_alias():
    for card, card_data in cards_table.items():
        if action.get("triggers"):
            for trigger, trigger_data in card_data["triggers"].items():
                if trigger.get("actions"):
                    for action in trigger["actions"]:
                        targets = action["target"]
                        if not isinstance(targets, list):
                            targets = [targets]
                        paths = []
                        for target in targets:
                            if type(target) == str:
                                #This is not meant to be here TODO Move to seek
                                paths.append(targets_table[target])
                            elif type(target) == dict:
                                paths.append(target)
                            else:
                               log("OOPSY target isn't string or dict") 
                               log(target) 
                        action["target"] = paths

def weakest_reduce():
    #This could accept a list of targets, then return the one with the least health, so you have target which is a list of cards, then you have reduce which picks from those cards. Gives you a target weakest, or target weakest enemy.
    return

#Many possible locations, board and hand for full discard. Many whos Many locations. You need a who for each location. Have a targetting dict. Which reduce is a dict. containing a function name.
#This all as opposed to having the actions themselves just do all the shit. Including targetting. Would mean an action for every new target type.
#Worst case I can still do things like that.
#
#Why would an action have multiple target dicts? The whole point of many fold entity and locations is that you can target many  in one. What you really get is one target group per target.
#Targetting is designed to take a single target. So the action can call targetting on each of the target lists that it might need.
def targetting(action, card):
    for target_recipe in action["target"]:
        target_planned = zoning(target_recipe, card)
        zones = zoning(target_recipe,target_planned)
        for zone in zones:
            standard_reduce(zone)
    return target_groups

def identify(entity, card):
    result = []
    match entity:
        case "all":
            result.extend(table("entities").values())
        case "self":
            result.append(table("entities")[card["owner"]])
        case "enemies":
            for entity_data in table("entities").values():
                if entity_data["team"] != card["team"]:
                    result.append(entity_data)
        case "allies":
            for entity_data in table("entities").values():
                if entity_data["team"] == card["team"]:
                    result.append(entity_data)
    return result


def find(entity,location,card):
                    if type(location) == str:
                        selected_zones.append(entity[location])
                    elif type(location) == list:
                        for 
                        selected_zones.append(entity[location])
    if location = string
    if location == "card":
        return entity[card["location"]]
    if location == "all":
        return ["location"]
    else:
        return

    return card["location"]

def zoning(target_recipe, card):
    selected_entities = []
    entities = target_recipe["entities"]
    for entity_set in entities:
        if type(entity_set) == str:
                identify(entity_set, card)
        elif type(entity_set) == list:
            sub_selected_entities = []
            for entity in entity_set:
                sub_selected_entities.extend(identify(entity,card))
            selected_entities.append(sub_selected_entities)

    selected_zones = []
    locations = target_recipe["locations"]
    for entity in selected_entities:
        for location in locations:
            if type(entity) == dict:
                selected_zones.extend(find(entity,location,card))
            elif type(entity) == list:
                sub_selected_zones = []
                for ent in entity:
                    sub_selected_zones.extend(find(entity,location,card))
                selected_zones.extend(find(entity,location,card))

    selected_cards = []
    reduce_function = target_recipe["index"]
    reduce_args = target_recipe["args"]
    for zone in selected_zones:
        selected_cards.extend(globals()[reduce_function+"_reduce"](zone, args))
    return selected_cards



def seek(paths):
    #Check if path is a card
    targets = []
    for path in paths:
        if path.get("title"):
            continue
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
            pass
        except IndexError:
            print("INDEX ERROR")
            print(path)
            pass
    return targets

#CORE
def call_triggers(card, event_type):
    events = card["triggers"].get(event_type)
    if events:
        for event in events:
            function_name = event_type + "_trigger";
            if function_name in globals():
                globals()[function_name](event, card)
            else:
                standard_trigger(event, card)

def call_action(action, card):
    function_name = action["action"]+"_action"
    globals()[function_name](action, card)

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
targets_table = load({"file":"json/targets.json"})
card_target_alias(cards_table)
players_default = load({"file":"json/players.json"})
team_default = load({"file":"json/teams.json"})
teams_list = ["good","evil"]
game_table = load({"file":"json/game.json"})
entities_table = game_table["entities"]
local_players_table = {}
current_id = 1

def table(entity_type):
    if entity_type = "entities":
        return entities_table
    result = {}
    for entity, entity_data in entities_table.items():
        if entity_data[entity_type] == "team":
            result[entity] = entity_data
    return result

def saveBattle():
        with open('json/decks.json', 'w') as f:
            json.dump(decks_table,f)

def get_card_index(hand):
    #should get all card indexes than random select
    card_indexes = []
    for index, card in enumerate(hand):
        if card:
            card_indexes.append(index)
    if card_indexes:
        return random.choice(card_indexes)
    else:
        return None

def get_empty_index(board):
    for index, card in enumerate(board):
        if not card:
            return index
    return None

#Back bone of flow
#If index not specified find empty index
#Move action will look for a destination paramater much like amount.
def move(card, to, index = -1):
    card_owner = card["owner"]
    card_location = card["location"]
    player_data = table("players").get(card_owner)
    if to == "board":
        card["team"] = get_team(card_owner)
        table("teams")[card["team"]][to][index] = card
    elif to == "hand":
        if player_data:
            player_data[to][index] = card
    else:
        if player_data:
            player_data[to].append(card)

    if card_location == "board":
        call_triggers(card,"exit")
        table("teams")[card["team"]][card_location][card["index"]] = 0
    elif card_location == "hand":
        if player_data:
            player_data[card_location][card["index"]] = 0
    elif card_location == "deck":
        deck = player_data["deck"]
        player_discard = player_data["discard"]
        if len(deck) <= 0:
            for discarded in player_discard:
                move(discarded,"deck")
            random.shuffle(deck)
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
    for team, team_data in table("teams").items():
        for location, location_data in team_data.items():
            for card in location_data:
                if card:
                    call_triggers(card,"timer")

#Effect tick is really a pre tick.
        #An effect can be applied to a card that is not in play, but it shouldn't be an effect with expiration tick.
        #Effects are a list of dicts with expirations.
        #Get effect looks for all entries of that type.
        #I want to get all items by expiration for fast removal
        #Or all items by type for fast reading.
        #[{"effect":"armor", "duration":"tick", "amount":1, "type":"sum"}]
        #Get effect, calls all the effects in a list
        #Could just do : {"armor":[[1,"tick"]]}
        #You could just have effect apply, then simply on move of the card that is causing effect remove effect. But then where is that list stored. In effected? How do you know which one to remove? You could simply give a pointer out, then on move remove the pointer.
def effect_tick():
    for team, team_data in table("teams").items():
        for location, location_data in team_data.items():
            for card in location_data:
                if card:
                    call_triggers(card,"effect")

#Cleanup is really just a post tick.
def cleanup_tick():
    for team, team_data in table("teams").items():
        for location, cards in team_data.items():
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

def ai_tick():
    #Could be refactored to just run play_action
    for player, player_data in table("players").items():
        if player_data["ai"]:
            hand = player_data["hand"]
            card_from_index = get_card_index(hand)
            card_to_index = get_empty_index(get_board(player))
            if card_from_index is not None and card_to_index is not None:
                card = hand[card_from_index]
                play_action(card, {"to":card_to_index})

async def tick():
    while True:
        await asyncio.sleep(game_table["tick_duration"])
        if game_table.get("reset"):
            game_table["reset"] = 0
            await update_state(local_players_table.keys())
        if game_table["running"]:
            for player in list(table("players")):
                if table("players").get(player).get("quit"):
                    del entities_table[player]
            #Effects happen first since they are things that are removeable. They are added at start, removed at end
            effect_tick()
            location_tick()
            ai_tick()
            await update_state(local_players_table.keys())
            cleanup_tick()

def remove_quit_players(team_data):
    del entities_table[player]

def tick_rate():
    return game_table["tick_duration"]*game_table["tick_value"]

def safe_get(l, idx, default=0): 
    try: 
        return l[idx] 
    except IndexError: 
        return default


def reset_teams():
    for team in list(table("teams").keys()):
        initialize_team(team)

def initialize_team(team):
    game_table["entities"][team] = copy.deepcopy(team_default)
    #Need to add a card to base
    game_table["entities"][team]["team"] = team
    game_table["entities"][team]["base"][0] = initialize_card(team, "", "base",team)

def initialize_teams(teams):
    for team in teams:
        initialize_team(team)

def reset_state():
    reset_teams()
    for username in list(table("players").keys()):
        load_deck(username)
        draw_action({"amount":3},{"owner":username})
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
    table("players")[username].update(copy.deepcopy(players_default))
    deck_to_load = decks_table[deck_type]
    random.shuffle(deck_to_load)
    deck = []
    for card_name in deck_to_load:
        baby_card = initialize_card(card_name, username)
        deck.append(baby_card)
    table("players")[username]["deck"] = deck
    table("players")[username]["discard"] = []
    table("players")[username]["tent"][0] = initialize_card("player", username, "tent")


def is_team(target = ""):
    if target in list(table("teams").keys()):
        return True

async def update_state(players):
    for player in players:
        if player in local_players_table:
            await local_players_table[player]["socket"].send(str({"game_table":game_table,"me":player}))

def strip_keys_copy(keys, table):
    copied_table = copy.deepcopy(table)
    for key in keys:
        copied_table.pop(key, None)

def owner_card(owner):
    return game_table["players"][owner]["tent"][0]

def find_triggers_with_action_name(card, action):
    triggers = []
    for trigger in card["triggers"]:
        for action in trigger["actions"]:
            if "action_name" == action["action"]:
                triggers.append(trigger)
                continue


def get_team(username):
    return table("players")[username]["team"]

def get_board(username):
    return table("teams")[get_team(username)]["board"]

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
    table("players")[username]["deck"].append(baby_card)

def save_random_cards(username):
    with open('json/cards.json', 'w') as f:
        json.dump(cards_table,f)

def join_evil(username):
    log(username + " joined evil")
    table("players")[username]["team"] = "evil"

def join_good(username):
    log(username + " joined good")
    table("players")[username]["team"] = "good"

def reset_game(username):
    game_table["loser"] = "good"
    reset_state()

def add_ai_evil(username):
    add_player("evil",1)

def add_ai_good(username):
    add_player("good",1)

def quit(username):
    table("entities")[username]["quit"] = 1

def remove_ai(username):
    #Needs to mark for removal then remove after tick to avoid issues
    for player, player_data in table("players").items():
        if player_data["ai"]:
            player_data["quit"] = 1

def add_player(team,ai):
    username = "player" + str(get_unique_id())
    log("Player Added: "+username)
    entities_table[username] = {"type":"player","team":team,"ai":ai}
    load_deck(username)
    draw_action({"amount":3},{"owner":username})
    return username

def log(*words):
    for word in words:
        print(word)



async def handle_play(username,card_json):
    team = get_team(username)
    card_id = int(card_json["id"])
    card_index = int(card_json["index"])
    card = card_from(card_id, table("players")[username]["hand"])
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
