import sys
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
import shlex
import copy
from itertools import takewhile

command_descriptions_dict = {
"do" : '''Run a custom attack with no sender:
do --target climber --landFudge 1d20+4$ --check 10 --weaponFudge 1d8@bludgeoning 1d4@piercing --blockMult 0.5 --save
''',

"use" : '''Do a generic action weapon or cast:
use --do greatsword --sender groovyBoy --target druid#3 --times 1 --advantage 1
''',

"action" : '''Do a generic action:
action --do Multiattack --sender sahuagin#2 --target druid#3 --times 1 --advantage 1
''',

"weapon" : '''Use a weapon:
weapon --do greatsword --sender sahuagin#2 --target druid#3 --times 3 --advantage -1
''',

"cast" : '''Cast a spell:
cast --sender druid#3 --target sahuagin#2 --times 2 --do fire-bolt --level 4 --advantage 0
''',

"remove" : '''Remove an item:
remove --target sahuagin#2
''',

"request" : '''Make a request:
request --path monsters sahuagin
''',

"set" : '''Set some aspect of the character or other item:
set --target sahuagin# --path initiative --change 18
''',

"mod" : '''Modify a stat on a creature:
mod --target sahuagin#2 --path initiative --change -5
''',

"list" : '''List the features of a creature:
list --target sahuagin#2 --path actions
''',

"listkeys" : '''List the keys for an item:
listkeys --target sahuagin#2 --path actions
''',

"add" : '''Add a creature:
add --target sahuagin --times 2 --identity Aqua-Soldier
''',

"init" : '''Roll for initiative:
initiative --target sahuagin#2
''',

"load" : '''Load a content by file name:
load --category monsters --file new_creature.json
load --category equipment --file new_weapon.json
load --category spells --file new_spell.json
''',

"turn" : '''Increments turn:
turn
''',

"auto" : '''Set an automated command:
auto --target sahuagin --commandString "action --target party!random --sender sahuagin --do multiattack"
''',

"group" : '''Set a group for use in targetting. Will be resolved to listed targets:
group --member sahuagin sahuagin#2 --group sahuagang
''',

"info" : '''Shows all info for reference:
info --info groups
''',

"roll" : '''Roll dice:
roll --dice 1d20+2
''',

"store" : '''Store a command for use later:
store --commandString "add -t sahuagin -n 2" --path encounter#2 --append
''',

"shortrest" : '''Auto heal from short rest:
shortrest -t party 
''',

"longrest" : '''AutoHeal from long rest:
longrest -t party 
''',

"jump" : '''This persons turn: jump -t goblin#2
''',

"skip" : '''Do nothing:
skip
''',

"pause" : '''Forces a pause when the targets turn is there without removing his auto commands:
pause -t thinker
''',

"resume" : '''Set creature to run auto command when it is their turn:
resume -t menial-minded
''',

"enable" : '''Dont skip this persons turn:
enable -t no-longer-stunned-person
''',

"disable" : '''Skip this persons turn and try running the auto command for the next person:
disable -t not-yet-in-combat
''',

"addAuto" : '''Adds a creature and sets up a basic attack and target for it. In the case of monsters this is action #0:
addAuto --target giant-rat
addAuto --target npc-helper --do dagger --identity greg --method order --party
''',

"delete" : '''Delete a command or information entry such as a group:
delete -p commands loadParty 1
''',

"help" : '''Display this message:
help
''',

}


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

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

def get_nested_item(input_dict, nested_key):
    internal_dict_value = input_dict
    for k in nested_key:
        internal_dict_value = geti(internal_dict_value, k, None)
        if internal_dict_value is None:
            return None
    return internal_dict_value

def weedNones(dictionary):
    return {k:v for k,v in dictionary.items() if v is not None}
                
def load(a):
    with open(a["file"]) as f:
            return json.load(f)

def callLoad(a):
    global cacheTable
    directory = ""
    if a.get("directory"):
        directory = a["directory"]
    for newFile in a["file"]:
        creatureJson = load({"file": directory+"/"+newFile})
        hasCategory = cacheTable.get(a["category"])
        if hasCategory:
            cacheTable[a["category"]][creatureJson["index"]] = creatureJson
        else:
            print("Invalid category to load into")
 
cacheTable = defaultify(load({"file":"data.json"}))
battleTable = defaultify(load({"file":"battle.json"}))
battleInfo = defaultify(load({"file":"battle_info.json"}))
battleOrder = []

def getJsonFromApi(steps,save=True):
        api_base = "https://www.dnd5eapi.co/api/"
        for x in steps:
            api_base += x + "/"
        try:
            package = requests.get(api_base)
        except:
            print("Api not reachable",api_base)
            return False
        response = package.json()
        if response.get("error"):
            #print("Content not in api nor cache", steps)
            return False

        if save:
            with open('data.json') as f:
                global cacheTable
                cacheTable = set_nested_item(cacheTable,steps,response)
            
            with open('data.json', 'w') as f:
                json.dump(dictify(cacheTable),f)

        return response

def saveBattle():
        with open('battle.json', 'w') as f:
            json.dump(dictify(battleTable),f)       
        with open('battle_info.json', 'w') as f:
            json.dump(dictify(battleInfo),f)
        with open('data.json', 'w') as f:
            json.dump(dictify(cacheTable),f)

def printJson(json):
    pprint.pprint(dictify(json), sort_dicts=False)
                
def getJson(steps):
        global cacheTable
        cache = cacheTable
        
        for i,x in enumerate(steps):
                cache = cache[x]
                if cache == {} and i > 0:
                        #print("Not cached, trying api")
                        return getJsonFromApi(steps)
        return cache.copy()
        
def getState():
        print("index initiative name type hp/max_hp")
        state_result = []
        for i, nick in enumerate(battleOrder):
            x = battleTable[nick]
            turn = ""
            if x.get("my_turn"):
                turn = "<-----------------| My Turn"
            temphp = 0
            if x.get("temp_hp"):
                temphp = x.get("temp_hp")

            print(i,x["initiative"],nick,x["index"],str(x["current_hp"]+temphp)+"/"+str(x["max_hp"])+turn)
            state_result.append(str(x["initiative"]) + ' ' + nick + ' ' + str(x["index"]) + ' ' + str(x["current_hp"]) + "/" + str(x["max_hp"]))
        return state_result

def rollString(a):
    for dice in a["dice"]:
        roll(dice)

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

def applyDamage(targetJson,damage):
    if targetJson.get("temp_hp"):
        damage = damage - int(targetJson.get("temp_hp"))
    if damage > 0:
        targetJson["temp_hp"] = 0
        targetJson["current_hp"] -= math.floor(damage)
        targetJson["current_hp"] = max(targetJson["current_hp"],0)
    if damage < 0:
        targetJson["temp_hp"] = -1*damage

def getAffinityMod(targetJson,damageType):
    immunities = targetJson.get("damage_immunities")
    vulnerabilities = targetJson.get("damage_vulnerabilities")
    resistances = targetJson.get("damage_resistances")

    if immunities:
        for affinity in immunities:
            if affinity == damageType:
                return 0
    if vulnerabilities:
        for affinity in vulnerabilities:
            if affinity == damageType:
                return 2 
    if resistances:
        for affinity in resistances:
            if affinity == damageType:
                return 0.5
    if damageType == "heal":
        return -1
    if damageType in ["temp","temp_hp","temphp"]:
        return "temphp"
    return 1

classSavesDict = {
"barbarian" : ["str","con"],
"bard" : ["dex","cha"],
"cleric" : ["wis","cha"],
"druid" : ["int","wis"],
"fighter" : ["str","con"],
"monk" : ["str","dex"],
"paladin" : ["wis","cha"],
"ranger" : ["str","dex"],
"rogue" : ["dex","int"],
"sorcerer" : ["con","cha"],
"warlock" : ["wis","cha"],
"wizard" : ["int","wis"],
}
        
def getMod(modType, attackJson, combatantJson, additional = 0):
        modSum = 0
        if modType == "actionHit" and attackJson.get("attack_bonus"):
            modSum += attackJson.get("attack_bonus")
        else:
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
                saveType = attackJson["dc"]["dc_type"]["index"]
                modSum += statMod(combatantJson[expandStatWord(saveType)])
                saveProficiencies = geti(classSavesDict,combatantJson.get("class"),[])
                if saveType in saveProficiencies:
                    modSum += getProf(combatantJson)
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

def printUse(a):
    print(a["sender"].upper(), "uses", a["do"], "on", a["target"])

def applyAction(a):
    actionKey = a["do"]
    sender = a["sender"]
    target = a["target"]
    landFudge = a.get("landFudge")
    weaponFudge = a.get("weaponFudge")
    advantageIn = int(a["advantage"])
    senderJson = battleTable[sender]
    targetJson = battleTable[target]
    actions = senderJson.get("actions")
    specialAbilities = senderJson.get("special_abilities")

    action = False
    action_result = ''
    if actions:
        for act in actions:
            if act["name"] == actionKey:
                action = act
    if specialAbilities:
        for special in specialAbilities:
            if special["name"] == actionKey:
                action = special
    if action:
        threshold = int(targetJson["armor_class"])

        advMod = 0 
        dc = action.get("dc")

        blockMult = 0
        mod = 0
        if dc:
            threshold = int(dc.get("dc_value"))
            if not threshold:
                print("Has a dc for this action but no dc_value. Defaulting to 10")
                threshold = 10

            if dc.get("dc_success") == "half" or dc.get("success_type") == "half":
                blockMult = 0.5
            advMod = int(targetJson["save_advantage"])
            mod = getMod("saveDc", action, targetJson)
        else:
            mod = getMod("actionHit",action,senderJson)
            advMod = int(senderJson["advantage"])
        printUse(a)
        advNum = advantageIn + advMod

        advantage = ""
        if advNum > 0:
           advantage = "advantage" 
        elif advNum < 0:
           advantage = "disadvantage" 
        if action.get("damage"):
            for damage in action["damage"]:         
                if damage.get("choose"):
                    for actions in range(int(damage["choose"])):
                        chosenAction = random.choice(damage["from"])
                        damageType = chosenAction["damage_type"]["index"]
                        hurtString = chosenAction["damage_dice"]+"@"+damageType

                        landString = "1d20+"+str(mod)

                        if advantage:
                            landString = landString + "!" + advantage

                        save = dc
                        if not landFudge:
                            landFudge = []
                        if not weaponFudge:
                            weaponFudge = []
                        a.update({"save" : save, "blockMult" : blockMult, "weaponFudge" : [hurtString]+weaponFudge, "landFudge" : [landString]+landFudge, "check" : threshold, "multiCrit" : ["20"]})
                        callDo(a)

                else:   
                    damageType = damage["damage_type"]["index"]
                    hurtString = damage["damage_dice"] + "@" + damageType
                    landString = "1d20+"+str(mod)

                    if advantage:
                        landString = landString + "!" + advantage

                    save = dc
                    if not landFudge:
                        landFudge = []
                    if not weaponFudge:
                        weaponFudge = []
                    a.update({"save" : save, "blockMult" : blockMult, "weaponFudge" : [hurtString]+weaponFudge, "landFudge" : [landString]+landFudge, "check" : threshold, "multiCrit" : ["20"]})
                    callDo(a)
    else:
        print('Invalid action for this combatant')
        action_result = 'Invalid action for this combatant'

    action_result = '' # This will be returned at the end
    return action_result

def command_parse(input_command_string):
    if input_command_string == "vomit":
        print ("ewwwww")
        
def applyInit(participant):
    who = participant["target"]
    combatant = geti(battleTable,who,False)
    if combatant:
        combatant["initiative"] = roll("1d20+" + str(statMod(combatant["dexterity"])))["roll"]
    else:
        print("I'm sorry I couldn't find that combatant to apply init to.")

def setBattleOrder():
    initiativeOrder = sorted(battleTable.items(), key=lambda x: int(x[1]["initiative"]), reverse=True)
    tempOrder = []
    for keyPair in initiativeOrder:
        tempOrder.append(keyPair[0])
    global battleOrder
    battleOrder = tempOrder
    
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

def getStringMethodType(fudge):
    fudgeString = ""
    method = ""
    damage = ""
     
    methodSplit = fudge.split("!")
    methodDirty = methodSplit[len(methodSplit)-1]
    method = "".join(takewhile(lambda x: (not x.isnumeric() and x != "@"), methodDirty))

    damageSplit = fudge.split("@")
    damageDirty = damageSplit[len(damageSplit)-1]
    damage = "".join(takewhile(lambda x: (not x.isnumeric() and x != "!"),damageDirty))

    fudgeString = "".join(takewhile(lambda x: (not (x in ["@","!"] )),fudge))

    return [fudgeString,method,damage]

def getStringMethodTypeOrig(fudge):
    fudgeString = ""
    method = ""
    damage = ""

    valueMethod = fudge.split("!")
    methodTypeRaw = geti(valueMethod,1,False)
    if methodTypeRaw:
        fudgeString = valueMethod[0]
        methodType = methodTypeRaw.split("@")
        method = geti(methodType,0,False)
        damage = geti(methodType,1,"")
    else:
        valueDamage = valueMethod[0].split("@")
        fudgeString = valueDamage[0]
        method = False
        damage = geti(valueDamage,1,"")

    return [fudgeString,method,damage]

def callWeapon(a):
    attackPath = a["do"].lower()
    attackJson = getJson(["equipment",attackPath])
    landFudge = a.get("landFudge")
    weaponFudge = a.get("weaponFudge")
    if attackJson:
        printUse(a)
        sender = a["sender"]
        target = a["target"]
        targetJson = battleTable[target]
        senderJson = battleTable[sender]
        mod = getMod("hit",attackJson,senderJson)
        threshold = int(targetJson["armor_class"])

        advMod = int(senderJson["advantage"])
        advNum = int(a["advantage"]) + advMod

        advantage = ""
        if advNum > 0:
           advantage = "advantage" 
        elif advNum < 0:
           advantage = "disadvantage" 

        landString = "1d20+"+str(mod)

        if advantage:
            landString = landString + "!" + advantage

        damageType = attackJson["damage"]["damage_type"]["index"]
        hurtString = attackJson["damage"]["damage_dice"]+"+"+str(getMod("dmg",attackJson,senderJson)) + "@" + damageType
        blockMult = 0
        save = False
        if not landFudge:
            landFudge = []
        if not weaponFudge:
            weaponFudge = []
        a.update({"save" : save, "blockMult" : blockMult, "weaponFudge" : [hurtString]+weaponFudge, "landFudge" : [landString]+landFudge, "check" : threshold, "multiCrit" : ["20"]})
        callDo(a)
    else:
        return False
    return True

def callCast(a):
    attackPath = a["do"].lower()
    attackJson = getJson(["spells",attackPath])
    landFudge = a.get("landFudge")
    weaponFudge = a.get("weaponFudge")
    if attackJson:
        sender = a["sender"]
        target = a["target"]
        level = a["level"]
        advantage = int(a["advantage"])
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

        blockMult = 0
        mod = 0;
        threshold = 0;
        
        dc = attackJson.get("dc")
        advMod = 0
        if dc:
            mod = getMod("saveDc", attackJson, targetJson)
            if cantrip:
                level = 0
            threshold = getMod("spellDc",attackJson,senderJson,int(level))

            if dc.get("dc_success") == "half" or dc.get("success_type") == "half":
                blockMult = 0.5
            advMod = int(targetJson["save_advantage"])
        else:
            mod = getMod("spellHit",attackJson,senderJson)
            threshold = int(targetJson["armor_class"])
            advMod = int(senderJson["advantage"])
        
        printUse(a)

        damageType = attackJson["damage"]["damage_type"]["index"]
        hurtString = dmgString + "@" + damageType

        advNum = int(a["advantage"]) + advMod

        advantage = ""
        if advNum > 0:
           advantage = "advantage" 
        elif advNum < 0:
           advantage = "disadvantage" 

        landString = "1d20+"+str(mod)

        if advantage:
            landString = landString + "!" + advantage

        save = dc
        if not landFudge:
            landFudge = []
        if not weaponFudge:
            weaponFudge = []
        a.update({"save" : save, "blockMult" : blockMult, "weaponFudge" : [hurtString]+weaponFudge, "landFudge" : [landString]+landFudge, "check" : threshold, "multiCrit" : ["20"]})
        callDo(a)
    else:
        return False
    return True

def removeDown(a=''):
    for nick, combatant in battleTable.copy().items():
        if combatant["current_hp"] <= 0:
            if not (combatant.get("downable") == "True"):
                remove({"target": nick})
            else:
                combatant["current_hp"] = 0
        elif combatant["current_hp"] > combatant["max_hp"]:
            combatant["current_hp"] = combatant["max_hp"]

def callRequest(a):
    steps = a["path"]
    result = dictify(getJson(steps))
    pprint.pprint(dictify(getJson(steps)), sort_dicts=False)

    directory = ""
    if a.get("directory"):
        directory = a["directory"]
    if a.get("file"):
        for output in a.get("file"):
            if directory:
                with open(directory+"/"+output, 'w') as f:
                    json.dump(dictify(result),f,indent=4)       
            else:
                with open(output, 'w') as f:
                    json.dump(dictify(result),f,indent=4)       

def remove(a):
    nick = a["target"]
    if battleTable.get(nick):
        myTurn = battleTable.get(nick).get("my_turn")
        nickNext = whoTurnNext()
        battleTable.pop(nick)
        battleOrder.remove(nick)
        groups = battleInfo["groups"]

        for group, members in groups.copy().items():
            if nick in members:
                members.remove(nick)

        for group in list(groups):
            if len(battleInfo["groups"][group]) == 0:
                callDelete({"path":["groups",group]})

        if myTurn and nickNext and len(battleOrder)>0:
            callJump({"target":nickNext})
    return "removed " + nick

def callAction(a):
    a["do"] = a["do"].title()
    actionKey = a["do"]
    sender = a["sender"]
    senderJson = battleTable[sender]
    actions = senderJson.get("actions")
    specialAbilities = senderJson.get("special_abilities")
    action_result = ''
    runAction = False
    if actionKey.isnumeric():
        runAction = geti(actions,int(actionKey),False)
    else:
        if actions:
            for action in actions:
                if action["name"] == actionKey:
                    runAction = action
        if specialAbilities:
            for special in specialAbilities:
                if special.get("name") == actionKey:
                    runAction = special
    if runAction:
        a["do"] = runAction["name"]
        if a["do"] == "Multiattack":
            for i in range(int(runAction["options"]["choose"])):
                for action in random.choice(runAction["options"]["from"]):
                    a["do"] = action["name"]
                    applyAction(a)
            else:
                print("This combatant cannot multiattack")
                action_result = 'This combatant cannot use ' + actionKey
        else:
            applyAction(a)
    else:
        return False
    return True

def followPath(a):
    steps = a["path"]
    diff = a.get("change")
    command = a["command"]
    target = a["target"]
    battle = battleTable
    
    finalStep = False
    if steps:
        finalStep = geti(steps,len(steps)-1,False)

    if not finalStep:
        finalStep = target
    else:
        battle = battle[target]
        for i,key in enumerate(steps):
            if i < len(steps)-1:
                if key.isnumeric():
                    battle = battle[int(key)]
                else:
                    battle = battle[key]

    if finalStep.isnumeric():
        finalStep = int(finalStep)

    if command == "mod":
        battle[finalStep] += int(diff)
    elif command == "set":
        battle[finalStep] = diff
    elif command == "list":
        pprint.pprint(dictify(battle[finalStep]), sort_dicts=False)
    elif command == "listkeys":
        string = ""
        if isinstance(battle[finalStep],list):
            print("Can't list the keys of an list. Try `list` instead of `listkeys`")
        else:
            for key, val in battle[finalStep].items():
                string += key + ","
            string[:-1]
            print(string)

def say(string):
    printJson(string)

#This is a pretty meta command that simply speeds up functionality
def callAddAuto(a):
    target = a["target"] 
    identity = a["identity"]
    do = a["do"]
    party = a["party"]
    method = a["method"]

    if not method:
        method = "random"

    if not do or do == "none":
        do = "0"

    opponent = ""
    if party:
        party = "party" 
        opponent = "enemies"
    else:
        party = "enemies"
        opponent = "party"

    if identity:
        parseAndRun("add -t "+target+" -i "+identity+" -g "+identity+"s "+party+" --append") 
        parseAndRun("auto -t "+identity+"s -c 'use -d "+do+" -t "+opponent+"!"+method+"'") 
    else:
        parseAndRun("add -t "+target+" -g "+target+"s "+party+" --append") 
        parseAndRun("auto -t "+target+"s -c 'use -d "+do+" -t "+opponent+"!"+method+"'") 

def findAvailableNick(nick):
    nickPair = nick.split("#")
    nickName = geti(nickPair,0,"")
    nickNumber = int(geti(nickPair,1,2))
    findingAvailableNick = True
    while findingAvailableNick:
        findingAvailableNick = False
        for existingNick,existingCombatant in battleTable.items():
            if existingNick == nick:
                nick = nickName + "#" + str(nickNumber)
                nickNumber += 1 
                findingAvailableNick = True
    return nick


def addCreature(a):
    name = a["target"]
    combatant = getJson(["monsters",name])

    nick = a["identity"]
    if nick == "":
        nick = combatant["index"]

    nick = findAvailableNick(nick)
    
    if combatant:
        hitDice = combatant.get("hit_dice")
        hitPoints = combatant.get("hit_points")
        if hitDice:
            hp = roll(hitDice)["roll"]
            combatant["max_hp"] = hp
            combatant["current_hp"] = hp
        elif hitPoints:
            combatant["max_hp"] = hitPoints
            combatant["current_hp"] = hitPoints

        myClass = combatant.get("class")
        if myClass:
            combatant["rest_dice"] = int(combatant["level"])
            
        combatant["disabled"] = False
        combatant["paused"] = False
        combatant["identity"] = nick
        combatant["advantage"] = 0
        combatant["save_advantage"] = 0
    
        combatant["nick"] = nick
        battleTable[nick] = combatant
        a["target"] = nick
        if a.get("group"):
            a["append"] = True
            a["member"] = [nick]
            callGroup(a)
        applyInit(a)

def legacyCreateCharacter(a):
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
    monsterCache["hit_points"] = int(input("Max Hp?"))
    monsterCache["armor_class"] = int(input("Armor Class?"))
    spellcasting = canCast(monsterCache)
    level = int(input("Level?"))
    spellcasting["level"] = level
    monsterCache["proficiency_bonus"] = crToProf(level)
    
    with open('data.json', 'w') as f:
        json.dump(dictify(cacheTable),f)

def showInfo(a):
    if a.get("info") == "all" or (not a.get("info")):
        printJson(battleInfo)
    else:
        printJson(battleInfo[a["info"]])

def callUse(a):
    if callAction(a):
        return True
    elif callWeapon(a):
        return True
    elif callCast(a):
        return True
    else:
        print("Trying to use/do something that is not a weapon nor a spell nor an action.")
        print(a)


def handleFudgeInput(fudge):
    fudgeNext = ""
    if fudge and ("$" in fudge):
        fudge = fudge.replace("$","")
        override = input("`enter`->"+ fudge +". `skip`->nothing Override?->")

        if override == "skip":
            fudge = ""
        elif len(override) != 0:
            if override == "$":
                fudgeNext = fudge + "$"
            else:
                fudgeNext = override
                fudge = override.replace("$","")
    return [fudge,fudgeNext]


def handleThreshold(a):
    resultDict = {}
    threshold = a["threshold"]
    target = a["target"]
    targetJson = battleTable[target]

    if threshold.isnumeric():
        resultDict = {"threshold":int(threshold),"save":False}
    elif threshold == "ac":
        threshold = targetJson["armor_class"]
        resultDict = {"threshold":int(threshold),"save":True}

    a.update(resultDict)

def callDo(a):
    target = a["target"]
    sender = a["sender"]
    targetJson = battleTable.get(target)
    senderJson = battleTable.get(sender)
    threshold = a["check"]
    landStrings = a["landFudge"]
    hurtStrings = a["weaponFudge"]
    blockMult = a["blockMult"]
    critValues = a["multiCrit"]
    save = bool(a.get("save"))
    threshold = handleCheckAliases(threshold,senderJson,targetJson)

    if not blockMult:
        blockMult = 0

    if not save and not critValues:
        critValues = ["20"]

    hitCrit = {"roll":0,"critHit":False}
    if not landStrings:
        landStrings = ["100"]
    for landString in landStrings:
        hitCrit = rollFudge(senderJson,targetJson,hitCrit,landString,1,False,critValues,"hit")
    hit = hitCrit["roll"]
    critHit = hitCrit["critHit"] 

    hasDamage = 0
    success = False
    if critHit:
        hasDamage = 1
        success = True
    elif not ((hit >= threshold) == save):
        hasDamage = 1
        success = True
    elif blockMult:
        success = False
        hasDamage = blockMult

    print("Hit or failed save?", str(success)+".", " Is", hit, ">=",threshold, "Crit?",critHit)

    if hasDamage:
        damage = {"roll":0,"critHit":False} #This may show critHit false but we pass into the critDmg variable below so it's ok.
        for hurtString in hurtStrings:
            damage = rollFudge(senderJson,targetJson,damage,hurtString,hasDamage,critHit,[], "dmg")
        if targetJson:
            applyDamage(targetJson,damage["roll"])

def handleHitModAliases(rollString,senderJson,targetJson, isSave=False):
    if (senderJson and not isSave) or (targetJson and isSave):
        proficiency = 0
        saveProficiency = 0
        finesseMod = 0
        martialMod = 0
        simpleMod = 0
        spellHit = 0
        if isSave:
            Json = targetJson
            proficiency = getProf(Json)
            saveProficiencies = geti(classSavesDict,Json.get("class"),[])
            if saveType in saveProficiencies:
                saveProficiency = proficiency
        else:
            Json = senderJson
            proficiency = getProf(Json)
            if "finesse" in rollString:
                finesseMod = max(statMod(int(Json["strength"])),statMod(int(Json["dexterity"])))
            else:
                finesseMod = statMod(int(Json["strength"]))

            if "martial" in Json["weapon_proficiencies"]:
                martialMod = proficiency

            if "simple" in Json["weapon_proficiencies"]:
                simpleMod = proficiency

            if "spellhit" in rollString:
                spellcasting = canCast(Json)
                spellHit = 8 + statMod(Json[expandStatWord(spellcasting["ability"]["index"])]) + getProf(Json)
        
        if not isSave:
            rollString = rollString.replace("normal",str(statMod(int(Json["strength"]))))
            rollString = rollString.replace("finesse",str(finesseMod))

            rollString = rollString.replace("martial",str(martialMod))
            rollString = rollString.replace("simple",str(simpleMod))

        rollString = rollString.replace("any",str(proficiency))
        rollString = rollString.replace("proficiency",str(proficiency))
        rollString = rollString.replace("prof",str(proficiency))

        rollString = rollString.replace("spellhit",str(statMod(int(Json["charisma"]+saveProficiency))))
        rollString = rollString.replace("str",str(statMod(int(Json["strength"]+saveProficiency))))
        rollString = rollString.replace("dex",str(statMod(int(Json["dexterity"]+saveProficiency))))
        rollString = rollString.replace("con",str(statMod(int(Json["constitution"]+saveProficiency))))
        rollString = rollString.replace("int",str(statMod(int(Json["intelligence"]+saveProficiency))))
        rollString = rollString.replace("wis",str(statMod(int(Json["wisdom"]+saveProficiency))))
        rollString = rollString.replace("cha",str(statMod(int(Json["charisma"]+saveProficiency))))
        rollString = rollString.replace("spellhit",str(spellHit))
        rollString = rollString.replace(".",str("1d20"))

    return rollString

def handleDmgModAliases(rollString,senderJson):
    if senderJson:
        rollString = rollString.replace("str",str(statMod(int(senderJson["strength"]))))
        rollString = rollString.replace("dex",str(statMod(int(senderJson["dexterity"]))))
        rollString = rollString.replace("con",str(statMod(int(senderJson["constitution"]))))
        rollString = rollString.replace("int",str(statMod(int(senderJson["intelligence"]))))
        rollString = rollString.replace("wis",str(statMod(int(senderJson["wisdom"]))))
        rollString = rollString.replace("cha",str(statMod(int(senderJson["charisma"]))))
        rollString = rollString.replace("normal",str(statMod(int(senderJson["strength"]))))
        proficiency = getProf(senderJson)
        rollString = rollString.replace("any",str(proficiency))
        rollString = rollString.replace("proficiency",str(proficiency))
        rollString = rollString.replace("prof",str(proficiency))
        finesseMod = 0
        if "finesse" in rollString:
            finesseMod = max(statMod(int(senderJson["strength"])),statMod(int(senderJson["dexterity"])))
            rollString = rollString.replace("finesse",str(0))

    return rollString

def handleCheckAliases(checkString,senderJson,targetJson):
    checkString = str(checkString).lower()
    if targetJson:
        checkString = checkString.replace("ac",str(targetJson["armor_class"]))
    if senderJson and "spelldc" in checkString:
        getProf(senderJson)
        spellcasting = canCast(senderJson)
        threshold = 8 + statMod(senderJson[expandStatWord(spellcasting["ability"]["index"])]) + getProf(senderJson)
        checkString = checkString.replace("spelldc",str(threshold))
    return int(checkString)

def getModAlt(modType, attackJson, combatantJson, additional = 0):
        modSum = 0
        if modType == "actionHit" and attackJson.get("attack_bonus"):
            modSum += attackJson.get("attack_bonus")
        else:
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
                saveType = attackJson["dc"]["dc_type"]["index"]
                modSum += statMod(combatantJson[expandStatWord(saveType)])
                saveProficiencies = geti(classSavesDict,combatantJson.get("class"),[])
                if saveType in saveProficiencies:
                    modSum += getProf(combatantJson)
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

def rollFudge(senderJson, targetJson, priorDict, fudge, successLevelMult=1, critDmg=False, critValues=[],rollType="hit"):
    if fudge:
        fudgePlusNext = handleFudgeInput(fudge)
        fudge = fudgePlusNext[0]
        fudgeNext = fudgePlusNext[1]

        stringMethodType = getStringMethodType(fudge)
        fudgeString = stringMethodType[0]
        if rollType == "hit":
            fudgeString = handleHitModAliases(fudgeString,senderJson,targetJson)
        elif rollType == "dmg":
            fudgeString = handleDmgModAliases(fudgeString,senderJson)

        method = stringMethodType[1]
        damageType = stringMethodType[2]
        affinityMod = 1
        if targetJson:
            affinityMod = getAffinityMod(targetJson,damageType)
        fudgeDict = handleFudge(fudgeString,method,priorDict,affinityMod,successLevelMult,critDmg,critValues,targetJson)
        return rollFudge(senderJson,targetJson,fudgeDict,fudgeNext,successLevelMult,critDmg,critValues,rollType)
    else:
        return priorDict

def handleFudge(fudgeString,method,currentDict,affinityMult=1,successLevelMult=1,critDmg=False,critValues=[],targetJson="only for temp hp"):
    result = 0
    temphp = affinityMult == "temphp"
    if temphp:
        affinityMult = 1

    fudgeCrit = roll(fudgeString,critDmg,affinityMult,successLevelMult,critValues)
    fudge = fudgeCrit["roll"]
    critHit = fudgeCrit["critHit"]

    fudgeCrit2 = {}
    fudge2 = "1"
    critHit2 = False
    if method in ["a","advantage","d","disadvantage"]:
        fudgeCrit2 = roll(fudgeString,critDmg,affinityMult,successLevelMult,critValues)
        fudge2 = fudgeCrit2["roll"]
        critHit2 = fudgeCrit2["critHit"]

    currentVal = currentDict["roll"]
    currentCritHit = currentDict["critHit"]
    if temphp:
        result = 0
        if method in ["a","advantage"]:
            result = max(fudge2,fudge)
        elif method in ["d","disadvantage"]:
            result = min(fudge2,fudge)
        else:
            result = fudge

        if targetJson.get("temp_hp"):
            targetJson["temp_hp"] = int(targetJson["temp_hp"]) + int(result)
        else:
            targetJson["temp_hp"] = result
        return currentDict

    if not method:
        method = "mod"
    if method in ["mod","m"]:
        critHit = critHit or currentCritHit
        result = currentVal + fudge
    #These refer to previous summed value
    if method in ["greater","g"]:
        critHit = currentCritHit or critHit
        result = max(currentVal,fudge)
    if method in ["lesser","l"]:
        critHit = currentCritHit and critHit
        result = min(currentVal,fudge)
    #These refer to a best of 2 rolls
    if method in ["advantage","a"]:
        critHit = critHit2 or critHit
        result = max(fudge2,fudge)
    if method in ["disadvantage","d"]:
        fudge2 = roll(fudgeString,critDmg,affinityMult,successLevelMult,critValues)["roll"]
        critHit2 = roll(fudgeString,critDmg,affinityMult,successLevelMult,critValues)["critHit"]
        critHit = critHit2 and critHit
        result = min(fudge2,fudge)
    if method in ["reroll","r"]:
        result = fudge

    return {"roll":result,"critHit":critHit}

def roll(dice_strings,critDmg=False,affinityMod=1,saveMult=1,critValues=[]):
    '''
    # PRECONDITIONS #
    Input: String with dice number, type, and modifier, e.g. 3d20+1

    Example Input: '1d20'
    Another Example Input: '1d4+2'
    Side Effects/State: None

    # POSTCONDITIONS #
    Return: Integer returned, representing the dice roll result
    Side Effects/State: None
    '''
    diceStrings = dice_strings.split(",")
    total = 0
    critHit = False

    for dice_string in diceStrings: 
        dsplit = dice_string.split("d")
        usesDice = len(dsplit)>1
        diceMod = 0
        if usesDice:
            remaining = dsplit[1]
            if "+" in dice_string:
                remaining = dsplit[1].split("+")
                diceMod = float(remaining[1])
                remaining = remaining[0]
            elif "-" in dice_string:
                remaining = dsplit[1].split("-")
                diceMod = -1*float(remaining[1])
                remaining = remaining[0]
            
            diceCount = int(dsplit[0])

            if critDmg:
                diceCount = diceCount*2

            diceType = int(remaining)
            for x in range(diceCount):
                roll = math.ceil(diceType*random.random())
                total += roll
                if (diceCount == 1) and (str(roll) in critValues):
                    critHit = True
            total += diceMod
        else:
            total += int(dice_string)

    total = math.floor(total * affinityMod * saveMult)

    message = dice_strings.replace(","," + ")
    if critDmg:
        message = "CRIT! Double dice count for "+message
    if affinityMod != 1:
        message = "AFFINITY! " + str(affinityMod) +"*("+ message +")"
    if saveMult != 1:
        message = "SAVE! " + str(saveMult) +"*("+ message +")"

    print("roll",message,"=",total)
    
    return {"roll":int(total), "critHit":critHit}

def helpMessage(a):
    for key, value in a["commandDescriptions"].items():
        print(key, ":", value)
    print("For more detailed help on a given *commandName* run:\n commandName --help")

def whoTurn():
    for i, nick in enumerate(battleOrder):
        x = battleTable[nick]
        if x.get("my_turn"):
            return battleOrder[i]

    return geti(battleOrder,0,False) 

def whoTurnNext():
    turn = 0 
    for i, nick in enumerate(battleOrder):
        x = battleTable[nick]
        if x.get("my_turn"):
            turn = i
    return geti(battleOrder,(turn+1) % len(battleOrder),False)

def validateCommand(commandDict):
    a = commandDict
    a = handleAllAliases(a)
    has = hasParse(a["command"])
    
    if has.get("target"):
        targets = onlyAlive(a["target"])
        oneTarget = geti(targets,0,False)
        if not oneTarget:
            return False

    if has.get("sender"):
        senders = onlyAlive(a["sender"])
        oneSender = geti(senders,0,False)
        if not oneSender:
            return False
    #Maybe some day add validation here that checks api and cache to see if a["do"] is a spell, action, or weapon that exists. For now I don't see a way to do it that isn't very slow due to calling the api far more than needed.

    return True

def validateCommands(combatantJson):
    commands = combatantJson.get("autoDict")
    if commands:
        for commandDict in commands:
            if validateCommand(commandDict.copy()):
                return True
    return False

def turnTo(nickNext):
    callJump({"target": nickNext})
    callTurn({"target": nickNext},False)

def callTurn(a,directCommand=True):
    if len(battleOrder) != 0:
        nickCurrent = a["target"]
        if directCommand:
            callJump({"target" : nickCurrent})
        if whoTurn() == nickCurrent:
            nickNext = whoTurnNext()

            combatantJson = battleTable[nickCurrent]
            isValidCommand = validateCommands(combatantJson)
            if isValidCommand and ((not combatantJson["paused"]) or directCommand):
                if not combatantJson["disabled"]:
                    runAuto(combatantJson)
                if whoTurn() == nickCurrent:
                    nickNext = whoTurnNext() #In case the next person died
                else:
                    nickNext = whoTurn() #If we died during the action, remove set the next turn to current
                turnTo(nickNext)
            elif directCommand:
                turnTo(nickNext)
            else:
                #"Paused due to no target for auto commands or no commands or you simply marked this creature for pausing"
                print("Paused --> Needs commands?", not combatantJson.get("autoDict"), ". Paused set?",combatantJson["paused"], ". No targets or senders?", (not isValidCommand) and bool(combatantJson.get("autoDict")))
        else:
            print("Bounced an invalid turn attempt trying to callturn on someone who's turn it is not")
    else:
        print("Hmm, nobodies home to do a turn")

def callJump(a):
    nickCurrent = whoTurn()
    if whoTurn:
        battleTable[nickCurrent]["my_turn"] = False
    battleTable[a["target"]]["my_turn"] = True

def callSkip(a):
    do=0

def callPause(a):
    target = a["target"]
    combatantJson = battleTable[target]
    combatantJson["paused"] = True 
def callResume(a):
    target = a["target"]
    combatantJson = battleTable[target]
    combatantJson["paused"] = False 
def callEnable(a):
    target = a["target"]
    combatantJson = battleTable[target]
    combatantJson["disabled"] = False 
def callDisable(a):
    target = a["target"]
    combatantJson = battleTable[target]
    combatantJson["disabled"] = True

class ArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        print(self.format_help())
        self.exit(2, '%s: error: %s\n' % (self.prog,message))
    def print_help(self, file=None):
        print(self.format_help())

def hasParse(command):
    attributeDict = {}
    attributeList = hasDict.get(command)
    if attributeList:
        for attribute in attributeList:
            attributeDict[attribute] = True
    return attributeDict

def hasAttribute(attribute,command):
    if attribute in hasDict.get(command):
        return True
    else:
        return False

def onlyAlive(combatants):
    aliveCombatants = []
    for combatant in combatants:
        if battleTable.get(combatant) or combatant == "?" or combatant == "ambiguous":
            aliveCombatants.append(combatant)
        elif battleInfo.get("groups").get(combatant):
            aliveCombatants = aliveCombatants + battleInfo.get("groups").get(combatant)
    return aliveCombatants

def handleStar(starString):
    combatantList = []
    parts = starString.split("*")
    for combatant in battleOrder:
        addCombatant = True
        for part in parts:
            if not (part in combatant):
                addCombatant = False
        if addCombatant:
            combatantList.append(combatant)
    return combatantList

def handleAliases(combatantLists,resolve=True,doAll=False):
    result = []
    for combatantListAliased in combatantLists:
        listMethod = combatantListAliased.split("!")
        combatantListAliased = listMethod[0].split(",")
        combatantList = []

        for index,combatant in enumerate(combatantListAliased):
            if combatant.isnumeric():
                comb = geti(battleOrder,int(combatant),False)
                if comb:
                    combatantList.append(comb)
            
            if resolve:
                if combatant in battleInfo["groups"].keys():
                    combatantList = onlyAlive(combatantList + battleInfo["groups"][combatant])
                elif combatant == "all":
                    combatantList = combatantList + battleOrder
                elif combatant == "me":
                    combatantList.append(whoTurn())
                elif combatant == "?":
                    combatantList.append("?")
                elif "*" in combatant:
                    combatantList = combatantList + handleStar(combatant)

            if not combatantList:
                combatantList.append(combatant)

            if resolve:
                #should be no group names in here at this point so let's thin out the non existent names
                combatantList = onlyAlive(combatantList)

        method = geti(listMethod,1,"simultaneous")
        livingCount = len(combatantList)
        if resolve:
            if combatantList:
                if method == "order" or method == "o":
                    result.append(combatantList[0])
                elif method == "random" or method == "r":
                    randomCombatant = combatantList[math.floor(livingCount*random.random())]
                    result.append(randomCombatant)
                elif method == "simultaneous" or method == "s":
                    result = result + combatantList
                else:
                   print("Invalid method for targetting") 
        else:
            resultString = ""
            for i ,combatant in enumerate(combatantList):
                comma = ","
                if i == 0:
                    comma = ""
                resultString = resultString + comma + combatant 
            resultString = resultString + "!" + method
            result.append(resultString)

        if result and not doAll:
            break

    return result

def handleNumerics(combatantList):
    result = []
    for combatant in combatantList:
        if combatant.isnumeric():
            comb = geti(battleOrder,int(combatant),False)
            if comb:
                result.append(comb)
        else: 
            result.append(combatant)
    return result

def handleAllAliases(toDict,resolve=True):
    command = toDict["command"]
    has = hasParse(command)

    #sender is optional some times
    if (not has.get("no-alias") and has.get("sender")) and toDict.get("sender"):
        toDict["sender"] = handleAliases(toDict["sender"],resolve,True)

    if (not has.get("no-alias") and has.get("target")) and toDict.get("target"):
        toDict["target"] = handleAliases(toDict["target"],resolve,has.get("target-all"))

    if toDict.get("group") and command != "add":
        toDict["member"] = handleAliases(toDict["member"],resolve,True)

    if has.get("target-single-optional") and resolve:
        if (not toDict.get("target")):
            if command == "turn":
                toDict["target"] = [whoTurn()]
            else:
                toDict["target"] = [whoTurnNext()]
        else:
            toDict["target"] = [toDict["target"]]
        toDict["target"] = handleNumerics(toDict["target"])
        
    return toDict


def runAuto(combatantJson, target=""):
    autoDicts = combatantJson.get("autoDict")
    for commandDict in autoDicts:
        if target:
            commandDict["target"] = [target]
        parse_command_dict(commandDict)

def callAuto(a):
    sender = a["sender"]
    target = a["target"]
    senderJson = battleTable[sender]
    runAuto(senderJson,target)

def callRun(a):
    for string in a["string"]:
        parseAndRun(string)

def setAutoDict(a):
    combatant = a["target"]
    combatantJson = battleTable[combatant]
    mode = a["mode"]
    if mode == "append" or mode == "mod":
        if not combatantJson.get("autoDict"):
            combatantJson["autoDict"] = []
    elif mode == "set":
        combatantJson["autoDict"] = []

    commandDicts = processCommandStrings(a)
    if mode == "mod":
        if a.get("path"):
            commandDicts = modInfo([combatant,"autoDict"]+a["path"],commandDicts,battleTable)
        else:
            commandDicts = modInfo([combatant,"autoDict"],commandDicts,battleTable)
    for commandDict in commandDicts:
        command = commandDict["command"]
        has = hasParse(command)
        if has.get("sender") and ((not commandDict.get("sender")) or (geti(commandDict.get("sender"),0,False) == "none")):
            commandDict["sender"] = [combatant]
        if has.get("target") and ((not commandDict.get("target")) or (geti(commandDict.get("target"),0,False) == "none")):
            commandDict["target"] = [combatant]
        if mode == "append" or mode == "set":
            combatantJson["autoDict"].append(commandDict)

def processCommandStrings(a):
    if a.get("command") != "store":
        combatant = a["target"]
        combatantJson = battleTable.get(combatant)
        autoDicts = combatantJson.get("autoDict")
        startIndex = a.get("path")
        if not startIndex:
            startIndex = 0

    commandDicts = []
    for index,commandString in enumerate(a["commandString"]):
        if (not (a.get("method") in ["append","a"])) and a.get("command") != "store":
            args = commandString.split(" ")
            subCommand = args[0]
            if not(subCommand in funcDict):
                baseCommand = getBaseCommand(subCommand)
                if not baseCommand:
                    subCommand = autoDicts[index+startIndex]["command"]
                    commandString = subCommand +" "+ commandString
            
        argDictTemps = parse_command_string(commandString,a.get("command"),a.get("verify"))
        for argDictTemp in argDictTemps:
            commandDicts.append(handleAllAliases(argDictTemp,a["resolve"]))
    return commandDicts

#This is an unused function but it makes it clear that most of processCommandStrings relates to setAutoDict and not callStore
def proccessCommandStringsStore(a):
    commandDicts = []
    for index,commandString in enumerate(a["commandString"]):
        argDictTemps = parse_command_string(commandString,a.get("command"),a.get("verify"))
        for argDictTemp in argDictTemps:
            commandDicts.append(handleAllAliases(argDictTemp,a["resolve"]))

    return commandDicts

def callStore(a):
    commandDicts = processCommandStrings(a)
    path = ["commands"]+a["path"]
    mode = a["mode"]
    if mode == "append":
        storeInfo(path,commandDicts,True)
    elif mode == "set":
        storeInfo(path,commandDicts,False)
    elif mode == "mod":
        modInfo(path,commandDicts,battleInfo)
    else:
        print("Invalid mode snuck by somehow")

def getInfo(path):
    return get_nested_item(battleInfo,path)

#add a mode which allows for the use of append_value instead of update so you could bless someone with two different options
def modInfo(path,modDictionaries,dictionary):
    startPosition = path[-1]
    if startPosition == None:
        startPosition = 0
        path = path[:-1]
    elif startPosition.isnumeric():
        startPosition = int(startPosition)
        path = path[:-1]
    else:
        startPosition = 0
    existingDictionaries = get_nested_item(dictionary,path)
    if existingDictionaries:
        for index, modDictionary in enumerate(modDictionaries):
            existingDictionary = geti(existingDictionaries,index+startPosition,False)
            if existingDictionary:
                modDictionary = weedNones(modDictionary)
                existingDictionary.update(modDictionary)
            else:
                dictionary = set_nested_item(dictionary, path+[index+startPosition], modDictionary)
    else:
        dictionary = set_nested_item(dictionary, path, modDictionaries)
    return get_nested_item(dictionary,path)

def append_value(dict_obj, key, value):
    if key in dict_obj:
        if not isinstance(dict_obj[key], list):
            dict_obj[key] = [dict_obj[key]]
        dict_obj[key].append(value)
    else:
        dict_obj[key] = value

        
def storeInfo(path,value,append):
    global battleInfo
    if append:
        appendTo = get_nested_item(battleInfo,path)
        if appendTo:
            battleInfo = set_nested_item(battleInfo, path, appendTo + value)
        else:
            battleInfo = set_nested_item(battleInfo, path, value)
    else:
        battleInfo = set_nested_item(battleInfo, path, value)

def callGroup(a):
    members = a["member"] 
    groups = a["group"]
    append = a["append"]
    remove = a.get("remove")
    for group in groups:
        if remove:
            for member in members:
                if member in battleInfo["groups"][group]:
                    battleInfo["groups"][group].remove(member)
                if len(battleInfo["groups"][group]) == 0:
                    callDelete({"path":["groups",group]})
        else:
            storeInfo(["groups",group],list(set(members)),append)

def pathing(steps,dictionary):
    for step in steps:
        if step.isnumeric():
            dictionary = dictionary.get(int(step))
        else:
            dictionary = dictionary.get(step)
    return dictionary

def callDelete(a):
    path = a["path"]
    deep = pathing(path[:-1],battleInfo)
    if isinstance(deep, list):
        deep.pop(int(path[-1]))
    else:
        deep.pop(path[-1],None)

def callShortRest(a):
    combatant = a["target"]
    combatantJson = battleTable[combatant]
    if combatantJson.get("rest_dice"):
        if combatantJson["rest_dice"] > 0 and combatantJson["current_hp"] < combatantJson["max_hp"]:
            combatantJson["current_hp"] = combatantJson["current_hp"] + roll(hitDieFromClass(combatantJson["class"])+"+"+str(statMod(int(combatantJson["constitution"]))))["roll"]
            combatantJson["rest_dice"] = combatantJson["rest_dice"] - 1

def callLongRest(a):
    combatant = a["target"]
    combatantJson = battleTable[combatant]
    if combatantJson.get("rest_dice"):
        combatantJson["rest_dice"] = int(combatantJson["level"])
        combatantJson["current_hp"] = combatantJson["max_hp"]

def hitDieFromClass(myClass):
    d6 = ["sorcerer","wizard"]
    d8 = ["artificer","bard","cleric","druid","monk","rogue","warlock"]
    d10 = ["fighter","paladin","ranger"]
    d12 = ["barbarian"]
    dice = "1d8"
    if myClass.lower() in d6:
        dice = "1d6"
    if myClass.lower() in d8:
        dice = "1d8"
    if myClass.lower() in d10:
        dice = "1d10"
    if myClass.lower() in d12:
        dice = "1d12"
    return dice

def dictToCommandString(dictionary):
    commandString = dictionary["command"]
    for key, value in dictionary.items():
        valueString = ""
        if key == "commandString":
            for string in value:
                    valueString = valueString + " '" + string + "'" 
            commandString = commandString +" --"+ key + valueString

        elif key != "command" and key != "has":
            if isinstance(value,list):
                for val in value:
                    valueString = valueString + " " + str(val)
            else:
                if isinstance(value, bool):
                    valueString = ""
                else:
                    valueString = " " + str(value)

            if bool(value) and (not (key == "times" and value == 1)):
                commandString = commandString +" --"+ key + valueString
    return commandString

def populateParserArguments(parser,has,metaHas,verify=True):
    if has.get("fudge"):
        parser.add_argument("--landFudge", "-l", help='A dice string to be used for fudging a hit',nargs='+',default=[])
        parser.add_argument("--weaponFudge", "-w", help='A dice string to be used for fudging damage',nargs='+',default=[])

    if has.get("times"):
        parser.add_argument("--times", "-n", help='How many times to run the command')

    if has.get("sender"):
        parser.add_argument("--sender", "-s", required=(not metaHas.get("optionalSenderAndTarget")) and not has.get("optionalSenderAndTarget") and verify and not has.get("optionalTarget"), help='sender/s for command', nargs='+')

    if has.get("must-do"):
        parser.add_argument("--do", "-d", required=(True and verify), help='What the sender is using on the target', nargs='+')

    if has.get("do"):
        parser.add_argument("--do", "-d", help='What the sender is using on the target', nargs='+')

    if has.get("path"):
        parser.add_argument("--path", "-p", required=(not has.get("optionalPath")) and verify, nargs='+',help='Path for json or api parsing with command. Space seperated')
        if has.get("change"):
            parser.add_argument("--change", "-c", required=True and verify, help='What you would like to set or modify a number by')
            parser.add_argument("--roll", "-r", help='Whether or not the change indicated is a dice change', dest='roll', action='store_true')
            parser.set_defaults(roll=False)

    if has.get("level"):
        parser.add_argument("--level", help='Level to cast a spell at')

    if has.get("target"):
        if (has.get("identity") or has.get("file")):
            parser.add_argument("--target", "-t", required=True and verify, help='Target/s creature types to fetch from the cache the api or a file', nargs='+')
        else:
            parser.add_argument("--target", "-t", required=((not metaHas.get("optionalSenderAndTarget")) and verify and (not has.get("optionalSenderAndTarget"))), help='Target/s for command', nargs='+')

    if has.get("target-single-optional"):
        parser.add_argument("--target", "-t", help='Target for command')

    if has.get("group"):
        req = True and verify
        if has.get("no-alias"):
            req = False
        else:
            parser.add_argument("--member", "-m", help='members to be placed into a group', required=req, nargs='+')
        parser.add_argument("--group", "-g", help='A group which will be reduced to a target list', required=req, nargs='+')

    if has.get("category"):
        parser.add_argument("--category", "-c", choices=['monsters','equipment','spells'], help='A category for content',required=True and verify)

    if has.get("commandString"):
        parser.add_argument("--commandString", "-c", help='A command string to be run', nargs='+',required=True and verify)
        parser.add_argument("--resolve", "-r", help='Whether or not to resolve aliases inside command string. party -> guy1 guy2 girl', dest='resolve', action='store_true')
        parser.set_defaults(resolve=False)

    if has.get("arbitraryString"):
        parser.add_argument("--string", "-s", help='A string to run from the very top level with no processing when saved', nargs='+',required=True and verify)

    if has.get("allowIncomplete"):
        parser.add_argument("--verify", "-v", help='Whether or not what is being stored is an incomplete command', dest='verify', action='store_true')

    if has.get("identity"):
        parser.add_argument("--identity", "-i", help='Identities for added monsters', nargs='+')

    if has.get("info"):
        parser.add_argument("--info", "-i", help='Info category to interact with')

    if has.get("advantage"):
        parser.add_argument("--advantage", "-a", choices=["1","0","-1","?"], help='Advantage for attacks', nargs='+')

    if has.get("file"):
        parser.add_argument("--file", "-f", help='The file you would like to interact with', nargs='+')
        parser.add_argument("--directory", "-d", help='The directory path you would like to interact with')
        
    if has.get("mode"):
        parser.add_argument("--mode", "-m", choices=["set","append","mod","?"],help='How does this information fit with the previous existing information?')
        parser.set_defaults(mode="mod")

    if has.get("append"):
        parser.add_argument("--append", "-a", help='Whether this command should replace the existing set or be added on', dest='append', action='store_true')
        parser.set_defaults(append=False)

    if has.get("check"):
        parser.add_argument("--blockMult", "-b", help='How much damage remains when blocked?')
        parser.add_argument("--check", "-c", help='What the threshold is for blocking. To include level of spell simply do spelldc+3. If it is a third level spell', default=-100)
        parser.add_argument("--save", "-d", help='Is this a save threshold?', dest='append', action='store_true')
        parser.add_argument("--multiCrit", "-m", help='values which constitute a critical', nargs='+')
        parser.set_defaults(append=False)

    if has.get("party"):
        parser.add_argument("--party", "-p", help='Should this be automated as a member of the party instead of as an enemy?', dest='party', action='store_true')
        parser.set_defaults(party=False)

    if has.get("method"):
        parser.add_argument("--method", "-m", help='How to target enemies', choices=["r","s","o","simultaneous","random","order"])

    if has.get("remove"):
        parser.add_argument("--remove", "-r", help='Whether this command should replace the existing set or be added on', dest='remove', action='store_true')
        parser.set_defaults(remove=False)

    if has.get("dice"):
        parser.add_argument("--dice", "-d", help='A dice string to be used',required=True and verify, nargs='+')

funcDict = {
"do" : callDo,
"use" : callUse,
"action" : callAction,
"weapon" : callWeapon,
"cast" : callCast,
"remove" : remove,
"request" : callRequest,
"set" : followPath,
"mod" : followPath,
"list" : followPath,
"listkeys" : followPath,
"add" : addCreature,
"init" : applyInit,
"load" : callLoad,
"help" : helpMessage,
"turn" : callTurn,
"auto" : setAutoDict,
"group" : callGroup,
"info" : showInfo,
"store" : callStore,
"roll" : rollString,
"shortrest" : callShortRest,
"longrest" : callLongRest,
"jump" : callJump,
"skip" : callSkip,
"callAuto" : callAuto,
"pause" : callPause,
"resume" : callResume,
"enable" : callEnable,
"disable" : callDisable,
"save" : "",
"exit" : "",
"abort" : "",
"addAuto": callAddAuto,
"delete": callDelete,
"run": callRun,
}

senderList = ["sender","target","advantage","times","fudge","must-do"]
hasDict = {
"action": senderList,
"weapon": senderList,
"cast": senderList + ["level"],
"use": senderList + ["level"],
"request": ["path","file"],
"mod": ["path", "target", "change", "times", "target-all","sort"],
"set": ["path", "target", "change", "target-all","sort"],
"list": ["path", "target", "target-all", "optionalPath"],
"listkeys": ["path", "target", "target-all"],
"store": ["path", "commandString", "mode", "allowIncomplete"],
"init": ["target", "sort", "target-all"],
"remove": ["target", "target-all"],
"auto": ["target", "commandString", "mode", "target-all", "optionalSenderAndTarget","path","allowIncomplete","optionalPath"],
"add": ["target", "identity", "sort", "times", "group", "append", "no-alias", "target-all"],
"longrest": ["target", "times", "target-all"],
"shortrest": ["target", "times", "target-all"],
"callAuto": ["target","times", "target-all","sender","optionalTarget"],
"enable": ["target", "target-all"],
"disable": ["target", "target-all"],
"pause": ["target", "target-all"],
"resume": ["target", "target-all"],
"load": ["file", "category"],
"roll": ["times", "dice"],
"turn": ["times", "target-single-optional"],
"group": ["group", "append","remove"],
"info": ["info"],
"jump": ["target-single-optional"],
"addAuto": ["target", "identity", "sort", "times", "no-alias", "target-all","do","party","method"],
"delete": ["path"],
"run": ["arbitraryString"],
"do": ["target", "fudge", "check","sender","optionalSenderAndTarget"],
}

def getBaseCommand(command):
    if command in funcDict:
        return command
    comList = battleInfo["commands"].get(command)
    comDict = geti(comList, 0,False)
    com = False
    if comDict:
        com = comDict.get("command")
    if com:
        if com in funcDict:
            return com
        else:
            return getBaseCommand(com)
    else:
        return False

def parseOnly(command_string_to_parse,metaCommand="",verify=True):
    args = command_string_to_parse.split(" ")
    command = args[0]

    entryString = ""
    desc = "Dnd DM Assistant"
    if "-" in command and not verify:
        command = ""
        entryString = command_string_to_parse
    else:
        entryString = " ".join(args[1:])
    desc = geti(command_descriptions_dict,command,'Dnd DM Assistant')

    has = hasParse(command)
    metaHas = hasParse(metaCommand)
    parser = ArgumentParser(
            prog=command,
            description=desc,
            formatter_class=argparse.RawTextHelpFormatter
            )
    populateParserArguments(parser,has,metaHas,verify)
    entries = shlex.split(entryString)
    #parameters
    a = parser.parse_args(entries)
    argDictMain = vars(a)
    argDictMain["command"] = command

    return argDictMain

def replaceWithInput(value,key):
    replacing = True
    result = value
    while replacing:
        if "?" in result:
            result = result.replace("?",input("What is the "+str(key)+"?"),1)
        else:
            replacing = False
    return result

def parseQuestions(a):
    dictionary = a
    for key, value in dictionary.items():
        if key != "commandString":
            if isinstance(value,list):
                dictionary[key] = []
                for val in value:
                    result = replaceWithInput(val,key)
                    dictionary[key].append(result)
            elif value and (not isinstance(value, bool)):
                result = replaceWithInput(value,key)
                dictionary[key] = result

def parse_command_string(command_string_to_parse,metaCommand="",verify=True):
    args = command_string_to_parse.split(" ")
    command = args[0]
    argDictMains = []

    if not(command in funcDict):
        commandDict = battleInfo["commands"].get(command)
        if commandDict:
            if len(args) > 1:
                baseCommand = getBaseCommand(command)
                if baseCommand:
                    if len(commandDict) == 1:
                        entryString = " ".join(args[1:])
                        aliasDict = parseOnly(baseCommand + " " + entryString,metaCommand,False)
                        aliasDict = weedNones(aliasDict)
                        copyDict = copy.deepcopy(commandDict[0])
                        copyDict.update(aliasDict)
                        argDictMains.append(copyDict)
                    else:
                        print("Can't fill alias arguments for aliases that map to multiple commands")
                else:
                    print("Here would be some arbitrary command handling that does it's best to get args without command context")
            else:
                argDictMains = copy.deepcopy(commandDict)
        else:
            print("Invalid command. None specified or not an alias nor built in command")
    else:
        argDictMains.append(parseOnly(command_string_to_parse,metaCommand,verify))

    if "?" in command_string_to_parse:
        print("Evaluating manual input for:\n"+command_string_to_parse)
        for argDictMain in argDictMains:
            parseQuestions(argDictMain)

    return argDictMains

def parseAndRun(command_string_to_run):
    command_string_to_run = command_string_to_run.replace("\"-","\" -")#Ugh arg parse can't handle: auto -t guy -c "-t guy"
    command_string_to_run = command_string_to_run.replace("\'-","\' -")#Ugh arg parse can't handle: auto -t guy -c "-t guy"
    #But it can handle: auto -t guy -c " -t guy" 
    returns = []
    for dictionary in parse_command_string(command_string_to_run):
        returns.append(parse_command_dict(dictionary))
    return returns

def parse_command_dict(argDictToParse):
    argDictMain = copy.deepcopy(argDictToParse)
    command = argDictMain["command"]
    has = hasParse(command)

    command_result = ''

    times = argDictMain.get("times")
    if not times:
        times = "1";

    if command == "help":
        argDictMain["commandDescriptions"] = command_descriptions_dict

    if not has.get("sender"):
        argDictMain["sender"] = ["none"]

    if not has.get("target") and not has.get("target-single-optional"):
        argDictMain["target"] = ["none"]

    if command == "do":
        if argDictMain["target"] == None:
            argDictMain["target"] = ["ambiguous"]
        if argDictMain["sender"] == None:
            argDictMain["sender"] = ["ambiguous"]

    if argDictMain.get("roll"):
        argDictMain["change"] = roll(argDictMain["change"])["roll"]

    if command == "save":
        saveBattle()
        return True
        
    if command == "exit":
        saveBattle()
        return "EXIT"

    if command == "abort":
        return "EXIT"

    argDictCopy = handleAllAliases(copy.deepcopy(argDictMain))
    argDictSingle = copy.deepcopy(argDictCopy)

    for time in range(int(times)):
        for sender in argDictCopy["sender"]:
            argDictSingle["sender"] = sender
            for number,target in enumerate(argDictCopy["target"]):
                argDictSingle["target"] = target

                if has.get("identity"):
                    argDictSingle["identity"] = geti(argDictCopy["identity"],number,target)
                if has.get("advantage"):
                    argDictSingle["advantage"] = geti(argDictCopy["advantage"],number,0)

                if battleTable.get(target) or not has.get("target") or has.get("no-alias") or command == "load" or target == "ambiguous":
                    if not argDictCopy.get("do"):
                        argDictCopy["do"] = ["none"]
                    for do in argDictCopy["do"]:
                        argDictSingle["do"] = do
                        command_result += str(funcDict[command](copy.deepcopy(argDictSingle)))
                        removeDown()
                        argDictCopy = handleAllAliases(copy.deepcopy(argDictMain))
                else:
                    command_result += "ignored an invalid target"
                    print('ignored an invalid target',target)
    if has.get("sort"):
        setBattleOrder()

    return command_result

def run_assistant():
    results = []
    error_count = 0 # Detect error spam
    setBattleOrder()
    while not("EXIT" in results):
        try:
            getState()
            command_input_string = input("Command?")
            results = parseAndRun(command_input_string)
        except SystemExit:
            print("")#This catches argParses attempts to exit.

        except Exception:
            print("ERROR, enter the 'exit' command to exit.")
            traceback.print_exc()

            # Error Spam Prevention #
            error_count = error_count + 1
            if error_count >= 10:
                error_spam_prompt = input('Error count has reached 10. \n Program will now exit. \n But you can enter "continue" if you still \n want to keep this up? ->')
                if error_spam_prompt.lower() != 'continue':
                    results = ["EXIT"] # Brute force error spam prevention
                    sys.exit('Exit due to error Spam')
                else:
                    error_count = 0

if __name__ == "__main__":
    run_assistant()
