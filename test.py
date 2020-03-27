import multiprocessing


class myclass:
    def __init__(self, name):
        self.name = name

    def fun(self, args=False):
        print("name: {0}, num: {1}".format(self.name, args))


if __name__ == '__main__':
    class_list = []
    for i in range(4):
        class_list.append(myclass(name=i))
    p_list = []
    for mc in class_list:
        p_list.append(multiprocessing.Process(target=mc.fun, args=[False,]))

    for p in p_list:
        p.start()
