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
from collections import defaultdict
import pprint
import tkinter as tk
import argparse
import re

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
battleOrder = []

def getJsonFromApi(steps,save=True):
        api_base = "https://www.dnd5eapi.co/api/"
        for x in steps:
            api_base += x + "/"
        print(api_base)
        package = requests.get(api_base)
        response = package.json()
        if response.get("error"):
            print("Content not in api nor cache", steps);
            return False

        if save:
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
        print("initiative name type hp/max_hp")
        for nick in battleOrder:        
            x = battleTable[nick]
            print(x["initiative"],nick,x["index"],str(x["current_hp"])+"/"+str(x["max_hp"]))

text_box = ""
text_box2 = ""
def windowLog():
    root = tk.Tk()
    global text_box
    text_box = tk.Text(root, width = 25, height = 2)
    text_box.grid(row = 10, column = 0, columnspan = 20)

def windowState():
    root = tk.Tk()
    global text_box2
    text_box2 = tk.Text(root, width = 25, height = 2)
    text_box2.grid(row = 1, column = 0, columnspan = 2)

def log(content):
    text_box.insert("end-1c", content+"\n")

def setState(content):
    text_box2.delete(1.0,"end-1c")
    text_box2.insert("end-1c",content+"\n")

def roll(dice):
    print(dice)
    dsplit = dice.split("d")
    usesDice = len(dsplit)>1
    sum = 0
    diceMod = 0
    if usesDice:
        remaining = dsplit[1].split("+")
        if "+" in dice:
            diceMod = float(remaining[1])
        diceCount = int(dsplit[0])
        diceType = float(remaining[0])
        for x in range(diceCount):
            sum += math.ceil(diceType*random.random())
    else:
        sum = int(dice)
    
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

def applyDamage(targetJson,damage,dmgType):
    immunities = targetJson.get("damage_immunities")
    vulnerabilities = targetJson.get("damage_vulnerabilities")
    resistances = targetJson.get("damage_resistances")

    damageDealt = damage
    damageType = dmgType["index"]
    searching = True
    if immunities and searching:
        for method in immunities:
            if method == damageType:
                damageDealt = 0
                searching = False
    if vulnerabilities and searching:
        for method in vulnerabilities:
            if method == damageType:
                damageDealt *= 2 
                searching = False
    if resistances and searching:
        for method in resistances:
            if method == damageType:
                damageDealt *= 0.5

    targetJson["current_hp"] -= math.floor(damageDealt)

        
def getMod(modType, attackJson, combatantJson, additional = 0):
        modSum = 0
        if modType == "hit" or modType == "dmg":
            finesse = False
            properties = attackJson.get("properties")
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

        if modType == "spellHit" or modType == "spellDc":
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

        return modSum


def statMod(stat):
        return math.floor((stat-10)/2)


def applyAction(senderJson,targetInfo,actionKey):
    targetJson = battleTable[targetInfo[0]]
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
                        chosenAction = random.choice(damage["from"])
                        applyDamage(targetJson,roll(chosenAction["damage_dice"]),chosenAction["damage_type"])
                else:   
                    applyDamage(targetJson,roll(damage["damage_dice"]),damage["damage_type"])
    else:
        print("Invalid action for this combatant")


def command_parse(input_command_string):
    if input_command_string == "vomit":
        print ("ewwwww")
        
def callAction(sender, actionKey, targetInfo):
    senderJson = battleTable[sender]
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

def setBattleOrder():
    initiativeOrder = sorted(battleTable.items(), key=lambda x: x[1]["initiative"], reverse=True)
    tempOrder = []
    for keyPair in initiativeOrder:
        tempOrder.append(keyPair[0])
    global battleOrder
    battleOrder = tempOrder
    
                    
def callInit(who):
    if who == "all":
        for nick, combatant in battleTable.items():
            applyInit(combatant)
    elif geti(battleTable,who,False):
        combatant = battleTable[who]
        applyInit(combatant)
    else:
        print("Can't find what you are trying to roll initiative for.")
        return
    setBattleOrder()

def spellType(attackJson):
    if attackJson["damage"].get("damage_at_character_level"):
        return "damage_at_character_level"
    elif attackJson["damage"].get("damage_at_slot_level"):
        return "damage_at_slot_level"
    else:
        raise Exception("Oops this is not a spell")

def isCantrip(attackJson):
    if attackJson["damage"].get("damage_at_character_level"):
        return True
    elif attackJson["damage"].get("damage_at_slot_level"):
        return False
    else:
        raise Exception("Oops this is not a spell", attackJson)

def callCast(sender, attackPath, target, level):
    attackJson = getJson(["spells",attackPath])
    targetJson = battleTable.get(target)
    senderJson = battleTable.get(sender)
    if not targetJson or not senderJson:
        print("target or sender no longer exists")
        return

    dmgAtKey = spellType(attackJson)
    cantrip = isCantrip(attackJson)
    dmgString = ""

    spellcasting = canCast(senderJson)

    if cantrip:
        level = geti(spellcasting, "level", -1)

    lowestLevel = "1000000"
    for levelKey, damage in attackJson["damage"][dmgAtKey].items():
        if int(levelKey) < int(lowestLevel):
            lowestLevel = levelKey
        if int(level) >= int(levelKey):
            dmgString = attackJson["damage"][dmgAtKey][levelKey]
    if dmgString == "":
        dmgString = attackJson["damage"][dmgAtKey][lowestLevel]
        print("Defaulting cast to lowest level",lowestLevel)

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
            applyDamage(targetJson,roll(dmgString),attackJson["damage"]["damage_type"])
        elif successMult != 0:
            applyDamage(targetJson,successMult*roll(dmgString),attackJson["damage"]["damage_type"])

def removeDown():
    for nick, combatant in battleTable.copy().items():
        if combatant["current_hp"] <= 0:
            battleTable.pop(nick)
            battleOrder.remove(nick)

def callRequest(steps):
    pprint.pprint(dictify(getJsonFromApi(steps,False)), sort_dicts=False)

def run_assistant():
    running = True
    setBattleOrder()
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
            elif command == "request":
                callRequest(args[1].split(","))
    
            elif command == "init" or command == "initiative":
                try:
                    who = args[1]
                except:
                    who = "all"
                callInit(who)
    
            elif command == "auto":
                print("attempting auto")
    
            elif command == "mod" or command == "set" or command == "list" or command == "listkeys":
                steps = args[1].split(",")
                diff = geti(args, 2, False)
                battle = battleTable.copy()
                
                for i,key in enumerate(steps):
                    if i < len(steps)-1:
                        if key.isnumeric():
                            battle = battle[int(key)]
                        else:
                            battle = battle[key]
    
                finalStep = steps[len(steps)-1]
                if command == "mod":
                    battle[finalStep] += int(diff)
                elif command == "set":
                    battle[finalStep] = int(diff)
                elif command == "list":
                    pprint.pprint(dictify(battle[finalStep]), sort_dicts=False)
                elif command == "listkeys":
                    string = ""
                    for key, val in battle[finalStep].items():
                        string += key + ","
                    string[:-1]
                    print(string)
    
    
            elif command == "cast":
                sender = args[1]
                senderJson = battleTable.get(sender)
                actionKey = args[2]
                targetInfos = args[3].split(",")
                level = geti(args,4,-1)
                times = int(geti(args, 5, 1))
                if senderJson:
                    if canCast(senderJson):
                        for time in range(times):
                            for targetInfo in targetInfos:
                                callCast(sender, actionKey, targetInfo, level)
                    else:
                        print("Did nothing. This creature has no cast type and cannot cast.")
                else:
                    print("The creature you are attempting to make a cast from does not exist.")
                                    
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
                targetJson = battleTable[target]
                senderJson = battleTable[sender]
                if attackJson:
                    for x in range(times):
                        hit = roll("1d20")
                        hit += getMod("hit",attackJson,senderJson)
                        print("hit",hit)
                        if hit >= targetJson["armor_class"]:
                            hurt = roll(attackJson["damage"]["damage_dice"]+"+"+str(getMod("dmg",attackJson,senderJson)))
                            applyDamage(targetJson,hurt,attackJson["damage"]["damage_type"])
            
            elif command == "add":
                name = args[1]
                combatant = getJson(["monsters",name])
    
                nick = geti(args,2,"")
                if nick == "":
                    nick = combatant["index"]
    
                nickPair = nick.split("#")
                nickName = geti(nickPair,0,"")
                nickNumber = int(geti(nickPair,1,1))
                findingAvailableNick = True
                while findingAvailableNick:
                    findingAvailableNick = False
                    for existingNick,existingCombatant in battleTable.items():
                        if existingNick == nick:
                            nick = nickName + "#" + str(nickNumber)
                            nickNumber += 1 
                            findingAvailableNick = True
                
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
                    battleTable[nick] = combatant
                    callInit(nick)
                                    
            elif command == "remove":
                    nick = args[1]
                    battleTable.pop(nick)
                    battleOrder.remove(nick)
                    
            elif command == "save":
                with open('battle.json', 'w') as f:
                    json.dump(dictify(battleTable),f)       
                
            elif command == "exit":
                with open('battle.json', 'w') as f:
                    json.dump(dictify(battleTable),f)
                running = False
    
            elif command == "abort":
                running = False
    
            elif command == "log":
                log(args[1])
    
            elif command == "state":
                setState(args[1])
    
            elif command == "windowLog":
                windowLog()
    
            elif command == "windowState":
                windowState()
        
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

if __name__ == "__main__":
    run_assistant()
