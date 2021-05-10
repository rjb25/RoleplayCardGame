import json
import math
import random
import requests
from functools import reduce
from operator import getitem
from collections import defaultdict
import pprint
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
			modSum += math.max(statMod(int(senderJson["strength"])),statMod(int(senderJson["dexterity"])))
		else:
			modSum += statMod(int(senderJson["strength"]))

	if modType == "hit":
		if senderJson.get("weapon_proficiencies"):
			if attackJson["weapon_category"] in senderJson["weapon_proficiencies"]:
				modSum += senderJson["proficiency_bonus"]
	return modSum

def statMod(stat):
	return math.floor((stat-10)/2)


def applyAction(senderJson,targetJson,actionKey):
	actionJson = senderJson.get("actions")
	action = False
	for x in actionJson:
		if x["name"] == actionKey:
			action = x
	if action:
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
			print(senderJson["index"], "used", actionKey, "with a hit of",hit, "and dealt",hurt,"damage to",targetJson["index"])
			targetJson["current_hp"] -= hurt
		else:
			print(senderJson["index"], "used", actionKey, "with a hit of", hit, "and missed",targetJson["index"])
	else:
		print("Invalid action for this combatant")

running = True
while running:
	getState()
	args = input("Command?").split(" ")
	command = args[0]
	if command == "action":
		sender = args[1]
		actionKey = args[2]
		target = args[3]

		targetJson = battleTable["combatants"][int(target)]
		senderJson = battleTable["combatants"][int(sender)]
		actionJson = senderJson.get("actions")
		if actionJson:
			if actionKey == "Multiattack":
				canMultiattack = False
				multiAction = {}
				for x in actionJson:
					if x["name"] == actionKey:
						multiAction = x
						canMultiAttack = True
				if canMultiAttack:
					for i in range(int(multiAction["options"]["choose"])):
						for action in random.choice(multiAction["options"]["from"]):
							applyAction(senderJson,targetJson,action["name"])
						
				else:
					print("This combatant cannot multiattack")		
			else:
				applyAction(actionJson,targetJson,actionKey)
				
	if command == "weapon":
		sender = args[1]
		attackPath = args[2]
		target = args[3]
		times = args[4]
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