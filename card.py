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
#Effects that can use targetting.
#Discard area next to hand
#Removeable triggers added
#Progressive enemies
#Session table and reset
#Start using images on cards
#Shop zone
#Add reset session option.
#Add different armor
#An an enter armor boost like in slay the spire
#Add armor decay?
#When an action finishes, outline the sending card, and  fill in the receiving card

#TODO WARN
#DEAR GOD DO NOT REFACTOR IN A WAY THAT IS NOT BITE SIZED EVER AGAIN
#DEAR GOD DO NOT PLAY GAMES AS RESEARCH IT IS SUCH A WASTE OF TIME

#TODO
#Have damage pass through by default, then certain cards bypass and certain cards do not
#Random start point on the card. Small image. Quick movement. Also death can show skull moving to discard. Deck that you can pay to draw from. Count on it of how many cards are in deck. Count on discard of how many cards in discard.
#Canvas, draw an image that moves from a card to a location. Coin for money. Explosion for damage
#Flavor means it's not automatic and core to the game. It's simply spice on top. So you can send flavor messages. Which will run a gif at a location on the client or play a sound.
#Add the ability to add flavor text, flavor images and flavor tick actions.
#Add some kind of label to the sections. Preferrably images

#Allow one card to be trashed per round
#Readme card
#Flavor text
#Flavor images
#Flavor sound?
#Pop up menu with choices or a map or something
#Events
#This would also allow for a card that reacts to a card being played across from it
#Need triggers that can be subscribed to like on ally cards die. I suppose I could add triggers to ally cards, but that seems weird.
#I would need a place to store subscription functions and parameters, then a way to call that list of functions

#TODO MAYBE
#Add draw button where you can buy draw more cards. This would be done by dragging the tent player to the zone
#Add upgrade card button too maybe?
#Health ticks down version
#Create random cards and allow them to be saved off if good


#TICK
#Maybe balance it so which team is called first in order is randomized
#Do not orgaize this. Let it be chaos
#SHOP

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


#TODO TRIGGERS
#On target action - When a target takes and action.... Specify name of action or category. Handled in trigger function.
#On target trigger - When a target trigger occurs... Specify name of trigger
#On draw triggers so when you draw the card you get money or something. Or you take damage when you draw the card.

#TODO Actions
#Mirror requres action to mirror as argument and does so. Basically trigger handles action

#TODO CARD IDEAS
#Card that freezes income or draw of opponent
#Card that reflects destabilize back at attacker
#Card that deals more damage when hurt
#Pool: income draw slow enemy income, slow enemy draw, protect neighbor cards, better versions of bomb cards. Combined cards, like spike shield. or Spiky bomb. Guardian that adds armor to neighbor cards. Card that increases tick rate of neighbor cards.

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
import argparse
import re
import shlex
import copy
import time
from itertools import takewhile
#Create self destructing trigger flag. Once called it removes itself
#Could make an action that accepts a trigger, then marks it as dead. Overly complicated. Flag is fine
#TARGETS
#Gets a list of card groups for targetting. Target group 1,2,3 etc
# acting({"action": "move", "target": ["my_deck", "my_hand"], "amount": 3}, {"owner": username})

#Should never return 0s
def get_target_groups(action, card):
    #If the action doesn't have a target, quit
    if not action.get("target"):
        log("no target")
        return []

    target_group_aliases = action["target"]
    #If it just wants to target itself, return card
    #if target_group_aliases == "self":
        #return [[card]]
    #If target_group_aliases is just a card
    if type(target_group_aliases) == dict and "id" in target_group_aliases.keys():
        return [[target_group_aliases]]
    #If the list of target aliases is just a single, then put it in a list
    if type(target_group_aliases) != list:
        target_group_aliases = [target_group_aliases]
    target_groups = []
    #For all aliases resolve them.
    #If you want to target append as a destination just cut it off here and return a fake target group that is a dict instead of a list. Dict containing:
    #location, entity, type:append. Or just enitity and location
    for target_group_alias in target_group_aliases:
        target_recipe = resolve_target_group_alias(target_group_alias)
        if "index" not in target_recipe.keys():
            target_recipe["index"] = "all"
        if target_recipe["index"] == "append":
            target_groups.append(target_recipe)
        else:
            target_groups.append(get_target_group(target_recipe, action, card))

    return target_groups

def resolve_target_group_alias(target_group_alias):
    target_group = targets_table[target_group_alias]
    return target_group

#For each target group get cards
def get_target_group(target_recipe, action, card):
    selected_entity_groups = []
    entity_aliases = target_recipe["entity"]
    if type(entity_aliases) != list:
        entity_aliases = [entity_aliases]
    #Main division here is between select from all entities combined zones, or select one from each entity.
    #Entity set could be an alias, or a list of aliases, or a list of actual entities

    for entity_alias in entity_aliases:
        selected_entity_groups.extend(resolve_entity_alias(entity_alias, card))

    #Selected zones is a list of joined or unjoined zones
    selected_zones = []
    location_aliases = target_recipe["location"]
    if type(location_aliases) != list:
        location_aliases = [location_aliases]

    for entity_group in selected_entity_groups:
        joined_entity = {"locations":{}}
        for entity in entity_group:
            for location_key in entity["locations"].keys():
                extend_nested(joined_entity,["locations",location_key], entity["locations"][location_key])
        for location_alias in location_aliases:
            card_zones = resolve_location_alias(joined_entity,location_alias,card)
            selected_zones.extend(card_zones)

    selected_cards = []
    select_function = target_recipe["index"]
    args = target_recipe.get("args")
    for zone in selected_zones:
        selected_cards.extend(get_cards(zone, select_function, args, action, card))
    return selected_cards

def listify(to_listify):
    return [[i] for i in to_listify]

#Returns a list of entity groups, big or size one.
# [[entity1 e2 e3][e2][e3]]
def resolve_entity_alias(entity_alias, card):
    entities = []
    match entity_alias:
        #Aliases handle combined or not
        case "all":
            for entity in table("entities").values():
                entities.append([entity])
        case "all-joined":
            all_entities = list(table("entities").values())
            entities.append(all_entities)
        case "card":
            entities.append([table("entities")[card["entity"]]])
        case "owner":
            entities.append([table("entities")[card["owner"]]])
        case "enemies" | "enemy":
            for entity_data in table("entities").values():
                if entity_data["team"] != card["team"]:
                    entities.append([entity_data])
        case "enemies-joined":
            #Odd that swords hurt themselves if you join enemy team after playing TODO
            enemies = []
            for entity_data in table("entities").values():
                if entity_data["team"] != card["team"]:
                    enemies.append(entity_data)
            entities.append(enemies)
        case "allies" | "ally":
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
#double list of cards
#[[c1 c2 c3][c1][c2]]
def resolve_location_alias(entity, location_alias, card):
    match location_alias:
        case "all":
            locations = list(entity["locations"].values())
            return locations
        case "all_joined":
            locations = [list(entity["locations"].values())]
            joined = sum(locations, [])
            return joined
        case "card":
            if card["location"] in entity["locations"]:
                return [entity["locations"][card["location"]]]
            else:
                return [[]]
        case _:
        #case ["deck","hand"]
            if type(location_alias) != list:
                location_alias = [location_alias]
            combined_zone = []
            for location in location_alias:
                if location in entity["locations"]:
                    combined_zone.extend(entity["locations"][location])
            return [combined_zone]

#Returns a list of cards from the zone
#Needs the zone, index function and args
def get_cards(zone, select_function, args, action, card):
    #Aborts if zone is empty
    if not zone:
        return []
    #Removes empty from zones to select from
    actual_zone = [i for i in zone if i]
    match select_function:
        case "all":
            return actual_zone
        case "random":
            return [random.choice(actual_zone)]
        case "random-slot":
            selection = random.choice(zone)
            if selection:
                return [selection]
            else:
                return []
        case "card":
            if card["index"] < len(zone) and zone[card["index"]]:
                return [zone[card["index"]]]
            else:
                return []
        case "fork":
            indices = [card["index"]-1,card["index"],card["index"]+1]
            result = []
            for index in indices:
                if index < len(zone) and zone[index]:
                    result.append(zone[index])
            return result
        case "neighbors":
            indices = [card["index"]-1,card["index"]+1]
            result = []
            for index in indices:
                if index < len(zone) and zone[index]:
                    result.append(zone[index])
            return result
        case "amount":
            amount = action["amount"]
            return actual_zone[-amount:]
        case _:
        #Case for if an literal index is passed
            return [zone[select_function]]

#TRIGGERS
#How do I handle other triggers like on base hurt. Or on anything dies. Or on purchase
#I can add a trigger event
#Call triggering on dispatch, with the card as a subscription argument. Do this on enter or on card initialization? When should a card subscribe?
#Global triggers can look at every card each time on trigger. Or you need a subscribe on enter and unsubscribe on exit
#For now it can just look at cards on the board
def triggering(card, event_type):
    events = card["triggers"].get(event_type)
    if events:
        for event in events:
            match event_type:
                case "timer":
                    timer = event
                    seconds_passed = timer.get("progress")
                    if timer["progress"] >= timer["goal"]:
                        timer["progress"] -= timer["goal"]
                        for action in timer["actions"]:
                            acting(action, card)
                    #The change comes after so the client gets a chance to see the progress
                    timer["progress"] += tick_rate()
                    #
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

    return data.get(keys[-1])

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

def acting(action, card =""):
    targets = get_target_groups(action, card)
    destinations = action.get("to")
    #try:
    match action["action"]:
        case "play":
            for played in targets[0]:
                username = played["owner"]
                captain = owner_card(username)
                if captain["gold"] >= played["cost"]:
                    game_table["running"] = 1
                    captain["gold"] -= played["cost"]
                    destination = destinations
                    move(played,destination)
        case "move":
            #Move is a great example. What the real functions need are a couple targets and parameters
            #Each target is either a path or a card.
            cards = targets[0]
            destination = destinations
            #If destination is just append to entities location, no need to zip
            for card in cards:
                move(card,destination)
        #Card to trash
        case "trash":
            #Move is a great example. What the real functions need are a couple targets and parameters
            #Each target is either a path or a card.
            cards = targets[0]
            #If destination is just append to entities location, no need to zip
            for card in cards:
                move(card,destination)
        case "effect_relative":
            # end trigger stored on casting card
            #{"action": "effect-relative", "target": ["my_base"], "effect_function":{"name":"armor","function":"add","value":1}, "end_trigger":"exit"}
            effect_function = action["effect_function"]
            target = action["target"]
            effect = {"effect_function":effect_function,"target":target, "card_id":card["id"], "id": get_unique_id()}
            game_table["ids"][effect["id"]] = effect
            append_nested(card,["triggers",action["end_trigger"]],{"actions": [{"action":"remove_effect","effect_id":effect["id"]}]})
            game_table["all_effect_recipes"].append(effect)
        case "effect_target":
            # end trigger stored on effected card
            effect_function = action["effect_function"]
            target = action["target"]
            #For all of the targets of this action, add the effect
            for target_groups in get_target_groups(target,card):
                for target_group in target_groups:
                    for targetted_card in target_group:
                        effect = {"effect_function": effect_function, "target": [targetted_card], "id":get_unique_id()}
                        game_table["ids"][effect["id"]] = effect
                        append_nested(targetted_card, ["triggers", action["end_trigger"]],{"action": "remove_effect", "effect_id": effect["id"]})
                        game_table["all_effect_recipes"].append(effect)
                        #No card below since the targets are evaluated upfront
        case "effect_positional":
            #Need to add a trigger somewhere that can remove the effect
            effect_function = action["effect_function"]
            target = action["target"]
            effect = {"effect_function":effect_function,"target":target, "id":get_unique_id()}
            game_table["ids"][effect["id"]] = effect
            #You would need to add a card to game events with just the trigger for removal
            append_nested(game_table,["entities","situation","events"],
                             {
                                       "triggers": {
                                           action["end_trigger"]: [
                                               {"actions": [
                                                   {"action": "remove_effect", "effect_id": effect["id"]}
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
            all_effect_recipes.remove(game_table["ids"][action["effect_id"]])
            del game_table["ids"][action["effect_id"]]
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
                #Maybe have this set the image too
                damage = action["amount"]
                animations.append({"sender": card, "receiver":victim, "size":damage, "image":"pics/bang.png"})
                armor = get_effect("armor", victim)
                remaining_shield = negative_remaining_damage = victim["shield"] - damage
                victim["shield"] = max(remaining_shield, 0)
                damage = -1 * negative_remaining_damage
                damage = max(0, damage - armor)
                victim["health"] -= damage
        case "shield":
            victims = targets[0]
            for victim in victims:
                shield = action["amount"]
                animations.append({"sender": card, "receiver":victim, "size":shield, "image":"pics/energyshield2.png"})
                victim["shield"] += shield
                victim["shield"] = min(victim["shield"],victim["max_shield"])
        case "income":
            recipients = targets[0]
            for recipient in recipients:
                recipient["gold"] += action["amount"]
                recipient["gold"] = max(0, recipient["gold"])
                recipient["gold"] = min(recipient["gold_limit"], recipient["gold"])
        case _:
            log("Not sure what action that is:")
            log(action["action"])
    #except IndexError:
        #log("TARGETS NOT AVAILABLE")


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
    acting({"action": "clean", "target": ["all"]})
    all_effect_recipes = game_table["all_effect_recipes"]
    all_effect_recipes.sort(key=effect_sort_func)
    for effect_recipe in all_effect_recipes:
        for target_list in get_target_groups(effect_recipe, game_table["ids"].get(effect_recipe["card_id"])):
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
    animations.append({"sender": card, "receiver": card, "size": 4, "image": "pics/skull.png"})
    acting({"action": "move", "target": card, "to": {"entity":"owner","location": "discard", "index": "append"}},
           card)

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
animations = []
default_session_table = {"ais":{},"players":{},"teams":{"good":{"losses":0},"evil":{"losses":0}},"send_reset":1, "level":1, "max_level":5, "first":1, "reward":1}
session_table = copy.deepcopy(default_session_table)
random_table = load({"file":"json/random.json"})
decks_table = load({"file":"json/decks.json"})
cards_table = load({"file":"json/cards.json"})
targets_table = load({"file":"json/targets.json"})
static_lists = ["hand","board","tent","base","trash","shop"]
game_table = load({"file":"json/game.json"})
current_id = 1

def table(entity_type):
    if entity_type == "entities":
        return game_table["entities"]
    result = {}
    for entity, entity_data in game_table["entities"].items():
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


def get_random_empty_index(board):
    # Find all indices where the card is empty (falsy)
    empty_indices = [index for index, card in enumerate(board) if not card]

    # If there are no empty indices, return None
    if not empty_indices:
        return None

    # Randomly select one of the empty indices
    return random.choice(empty_indices)

def get_path(path):
    try: 
        return game_table[path["entity"]][path["location"]][path["index"]]
    except IndexError: 
        log("Invalid destination")
        log(card)
        log(to)

def update_path(path, card):
    log("up")

def move(card, to):
    card_was = card["location"]
    card_is = to["location"]
    move_defaults(card,to)
    move_card(card,to)
    move_triggers(card,to,card_was,card_is)

def move_defaults(card, to):
    if "entity" not in to.keys():
        print(card["owner"])
        to["entity"] = card["owner"]
    if "location" not in to.keys():
        to["location"] = card["location"]
    if "index" not in to.keys():
        to["index"] = card["index"]

#Cards are actual cards
#Tos are empty spaces, they can be more vague
def move_card(card, to):
    to_entity = to["entity"]
    if to_entity == "owner":
        to_entity = card["owner"]
    to_location = get_nested(game_table, ["entities", to_entity, "locations", to["location"]])
    card_location = get_nested(game_table, ["entities", card["entity"], "locations", card["location"]])
    to_static = to["location"] in static_lists
    card_static = card["location"] in static_lists
    card_index = card.get("index")
    if to["index"] == "append":
        #To an array
        if to_static:
            if to_location is not None:
                to_available = get_empty_index(to_location)
                #If there's an empty slot
                if to_available is not None:
                    to_location[to_available] = card
                    #Add index
                    card["index"] = to_available
        #To a list
        else:
            if to_location is not None:
                to_location.append(card)
            #Remove index
            if "index" in card.keys():
                del card["index"]
    elif to["index"] == "random":
        if to_location is not None:
            to_available = get_random_empty_index(to_location)
            # If there's an empty slot
            if to_available is not None:
                to_location[to_available] = card
                # Add index
                card["index"] = to_available
    # Index is actual number
    else:
        if to_location is not None:
            if to_location[to["index"]]:
                #If card at location, discard it
                move(to_location[to["index"]],{"location":"discard","index":"append"})
                #acting({"action": "move", "target": to_location[to["index"]],
                        #"to": {"location": "discard", "index": "append"}})

            to_location[to["index"]] = card
        if to_static:
            card["index"] = to["index"]
        else:
            if "index" in card.keys():
                del card["index"]
    if card_static:
        card_location[card_index] = 0
    else:
        card_location.remove(card)

    card["location"] = to["location"]
    card["entity"] = to_entity

#Hmm this shouldn't be called after updating the card location
def move_triggers(card, to, card_was, card_is):
    card_location = card_was
    to_location = card_is
    if to_location == "board" and card_location != "board":
        card["team"] = get_team(card["owner"])
        triggering(card, "enter")
    if card_location == "board" and to_location != "board":
        triggering(card,"exit")
    elif card_location == "deck":
        card_owner = card["owner"]
        player_data = table("players").get(card_owner)
        deck = player_data["locations"]["deck"]
        discard = player_data["locations"]["discard"]
        if len(deck) <= 0:
            for discarded in discard:
                move(discarded,{"location":"deck","index":"append"})
            random.shuffle(deck)
    if to_location == "discard":
        refresh_card(card)

def location_tick():
    for team, team_data in table("teams").items():
        for location, location_data in team_data["locations"].items():
            for card in location_data:
                if card:
                    triggering(card,"timer")
                    #Decay shield
                    if card.get("shield"):
                        shield = max(card["shield"]-(math.sqrt(card["shield"])*tick_rate()+0.2)/10,0)
                        card["shield"] = shield

#Cleanup is really just a post tick.
def cleanup_tick():
    for team, team_data in table("teams").items():
        for location, cards in team_data["locations"].items():
            for card in cards:
                if card:
                    card["effects"] = {}
                    if card["health"] <= 0:
                        if card["location"] == "base":
                            session_table["teams"][get_team(card["owner"])]["losses"] += 1
                            if get_team(card["owner"]) == "evil":
                                if session_table["level"] < session_table["max_level"]:
                                    session_table["reward"] = 1
                                    session_table["level"] += 1
                                reset_state()
                            else:
                                #session_table["level"] -= 1
                                reset_state()
                        else:
                            kill_card(card)

def ai_tick():
    #Could be refactored to just run play_action
    for player, player_data in table("players").items():
        if player_data["ai"]:
            acting(
                {"action": "play", "target": ["my_hand"], "to": {"entity":player_data["team"],"location": "board", "index": "random"}, "amount": 1}
                ,{"owner":player}
            )

async def tick():
    while True:
        await asyncio.sleep(game_table["tick_duration"])
        if session_table.get("send_reset"):
            session_table["send_reset"] = 0
            await update_state(session_table["players"].keys())
        if game_table["running"]:
            for player in list(table("players")):
                if table("players").get(player).get("quit"):
                    del game_table["entities"][player]
            #Effects happen first since they are things that are removeable. They are added at start, removed at end
            effecting()
            location_tick()
            ai_tick()
            await update_state(session_table["players"].keys())
            cleanup_tick()

def remove_quit_players(team_data):
    del game_table["entities"][player]

def tick_rate():
    return game_table["tick_duration"]*game_table["tick_value"]

def safe_get(l, idx, default=0): 
    try: 
        return l[idx] 
    except IndexError: 
        return default

def initialize_situation():
    set_nested(game_table,["entities","situation"],{"team":"gaia","type":"gaia","locations":{"events":[]}})

def initialize_team(team):
    set_nested(game_table,["entities",team],
               {"type": "team",
                "team": team,
                "locations": {
                    "base": [0],
                    "board": [
                        0, 0, 0, 0, 0
                    ]
                }
                }
               )
    base_card = ""
    if team == "evil":
        #Plus level if you want upgrading team
        #game_table["entities"][team]["locations"]["base"][0] = initialize_card(team+session_table["level"], team, "base")
        game_table["entities"][team]["locations"]["base"][0] = initialize_card(team, team, "base",0)
    else:
        game_table["entities"][team]["locations"]["base"][0] = initialize_card(team, team, "base",0)

def initialize_player(team,ai,username, deck="beginner"):
    #Session needs to hold players/entities, not ais and players.
    deck_to_load = []
    if ai:
        session_table["ais"][username] = {"team":team,"ai":ai}
        deck = "ai"+str(session_table["level"])
        deck_to_load = decks_table[deck]
    else:
        if session_table["players"][username].get("deck"):
            deck_to_load = session_table["players"][username]["deck"]
        else:
            deck_to_load = decks_table[deck]
            copied_deck = copy.deepcopy(deck_to_load)
            # This way shop can add cards to a players recurring deck
            session_table["players"][username]["deck"] = copied_deck

    game_table["entities"][username] = {
        "type":"player",
        "team":team,
        "ai":ai,
        "gold": 10,
        "gold_limit": 50,
        "locations": {
            "hand": [
                0,0,0,0,0
            ],
            "deck": [],
            "discard": [],
            "shop": [0,0,0],
            "trash": [0],
            "tent": [
                0
            ]
        }
    }
    #Initialize some cards to the shop on player startup
    #baby_card = initialize_card(card_name, username)
    if session_table["reward"]:
        shop_deck = decks_table["shop"+str(session_table["level"])]
        random.shuffle(shop_deck)
        for index, slot in enumerate(game_table["entities"][username]["locations"]["shop"]):
            if index < len(shop_deck):
                game_table["entities"][username]["locations"]["shop"][index] = initialize_card(shop_deck[index], username, "shop",index)
    load_deck(username, deck_to_load)

    acting({"action":"move", "target": "my_deck", "to": {"location": "hand", "index": "append"}, "amount": 3},
           {"owner": username})



def initialize_teams():
    for team in session_table["teams"].keys():
        initialize_team(team)

def initialize_players():
    for username, value in session_table["players"].items():
        initialize_player(value["team"],0,username)
    session_table["reward"] = 0

def initialize_ais():
    for username, value in session_table["ais"].items():
        initialize_player(value["team"],1,username)

def initialize_game():
    initialize_situation()
    initialize_teams()
    initialize_players()
    initialize_ais()

def reset_state():
    #Clear game
    session_table["send_reset"] = 1
    global game_table
    game_table = load({"file": "json/game.json"})
    #Progress game from session data
    initialize_game()
    session_table["send_reset"] = 1

def get_unique_id():
    global current_id
    current_id += 1
    return str(current_id)

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
        card["shield"] = 0
        card["max_shield"] = 20
    except KeyError:
        pass

def initialize_card(card_name,username="",location="deck",index=-1):
    baby_card = copy.deepcopy(cards_table[card_name])
    if not("title" in baby_card.keys()):
        baby_card["title"] = card_name
    baby_card["name"] = card_name
    if username:
        baby_card["owner"] = username
        baby_card["entity"] = username
    if index >= 0:
        baby_card["index"] = index

    baby_card["team"] = get_team(username)
    baby_card["id"] = get_unique_id()
    baby_card["shield"] = 0
    baby_card["max_shield"] = 20
    game_table["ids"][baby_card["id"]] = baby_card
    baby_card["location"] = location
    refresh_card(baby_card)
    return baby_card

#Need an add card
def load_deck(username, deck_to_load):
    random.shuffle(deck_to_load)
    deck = []
    for card_name in deck_to_load:
        baby_card = initialize_card(card_name, username)
        deck.append(baby_card)
    set_nested(table("players"),[username,"locations","deck"], deck)
    set_nested(table("players"),[username,"locations","discard"], [])
    get_nested(table("players"),[username,"locations","tent"])[0] = initialize_card("player", username, "tent", 0)

def is_team(target = ""):
    if target in list(table("teams").keys()):
        return True

async def update_state(players):
    effecting()
    global animations
    for player in players:
        if player in session_table["players"]:
            out_table = copy.deepcopy(game_table)
            out_table["players"] = table("players")
            out_table["teams"] = table("teams")
            text = session_table["teams"]
            await session_table["players"][player]["socket"].send(str({"text":text,"game_table":out_table,"me":player,"animations":animations}))
    animations = []

def strip_keys_copy(keys, table):
    copied_table = copy.deepcopy(table)
    for key in keys:
        copied_table.pop(key, None)

def owner_card(owner):
    return game_table["entities"][owner]["locations"]["tent"][0]

def find_triggers_with_action_name(card, action):
    triggers = []
    for trigger in card["triggers"]:
        for action in trigger["actions"]:
            if "action_name" == action["action"]:
                triggers.append(trigger)
                continue

def get_team(username):
    return game_table["entities"][username]["team"]

def get_board(username):
    return table("teams")[get_team(username)]["locations"]["board"]

def get_enemy_team(team): 
    if team == "evil":
        return "good"
    else: 
        return "evil"

def initialize_time():
    timer_handle = asyncio.create_task(tick())

def print_json(json_message):
    #no_circ = remove_circular_refs(copy.deepcopy(json_message))
    log(json.dumps(
        json_message,
        sort_keys=True,
        indent=4,
        separators=(',',':')
    ))
def log_json(json_message):
    #no_circ = remove_circular_refs(copy.deepcopy(json_message))
    log(json.dumps(
        json_message,
        sort_keys=True,
        indent=4,
        separators=(',',':')
    ))

def remove_circular_refs(ob, _seen=0):
    if _seen == 0:
        _seen = set()
    if id(ob) in _seen:
        # circular reference, remove it.
        return 0
    _seen.add(id(ob))
    res = ob
    if isinstance(ob, dict):
        res = {
            remove_circular_refs(k, _seen): remove_circular_refs(v, _seen)
            for k, v in ob.items()}
    elif isinstance(ob, (list, tuple, set, frozenset)):
        res = type(ob)(remove_circular_refs(v, _seen) for v in ob)
    # remove id again; only *nested* references count
    _seen.remove(id(ob))
    return res

def card_from(card_id, cards):
    for card in cards:
        if card and card_id == card["id"]:
            return card
    return {}

async def new_client_connected(client_socket, path):
    username = "player" + get_unique_id()
    if session_table["first"]:
        session_table["first"] = 0
        ainame = "ai" + get_unique_id()
        initialize_player("evil",1,ainame)
    session_table["players"][username] = {"socket":client_socket, "team":"good"}
    initialize_player("good", 0, username)
    await update_state([username])

    try:
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
                await update_state(session_table["players"].keys())

    except websockets.ConnectionClosed as e:
        log("Client quit:", username)
        log(e)
        if session_table["players"].get(username):
            del session_table["players"][username]
        if game_table["entities"].get(username):
            del game_table["entities"][username]

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
    session_table["players"][username]["team"] = "evil"

def join_good(username):
    log(username + " joined good")
    table("players")[username]["team"] = "good"
    session_table["players"][username]["team"] = "good"

def reset_game(username):
    reset_state()

def reset_session(username):
    global session_table
    session_table = copy.deepcopy(default_session_table)
    reset_state()

def win_game(username):
    session_table["reward"] = 1
    session_table["teams"]["evil"]["losses"] += 1
    if session_table["level"] < session_table["max_level"]:
        session_table["level"] += 1
    reset_state()

def add_ai_evil(use):
    username = "ai" + get_unique_id()
    initialize_player("evil",1,username)

def add_ai_good(use):
    username = "ai" + get_unique_id()
    initialize_player("good",1,username)

def quit(username):
    table("entities")[username]["quit"] = 1

def remove_ai(username):
    #Needs to mark for removal then remove after tick to avoid issues
    for player, player_data in table("players").items():
        if player_data["ai"]:
            player_data["quit"] = 1
            del session_table["ais"][player]


def log(*words):
    for word in words:
        print(word)

async def handle_play(username,card_json):
    card_id = card_json["id"]
    card_index = int(card_json["index"])
    card_to = card_json["location"]
    # Get card from id
    card = game_table["ids"].get(card_id)
    if not card:
        return
    card_from = card["location"]
    team = get_team(username)
    if card_to == "trash" and card_from == "hand":
        acting({"action": "trash", "target": card })

    if card_to == "board" and card_from == "hand":
        if not game_table["entities"][team]["locations"]["board"][card_index]:
            acting({"action": "play", "target": card, "to": {"entity":team, "location":"board", "index": card_index}})
    if card_to == "discard" and card_from == "hand":
        acting({"action": "move", "target": card, "to": {"entity":card["owner"],"location":"discard", "index": "append"}})
    if card_to == "hand":
        if card_from == "shop":
            acting({"action": "move", "target": card, "to": {"entity":card["owner"],"location":"hand", "index": card_index}})
            #TODO, obliterate the leftover cards so they are removed from the card dict. Technically they are still in the shop.
            session_table["players"][username]["deck"].append(card["title"])
            game_table["entities"][card["owner"]]["locations"]["shop"] = [0,0,0]

    await update_state(session_table["players"].keys())

#There's also a full log in javascript message container
def game_log(username):
    log_json(game_table)
    #for key, value in game_table.items():
    #    if type(value) == dict:
    #        print(key,value)
    #    if type(value) == dict:
    #        print(key,value)


async def start_server():
    log("Server started!")
    reset_state()
    initialize_time()
    await websockets.serve(new_client_connected, "localhost", 12345)

if __name__ == '__main__':
    event_loop = asyncio.get_event_loop()
    event_loop.run_until_complete(start_server())
    event_loop.run_forever()
