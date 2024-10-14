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
#EFFECTS
#Effects global and card based with triggers. Effects contain a target if global. Effects are calculated before round and applied to cards
#Handle defence effect not working if card was spawned in during play. This would simply be a matter of applying effect to card while it's in hand

#TRIGGER
#Creation of triggers that disappear after one use
#Maybe an N times trigger? Uses attribute on triggers
#Then a trigger flag that says no really, remove this after it's used for tracking effects

#EVENTS
#Need triggers that can be subscribed to like on ally cards die. I suppose I could add triggers to ally cards, but that seems weird.
#I would need a place to store subscription functions and parameters, then a way to call that list of functions

#TICK
#Maybe balance it so which team is called first in order is randomized
#Do not orgaize this. Let it be chaos

#DISCARD

#SHOP

#Health ticks down version


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
#Create self destructing trigger flag. Once called it removes itself
#Could make an action that accepts a trigger, then marks it as dead. Overly complicated. Flag is fine
#TARGETS
def resolve_target_group_alias(target_group_alias):
    target_group = targets_table[target_group_alias]
    return target_group

#Gets a list of card groups for targetting. Target group 1,2,3 etc
# acting({"action": "move", "target": ["my_deck", "my_hand"], "amount": 3}, {"owner": username})
def get_target_groups(action, card):
    #If the action doesn't have a target, quit
    if not action.get("target"):
        print("no target")
        return []

    target_group_aliases = action["target"]
    #If the list of target aliases is just a single, then put it in a list
    if type(target_group_aliases) != list:
        print("no list")
        target_group_aliases = [target_group_aliases]
    target_groups = []
    #For all aliases resolve them.
    for target_group_alias in target_group_aliases:
        target_recipe = resolve_target_group_alias(target_group_alias)
        print("Started from the bottom")
        print_json(target_recipe)
        print_json(action)
        print_json(card)
        target_groups.append(get_target_group(target_recipe, action, card))
    return target_groups

#For each target group get cards
def get_target_group(target_recipe, action, card):
    selected_entity_groups = []
    entity_aliases = target_recipe["entities"]
    if type(entity_aliases) != list:
        entity_aliases = [entity_aliases]
    #Main division here is between select from all entities combined zones, or select one from each entity.
    #Entity set could be an alias, or a list of aliases, or a list of actual entities
    for entity_alias in entity_aliases:
        selected_entity_groups.extend(resolve_entity_alias(entity_alias, card))

    print("hmm")
    print_json(selected_entity_groups)

    #Selected zones is a list of joined or unjoined zones
    selected_zones = []
    location_aliases = target_recipe["locations"]
    if type(location_aliases) != list:
        print("enlist")
        location_aliases = [location_aliases]
    for entity_group in selected_entity_groups:
        #This joined entity does not have a hand
        joined_entity = {"locations":{}}
        for entity in entity_group:
            #DO A JOIN entities here, so it's one entity, then you can do below
            for location_key in entity["locations"].keys():
                print("llave")
                print(location_key)
                extend_nested(joined_entity,["locations",location_key], entity["locations"][location_key])
        print("united")
        print_json(joined_entity)
        for location_alias in location_aliases:
            card_zones = resolve_location_alias(joined_entity,location_alias,card)
            selected_zones.extend(card_zones)

    selected_cards = []
    select_function = target_recipe["cards"]
    args = target_recipe.get("args")
    for zone in selected_zones:
        #Slot level effects
        #Make zones a list of slots instead of a list of cards
        #I would be adding slots, which is a lot of complexity, just for what? Easier time coding targetting?
        #You could just instead have select return a card with {"index":index, "location",`}
        selected_cards.extend(get_cards(zone, select_function, args, action, card))
    return selected_cards

def listify(to_listify):
    return [[i] for i in to_listify]

#Returns a list of entity groups, big or size one.
def resolve_entity_alias(entity_alias, card):
    entities = []
    match entity_alias:
        #Aliases handle combined or not
        case "all":
            all_entities = listify(table("entities").values())
            entities.extend(all_entities)
        case "all-joined":
            all_entities = [table("entities").values()]
            entities.append(all_entities)
        case "self" | "card":
            entities.append([table("entities")[card["owner"]]])
        case "enemies":
            for entity_data in table("entities").values():
                if entity_data["team"] != card["team"]:
                    entities.append([entity_data])
        case "enemies-joined":
            enemies = []
            for entity_data in table("entities").values():
                if entity_data["team"] != card["team"]:
                    enemies.append(entity_data)
            entities.append(enemies)
        case "allies":
            for entity_data in table("entities").values():
                if entity_data["team"] == card["team"]:
                    entities.append([entity_data])
        case "allies-joined":
            allies = []
            for entity_data in table("entities").values():
                if entity_data["team"] == card["team"]:
                    allies.append(entity_data)
            entities.append(allies)
    return entities

#Returns a list of joined or separate card lists which will be selected from
def resolve_location_alias(entity, location_alias, card):
    match location_alias:
        case "all":
            return [listify(entity["locations"].values())]
        case "all_joined":
            return [entity["locations"].values()]
        case "card":
            return [entity["locations"][card["location"]]]
        case _:
            #acting({"action": "move", "target": ["my_deck", "my_hand"], "amount": 3}, {"owner": username})
            return [entity["locations"][location_alias]]

#Returns a list of cards from the zone
#Needs the zone, index function and args
def get_cards(zone, select_function, args, action, card):
    match select_function:
        case "all":
            return zone
        case "random":
            return [random.choice(zone)]
        case "card":
            return [card]
        case "amount":
            amount = action["amount"]
            print("amount")
            print(amount)
            print(zone)
            print(zone[-amount:])
            return zone[-amount:]

#TRIGGERS
#How do I handle other triggers like on base hurt. Or on anything dies. Or on purchase
#I can add a trigger event
#Call triggering on dispatch, with the card as a subscription argument. Do this on enter or on card initialization? When should a card subscribe?
#Global triggers can look at every card each time on trigger. Or you need a subscribe on enter and unsubscribe on exit
def triggering(card, event_type):
    events = card["triggers"].get(event_type)
    if events:
        for event in events:
            match event_type:
                case "timer":
                    seconds_passed = timer.get("progress")
                    if timer["progress"] >= timer["goal"]:
                        timer["progress"] -= timer["goal"]
                        for action in timer["actions"]:
                            acting(action, card)
                    #The change comes after so the client gets a chance to see the progress
                    timer["progress"] += tick_rate()
                case _:
                    for action in event["actions"]:
                        acting(action, card)
            if event.get("once"):
                events.remove(event)

def get_nested(data, keys):
    for key in keys[:-1]:
        if key not in data or not isinstance(data[key], dict):
            return None
        data = data[key]

    return data[keys[-1]]

def set_nested(data, keys, value):
    for key in keys[:-1]:
        if key not in data or not isinstance(data[key], dict):
            data[key] = {}
        data = data[key]

    data[keys[-1]] = value

def try_nested(data, keys, value):
    for key in keys[:-1]:
        if key not in data or not isinstance(data[key], dict):
            return
        data = data[key]

    data[keys[-1]] = value

def append_nested(data, keys, value):
    for key in keys[:-1]:
        if key not in data or not isinstance(data[key], dict):
            data[key] = {}
        data = data[key]

    if data.get(keys[-1]):
        data[keys[-1]].append(value)
    else:
        data[keys[-1]] = [value]

def extend_nested(data, keys, value):
    for key in keys[:-1]:
        if key not in data or not isinstance(data[key], dict):
            data[key] = {}
        data = data[key]

    if data.get(keys[-1]):
        data[keys[-1]].extend(value)
    else:
        data[keys[-1]] = value

def acting(action, card):
    targets = get_target_groups(action, card)
    #Targets will be many lists of tuples with paired lists and indexes
    match action["action"]:
        case "play":
            for played, play_to in zip(targets[0], targets[1]):
                username = played["owner"]
                captain = owner_card(username)
                if captain["gold"] >= played["cost"]:
                    game_table["running"] = 1
                    captain["gold"] -= played["cost"]
                    move(played,play_to)
        case "move":
            #Move is a great example. What the real functions need are a couple targets and parameters
            #Each target is either a path or a card.
            print("pre-game")
            print_json(targets[0])
            print_json(targets[1])
            for played, play_to in zip(targets[0], targets[1]):
                print_json(played)
                print_json(play_to)
                move(played,play_to)
        # {"action": "effect-relative", "target": ["my_base"], "effect_function":{"name":"armor","function":"add","value":1}, "end_trigger":"exit", "end_holder":"me"}}
        # end trigger stored on casting card
        case "effect_relative":
            effect_function = action["effect_function"]
            target = action["target"]
            effect = {"effect_function":effect_function,"target":target,"card":card}
            append_nested(card,["triggers",action["end_trigger"]],{"action":"remove_effect","effect":effect})
            game_table["all_effect_recipes"].append(effect)
        # end trigger stored on effected card
        case "effect_target":
            effect_function = action["effect_function"]
            target = action["target"]
            #For all of the targets of this action, add the effect
            for target_groups in get_target_groups(target,card):
                for target_group in target_groups:
                    for targetted_card in target_group:
                        effect = {"effect_function": effect_function, "target": [targetted_card], "card": ""}
                        append_nested(targetted_card, ["triggers", action["end_trigger"]],{"action": "remove_effect", "effect": effect})
                        game_table["all_effect_recipes"].append(effect)
                        #No card below since the targets are evaluated upfront
            #Need to add a trigger somewhere that can remove the effect
        case "effect_positional":
            effect_function = action["effect_function"]
            target = action["target"]
            effect = {"effect_function":effect_function,"target":target,"card":card}
            #You would need to add a card to game events with just the trigger for removal
            append_nested(game_table,["entities","situation","events"],
                             {
                                       "triggers": {
                                           action["end_trigger"]: [
                                               {"actions": [
                                                   {"action": "remove_effect", "effect": effect}
                                               ]}
                                           ]
                                       }
                                   })
            game_table["all_effect_recipes"].append(effect)
        case "clean":
            recipients = targets[0]
            for recipient in recipients:
                recipient["effects"] = {}
        case "remove_effect":
            all_effect_recipes = game_table["all_effect_recipes"]
            all_effect_recipes.remove(action["effect"])
        case "vampire":
            victims = targets[0]
            monsters = targets[1]
            for victim, monster in zip(victims,monsters):
                steal = action["amount"]
                victim["health"] -= steal
                monster["health"] += steal
                #Modify value function for damage and health that checks max, checks alive and adds to a cleanup list.
                #Modify value also handles effects
                #Replace below with get effect which searches effect list
                damage = max(0, steal - get_effect("armor",victim))
                victim["health"] -= steal
        case "damage":
            victims = targets[0]
            for victim in victims:
                damage = action["amount"]
                damage = max(0, damage - ["armor"])
                victim["health"] -= damage
        case "income":
            recipients = targets[0]
            for recipient in recipients:
                recipient["gold"] += action["amount"]
                recipient["gold"] = max(0, recipient["gold"])
                recipient["gold"] = min(recipient["gold_limit"], recipient["gold"])


#Goes through list of effects and makes a dict which can be referenced by index and effect to get effect a list of operations which can be done to get value
def effect_sort_func(effect_recipe):
    match effect_recipe["effect_function"]["function"]:
        case "add":
            return 0
        case "multiply":
            return 1
        case "max":
            return 2
        case "min":
            return 2

def effecting():
    #Not that expensive, could just be run every time get_effect is called. If it's a performance problem, then just move it to pre tick
    #The fact that effects is a list means you cannot calculate just one card. Can't sort by affected card though since targets can have multiple
    acting({"action": "clean", "target": ["all"]}, {"owner": username})
    all_effect_recipes = game_table["all_effect_recipes"]
    all_effect_recipes.sort(key=effect_sort_func)
    for effect_recipe in all_effect_recipes:
        for target_list in targetting(effect_recipe, effect_recipe["card"]):
            for target in target_list:
                add_effect(effect_recipe["effect_function"],target)

def add_effect(effect_function, card):
    effects = card["effects"]
    effect_name = effect_function["name"]
    if effect_function["function"] == "add":
        if effects.get(effect_name):
            effects[effect_name] += effect_function["value"]
        else:
            effects[effect_name] = effect_function["value"]

    if effect_function["function"] == "multiply":
        if effects.get(effect_name):
            effects[effect_name] *= effect_function["value"]

    if effect_function["function"] == "max":
        if effects.get(effect_name):
            effects[effect_name] = max(effects[effect_name],effect_function["value"])

    if effect_function["function"] == "min":
        if effects.get(effect_name):
            effects[effect_name] = min(effects[effect_name],effect_function["value"])

def get_effect(effect_to_get, card):
    effecting()
    effect_value = get_nested(card, ["effects",effect_to_get])
    if not effect_value:
        effect_value = 0
    return effect_value

#MAIN FUNCTIONS:
#Effect action, type as parameter, with duration amount etc as parameters
#Play action
#Move action
#Value action, with certain values having checks they run. Like if gold, check gold_limit. If health, check armor effect. Any value check resist effect. If any of these values apply this effect etc. One change function for math values.
#If a card spawns other cards, that is a different story
#Play action would call value action with the amount
#Play is really just play


#Maybe make this an action?
def kill_card(card):
    move(card,{"location":"discard"})

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
players_default = load({"file":"json/players.json"})
team_default = load({"file":"json/teams.json"})
teams_list = ["good","evil"]
game_table = load({"file":"json/game.json"})
entities_table = game_table["entities"]
local_players_table = {}
current_id = 1

def table(entity_type):
    if entity_type == "entities":
        return entities_table
    result = {}
    for entity, entity_data in entities_table.items():
        if entity_data["type"] + "s" == entity_type:
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

def get_path(path):
    try: 
        return game_table[path["entity"]][path["location"]][path["index"]]
    except IndexError: 
        log("Invalid destination")
        log(card)
        log(to)

def assign_path(path, card):
    #I do not need set nested since a spot needs to exist for a card
    #try_nested(game_table,[path["entity"],path["location"],path["index"]],card)
    try:
        game_table[path["entity"]][path["location"]][path["index"]] = card
    except IndexError:
        log("Invalid destination")
        log(card)
        log(to)

def update_path(path, card):
    card["entity"] = path["entity"]
    card["location"] = path["location"]
    card["index"] = path["index"]

#Need a way to handle 0s
def move(card, to):
    #Check if "to" string allow for defaults
    print("up to")
    print(card)
    print(to)
    if not to.get("location"):
        to["location"] = card["location"]
    if not to.get("entity"):
        to["entity"] = card["entity"]
    if not to.get("index"):
        to["index"] = card["index"]
    card_location = card["location"]
    assign_path(to,card)
    if to["location"] == "board" and card_location != "board":
        triggering(card, "enter")
    if card_location == "board":
        triggering(card,"exit")
    elif card_location == "deck":
        card_owner = card["owner"]
        player_data = table("players").get(card_owner)
        deck = player_data["deck"]
        discard = player_data["discard"]
        if len(deck) <= 0:
            for discarded in discard:
                move(discarded,{"location":"deck"})
            random.shuffle(deck)
    if to == "discard":
        refresh_card(card)
    update_path(path,card)


def location_tick():
    for team, team_data in table("teams").items():
        for location, location_data in team_data.items():
            for card in location_data:
                if card:
                    triggering(card,"timer")

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

def initialize_situation():
    set_nested(game_table,["entities","situation"],{"type":"gaia","events":[]})

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
        acting({"action":"move","target":["my_deck","my_hand"],"amount":1},{"owner":username})
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
    set_nested(table("players"),[username,"locations","deck"], deck)
    set_nested(table("players"),[username,"locations","discard"], [])
    get_nested(table("players"),[username,"locations","tent"])[0] = initialize_card("player", username, "tent")

def is_team(target = ""):
    if target in list(table("teams").keys()):
        return True

async def update_state(players):
    for player in players:
        if player in local_players_table:
            out_table = copy.deepcopy(game_table)
            out_table["players"] = table("players")
            out_table["teams"] = table("teams")
            await local_players_table[player]["socket"].send(str({"game_table":out_table,"me":player}))

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

def print_json(json_message):
    print(json.dumps(
        json_message,
        sort_keys=True,
        indent=4,
        separators=(',',':')
    ))

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
        if "id" in card_json.keys():
            await handle_play(username,card_json)
        if card_json.get("command"):
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
    table("players")[username]["locations"]["deck"].append(baby_card)

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
    entities_table[username] = {"type":"player","team":team,"ai":ai,"locations":{}}
    load_deck(username)
    acting({"action":"move","target":["my_deck","my_hand"],"amount":1},{"owner":username})
    return username

def log(*words):
    for word in words:
        print(word)

async def handle_play(username,card_json):
    team = get_team(username)
    card_id = int(card_json["id"])
    card_index = int(card_json["index"])
    card = card_from(card_id, table("players")[username]["locations"]["hand"])
    if card:
        play_action(card,{"to":card_index})

    await update_state(local_players_table.keys())

async def start_server():
    log("Server started!")
    initialize_situation()
    initialize_teams(teams_list)
    initialize_time()
    await websockets.serve(new_client_connected, "localhost", 12345)

if __name__ == '__main__':
    event_loop = asyncio.get_event_loop()
    event_loop.run_until_complete(start_server())
    event_loop.run_forever()
