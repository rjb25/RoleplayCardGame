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
        internal_dict_value = internal_dict_value.get(k, None)
        if internal_dict_value is None:
            return None
    return internal_dict_value
                
def load(a):
    with open(a["file"]) as f:
            return json.load(f)

def loadCategory(a):
    creatureJson = load(a)
    global cacheTable
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
            print(i,x["initiative"],nick,x["index"],str(x["current_hp"])+"/"+str(x["max_hp"])+turn)
            state_result.append(str(x["initiative"]) + ' ' + nick + ' ' + str(x["index"]) + ' ' + str(x["current_hp"]) + "/" + str(x["max_hp"]))
        return state_result

def rolld20(advantage = 0, modifier=0):
    d20 = 0
    mod = str(modifier)
    if advantage == 0:
        d20 = roll("1d20+"+mod)
    elif advantage > 0:
        d20 = max(roll("1d20+"+mod),roll("1d20+"+mod))
    elif advantage < 0:
        d20 = min(roll("1d20+"+mod),roll("1d20+"+mod))
    else:
        print("invalid advantage type", advantage)
        action_result += '\n' + advantage + ' is an invalid advantage type.'
        d20 = roll("1d20+"+mod)
    return d20

def roll(dice_string,crit=False):
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
    dsplit = dice_string.split("d")
    usesDice = len(dsplit)>1
    sum = 0
    diceMod = 0
    if usesDice:
        remaining = dsplit[1].split("+")
        if "+" in dice_string:
            diceMod = float(remaining[1])
        
        diceCount = int(dsplit[0])
        if crit:
            diceCount = diceCount*2
            dice_string = "2*"+dice_string
        diceType = float(remaining[0])
        for x in range(diceCount):
            sum += math.ceil(diceType*random.random())
    else:
        sum = int(dice_string)
    print("roll",dice_string,"=",sum+diceMod)
    
    return int(sum + diceMod)

def rollString(a):
    roll(a["dice"])

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

def applyAction(a):
    actionKey = a["do"]
    sender = a["sender"]
    target = a["target"]
    advantage = a["advantage"]
    senderJson = battleTable[sender]
    targetJson = battleTable[target]
    actions = senderJson.get("actions")
    specialAbilities = senderJson.get("special_abilities")

    action = False
    action_result = ''
    for act in actions:
        if act["name"] == actionKey:
            action = act
    for special in specialAbilities:
        if special["name"] == actionKey:
            action = special
    if action:
        threshold = targetJson["armor_class"]

        advMod = senderJson["advantage"]
        dc = action.get("dc")

        saveMult = 0
        mod = 0
        if dc:
            threshold = dc.get("dc_value")
            if not threshold:
                print("Has a dc for this action but no dc_value. Defaulting to 10")
                threshold = 10

            if dc.get("dc_success") == "half" or dc.get("success_type") == "half":
                saveMult = 0.5
            advMod = senderJson["advantage"]
            mod = getMod("saveDc", action, targetJson)
        else:
            mod = getMod("actionHit",action,senderJson)

        hitCrit = checkHit(mod,threshold,advantage+advMod,bool(dc))
        if hitCrit[0]:
            saveMult = 1
        if hitCrit[0] or saveMult !=0:
            for damage in action["damage"]:         
                if damage.get("choose"):
                    for actions in range(int(damage["choose"])):
                        chosenAction = random.choice(damage["from"])
                        applyDamage(targetJson,saveMult*roll(chosenAction["damage_dice"],hitCrit[1]),chosenAction["damage_type"])
                else:   
                    applyDamage(targetJson,saveMult*roll(damage["damage_dice"],hitCrit[1]),damage["damage_type"])
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
        combatant["initiative"] = roll("1d20+" + str(statMod(combatant["dexterity"])))
    else:
        print("I'm sorry I couldn't find that combatant to apply init to.")

def setBattleOrder():
    initiativeOrder = sorted(battleTable.items(), key=lambda x: x[1]["initiative"], reverse=True)
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

def callWeapon(a):
    attackPath = a["do"].lower()
    attackJson = getJson(["equipment",attackPath])
    if attackJson:
        sender = a["sender"]
        target = a["target"]
        advantage = a["advantage"]
        targetJson = battleTable[target]
        senderJson = battleTable[sender]
        mod = getMod("hit",attackJson,senderJson)
        threshold = targetJson["armor_class"]
        advMod = senderJson["advantage"]
        hitCrit = checkHit(mod,threshold,advantage+advMod)
        if hitCrit[0]:
            hurt = roll(attackJson["damage"]["damage_dice"]+"+"+str(getMod("dmg",attackJson,senderJson)),hitCrit[1])
            applyDamage(targetJson,hurt,attackJson["damage"]["damage_type"])

def checkHit(mod,threshold,advantage=0,save=False):
    d20 = rolld20(advantage,mod)
    got20 = ((int(d20) - int(mod)) == 20)
    crit = (got20) and (not save)
    success = False
    if crit:
        success = True
    else:
        success = not ((d20 >= threshold) == save)

    print("Hit?", success, "is", d20, ">",threshold, "Crit?",crit)
    return [success, crit]

def callCast(a):
    attackPath = a["do"].lower()
    attackJson = getJson(["spells",attackPath])
    if attackJson:
        sender = a["sender"]
        target = a["target"]
        level = a["level"]
        advantage = a["advantage"]
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

        saveMult = 0
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
                saveMult = 0.5
            advMod = senderJson["advantage"]
        else:
            mod = getMod("spellHit",attackJson,senderJson)
            threshold = targetJson["armor_class"]
            advMod = targetJson["advantage"]
        
        hitCrit = checkHit(mod,threshold,advantage+advMod,bool(dc))
        if hitCrit[0]:
            applyDamage(targetJson,roll(dmgString,hitCrit[1]),attackJson["damage"]["damage_type"])
        elif saveMult != 0:
            applyDamage(targetJson,saveMult*roll(dmgString,hitCrit[1]),attackJson["damage"]["damage_type"])

def removeDown(a=''):
    for nick, combatant in battleTable.copy().items():
        if combatant.get("current_hp"):
            if combatant["current_hp"] <= 0:
                remove({"target": nick})
            elif combatant["current_hp"] > combatant["max_hp"]:
                combatant["current_hp"] = combatant["max_hp"]
        else:
            print(nick, "does not have key current_hp")

def callRequest(a):
    steps = a["path"]
    pprint.pprint(dictify(getJson(steps)), sort_dicts=False)

def remove(a):
    nick = a["target"]
    if battleTable.get(nick):
        myTurn = battleTable.get(nick).get("my_turn")
        nickNext = whoTurnNext()
        battleTable.pop(nick)
        battleOrder.remove(nick)
        if myTurn and nickNext:
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
                if special["name"] == actionKey:
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
    return action_result
def assignDeep(json,steps,value):
    battle = battleTable.copy()
    
    for i,key in enumerate(steps):
        if i < len(steps)-1:
            if key.isnumeric():
                battle = battle[int(key)]
            else:
                battle = battle[key]
    return

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
            print("Can't list the keys of a list. Try `list` instead of `listkeys`")
        else:
            for key, val in battle[finalStep].items():
                string += key + ","
            string[:-1]
            print(string)

def say(string):
    printJson(string)

def addCreature(a):
    name = a["target"]
    combatant = getJson(["monsters",name])

    nick = a["identity"]
    if nick == "":
        nick = combatant["index"]

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
    
    if combatant:
        hitDice = combatant.get("hit_dice")
        hitPoints = combatant.get("hit_points")
        if hitDice:
            hp = roll(hitDice)
            combatant["max_hp"] = hp
            combatant["current_hp"] = hp
        myClass = combatant.get("class")
        if myClass:
            combatant["rest_dice"] = int(combatant["level"])
            
        if hitPoints:
            combatant["max_hp"] = hitPoints
            combatant["current_hp"] = hitPoints
        combatant["identity"] = nick
        combatant["advantage"] = 0
        combatant["useAuto"] = False
    
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

def callGroup(a):
    members = a["member"] 
    group = a["group"]
    toAppend = a["append"]
    groupRef = battleInfo["groups"].get(group)
    if not groupRef or not toAppend:
        battleInfo["groups"][group] = []

    battleInfo["groups"][group] = battleInfo["groups"][group] + members 

def showInfo(a):
    if a.get("info") == "all" or (not a.get("info")):
        printJson(battleInfo)
    else:
        printJson(battleInfo[a["info"]])


def callUseStrict(a):
    attackPath = a["do"].lower()
    attackWeapon = getJson(["equipment",attackPath])
    if attackWeapon:
        callWeapon(a)
        return

    attackSpell = getJson(["spells",attackPath])
    if attackSpell:
        callCast(a)
        return

    actionKey = a["do"].title()
    sender = a["sender"]
    senderJson = battleTable[sender]
    actions = senderJson.get("actions")
    attackAction = actionKey in actions
    if attackAction:
        callAction(a)
        return

    print("Trying to use/do something that is not a weapon nor a spell nor an action.")

def callUse(a):
    isnumber = a["do"].lower().isnumeric()
    if not isnumber:
        callWeapon(a)
        callCast(a)
    callAction(a)

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

def validateCommand(commandString):
    say(commandString)
    a = parseOnly(commandString)
    a = handleAllAliases(a)
    has = a["has"]

    if has["target"]:
        targets = onlyAlive(a["target"])
        oneTarget = geti(targets,0,False)
        if not oneTarget:
            return False

    if has["sender"]:
        senders = onlyAlive(a["sender"])
        oneSender = geti(senders,0,False)
        if not oneSender:
            return False

    return True

def validateCommands(combatantJson):
    commands = combatantJson.get("autoCommand")
    for commandString in commands:
        if validateCommand(commandString):
            return True
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

            useAuto = combatantJson.get("useAuto")

            if useAuto:
                if validateCommands(combatantJson):
                    runAuto(combatantJson,nickCurrent)
                    if whoTurn() == nickCurrent:
                        nickNext = whoTurnNext() #In case the next person died
                    else:
                        nickNext = whoTurn() #If we died during the action remove set the next turn to current
                    turnTo(nickNext)
                elif directCommand:
                    turnTo(nickNext)
                else:
                    print("Paused because an automated creature has no target for any of its commands")
                    combatantJson["useAuto"] = False
            elif directCommand:
                    turnTo(nickNext)
            else:
                print("Paused due to non automated creature")
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

class ArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        print(self.format_help())
        self.exit(2, '%s: error: %s\n' % (self.prog,message))
    def print_help(self, file=None):
        print(self.format_help())

def hasParse(command):
    has = hasDict.copy()
    for key, hasList in has.items():
        if hasList.count(command) > 0:
            has[key] = True
        else:
            has[key] = False
    return has

def onlyAlive(combatants):
    aliveCombatants = []
    for combatant in combatants:
        if battleTable.get(combatant):
            aliveCombatants.append(combatant)
    return aliveCombatants

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
                    combatantList = combatantList + list(battleTable.keys())

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
    has = toDict["has"]

    #sender is optional some times
    if (not has["no-alias"] and has["sender"]) and toDict.get("sender"):
        toDict["sender"] = handleAliases(toDict["sender"],resolve,True)

    if not has["no-alias"] and has["target"]:
        toDict["target"] = handleAliases(toDict["target"],resolve,has["target-all"])

    if has["group"] and command != "add":
        toDict["member"] = handleAliases(toDict["member"],resolve,True)

    if has["target-single-optional"] and resolve:
        if (not toDict.get("target")):
            if command == "turn":
                toDict["target"] = [whoTurn()]
            else:
                toDict["target"] = [whoTurnNext()]
        else:
            toDict["target"] = [toDict["target"]]
        toDict["target"] = handleNumerics(toDict["target"])
        
    return toDict


def runAuto(combatantJson,caller):
    autoCommands = combatantJson.get("autoCommand")
    for commandString in autoCommands:
        parse_command(commandString,caller)

def callAuto(a):
    combatant = a["target"]
    combatantJson = battleTable[combatant]
    runAuto(combatantJson,combatant)

def setAuto(a):
    combatant = a["target"]
    combatantJson = battleTable[combatant]
    combatantJson["useAuto"] = True
    append = a["append"]
    if append:
        if not combatantJson.get("autoCommand"):
            combatantJson["autoCommand"] = []
    else:
        combatantJson["autoCommand"] = []

    commandStrings = a["commandString"]
    for commandString in commandStrings:
        argDict = parseOnly(commandString,"auto")
        if argDict["has"]["sender"] and not argDict["sender"]:
            commandString = commandString + " --sender " + combatant
        combatantJson["autoCommand"].append(commandString)

def callStore(a):
    commandStrings = a["commandString"]
    path = ["commands"]+a["path"]
    append = a["append"]
    global battleInfo
    if append:
        set_nested_item(battleInfo, path, get_nested_item(battleInfo,path)+commandStrings)
    else:
        battleInfo = set_nested_item(battleInfo, path, commandStrings)

def callRun(a):
    path = ["commands"]+a["path"]
    global battleInfo
    for command in get_nested_item(battleInfo,path):
        parse_command(command)

def callShortRest(a):
    combatant = a["target"]
    combatantJson = battleTable[combatant]
    if combatantJson.get("rest_dice"):
        if combatantJson["rest_dice"] > 0 and combatantJson["current_hp"] < combatantJson["max_hp"]:
            combatantJson["current_hp"] = combatantJson["current_hp"] + roll(hitDieFromClass(combatantJson["class"])+"+"+str(statMod(int(combatantJson["constitution"]))))
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
                    valueString = " " + str(value)
            if bool(value) and (not (key == "times" and value == 1)):
                commandString = commandString +" --"+ key + valueString
    say(commandString)
    return commandString

def populateParserArguments(parser,has,metaHas):
    if has.get("times"):
        parser.add_argument("--times", "-n", help='How many times to run the command',type=int, default=1)

    if has.get("sender"):
        parser.add_argument("--sender", "-s", required=(not metaHas.get("optionalSender")), help='sender/s for command', nargs='+')
        parser.add_argument("--do", "-d", required=True, help='What the sender is using on the target', nargs='+')

    if has.get("path"):
        parser.add_argument("--path", "-p", nargs='+',help='Path for json or api parsing with command. Space seperated')
        if has.get("change"):
            parser.add_argument("--change", "-c", required=True, help='What you would like to set or modify a number by')
            parser.add_argument("--roll", "-a", help='Whether this command should replace the existing set or be added on', dest='roll', action='store_true', required=False)
            parser.set_defaults(roll=False)

    if has.get("level"):
        parser.add_argument("--level", "-l", type=int, help='Level to cast a spell at')

    if has.get("target"):
        if (has.get("identity") or has.get("file")):
            parser.add_argument("--target", "-t", required=True, help='Target/s creature types to fetch from the cache the api or a file', nargs='+')
        else:
            parser.add_argument("--target", "-t", required=True, help='Target/s for command', nargs='+')

    if has.get("target-single-optional"):
        parser.add_argument("--target", "-t", required=False, help='Target for command')

    if has.get("group"):
        req = True
        if has.get("no-alias"):
            req = False
        else:
            parser.add_argument("--member", "-e", help='members to be placed into a group', required=req, nargs='+')
        parser.add_argument("--group", "-g", help='A group which will be reduced to a target list', required=req)

    if has.get("category"):
        parser.add_argument("--category", "-c", choices=['monsters','equipment','spells'], help='A category for content',required=True)

    if has.get("commandString"):
        parser.add_argument("--commandString", "-c", help='A command string to be run', nargs='+',required=True)
        parser.add_argument("--resolve", "-r", help='Whether or not to resolve aliases inside command string. party -> guy1 guy2 girl', dest='resolve', action='store_true', required=False)
        parser.set_defaults(resolve=False)

    if has.get("identity"):
        parser.add_argument("--identity", "-i", help='Identities for added monsters', nargs='+')

    if has.get("info"):
        parser.add_argument("--info", "-i", help='Info category to interact with')

    if has.get("advantage"):
        parser.add_argument("--advantage", "-a", choices=[1,0,-1], type=int, help='Advantage for attacks', nargs='+')

    if has.get("file"):
        parser.add_argument("--file", "-f", help='The file you would like to interact with')
        
    if has.get("append"):
        parser.add_argument("--append", "-a", help='Whether this command should replace the existing set or be added on', dest='append', action='store_true', required=False)
        parser.set_defaults(append=False)

    if has.get("dice"):
        parser.add_argument("--dice", "-d", help='A dice string to be used',required=True)

command_descriptions_dict = {
"action" : 'Do a generic action. Like:\n\taction --do Multiattack --sender sahuagin#2 --target druid#3 --times 1 --advantage 1\n',
"weapon" : 'Use a weapon. Like:\n\tweapon --do greatsword --sender sahuagin#2 --target druid#3 --times 3 --advantage -1\n',
"cast" : 'Cast a spell. Like:\n\tcast --sender druid#3 --target sahuagin#2 --times 2 --do fire-bolt --level 4 --advantage 0\n',
"remove" : 'Remove an item. Like:\n\tremove --target sahuagin#2\n',
"request" : 'Make a request. Like:\n\trequest --path monsters sahuagin\n',
"set" : 'Set some aspect of the character or other item. Like:\n\tset --target sahuagin# --path initiative --change 18\n',
"mod" : 'Modify a stat on a creature. Like:\n\tmod --target sahuagin#2 --path initiative --change -5\n',
"list" : 'List the features of a creature. Like:\n\tlist --target sahuagin#2 --path actions\n',
"listkeys" : 'List the keys for an item. Like:\n\tlistkeys --target sahuagin#2 --path actions\n',
"add" : 'Add a creature. Like:\n\tadd --target sahuagin --times 2 --identity Aqua-Soldier\n',
"init" : 'Roll for initiative. Like:\n\tinitiative --target sahuagin#2\n',
"initiative" : 'Roll for initiative. Like:\n\tinitiative --target all\n',
"load" : 'Load a content by file name. Like:\n\tload --category monsters --file new_creature.json\n\tload --category equipment --file new_weapon.json\n\tload --category spells --file new_spell.json\n',
"turn" : 'Increments turn. Like:\n\tturn\n',
"auto" : 'Set an automated command. Like:\n\tauto --target sahuagin --commandString "action --target goblin --sender sahuagin --do multiattack"\nauto --target good-guy-greg --order goblin+goblin#2,giant-rat --method random --commandString "use --do greatsword"\n',
"group" : 'Set a group for use in targetting. Will be resolved to listed targets. Like:\n\tgroup --member sahuagin sahuagin#2 --group sahuagang\n',
"info" : 'Shows all info for reference. Like:\n\info --info groups\n',
"roll" : 'Roll dice. Like:\n\troll --target sahuagin sahuagin#2 --group sahuagang\n',
"store" : 'Store a command for use later. Like:\n\store --commandString "add -t sahuagin -n 2" --path encounter#2 --append\n',
"run" : 'Run a stored command Like:\n\run --path encounter#2 \n',
"shortrest" : 'Auto heal from short rest Like:\n\run --path encounter#2 \n',
"longrest" : 'AutoHeal from long restLike:\n\run --path encounter#2 \n',
"jump" : 'This persons turn:\n\jump -t goblin#2 \n',
"skip" : 'Do nothing:\n\skip\n',
"help" : 'Display this message. Like:\n\thelp\n',
}

funcDict = {
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
"initiative" : applyInit,
"load" : loadCategory,
"help" : helpMessage,
"turn" : callTurn,
"auto" : setAuto,
"group" : callGroup,
"info" : showInfo,
"store" : callStore,
"run" : callRun,
"roll" : rollString,
"shortrest" : callShortRest,
"longrest" : callLongRest,
"jump" : callJump,
"skip" : callSkip,
"callAuto" : callAuto,
}

hasDict = {
"sender" : ["action","weapon","cast","use"],
"path" : ["request","mod","set","list","listkeys","store","run"],
"target" : ["init","initiative","remove","mod","set","list","listkeys","auto","add","longrest","shortrest","callAuto"],
"change" : ["mod","set"],
"level" : ["cast"],
"identity" : ["add"],
"advantage" : [],
"sort" : ["add","init","initiative"],
"file" : ["load"],
"category" : ["load"],
"times" : ["mod", "add","roll","longrest","shortrest","callAuto"],
"commandString" : ["auto","store"],
"group" : ["group","add"],
"dice" : ["roll"],
"info" : ["info"],
"append" : ["group","add","auto","store"],
"no-alias" : ["add"],
"target-all" : [],
"target-single-optional" : ["turn","jump"],
"optionalSender" : ["auto"],
}
hasDict["target-all"] = hasDict["target-all"] + hasDict["target"]
hasDict["target"] = hasDict["target"] + hasDict["sender"]
hasDict["advantage"] = hasDict["advantage"] + hasDict["sender"]
hasDict["times"] = hasDict["times"] + hasDict["sender"]

def parseOnly(command_string_to_parse,metaCommand=""):
    args = command_string_to_parse.split(" ")
    command = args[0]
    has = hasParse(command)
    metaHas = hasParse(metaCommand)
    parser = ArgumentParser(
            prog=command,
            description=geti(command_descriptions_dict,command,'Dnd DM Assistant'),
            formatter_class=argparse.RawTextHelpFormatter
            )
    populateParserArguments(parser,has,metaHas)
    entryString = " ".join(args[1:])
    entries = shlex.split(entryString)
    #parameters
    a = parser.parse_args(entries)
    argDictMain = vars(a)
    argDictMain["command"] = command
    argDictMain["has"] = has

    return argDictMain

def parse_command(command_string_to_parse, caller=False):
    argDictMain = parseOnly(command_string_to_parse)
    command = argDictMain["command"]
    has = argDictMain["has"]

    command_result = ''
    times = 1;
    if has["times"]:
        times = argDictMain["times"]

    if command == "help":
        argDictMain["commandDescriptions"] = command_descriptions_dict

    if has["commandString"]:
        commandStrings = []
        for commandString in argDictMain["commandString"]:
            argDictTemp = parseOnly(commandString,command)
            argDictTemp = handleAllAliases(argDictTemp,argDictMain["resolve"])
            
            commandStrings.append(dictToCommandString(argDictTemp))
        argDictMain["commandString"] = commandStrings

    if not has["sender"]:
        argDictMain["sender"] = ["none"]

    if not has["target"] and (not has["target-single-optional"]):
        argDictMain["target"] = ["none"]

    if argDictMain.get("roll"):
        parts = str(argDictMain["change"]).split(",")
        mathString = ""
        for part in parts:
            sign = ""
            dice = part
            if "-" in part:
                dice = part.split("-")[1]
                sign = "-"
            else:
                sign = "+"

            if "d" in dice:
                dice = str(roll(dice))

            mathString = mathString + sign + dice
        argDictMain["change"] = eval(mathString)



    if command == "save":
        saveBattle()
        return True
        
    if command == "exit":
        saveBattle()
        return "EXIT"

    if command == "abort":
        return "EXIT"

    argDictCopy = handleAllAliases(argDictMain.copy())
    argDictSingle = argDictCopy.copy()
    say("times")
    say(times)
    say(argDictCopy)

    for time in range(times):
        for sender in argDictCopy["sender"]:
            argDictSingle["sender"] = sender
            for number,target in enumerate(argDictCopy["target"]):
                argDictSingle["target"] = target
                if has["identity"]:
                    argDictSingle["identity"] = geti(argDictCopy["identity"],number,argDictCopy["target"])
                if has["advantage"]:
                    argDictSingle["advantage"] = geti(argDictCopy["advantage"],number,0)

                if command in funcDict:
                    if battleTable.get(target) or not has["target"] or command == "add" or command == "load":
                        if not argDictCopy.get("do"):
                            argDictCopy["do"] = ["none"]
                        for do in argDictCopy["do"]:
                            argDictSingle["do"] = do
                            command_result += str(funcDict[command](argDictSingle))
                            removeDown()
                            argDictCopy = handleAllAliases(argDictMain.copy())
                    else:
                        command_result += "ignored an invalid target"
                        print('ignored an invalid target',target)
                else:
                    print('Incorrect command. Try running the `help` command')
                    command_result += 'incorrect command was entered. Try again?'
    if has["sort"]:
        setBattleOrder()

    return command_result

def run_assistant():
    result = ""
    error_count = 0 # Detect error spam
    setBattleOrder()
    while result != "EXIT":
        try:
            getState()
            command_input_string = input("Command?")
            result = parse_command(command_input_string)
        except SystemExit:
            print("")#This catches argParses attempts to exit.

        except Exception:
            print("oneechan makes awkward-sounding noises at you, enter the 'exit' command to exit.")
            traceback.print_exc()
            result = ""

            # Error Spam Prevention #
            error_count = error_count + 1
            if error_count >= 10:
                error_spam_prompt = input('Error count has reached 10. \n Program will now exit. \n But you can enter "continue" if you still \n want to keep this up? ->')
                if error_spam_prompt.lower() != 'continue':
                    result = "EXIT" # Brute force error spam prevention
                    sys.exit('Exit due to error Spam')
                else:
                    error_count = 0

if __name__ == "__main__":
    run_assistant()
