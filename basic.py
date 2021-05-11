import json
import math
import random
import requests
import traceback
from functools import reduce
from operator import getitem
from collections import defaultdict
import pprint
import tkinter
from tkinter import *
import tkinter.messagebox
import tkinter.ttk

def geti(list, index, default_value):
    try:
        return list[index]
        
    except:
        return default_value

def dd_rec():
    return defaultdict(dd_rec)

def defaultify(d):
    if not isinstance(d, dict):
        return d
    return defaultdict(dd_rec, {k: defaultify(v) for k, v in d.items()})

def dictify(d):
    if isinstance(d, defaultdict):
        d = {k: dictify(v) for k, v in d.items()}
    return d
                
def set_nested_item(dataDict, mapList, val):
    """Set item in nested dictionary"""
    reduce(getitem, mapList[:-1], dataDict)[mapList[-1]] = val
    return dataDict
                
def loadData():
        with open('data.json') as f:
                return json.load(f)
                
def loadBattle():
        with open('battle.json') as f:
                return json.load(f)
                
 
cacheTable = defaultify(loadData());
battleTable = defaultify(loadBattle());

def getJsonFromApi(steps):
        api_base = "https://www.dnd5eapi.co/api/"
        for x in steps:
                api_base += x + "/"
        package = requests.get(api_base)
        response = package.json()
        if response.get("error"):
                print("Content not in api nor cache", steps);
                return False
        with open('data.json') as f:
                global cacheTable
                cacheTable = set_nested_item(cacheTable,steps,response)
        
        with open('data.json', 'w') as f:
                json.dump(dictify(cacheTable),f)
                return response
                
def getJson(steps):
        global cacheTable
        cache = cacheTable
        for i,x in enumerate(steps):
                cache = cache[x]
                if cache == {} and i > 0:
                        print("Not cached, trying api")
                        return getJsonFromApi(steps)
        return cache.copy()
        
def getState():
        print("index name hp/max_hp")
        for i,x in enumerate(battleTable["combatants"]):        
                print(i,x["index"],str(x["current_hp"])+"/"+str(x["max_hp"]))

def window():
    window = Tkinter.Tk()
    window.wm_withdraw()

    #centre screen message
    window.geometry("1x1+"+str(window.winfo_screenwidth()/2)
                    +"+"+str(window.winfo_screenheight()/2))
    tkMessageBox.showinfo(title=" ", message=" hola")

def roll(dice):
        dsplit = dice.split("d")
        
        diceCount = int(dsplit[0])
        remaining = dsplit[1].split("+")
        diceType = float(remaining[0])
        if "+" in dice:
                diceMod = float(remaining[1])
        else:
                diceMod = 0
        sum = 0
        for x in range(diceCount):
                sum += math.ceil(diceType*random.random())
        return int(sum + diceMod)
        
def getMod(modType, attackJson, senderJson):
        modSum = 0
        if modType == "hit" or modType == "dmg":
            finesse = False
            for x in attackJson["properties"]:
                if x["index"] == "finesse":
                    finesse = True
            if finesse:
                modSum += max(statMod(int(senderJson["strength"])),statMod(int(senderJson["dexterity"])))
            else:
                modSum += statMod(int(senderJson["strength"]))

        if modType == "hit":
            if senderJson.get("weapon_proficiencies"):
                if attackJson["weapon_category"] in senderJson["weapon_proficiencies"]:
                    modSum += senderJson["proficiency_bonus"]
        return modSum

def statMod(stat):
        return math.floor((stat-10)/2)


def applyAction(senderJson,targetInfo,actionKey):
    targetJson = battleTable["combatants"][int(targetInfo[0])]
    advantage = int(geti(targetInfo,1,0))
    actions = senderJson.get("actions")
    action = False
    adv = ""
    for act in actions:
        if act["name"] == actionKey:
            action = act
    if action:
        hit = 0
        if advantage == 0:
            hit = roll("1d20")
            adv = ""
        elif advantage == 1:
            hit = max(roll("1d20"),roll("1d20"))
            adv = " at advantage"
        elif advantage == -1:
            hit = min(roll("1d20"),roll("1d20"))
            adv = " at disadvantage"
        else:
            print("invalid advantage type")
            hit = roll("1d20")
        hit += action["attack_bonus"]
        
        if hit >= targetJson["armor_class"]:
            hurt = 0
            for damage in action["damage"]:         
                if damage.get("choose"):
                    for actions in range(int(damage["choose"])):
                        hurt += roll(random.choice(damage["from"])["damage_dice"])
                else:   
                     hurt += roll(damage["damage_dice"])
            print(senderJson["index"], "used", actionKey + str(adv),"with a hit of",hit, "and dealt",hurt,"damage to",targetJson["index"])
            targetJson["current_hp"] -= hurt
        else:
            print(senderJson["index"], "used", actionKey + str(adv),"with a hit of", hit, "and missed",targetJson["index"])
    else:
        print("Invalid action for this combatant")

running = True

def command_parse(input_command_string):
    if input_command_string == "vomit":
        print ("ewwwww")
        
def callAction(sender, actionKey, targetInfo):
    senderJson = battleTable["combatants"][int(sender)]
    actions = senderJson.get("actions")
    if actions:
        if actionKey == "Multiattack":
            canMultiattack = False
            multiAction = {}
            for act in actions:
                if act["name"] == actionKey:
                    multiAction = act
                    canMultiAttack = True
            if canMultiAttack:
                for i in range(int(multiAction["options"]["choose"])):
                    for action in random.choice(multiAction["options"]["from"]):
                        applyAction(senderJson,targetInfo,action["name"])
            else:
                print("This combatant cannot multiattack")              
        else:
            applyAction(actions,targetInfo,actionKey)
                    


while running:
    try:
        getState()
        args = input("Command?").split(" ")
        command = args[0]
        if command == "action":
            sender = args[1]
            actionKey = args[2]
            targetInfos = args[3].split(",")
            for targetInfo in targetInfos:
                callAction(sender, actionKey, targetInfo.split("."))
                                
        elif command == "weapon":
            '''This should do bonuses to 
            Looks at the strength of the sender
            then applies the strength of the sender
            to the hit roll of the weapon.'''
            sender = args[1]
            attackPath = args[2]
            target = args[3]
            times = geti(args, 4, 1)
            attackJson = getJson(["equipment",attackPath])
            targetJson = battleTable["combatants"][int(target)]
            senderJson = battleTable["combatants"][int(sender)]
            if attackJson:
                hit = roll("1d20")
                hit += getMod("hit",attackJson,senderJson)
                print("hit",hit)
                if hit >= targetJson["armor_class"]:
                    targetJson["current_hp"] -= roll(attackJson["damage"]["damage_dice"]+"+"+str(getMod("dmg",attackJson,senderJson)))
        elif command == "list":
            steps = args[1].split(",")
            battle = battleTable.copy()
            
            for x in steps:
                if x.isnumeric():
                    battle = battle[int(x)]
                else:
                    battle = battle[x]
            pprint.pprint(battle, sort_dicts=False)
        
        elif command == "add":
            name = args[1]
            combatant = getJson(["monsters",name])
            
            if combatant:
                hitDice = combatant.get("hit_dice")
                hitPoints = combatant.get("hit_points")
                if hitDice:
                    hp = roll(hitDice)
                    combatant["max_hp"] = hp
                    combatant["current_hp"] = hp
                    
                elif hitPoints:
                    combatant["max_hp"] = hitPoints
                    combatant["current_hp"] = hitPoints
            
                battleTable["combatants"].append(combatant)
                                
        elif command == "remove":
                index = int(args[1])
                battleTable["combatants"].pop(index)
                
        elif command == "save":
            with open('battle.json', 'w') as f:
                json.dump(dictify(battleTable),f)       
            
        elif command == "exit":
            with open('battle.json', 'w') as f:
                json.dump(dictify(battleTable),f)
            running = False
    
        elif command == "character":
            name = input("Name?")

            monsterCache = cacheTable["monsters"][name]
            monsterCache["index"] = name
            monsterCache["strength"] = input("str?")
            monsterCache["dexterity"] = input("dex?")
            monsterCache["constitution"] = input("con?")
            monsterCache["intelligence"] = input("int?")
            monsterCache["wisdom"] = input("wis?")
            monsterCache["charisma"] = input("cha?")
            monsterCache["weapon_proficiencies"] = input("Weapon proficiencies? (eg simple,martial)")
            monsterCache["proficiency_bonus"] = input("Proficiency Bonus?")
            monsterCache["max_hp"] = input("Max Hp?")
            monsterCache["current_hp"] = monsterCache["max_hp"]
            
            with open('data.json', 'w') as f:
                json.dump(dictify(cacheTable),f)
        else: 
            print('incorrect command')
    except Exception:
        print("oneechan makes awkward-sounding noises at you, enter the 'exit' command to exit.")
        traceback.print_exc()

