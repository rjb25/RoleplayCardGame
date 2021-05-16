import requests
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
import tkinter
from tkinter import *
import tkinter.messagebox
import tkinter.ttk
import argparse

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

def crToProf(cr):
    crVal = float(sum(Fraction(s) for s in str(cr).split()))
    if cr < 5:
        return 2
    if cr <9:
        return 3
    if cr<13:
        return 4
    elif cr<17:
        return 5
    elif cr<21:
        return 6
    elif cr<25:
        return 7
    elif cr <29:
        return 8
    elif cr < 31:
        return 9
    else:
        print("Hmm is a monster really this high level? Proficiency issue")
        return 10

def expandStatWord(stat):
    if stat == "wis":
        return "wisdom"
    elif stat == "str":
        return "strength"
    elif stat == "dex":
        return "dexterity"
    elif stat == "con":
        return "constitution"
    elif stat == "cha":
        return "charisma"
    elif stat == "int":
        return "intelligence"
    else:
        raise Exception("not a valid stat word", stat)

def getProf(combatant):
    proficiency = combatant.get("proficiency_bonus")
    cr = combatant.get("challenge_rating")
    if proficiency:
        return proficiency
    elif cr:
        newProficiency = crToProf(cr)
        combatant["proficiency_bonus"] = newProficiency
        return newProficiency
    else:
        raise Exception("This combatant has neither a proficiency_bonus nor a CR", combatant)
def canCast(combatantJson):
    for ability in combatantJson["special_abilities"]:
        spellcasting = ability.get("spellcasting")
        if spellcasting:
            return spellcasting
    return False
        
def getMod(modType, attackJson, combatantJson, additional = 0):
        modSum = 0
        if modType == "hit" or modType == "dmg":
            finesse = False
            properties = attackJson.get["properties"]
            if properties:
                for x in properties:
                    if x["index"] == "finesse":
                        finesse = True
            if finesse:
                modSum += max(statMod(int(combatantJson["strength"])),statMod(int(combatantJson["dexterity"])))
            else:
                modSum += statMod(int(combatantJson["strength"]))

        if modType == "hit":
            if combatantJson.get("weapon_proficiencies"):
                if attackJson["weapon_category"] in combatantJson["weapon_proficiencies"]:
                    modSum += getProf(combatantJson)
        if modType == "spellHit" or modType == "spellDc":
            modSum += getProf(combatantJson)

        if modType == "saveDc":
            modSum += statMod(combatantJson[expandStatWord(attackJson["dc"]["dc_type"]["index"])])

        if modType == "spellHit" or modType == "spellDc" or modType == "saveDc":
            special_abilities = combatantJson.get("special_abilities")
            if special_abilities:
                spellcasting = canCast(combatantJson)
                if spellcasting:
                    if modType == "spellHit" or modType == "spellDc":
                        modSum += statMod(combatantJson[expandStatWord(spellcasting["ability"]["index"])])

                    if modType == "spellDc":
                        modSum += additional + 8 #In this case additional should be level of spell
                else:
                    raise Exception("Attempted to have a non spellcaster cast a spell")

                        #modifier = spellcasting["modifier"]
                        #if modifier and modType == "spellHit":
                            #NOTE THE HARD = HERE
                            #modSum = spellcasting["modifier"]

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
            adv = " with advantage"
        elif advantage == -1:
            hit = min(roll("1d20"),roll("1d20"))
            adv = " with disadvantage"
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
            print(senderJson["index"], "used", actionKey + str(adv),"for a hit of",hit, "and dealt",hurt,"damage to",targetJson["index"])
            targetJson["current_hp"] -= hurt
        else:
            print(senderJson["index"], "used", actionKey + str(adv),"for a hit of", hit, "and missed",targetJson["index"])
    else:
        print("Invalid action for this combatant")


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
            applyAction(senderJson,targetInfo,actionKey)

def applyInit(combatant):
    combatant["initiative"] = statMod(combatant["dexterity"]) + roll("1d20")
                    
def callInit(who):
    if who == "all":
        for combatant in battleTable["combatants"]:
            applyInit(combatant)
    elif geti(battleTable["combatants"],int(who),False):
        combatant = battleTable["combatants"][int(who)]
        applyInit(combatant)
    else:
        print("Can't find what you are trying to roll initiative for.")
        return
        
    battleTable["combatants"] = sorted(battleTable["combatants"], key=itemgetter("initiative"), reverse=True)
def spellType(attackJson):
    if attackJson["damage"].get("damage_at_character_level"):
        return "damage_at_character_level"
    elif attackJson["damage"].get("damage_at_level"):
        return "damage_at_level"
    else:
        raise Exception("Oops this is not a spell")

def isCantrip(attackJson):
    if attackJson["damage"].get("damage_at_character_level"):
        return True
    elif attackJson["damage"].get("damage_at_level"):
        return False
    else:
        raise Exception("Oops this is not a spell", attackJson)

def callCast(sender, attackPath, target, level):
    attackJson = getJson(["spells",attackPath])
    targetJson = battleTable["combatants"][int(target)]
    senderJson = battleTable["combatants"][int(sender)]
    dmgAtKey = spellType(attackJson)
    cantrip = isCantrip(attackJson)
    dmgString = ""
    spellcasting = canCast(senderJson)
    if cantrip:
        level = spellcasting["level"]
        for levelKey, damage in attackJson["damage"][dmgAtKey].items():
            if level >= int(levelKey):
                dmgString = attackJson["damage"][dmgAtKey][levelKey]
    elif level == -1:
        dmgString = attackJson["damage"][dmgAtKey][0]
        print("No spell slot level specified, using lowest")
    print("Casting", dmgString)


    if dmgString == "":
        raise Exception("No damage found for spell", attackJson)

    if attackJson:
        dc = attackJson.get("dc")
        success = False
        successMult = 0
        if dc:
            saveMod = getMod("saveDc", attackJson, targetJson)
            saveRoll = roll("1d20")
            totalSave = saveMod + saveRoll
            successEffect = dc["dc_success"]
            if successEffect == "half":
                successMult = 0.5
            if cantrip:
                level = 0
            saveThreshold = getMod("spellDc",attackJson,senderJson,int(level))

            if totalSave < saveThreshold:
                success = True

        else:
            hit = roll("1d20")
            hit += getMod("spellHit",attackJson,senderJson)
            print("hit",hit)
            if hit >= targetJson["armor_class"]:
                success = True

        if success:
            targetJson["current_hp"] -= roll(dmgString)
        elif successMult != 0:
            targetJson["current_hp"] -= math.floor(successMult*roll(dmgString))


def removeDown():
    index = 0
    for combatant in battleTable["combatants"]:
        if combatant["current_hp"] <= 0:
            battleTable["combatants"].pop(index)
        else:
            index +=1

running = True
while running:
    try:
        removeDown()
        getState()
        args = input("Command?").split(" ")
        command = args[0]

        if command == "action":
            sender = args[1]
            actionKey = args[2]
            targetInfos = args[3].split(",")
            times = geti(args, 4, 1)

            for time in range(times):
                for targetInfo in targetInfos:
                    callAction(sender, actionKey, targetInfo.split("."))

        elif command == "init" or command == "initiative":
            try:
                who = args[1]
            except:
                who = "all"
            callInit(who)

        elif command == "cast":
            sender = args[1]
            senderJson = battleTable["combatants"][int(sender)]
            actionKey = args[2]
            targetInfos = args[3].split(",")
            level = geti(args,4,-1)
            times = int(geti(args, 5, 1))

            if canCast(senderJson):
                for time in range(times):
                    for targetInfo in targetInfos:
                        callCast(sender, actionKey, targetInfo, level)
            else:
                print("Did nothing. This creature has no cast type and cannot cast.")
                                
        elif command == "weapon":
            '''This should do bonuses too
            Looks at the strength of the sender
            then applies the strength of the sender
            to the hit roll of the weapon.'''
            sender = args[1]
            attackPath = args[2]
            target = args[3]
            times = int(geti(args, 4, 1))
            attackJson = getJson(["equipment",attackPath])
            targetJson = battleTable["combatants"][int(target)]
            senderJson = battleTable["combatants"][int(sender)]
            if attackJson:
                for x in range(times):
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
            
                applyInit(combatant)
                battleTable["combatants"].append(combatant)
                callInit(len(battleTable["combatants"])-1)
                                
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

        elif command == "abort":
            running = False
    
        elif command == "character":
            name = input("Name?")

            monsterCache = cacheTable["monsters"][name]
            monsterCache["index"] = name
            monsterCache["strength"] = int(input("str?"))
            monsterCache["dexterity"] = int(input("dex?"))
            monsterCache["constitution"] = int(input("con?"))
            monsterCache["intelligence"] = int(input("int?"))
            monsterCache["wisdom"] = int(input("wis?"))
            monsterCache["charisma"] = int(input("cha?"))
            monsterCache["special_abilities"] = []
            monsterCache["special_abilities"].append({"spellcasting": {"ability": {"index" : input("caster stat? (eg. int)")}}})
            monsterCache["weapon_proficiencies"] = input("Weapon proficiencies? (eg simple,martial)")
            monsterCache["max_hp"] = int(input("Max Hp?"))
            monsterCache["current_hp"] = int(monsterCache["max_hp"])
            monsterCache["armor_class"] = int(input("Armor Class?"))
            spellcasting = canCast(monsterCache)
            level = int(input("Level?"))
            spellcasting["level"] = level
            monsterCache["proficiency_bonus"] = crToProf(level)
            
            with open('data.json', 'w') as f:
                json.dump(dictify(cacheTable),f)
        else: 
            print('incorrect command')
    except Exception:
        print("oneechan makes awkward-sounding noises at you, enter the 'exit' command to exit.")
        traceback.print_exc()

