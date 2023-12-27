import asyncio
import websockets
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


def geti(list, index, default_value):
    try:
        return list[index]
    except:
        return default_value

def ddel(context,path):
    deep = pathing(path[:-1],context)
    if isinstance(deep, list):
        deep.pop(int(path[-1]))
    else:
        deep.pop(path[-1],None)

def dset(context, path, value):
    if not isinstance(path,list):
        path = [path]
    for key in path[:-1]:
        context = context.setdefault(key, {})
    context[path[-1]] = value

def dmod(context, path, value):
    if not isinstance(path,list):
        path = [path]
    for key in path[:-1]:
        context = context.setdefault(key, {})
    if dget(context,path[-1],None) == None:
        context[path[-1]] = int(value)
    else:
        context[path[-1]] = context[path[-1]] + int(value)

def dget(context, path, default=None):
    try:
        if not isinstance(path,list):
            path = [path]
        internal_dict_value = context
        for k in path:
            if isinstance(internal_dict_value,list):
                internal_dict_value = geti(context, int(k), default)
            else:
                internal_dict_value = internal_dict_value.get(k, default)
            if internal_dict_value is default:
                return default
        return internal_dict_value
    except:
        return default

def weedNones(dictionary):
    return {k:v for k,v in dictionary.items() if ((v is not None) and (v != [None])) and v != []}
                
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
            printw("Invalid category to load into")

library_table = load({"file":"json/library.json"})
state_table = load({"file":"json/state.json"})
def saveBattle():
        with open('json/state.json', 'w') as f:
            json.dump(state_table,f)


all_clients = []

async def send_message(message: str):
    for client in all_clients:
        await client.send(message)

async def new_client_connected(client_socket, path):
    print("New client connected!")
    all_clients.append(client_socket)

    while True:
        new_message = await client_socket.recv()
        print("Client sent:", new_message)
        await send_message(new_message)

async def start_server():
    print("Server started!")
    await websockets.serve(new_client_connected, "localhost", 12345)

if __name__ == '__main__':
    event_loop = asyncio.get_event_loop()
    event_loop.run_until_complete(start_server())
    event_loop.run_forever()
