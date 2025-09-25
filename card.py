#!/usr/bin/env python
#TODO
#Phone go hot. performance wize getBounding rect seems the culprit, or the size of json messages. Fix with static slots that are known to canvas after a resize, or updates that modify state with a hash instead of resetting it.
#You need a slot dict to handle slot level effects, and for storing cards and for generally making the one card one place(plus id table) rule true. Slots that disappear then reapear are confusing.
#The armor bunny number when hyped rolls over
#The discard beaver isn't working.
#Summon turtle should allow cards to be loadable. Or they should just be loadable.
#Some effect I think wasn't happening. Traffic turtle was not showing

#TODO TODONE

#TODO WARN
#DEAR GOD DO NOT REFACTOR IN A WAY THAT IS NOT BITE SIZED EVER AGAIN
#DEAR GOD DO NOT PLAY GAMES AS RESEARCH IT IS SUCH A WASTE OF TIME

#TODO MAYBE
#Play a cancel card with cancel beaver that adds cards across
#Or make attacks have scorched earth.
#Play a progress card that steps up active cooldowns.

#With slots, I could make them have health and when they take too much damage they
#Basic costs 0 slow health card for blocking
#Have kill effect cards mark cards instead of needing kill shots.
#Zoom buttons update CSS scale variable

#Readme card/ button people can click for a general explanation

#Add rooms
#Have glass cards that are used once then they trash themselves.
#make some kind of campaign co-op. Maybe just the versus ai.


#When a main action is identified, you can have a generic amount, speed, health, cost, hype. Hype could even tie into one of these traits for any given card. Or random trait temporarily?
#Hype the main action since you know what it is.
#Set 3 main stats, power, speed and health? Speed includes cooldown and how many times something triggers. Power changes trigger effect and storage size? Healths is well... health.
#Set up a way to indicate if power is being used with amount or if amount is flat. Something like goal - power * scaling shouldn't be undoable
#Power adds hmmm
#Speed increase rate of progress
#AI
#Add keeping health between rounds vs ai.
#Events
#This would also allow for a card that reacts to a card being played across from it
#Need triggers that can be subscribed to like on ally cards die. I suppose I could add triggers to ally cards, but that seems weird.
#I would need a place to store subscription functions and parameters, then a way to call that list of functions
#Add draw button where you can buy draw more cards. This would be done by dragging the tent player to the zone
#Add upgrade card button too maybe?
#Health ticks down version
#Create random cards and allow them to be saved off if good


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
#Card that deals a lot of damage to all cards, but stays for a while and is expensive. It even kills your own.
#Weaken, opposite of armor
#Pool: income draw slow enemy income, slow enemy draw, protect neighbor cards, better versions of bomb cards. Combined cards, like spike shield. or Spiky bomb. Guardian that adds armor to neighbor cards. Card that increases tick rate of neighbor cards.

#DON'T USE ORDERED DICT SINCE YOU CAN'T CHOOSE INSERTION POINT. JUST USE A LIST WITH REFERENCES TO A MEGA DICT

import asyncio
from collections import Counter
import websockets
from websockets.exceptions import ConnectionClosedOK
import sys
import requests
import functools
import os
import json
from fractions import Fraction
from operator import itemgetter, truediv
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
#Gets a list of card groups for targeting. Target group 1,2,3 etc
# acting({"action": "move", "target": ["my_deck", "my_hand"], "amount": 3}, {"owner": username})

#Should never return 0s
def quick_alias(target, card, result):
    if not target:
        log("no target")
        result["message"] = "target field empty"
        return result

    # If it just wants to target itself, return card
    if target == "self":
        slot = get_nested(game_table, ["entities", card["entity"], "locations", card["location"]])[card["index"]]
        result["slots"] = [slot]
        result["cards"] = [card]
        result["message"] = "self"
        return result

    # If target_group_aliases is just a card
    if type(target) == dict and target.get("exist"):
        a_card = target
        slot = None
        actual_slot = get_nested(game_table, ["entities", a_card["entity"], "locations", a_card["location"]])
        if actual_slot:
            slot = actual_slot[a_card["index"]]
        result["slots"] = [slot]
        result["cards"] = [a_card]
        result["message"] = "card"
        return result

    if target == "on_me":
        # If you cannot do this correctly you need to return them to discard
        # remove empty slots
        on_it = []
        for slot in card["storage"]:
            if slot:
                on_it.append(game_table["ids"].get(slot))
        result["message"] = "on_it"
        result["cards"] = on_it
        result["slots"] = []
        return result

    return False



def targeting(target, action, card):
    result = {"slots":[], "cards":[], "message":"default"}

    quick_return = quick_alias(target, card, result)
    if quick_return:
        return quick_return

    if type(target) is str:
        target = targets_table[target]
    return get_target_group(target, action, card, result)


#For each target group get cards
def get_target_group(target, action, card, result):
    entity_alias = ""
    if target.get("entity"):
        entity_aliases = target["entity"]
    else:
        entity_aliases = card["owner"]

    #list of entities, if not a list make it one.
    if type(entity_aliases) != list:
        entity_aliases = [entity_aliases]

    entities = []
    for entity_alias in entity_aliases:
        resolved = resolve_entity_alias(entity_alias, card)
        entities.extend(resolved)
    result["entities"] = entities

    #Selected zones is a list of joined or unjoined zones
    #All joined
    locations = target["location"]
    if type(locations) != list:
        locations = [locations]
    result["locations"] = locations

    slots = []
    for entity in entities:
        for location in locations:
            #Keep adding the slots
            #Should have a flat list of slots [slot1, slot2, slot3entity2, slot4entity2]
            slots.extend(resolve_location_alias(entity,location,card))
    result["slots-pre"] = slots

    if "index" not in target.keys():
        target["index"] = "all"

    select_function = target["index"]
    result["index"] = select_function

    result["slots"] = get_slots(slots, select_function, action, card)

    if "spot" not in target.keys():
        target["spot"] = "first"
    result["cards"] = get_cards(result["slots"], target["spot"], action, card)

    return result

def resolve_entity_alias(entity_alias, card):
    entities = []
    match entity_alias:
        case "all":
            all_entities = list(table("entities").values())
            entities.extend(all_entities)
        case "card":
            entities.append(table("entities")[card["entity"]])
        case "owner":
            entities.append(table("entities")[card["owner"]])
        case "loser":
            winning_team = get_winner(card)
            for entity_data in table("entities").values():
                if winning_team and entity_data["team"] == get_enemy_team(winning_team):
                    entities.append(entity_data)
        case "winner":
            winning_team = get_winner(card)
            for entity_data in table("entities").values():
                    if entity_data["team"] == winning_team:
                        entities.append(entity_data)
        case "enemies" | "enemy":
            for entity_data in table("entities").values():
                if entity_data["team"] != card["team"]:
                    entities.append(entity_data)
        case "allies" | "ally":
            for entity_data in table("entities").values():
                if entity_data["team"] == card["team"]:
                    entities.append(entity_data)
    #Entity is the alias
        case _:
            entities.append(table("entities")[entity_alias])
    return entities

#Returns a list of joined or separate card lists which will be selected from
#double list of cards
#[[c1 c2 c3][c1][c2]]
def resolve_location_alias(entity, location_alias, card):
    match location_alias:
        case "all":
            locations = list(entity["locations"].values())
            slots = []
            for location in locations:
                slots.extend(location)
            return slots
        case "card":
            slots = []
            if card["location"] in entity["locations"]:
                slots.extend(entity["locations"][card["location"]])
            return slots
        case _:
            slots = []
            location = location_alias
            if location in entity["locations"]:
                slots.extend(entity["locations"][location])
            return slots

#Returns a list of cards from the zone
#Needs the zone, index function and args
#Maybe have a miss section that gets generated here?
def get_cards(slots, select_function, action, card):
    result = []
    match select_function:
        case "all":
            for slot in slots:
                result.extend(slot["cards"])
        case "first":

            for slot in slots:
                if slot["cards"]:
                    result.append(slot["cards"][0])
        case "amount":
            for slot in slots:
                power = math.floor(get_power(action, card))
                result.extend(slot["cards"][:power])
        case _:
            log("nothing")
    return result

def get_slots(slots, select_function, action, card):
    #Aborts if zone is empty
    result = []
    if not slots:
        return result
    #Removes empty from zones to select from

    #actual_zone = [i for i in zone if exist(i)]
    match select_function:
        case "all":
            return slots
        case "random":
            return [random.choice(slots)]
        case "card":
            if card["index"] < len(slots):
                return [slots[card["index"]]]
            else:
                return []

        case "fork":
            indices = [card["index"]-1,card["index"],card["index"]+1]
            for index in indices:
                if index < len(slots):
                    result.append(slots[index])
            return result

        case "neighbors":
            indices = [card["index"]-1,card["index"]+1]
            for index in indices:
                if index < len(slots):
                    result.append(slots[index])
            return result

        case "amount":
            power = math.floor(get_power(action,card))
            return slots[:power]
        case "amount-vacant":
            power = math.floor(get_power(action,card))
            selected_slots = []
            count = 0
            for index, slot in enumerate(slots):
                if count < power:
                    if not slot["cards"]:
                        count += 1
                        selected_slots.append(slot)
            return selected_slots
        case "amount-any":
            power = math.floor(get_power(action,card))
            return slots[:power]
        case "append":
            for slot in slots:
                if not slot["cards"]:
                    return [slot]
            return [slots[0]]
        case _:
        #Case for if an literal index is passed
            return [slots[select_function]]

#TRIGGERS
#How do I handle other triggers like on base hurt. Or on anything dies. Or on purchase
#I can add a trigger event
#Call triggering on dispatch, with the card as a subscription argument. Do this on enter or on card initialization? When should a card subscribe?
#Global triggers can look at every card each time on trigger. Or you need a subscribe on enter and unsubscribe on exit
#For now it can just look at cards on the board
def triggering(card, event_type):
    events = ""
    try:
        events = card["triggers"].get(event_type)
    except KeyError:
        log("failed card")
        log(card)
        log(event_type)
    if events:
        for event in events:
            match event_type:
                case "timer":
                    timer = event
                    when = []
                    if timer.get("when"):
                        when = timer.get("when")
                    else:
                        when = ["board","tent","stall","auction","base"]
                    #When is a way to have timers only tick in certain areas
                    if card["location"] not in when:
                        continue;

                    if timer["progress"] >= timer["goal"]:
                        timer["progress"] -= timer["goal"]
                        for action in timer["actions"]:
                            acting(action, card)
                    #The change comes after so the client gets a chance to see the progress

                    speed = 1 + get_effect("speed", card)
                    timer["progress"] += tick_rate() * speed
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

def get_power(action, card):
    power = 0
    if action.get("allbid"):
        for team, bid in card["bid"].items():
            power += bid
    if action.get("amount"):
        power += action["amount"]
    if card and exist(card):
        if card.get("hype"):
            power += card["hype"] * card["scaling"]
        if card.get("level"):
            power += card["level"] * card["scaling"]
    return power

def get_winner(card):
    winning_team = ""
    best_bid = 0
    for team, bid in card["bid"].items():
        if bid == best_bid:
            winning_team = ""
        if bid > best_bid:
            winning_team = team
            best_bid = bid
    return winning_team

def checking(action, card):
    #Will need to change once multiple check start.
    for check in action["checks"]:
        match check:
            case "has_storage":
                if card["storage"][0]:
                    return True
                else:
                    return False
            case "has_across":
                has_across = any_exist(targeting({"target":"across"}, action, card)[0])
                if has_across:
                    return True
                else:
                    return False
            case "no_across":
                has_across = any_exist(targeting({"target":"across"}, action, card)[0])
                if has_across:
                    return False
                else:
                    return True
    return True

def acting(action, card =""):
    #Target groups should return both a list of slots targeted and further, a list of the contents of those slots
    targets = targeting(action.get("target"), action, card)
    slot_targets = []
    target_groups = []
    if targets:
        slot_targets = targets["slots"]
        target_groups = targets["cards"] #card_targets

    tos = targeting(action.get("to"), action, card)
    destinations = []
    card_tos = []
    if tos:
        destinations = tos["slots"] #slot_tos
        card_tos = tos["cards"]

    power = get_power(action,card)

    if action.get("checks") and not checking(action,card):
        return 0
    #try:
    match action["action"]:
        case "play":
            for played in target_groups:
                username = played["owner"]
                captain = owner_card(username)
                if captain["gold"] >= played["cost"]:
                    game_table["running"] = 1
                    captain["gold"] -= played["cost"]
                    destination = destinations[0]
                    move(played,destination)

        case "bid":
            prizes = target_groups
            for prize in prizes:
                username = card["owner"]
                captain = owner_card(username)
                if captain["gold"] >= card["cost"]:
                    game_table["running"] = 1
                    captain["gold"] -= card["cost"]
                    acting({"action": "move", "target": card, "to": {"entity":"owner","location": "discard", "index": "append"}}, card)
                    prize["bid"][get_team(card["owner"])] += card["cost"]

        case "buy":
            for shop_copy in target_groups:
                username = destinations[0]["entity"]
                captain = owner_card(username)
                if captain["gems"] >= shop_copy["value"]:
                    #session_table["players"][username]["deck"].append(shop_copy["title"])
                    animations.append(
                        {"sender": shop_copy, "receiver": game_table["entities"][username]["locations"]["tent"][0]["cards"][0],
                         "size": 1, "image": "pics/" + shop_copy["title"] + ".png"})

                    game_table["running"] = 1
                    captain["gems"] -= shop_copy["value"]
                    init_card(shop_copy["name"],
                                    destinations[0]["entity"], destinations[0]["location"],
                                    destinations[0]["index"])
        case "move":
            victims = target_groups
            if not destinations:
                return
            for index, victim in enumerate(victims):
                destination = destinations[index]
                move(victim,destination)
                if destination["location"] == "hand":
                    animations.append({"sender": card, "receiver": victim, "size": 1, "image": "pics/cards.png"})

        case "random_select":
            global random_deck
            victims = target_groups
            random.shuffle(random_deck)
            for victim in victims:
                victim["random"] = random_deck[0]
                for index, icon in enumerate(victim["ricons"]):
                    if icon == "random":
                        victim["icons"][index] = random_deck[0]
        case "create":
            #Need a to section and a move maybe?
            victims = target_groups
            what = action["what"]
            if card.get("random"):
                what = card["random"]

            for i in range(math.floor(power)):
                for victim in victims:
                    init_card(what, victim["owner"], "deck", "append")
                    #animations.append({"sender": card, "receiver": owner_card(username), "size": 1, "image": "pics/cards.png"})

        case "place":
            #Need a to section and a move maybe?
            what = action["what"]
            if exist(card) and card.get("random"):
                what = card["random"]

            my_board = get_nested(game_table, ["entities", get_team(card["owner"]), "locations", destinations[0]["location"]])
            for i in range(math.floor(power)):
                #This needs to check valid index
                for slot in my_board:
                   if not slot["exist"] :
                       init_card(what,
                                                 get_team(card["owner"]), destinations[0]["location"],
                                                 destinations[0]["index"], card["owner"])
                       break
                       #animations.append({"sender": card, "receiver": owner_card(username), "size": 1, "image": "pics/cards.png"})

        case "duplicate":
            cards = target_groups
            username = card["owner"]
            for i in range(math.floor(power)):
                for ca in cards:
                    init_card(ca["name"], username, "deck", "append")
                    animations.append({"sender": card, "receiver": owner_card(username), "size": 1, "image": "pics/cards.png"})

        case "trash":
            cards = target_groups
            #If destination is just append to entities location, no need to zip
            for card in cards:
                #FIXIT
                to =  {"entity": "owner", "location": "trash", "index": "append"}
                move(card,to)

        case "obliterate":
            cards = target_groups
            for card in cards:
                #card type to obliterate
                card_type = card["title"]
                all_cards = targeting({"target":"all"}, action, card)
                for target_group in all_cards:
                    for ca in target_group:
                        if ca.get("title") == card_type:
                            # FIXIT
                            to =  {"entity": "owner", "location": "trash", "index": "append"}
                            move(ca,to)

        case "effect_relative":
            # Following comment is the end trigger stored on casting card
            #{"action": "effect-relative", "target": ["my_base"], "effect_function":{"name":"armor","function":"add","value":1}, "end_trigger":"exit"}
            effect_function = action["effect_function"]
            if effect_function.get("value"):
                effect_function["value"] += get_power(action,card)
            target = action["target"]
            effect = {"effect_function":effect_function,"target":target, "card_id":card["id"], "id": get_unique_id()}
            game_table["ids"][effect["id"]] = effect
            #I think this is not happening properly A
            append_nested(card,["triggers",action["end_trigger"]],{"actions": [{"action":"remove_effect","effect_id":effect["id"]}]})
            game_table["all_effect_recipes"].append(effect)

        case "empty_storage":
            victims = target_groups
            victim = victims[0]
            storage = victim.get("storage")
            if storage:
                for index, slot in enumerate(storage):
                    storage[index] = ""

        case "upgrade":
            victims = target_groups
            #If destination is just append to entities location, no need to zip
            for victim in victims:
                if victim["level"] < victim["max_level"]:
                    victim["level"] += power
                if victim.get("values"):
                    for index, value in enumerate(victim["values"]):
                        if value:
                            victim["real_values"][index] = get_power({"amount":float(round(victim["values"][index],1))},victim)

        case "empower":
            victims = target_groups
            for victim in victims:
                if victim["hype"] < victim["max_hype"]:
                    victim["hype"] += action["amount"]
                if victim.get("values"):
                    for index, value in enumerate(victim["values"]):
                        if value:
                            victim["real_values"][index] = get_power({"amount":float(round(victim["values"][index],1))},victim)

        case "abduct":
            victims = target_groups
            #If destination is just append to entities location, no need to zip
            killer = game_table["ids"][card["killer"]]
            for victim in victims:
                #FIXIT
                to =  {"entity": killer["owner"], "location": "discard", "index": "append"}
                move(victim,to)
                #Get Owned!
                possess_card(victim, killer["owner"])

        case "hype":
            victims = target_groups
            #If you are storing a card that has it's own storage, clear that storage.
            for victim in victims:
                if card.get("storage"):
                    acting({"action": "move", "target": "on_me",
                            "to": {"entity": card["owner"], "location": "discard", "index": "append"}},card)
                storage = victim.get("storage")
                if storage:
                    for index, slot in enumerate(storage):
                        if not slot:
                            storage[index] = card["id"]
                            acting({"action": "move", "target": card,
                                    "to": {"entity": card["owner"], "location": "held", "index": "append"}})
                            break
                else:
                    if not card["title"] == "wood-card":
                        hype = action["amount"]
                        #Permanent hype
                        #if card.get("hype"):
                            #hype += card.get("hype")

                        acting({"action": "empower", "target": victim, "amount":hype}, card)
                        acting({"action": "move", "target": card, "to": {"entity":"owner","location": "discard", "index": "append"}}, card)

                ## end trigger stored on effected card
                #effect_function = action["effect_function"]
                #target = action["target"]
                ##For all the target_groups of this action, add the effect
                #for target_groups in get_target_groups(target,card):
                #    for target_group in target_groups:
                #        for targetted_card in target_group:
                #            effect = {"effect_function": effect_function, "target": [targetted_card], "id":get_unique_id()}
                #            game_table["ids"][effect["id"]] = effect
                #            append_nested(targetted_card, ["triggers", action["end_trigger"]],{"action": "remove_effect", "effect_id": effect["id"]})
                #            game_table["all_effect_recipes"].append(effect)
                #            #No card below since the target_groups are evaluated upfront
        case "effect_target":
            effect_function = action["effect_function"]
            target = action["target"]
            #For all of the target_groups of this action, add the effect
            for target_groups in targeting(target, action, card):
                for target_group in target_groups:
                    for targetted_card in target_group:
                        effect = {"effect_function": effect_function, "target": [targetted_card], "id":get_unique_id()}
                        game_table["ids"][effect["id"]] = effect
                        append_nested(targetted_card, ["triggers", action["end_trigger"]],{"action": "remove_effect", "effect_id": effect["id"]})
                        game_table["all_effect_recipes"].append(effect)
                        #No card below since the target_groups are evaluated upfront
        case "effect_positional":
            #Need to add a trigger somewhere that can remove the effect
            effect_function = action["effect_function"]
            target = action["target"]
            effect = {"effect_function":effect_function,"target":target, "id":get_unique_id()}
            game_table["ids"][effect["id"]] = effect
            #You would need to add a card to game events with just the trigger for removal
            goal = action.get("goal") if action.get("goal") else 1
            append_nested(game_table,["entities","situation","events"],
                             {
                                       "triggers": {
                                           action["end_trigger"]: [
                                               {"goal": goal, "progress":0, "actions": [
                                                   {"action": "remove_effect", "effect_id": effect["id"]}
                                               ]}
                                           ]
                                       }
                                   })
            game_table["all_effect_recipes"].append(effect)
        case "clean":
            recipients = target_groups
            for recipient in recipients:
                recipient["effects"].clear()
        case "remove_effect":
            all_effect_recipes = game_table["all_effect_recipes"]
            all_effect_recipes.remove(game_table["ids"][action["effect_id"]])
            del game_table["ids"][action["effect_id"]]

        case "damage":
            victims = target_groups
            for victim in victims:
                #Maybe have this set the image too
                damage = power
                animations.append({"sender": card, "receiver":victim, "size":damage, "image":"pics/bang.png"})
                if exist(victim):
                    armor = get_effect("armor", victim)
                    remaining_shield = negative_remaining_damage = victim["shield"] - damage

                    victim["shield"] = max(remaining_shield, 0)
                    damage = -1 * negative_remaining_damage
                    damage = max(0, damage - armor)
                    if not victim.get("health"):
                        log("hitting that which cannot be hit !!!!!!!!!!")
                        log(victim)
                        log(card)
                        log(action)
                    victim["health"] -= damage
                    if victim["health"] <= 0 and action.get("kill"):
                        victim["killer"] = card["id"]
                        victim["kill"] = action["kill"]
        case "shield":
            victims = target_groups
            for victim in victims:
                shield = power
                animations.append({"sender": card, "receiver":victim, "size":shield, "image":"pics/energyshield2.png"})
                victim["shield"] += shield
                victim["shield"] = min(victim["shield"],victim["max_shield"])
        case "income":
            recipients = target_groups
            for recipient in recipients:
                recipient["gold"] += power
                recipient["gold"] = max(0, recipient["gold"])
                recipient["gold"] = min(recipient["gold_limit"], recipient["gold"])
                if action["amount"] > 0:
                    animations.append({"sender": card, "receiver": recipient, "size": power, "image": "pics/coin3.png"})
                else:
                    animations.append({"sender": card, "receiver": recipient, "size": power, "image": "pics/theft.png"})

        case "accelerate":
            recipients = target_groups
            for recipient in recipients:
                goals = find_goals_with_action_name({"action":action["what"]}, recipient)
                for goal in goals:
                    goal["progress"] += power
                #animations.append({"sender": card, "receiver":recipient, "size":power, "image":"pics/speed.png"})

        case "finish":
            recipients = target_groups
            for recipient in recipients:
                goals = find_goals_with_action_name({"action":action["what"]}, recipient)
                for goal in goals:
                    goal["progress"] = goal["goal"]
                animations.append({"sender": card, "receiver":recipient, "size":power, "image":"pics/speed.png"})

        case "gems":
            recipients = target_groups
            #Maybe refactor so that recipient also has a missed section returned in another list
            for recipient in recipients:
                animations.append({"sender": card, "receiver":recipient, "size":action["amount"], "image":"pics/gem.png"})
                recipient["gems"] += power
                recipient["gems"] = max(0, recipient["gems"])
                recipient["gems"] = min(recipient["gems_limit"], recipient["gems"])
        case "trader":
            next_trader = action.get("next")
            session_table["trader_level"] += 0.35
            init_trader(next_trader)
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
    acting({"action": "clean", "target": "all"})
    all_effect_recipes = game_table["all_effect_recipes"]
    all_effect_recipes.sort(key=effect_sort_func)
    for effect_recipe in all_effect_recipes:
        for card in targeting(effect_recipe["target"],  "action",game_table["ids"].get(effect_recipe["card_id"]))["cards"]:
            add_effect(effect_recipe["effect_function"],card)

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
    if card.get("kill"):
        animations.append({"sender": card, "receiver": card, "size": 4, "image": "pics/trash.png"})
        kill = card["kill"]
        acting({"action": kill, "target": card},
               card)
    else:
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
#Run update on all rooms with sessions instead of just on players in single session
rooms_table = {}
default_session_table = {"ais":{},"players":{},"teams":{"good":{"losses":0},"evil":{"losses":0}},"send_reset":1, "level":1, "campaign":0,"max_level":2, "first":1, "reward":1, "trader_level":5, "trader":4, "max_trader":5}
session_table = copy.deepcopy(default_session_table)
random_table = load({"file":"json/random.json"})
decks_table = load({"file":"json/decks.json"})
random_deck = decks_table["trader1"] + decks_table["trader2"] + decks_table["trader3"] + decks_table["trader4"] + decks_table["trader5"]
cards_table = load({"file":"json/cards.json"})
targets_table = load({"file":"json/targets.json"})
static_lists = ["hand","board","tent","base","shop","auction"]
game_table = load({"file":"json/game.json"})
table_table = {"session":session_table, "game":game_table, "current_id": 1}

#Save and load button for user and session.
#If user was active in this session, possess.
#If user was saved but not active, load and possess.
#If user was saved and ist active, reject request.
#If user does not exist, save
#def save_deck(name,message):

#def load_deck(name, message):

def save_game(command):
    with open('json/save.json', 'w') as f: #+message["save"]+'.json', 'w') as f:
        json.dump(table_table, f, default = lambda o: '<not serializable>')

def load_game(command):
    #Might need something to wait till end of tick so the game state isn't influenced by what was running
    save = load({"file": 'json/save.json'}) #'+message["save"]+'.json'})
    global session_table
    global game_table
    global table_table
    session_table = save["session"]
    game_table = save["game"]
    #You could make this easier by having the tables be
    table_table["current_id"] = save["current_id"]

def table(entity_type):
    if entity_type == "entities":
        return game_table["entities"]
    result = {}
    for entity, entity_data in game_table["entities"].items():
        if entity_data["type"] + "s" == entity_type:
            result[entity] = entity_data
    return result


#def fetch_slot():
#def fetch_card():
def location_tick():
    tick_slots = []
    for team, team_data in table("teams").items():
        for location in list(team_data["locations"].values()):
            tick_slots.extend(location)

    #Make this clearer
    stall = get_nested(game_table, ["entities", "trader", "locations", "stall"])[0]
    auction = get_nested(game_table, ["entities", "trader", "locations", "auction"])[0]
    tick_slots.append(auction)
    tick_slots.append(stall)

    for player, player_data in table("players").items():
        tent_slot = player_data["locations"]["tent"][0]
        tick_slots.append(tent_slot)
        discard_slot = player_data["locations"]["discard"][0]
        tick_slots.append(discard_slot)

    for slot in tick_slots:
        for card in slot["cards"]:
            if exist(card):
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
                if exist(card):
                    #Memory cleanup
                    if location == "trash":
                        del game_table["ids"][card["id"]]
                    if card["health"] <= 0:
                        if card["location"] == "base":
                            session_table["teams"][get_team(card["owner"])]["losses"] += 1
                            #This needs to be able to target only one player instead of going global
                            animations.append(
                                {"size": 15, "image": "pics/" +  "defeat.png", "team":get_team(card["owner"]),"rate":0.008})
                            animations.append(
                                {"size": 15, "image": "pics/" +  "win.png", "team":get_enemy_team(get_team(card["owner"])),"rate":0.008})
                            if get_team(card["owner"]) == "evil":
                                if session_table["level"] < session_table["max_level"]:
                                    session_table["reward"] = 1
                                    # Versus workaround
                                    if session_table["campaign"]:
                                        session_table["level"] += 1
                                reset_state()
                            else:
                                #session_table["level"] -= 1
                                reset_state()
                        else:
                            kill_card(card)
            # Memory cleanup
            if location == "trash":
                del location[:]

def ai_tick():
    for player, player_data in table("players").items():
        if player_data["ai"]:
            acting(
                {"action": "play", "target": ["my_hand"], "to": {"entity":player_data["team"],"location": "board", "index": "random"}, "amount": 1}
                ,{"owner":player}
            )
            #acting({"action": "buy", "target": ["random_shop"], "to": {"entity":player,"location":"discard", "index": "append"}})

async def tick():
    while True:
        start_tick = time.perf_counter()
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

        end_tick = time.perf_counter()
        duration_tick = end_tick - start_tick
        await asyncio.sleep(game_table["tick_duration"]-duration_tick-0.01)

def tick_rate():
    return game_table["tick_duration"]*game_table["tick_value"]




def safe_get(l, idx, default=0):
    try: 
        return l[idx] 
    except IndexError: 
        return default


def reset_state():
    #Clear game
    session_table["send_reset"] = 1
    global game_table
    game_table = load({"file": "json/game.json"})
    #Progress game from session data
    init_game()
    session_table["send_reset"] = 1

def get_unique_id():
    table_table["current_id"] += 1
    return str(table_table["current_id"])

def get_unique_name():
    cards_table["current_name"] += 1
    return cards_table["current_name"]

###INITIALIZE###
def init_team(team):
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
    init_slots(team)

    #Slots will store a path to this
    #locations_copy = copy.deepcopy(get_nested(game_table,["entities",team,"locations"]))
    #set_nested(game_table,["entities",team,"slots"], locations_copy)

    base_card = ""
    if team == "evil":
        #Plus level if you want upgrading team
        init_card(team+str(session_table["level"]), team, "base",0)
    else:
        init_card(team, team, "base",0)

def init_slots(entity):
    #locations_copy = copy.deepcopy(get_nested(game_table,["entities",entity,"locations"]))
    #set_nested(game_table,["entities",entity,"slots"], locations_copy)
    for location_name,location in get_nested(game_table,["entities",entity,"locations"]).items():
        for index, card in enumerate(location):
            if not card:
                location[index] = init_slot(entity,location_name, index)

def init_slot(entity,location_name,index):
    slot = {
        "entity": entity,
        "location": location_name,
        "index": index,
        "exist": 0,
        "owner": entity,
        "effects": {},
        "id": get_unique_id(),
        "cards":[]
    }
    game_table["ids"][slot["id"]] = slot
    return slot

def init_player(team,ai,username, deck="beginner"):
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
        deck_to_load = decks_table["beginner"]

    #Workaround for vs mode
    game_table["entities"][username] = {
        "type":"player",
        "team":team,
        "ai":ai,
        "locations": {
            "hand": [
                0,0,0,0,0
            ],
            "deck": [0],
            "discard": [0],
            #If I want shop on each player instead of one for everyone this is a start. Individual shops would be best for rpg style.
            "shop": [0,0,0,0,0],
            "trash": [0],
            "held": [0],
            "tent": [
                0
            ]
        }
    }
    init_slots(username)
    # Initialize some cards to the shop on player startup
    # baby_card = init_card(card_name, username)

    #shop_deck = decks_table["shop" + str(session_table["level"])]
    #random.shuffle(shop_deck)

    #for index, slot in enumerate(game_table["entities"][username]["locations"]["shop"]):
    #    if index < len(shop_deck):
    #        game_table["entities"][username]["locations"]["shop"][index] = init_card(shop_deck[index], username, "shop", index)
    load_deck(username, deck_to_load)

    acting({"action":"move", "target": "my_deck", "to": {"location": "hand", "index": "amount-vacant"}, "amount": 3},
           {"owner": username})

def init_teams():
    for team in session_table["teams"].keys():
        init_team(team)

def init_players():
    for username, value in session_table["players"].items():
        init_player(value["team"],0,username)
    session_table["reward"] = 0

def init_situation():
    #Essentially this is auction
    set_nested(game_table,["entities","situation"],{"team":"gaia","type":"gaia","locations":{"events":[]}})

def exist(card):
    result = 0
    try:
        if card:
            result = card.get("exist")
    except AttributeError as e:
        log("likely a zero is still somehow around instead of a slot")
        log(card)
        log(e)
        raise
    return result

def any_exist(location):
    for card in location:
        if exist(card):
            return 1
    return 0


#def set_trader():

def init_trader(trader = "trader0",entity="trader"):

    #Resolve last auction
    if game_table["entities"].get("trader") and game_table["entities"]["trader"]["locations"]["auction"][0]:
        auction_card = game_table["entities"]["trader"]["locations"]["auction"][0]["cards"][0]
        winning_team = get_winner(auction_card)
        animations.append(
            {"sender": auction_card, "receiver": auction_card,"size": 4, "image": "pics/" + "fail.png", "team": get_enemy_team(winning_team), "rate": 0.008})
        animations.append(
            {"sender": auction_card, "receiver": auction_card,"size": 4, "image": "pics/" + "success.png", "team": winning_team, "rate": 0.008})
        #Tie
        if not winning_team:
            animations.append(
                {"sender": auction_card, "receiver": auction_card, "size": 4, "image": "pics/" + "tie.png",
                  "rate": 0.008})

        triggering(auction_card,"sold")

    # Memory cleanup
    if get_nested(game_table, ["entities", "trader"]):
        for spot in ["auction","stall","trash","shop"]:
            location = get_nested(game_table, ["entities", "trader", "locations", spot])
            for card in location:
                if exist(card):
                    del game_table["ids"][card["id"]]
            del location[:]


    #Set new trader
    set_nested(game_table,["entities",entity],{"team":"gaia","type":"gaia","locations":{"auction":[0],"stall":[0],"trash":[0],"shop":[0,0,0,0,0]}})
    init_slots(entity)

    #Set new auction reward
    auction_deck = decks_table["auction"]
    random.shuffle(auction_deck)
    auction = game_table["entities"]["trader"]["locations"]["auction"]
    init_card(auction_deck[0], "trader", "auction", 0)

    #Set up new shop
    shop_deck = decks_table[trader]
    random.shuffle(shop_deck)
    for index, slot in enumerate(game_table["entities"]["trader"]["locations"]["shop"]):
        shop = game_table["entities"]["trader"]["locations"]["shop"]
        if index < len(shop_deck) and index < len(shop) and index < session_table["trader_level"]:
            init_card(shop_deck[index], "trader", "shop", index)
    init_card(trader, "trader", "stall", 0)

def init_ais():
    for username, value in session_table["ais"].items():
        init_player(value["team"],1,username)

def init_game():
    game_table["all_effect_recipes"] = []
    session_table["trader_level"] = 5
    init_situation()
    init_teams()
    init_players()
    init_trader()
    #Workaround for versus
    init_ais()

def init_card(card_name,entity,location,index,username=""):
    if not username:
        username = entity
    baby_card = copy.deepcopy(cards_table[card_name])
    if not("title" in baby_card.keys()):
        baby_card["title"] = card_name
    baby_card["name"] = card_name
    animal = card_name.split("-")[0]

    if not baby_card.get("value"):
        if "cost" in baby_card.keys():
            baby_card["value"] = baby_card["cost"]

    if not baby_card.get("cooldown"):
        baby_card["cooldown"] = 10

    if not baby_card.get("scaling"):
        if animal == "bear":
            baby_card["scaling"] = 0.4
        else:
            baby_card["scaling"] = 0.2

    if not baby_card.get("max_hype"):
        baby_card["max_hype"] = 10

    if not baby_card.get("max_level"):
        baby_card["max_level"] = 20


    if baby_card.get("values"):
        if not baby_card.get("real_values"):
            baby_card["real_values"] = copy.deepcopy(baby_card["values"])
    baby_card["exist"] = 1
    baby_card["id"] = get_unique_id()
    baby_card["shield"] = 0
    baby_card["effects"] = {}
    baby_card["max_shield"] = 20
    baby_card["level"] = 0
    baby_card["hype"] = 0
    baby_card["index"] = "void"
    baby_card["entity"] = "void"
    baby_card["location"] = "void"
    baby_card["slot_id"] = "void"
    #for trigger in baby_card["trigger"]:
    #   for action in trigger:
    #       if "main" in action.keys():
    #           baby_card["
    game_table["ids"][baby_card["id"]] = baby_card
    possess_card(baby_card,username)
    #Move happens before refresh which creates the section that gets appended?
    refresh_card(baby_card)
    acting({"action":"move", "target": baby_card, "to": {"location": location, "index": index, "entity": entity}}, baby_card)
    triggering(baby_card,"init")
    return baby_card

###CARD###
def possess_card(card, owner):
    card["owner"] = owner
    card["team"] = get_team(owner)

def refresh_card(card):
    #try:
        baby_card = copy.deepcopy(cards_table[card["name"]])
        #This kills the on enter trigger for effects
        card["triggers"] = baby_card["triggers"]
        goal = 30
        if get_effect("discard", card):
            goal = 30 * get_effect("discard", card)


        append_nested(baby_card, ["triggers", "timer"],
                      {"goal": goal, "when": ["discard"], "progress": 0, "actions": [
                                    {"action": "move", "target": "self", "to": {"location": "deck", "index": "append", "entity": "owner"}}
                                ]
                            }
                      )
        if "fox" in card["title"]:
            append_nested(baby_card, ["triggers", "timer"],
                          {"goal": 30, "main": "green","progress": 0, "actions": [ ]
                                   }
                          )
        card["effects"].clear()
        card["max_health"] = baby_card["health"]
        #Permanent hype
        #card["hype"] = 0
        card["health"] = baby_card["health"]
        if card.get("icons"):
            card["icons"] = baby_card["icons"]
        card["shield"] = 0
        card["max_shield"] = 20
    #except KeyError:
        #log("You have had a serious key error.")
        #pass

def get_card_index(hand):
    #should get all card indexes than random select
    card_indexes = []
    for index, card in enumerate(hand):
        if exist(card):
            card_indexes.append(index)
    if card_indexes:
        return random.choice(card_indexes)
    else:
        return None

def get_empty_index(board):
    for index, card in enumerate(board):
        if not exist(card):
            return index
    return None


def get_random_empty_index(board):
    # Find all indices where the card is empty (falsy)
    empty_indices = [index for index, card in enumerate(board) if not exist(card)]

    # If there are no empty indices, return None
    if not empty_indices:
        return None

    # Randomly select one of the empty indices
    return random.choice(empty_indices)


# "to": {"location": "discard", "index": "append"}})
#Need to make resolving "to" more similar to resolving targets. I know to expects empty spaces, but still they should be combined.
def move(card, to):
    card_was = card["location"]
    success = move_card(card,to)
    if success:
        move_triggers(card,card_was)

def move_card(card, to):
    try:
        to["cards"].append(card)
        if card["entity"] != "void":
            from_location = get_nested(game_table, ["entities", card["entity"], "locations", card["location"]])[card["index"]]["cards"]
            from_location.remove(card)

        card["entity"] = to["entity"]
        card["location"] = to["location"]
        card["index"] = to["index"]
        return 1
    except Exception as e:
        log("#########MOVE COMMAND############")
        log_json(e)
        log_json(card)
        log_json(to)
        raise e


#Hmm this shouldn't be called after updating the card location
def move_triggers(card, card_was):
    from_location = card_was
    to_location = card["location"]
    if to_location == "board" and from_location != "board":
        card["team"] = get_team(card["owner"])
        triggering(card, "enter")
    if from_location == "board" and to_location != "board":
        triggering(card,"exit")
    #elif from_location == "deck" or from_location == "discard":
        #card_owner = card["owner"]
        #player_data = table("players").get(card_owner)
        #deck = player_data["locations"]["deck"]
        #if len(deck) <= 0:
            #player_data["locations"]["deck"] = player_data["locations"]["discard"]
            #player_data["locations"]["discard"] = []
            #if cooldown:
            #acting({"action": "move", "target": "my_discard",
                    #"to": {"entity": card["owner"], "location": "deck", "index": "append"}}, {"owner":card_owner})
            #acting({"action": "accelerate", "target": "my_tent", "what": "move", "amount": -20}, card)
            #random.shuffle(deck)
    if to_location == "discard":
        triggering(card, "discarded")
        refresh_card(card)

#Need an add card
def load_deck(username, deck_to_load):
    random.shuffle(deck_to_load)
    deck = []
    for card_name in deck_to_load:
        init_card(card_name, username, "deck", "append")
    init_card("player", username, "tent", 0)

def is_team(target = ""):
    if target in list(table("teams").keys()):
        return True

async def update_state(players):
    global animations
    missing_players = []
    present_players = []
    for player in session_table["players"]:
        #Could generalize this to allow for possession of ais
        if not session_table["players"][player].get("socket"):
            missing_players.append(player)
            #You might be sending to a subset of the players with a higher refresh rate for instance. But the above missing players check needs to check all players
        elif player in players:
            present_players.append(player)

    for player in present_players:
        out_table = game_table
        out_table["players"] = table("players")
        out_table["teams"] = table("teams")
        text = {"evil": {"losses": session_table["teams"]["evil"]["losses"]}, "good": {"losses": session_table["teams"]["good"]["losses"]}}
        hasFog = 1
        for card in out_table["teams"][get_team(player)]["locations"]["board"]:
            if exist(card):
                hasFog = 0
        try:
            await session_table["players"][player]["socket"].send(str({"missing":missing_players,"text":text,"game_table":out_table,"me":player,"animations":animations, "fog":hasFog}))
        except websockets.exceptions.ConnectionClosedOK as e:
            log("Client easy quit", player)
            log(e)
            session_table["players"][player]["socket"] = ""
        except websockets.exceptions.ConnectionClosedError as e:
            log("Client quit:", player)
            log(e)
            session_table["players"][player]["socket"] = ""
    animations = []

def strip_keys_copy(keys, table):
    copied_table = copy.deepcopy(table)
    for key in keys:
        copied_table.pop(key, None)

def owner_card(owner):
    return game_table["entities"][owner]["locations"]["tent"][0]["cards"][0]

def find_goals_with_action_name(target_action,card):
    results = []
    for event, goals in card["triggers"].items():
        for goal in goals:
            for action in goal["actions"]:
                if action["action"] == target_action["action"]:
                    results.append(goal)
    return results

def get_team(username):
    if game_table["entities"].get(username):
        return game_table["entities"][username]["team"]

def get_board(username):
    return table("teams")[get_team(username)]["locations"]["board"]

def get_enemy_team(team): 
    if team == "evil":
        return "good"
    if team == "good":
        return "evil"
    return ""

def init_time():
    try:
        timer_handle = asyncio.create_task(tick())
    except Exception as e:
        log("Time failure refrabulating terrazoids.")
        log(e)
        init_time()


def print_json(json_message):
    #no_circ = remove_circular_refs(copy.deepcopy(json_message))
    log(json.dumps(
        json_message,
        sort_keys=True,
        indent=4,
        separators=(',',':'),
        default=lambda o: '<not serializable>'
    ))
def log_json(json_message):
    #no_circ = remove_circular_refs(copy.deepcopy(json_message))
    log(json.dumps(
        json_message,
        sort_keys=True,
        indent=4,
        separators=(',',':'),
        default = lambda o: '<not serializable>'
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

async def new_client_connected(client_socket, path):
    username= "player" + "temp" + get_unique_id()

    if session_table["first"]:
        session_table["first"] = 0
        ainame = "ai" + get_unique_id()
        #Workaround Versus
        #init_player("evil",1,ainame)
    session_table["players"][username] = {"socket":client_socket, "team":"good"}
    init_player("good", 0, username)
    await update_state([username])

    #Could have a rejoin feature
    loop = {}
    loop["username"] = username
    try:
        while True:
            client_message = await client_socket.recv()
            message_json = json.loads(client_message)
            #If I do a rejoin, set username to be who I rejoin as and set my old username to missing. Also give the player I am rejoining my socket.
            #This is a pointer hack so username can be changed from external functions. Pass by reference
            message_json["loop"] = loop
            message_json["username"] = loop["username"]
            log("Client sent:", message_json)
            if message_json.get("command"):
                globals()[message_json["command"]](message_json)
                await update_state(session_table["players"].keys())

    except websockets.ConnectionClosed as e:
    #except Exception as e:
        log("Client quit:", loop["username"])
        log(e)
        if session_table["players"].get(loop["username"]):
            session_table["players"][loop["username"]]["socket"] = ""
    except websockets.exceptions.ConnectionClosedError as e:
        #except Exception as e:
        log("Client shutdown quit", loop["username"])
        log(e)
        session_table["players"][loop["username"]]["socket"] = ""
    except websockets.exceptions.ConnectionClosedOK as e:
        log("Client easy quit", loop["username"])
        log(e)
        session_table["players"][loop["username"]]["socket"] = ""

        #if "temp" in username:
        #    if session_table["players"].get(username):
        #        del session_table["players"][username]
        #    if game_table["entities"].get(username):
        #        del game_table["entities"][username]
    #except Exception as e:
    #    log("FATAL CRASH..... RESTARTING NOW")
    #    os.execl(sys.executable,'python', __file__, *sys.argv[1:])

def reconnect(command):
    current_name = command["loop"]["username"]
    re_name = command["reconnect"]
    if current_name == re_name:
        return
    #Now commands will be recognized as coming from the correct user.
    command["loop"]["username"] = re_name
    session_table["players"][re_name]["socket"] = session_table["players"][current_name]["socket"]
    session_table["players"][current_name]["socket"] = ""

def clear_animations(command):
    log("Clear!")

def dev_mode(command):
    log("heaven")
    username = command["username"]
    acting({"action": "income", "target": "my_tent", "amount": 50}, {"owner": command["username"]})
    acting({"action": "gems", "target": "my_tent", "amount": 50}, {"owner": command["username"]})
    acting({"action":"move", "target": "my_deck", "to": {"location": "hand", "index": "amount-vacant"}, "amount": 5}, {"owner": username})


def pause(command):
    log(command["username"] + " paused")
    if game_table["running"]:
        game_table["running"] = 0
    else:
        game_table["running"] = 1

def no_audio(command):
    log(command["username"] + "muted")

def add_random_card(command):
    username = command["username"]
    card_name = get_unique_name()
    baby_card = create_random_card(card_name)
    init_card(card_name, username, "deck", "append")

def save_random_cards(command):
    with open('json/cards.json', 'w') as f:
        json.dump(cards_table,f)

def join_evil(command):
    username = command["username"]
    log(username + " joined evil")
    table("players")[username]["team"] = "evil"
    session_table["players"][username]["team"] = "evil"

def join_good(command):
    username = command["username"]
    log(username + " joined good")
    table("players")[username]["team"] = "good"
    session_table["players"][username]["team"] = "good"

def reset_game(command):
    reset_state()

def reset_session(command):
    global session_table
    session_table = copy.deepcopy(default_session_table)
    reset_state()

def refresh(command):
    log("Refreshed")

def skip_trader(command):
    if session_table["trader"] < session_table["max_trader"]:
        session_table["trader"] += 1
    else:
        session_table["trader"] = 1
    init_trader("trader" + str(session_table["trader"]))

def win(command):
    current_name = command["loop"]["username"]
    acting({"action": "place", "what": "win", "to": {"entity": get_team(current_name), "location": "board", "index": 0}, "amount": 1}, {"owner": current_name})

def add_ai_evil(command):
    username = "ai" + get_unique_id()
    init_player("evil",1,username)
    #Set leveling
    session_table["campaign"] = 1


def add_ai_good(command):
    username = "ai" + get_unique_id()
    init_player("good",1,username,"ai1")

def quit(command):
    raise websockets.ConnectionClosed("Intentional")

def remove_ai(command):
    #Needs to mark for removal then remove after tick to avoid issues
    #Need memory clean up on ids of their cards
    for player, player_data in table("players").items():
        if player_data["ai"]:
            for key,location in player_data["locations"].items():
                for card in location:
                    if card:
                        if game_table["ids"].get(card["id"]):
                            del game_table["ids"][card["id"]]
            player_data["quit"] = 1
            del session_table["ais"][player]
    session_table["campaign"] = 0


def log(*words):
    for word in words:
        print(word)

def handle_play(command):
    card_json = command
    username = card_json["username"]
    #Could send the card itself instead of the id if I wanted to remove Ids
    card_id = card_json["id"]
    card_index = int(card_json["index"])
    card_to = card_json["location"]
    # Get card from id
    #Some of these checks are not made when init card or move card happens in code...
    #Solution is to move this check to move or to acting
    card = game_table["ids"].get(card_id)
    if not exist(card):
        return
    card_from = card["location"]
    team = get_team(username)
    if card_to == "trash" and card_from == "hand":
        acting({"action": "trash", "target": card })
        acting({"action": "income", "target": "my_tent",
            "amount": 3}, {"owner": username})

    if card_to == "board" and card_from == "hand":
        slot = game_table["entities"][team]["locations"]["board"][card_index]
        if not exist(slot):
            acting({"action": "play", "target": card, "to": {"entity":team, "location":"board", "index": card_index}})
        elif slot.get("loadable"):
            acting({"action": "hype", "target": slot, "amount": 1}, card)


    if card_to == "auction" and card_from == "hand":
        if not card["title"] == "wood-card":
            if game_table["entities"]["trader"]["locations"]["auction"][card_index]:
                to_bid = game_table["entities"]["trader"]["locations"]["auction"][card_index]
                acting({"action": "bid", "target": to_bid}, card)

    if card_to == "discard" and card_from == "hand" and not card["title"] == "wood-card":
        acting({"action": "move", "target": card, "to": {"entity":card["owner"],"location":"discard", "index": "append"}})

    if card_to == "hand":
        if card_from == "hand":
            to_hype = game_table["entities"][username]["locations"]["hand"][card_index]
            if to_hype and card_index != card["index"]:
                acting({"action": "hype", "target": to_hype, "amount":1}, card)

    if card_from == "shop" and card_to != "shop":
        acting({"action": "buy", "target": card, "to": {"entity":username,"location":"deck", "index": "append"}})

async def start_server():
    log("Server started!")
    reset_state()
    init_time()
    await websockets.serve(new_client_connected, "0.0.0.0", 12345)

if __name__ == '__main__':
    event_loop = asyncio.get_event_loop()
    event_loop.run_until_complete(start_server())
    event_loop.run_forever()
