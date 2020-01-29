import random


def dis(pos1, pos2):
    return abs(pos1[0]-pos2[0]) + abs(pos1[1]-pos2[1])


list = [(1, 2), (4, 3), (6, 1), (2, 4), (1, 0)]
pos = (0, 0)
s = sorted(list, key=lambda ps: dis(pos, ps))
print(s)
