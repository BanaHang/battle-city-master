import myscript4


q = myscript4.PriorityQueue()
q.put(3, (1, 1))
q.put(4, (2, 2))
q.put(1, (3, 3))

while not q.isEmpty():
    print(q.items)
    print(q.get())
