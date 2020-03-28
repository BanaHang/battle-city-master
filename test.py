import threading
import Queue


class myclass:
    def __init__(self, name):
        self.name = name

    def fun(self, args=False):
        while True:
            print("name: {0}, num: {1}".format(self.name, args))


if __name__ == '__main__':
    '''
    class_list = []
    for i in range(4):
        class_list.append(myclass(name=i))
    thread_list = []
    for mc in class_list:
        thread_list.append(threading.Thread(target=mc.fun))

    for t in thread_list:
        t.start()
    '''
    q = Queue.Queue()
    q.put(1)
    q.put(2)
    print(q.qsize())
    q.mutex.acquire()
    q.queue.clear()
    q.mutex.release()
    print(q.qsize())
