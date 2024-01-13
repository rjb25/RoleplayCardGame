from collections import defaultdict
#dictionary = {"hey":{"swaggins":3}, "hola":2, "heyo":3}
#upper = {"hey":{"yolo":2}, "hiola":4, "heyo":7}
#dictionary.update(upper)
#print(dictionary)
dictionary = {"hey":{"swaggins":3}, "hola":2, "heyo":3}
upper = {"hey":{"yolo":2}, "hiola":4, "heyo":7, "Jason":3}
def pro(me, you, yolo = "swaggins", other = "someone"):
    return me + you + yolo + other

print(pro("jason","nathan",other = "zach"))
