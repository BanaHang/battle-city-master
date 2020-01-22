import win32con
import win32gui
from PIL import ImageGrab
from PIL import Image
import time
import operator
import pykeyboard
import random


class Windowhandle:

    def __init__(self):
        self.hwnd = -1

        # current window of Battle City, type : PIL.Image.Image
        self.window = None

    def findBattleCity(self):
        '''
        find the window of Battle City
        :return: bool
        '''
        found = False
        hWndList = []
        win32gui.EnumWindows(lambda temp, param: param.append(temp), hWndList)
        for h in hWndList:
            # find window by WindowText
            if win32gui.GetWindowText(h) == "Battle City":
                self.hwnd = h
                found = True
        return found

    def showGameWindowToTheTop(self):
        '''
        show the current window of Battle City
        based on pywin32
        :return:
        '''

        # show the window, if the window is minimized
        if win32gui.IsIconic(self.hwnd):
            win32gui.ShowWindow(self.hwnd, win32con.SW_SHOWNORMAL)

        # let the window on the top
        win32gui.SetForegroundWindow(self.hwnd)
        # win32gui.SetWindowPos(self.hwnd, win32con.HWND_TOPMOST, 438, 170, 924-438, 615-170, win32con.SW_SHOWNORMAL)

    def cutWindow(self):
        '''
        cut the window of Battlc City
        :return:
        '''
        h = win32gui.GetForegroundWindow()
        if self.hwnd != h or win32gui.IsIconic(self.hwnd):
            self.showGameWindowToTheTop()
            # A time interval to show the window.
            time.sleep(0.3)

        left, top, right, bottom = win32gui.GetWindowRect(self.hwnd)
        gap = (right - left - 480)/2
        gap_top = bottom - top - 416 - gap
        # print("{0}, {1}, {2}, {3}".format(left, top, right, bottom))
        # print("{0}, {1}, {2}, {3}".format(left+gap, top+gap_top, right-gap, bottom-gap))
        # window = ImageGrab.grab(bbox=(left+gap, top+gap_top, right-gap, bottom-gap)).show()
        self.window = ImageGrab.grab(bbox=(left + gap, top + gap_top, left + gap + 416, bottom - gap))

    def cut(self):
        '''
        cut the current window of Battle City into 13*13 pictures
        :return: list
        '''
        pic_list = []
        for i in range(13):
            for j in range(13):
                pic_list.append(self.window.crop((32*j, 32*i, 32*(j+1), 32*(i+1))))
        return pic_list


class Calculator:

    def __init__(self):

        self.obstacle = []
        self.enemy = []
        self.player = []
        self.castle = []
        self.path = []

        self.gamestart = []
        self.gamestart.append(Image.open("samples/start_1.png"))
        self.gamestart.append(Image.open("samples/start_2.png"))

        self.gameover = Image.open("samples/gameover.png")

        for i in range(3):
            self.obstacle.append(Image.open("samples/z_{0}.png".format(i + 1)))

        for i in range(3):
            self.enemy.append(Image.open("samples/e_{0}.png".format(i + 1)))

        for i in range(2):
            self.player.append(Image.open("samples/t_{0}.png".format(i + 1)))

        for i in range(1):
            self.castle.append(Image.open("samples/s_{0}.png".format(i + 1)))

        for i in range(3):
            self.path.append(Image.open("samples/p_{0}.png".format(i + 1)))

        self.OBSTACLE = 0
        self.ENEMY = 1
        self.PLAYER = 2
        self.CASTLE = 3
        self.PATH = 4

    def hammingDistance(self, img1, img2):
        '''
        calculate the hamming distance between img1 and img2
        :param img1: image to compare
        :param img2: image to be compared
        :return: int
        '''
        image1 = img1.resize((20, 20), Image.ANTIALIAS).convert("L")
        image2 = img2.resize((20, 20), Image.ANTIALIAS).convert("L")

        pixels1 = list(image1.getdata())
        pixels2 = list(image2.getdata())

        avg1 = sum(pixels1) / len(pixels1)
        avg2 = sum(pixels2) / len(pixels2)

        hash1 = "".join(map(lambda p: "1" if p > avg1 else "0", pixels1))
        hash2 = "".join(map(lambda p: "1" if p > avg2 else "0", pixels2))

        match = sum(map(operator.ne, hash1, hash2))
        return match

    def similarity(self, img, typelist):
        '''
        calculate the highest similarity of this pic
        :param img: image to be compared
        :param typelist: images of this type
        :return: int
        '''
        sim = -1
        for i in typelist:
            hd = self.hammingDistance(img, i)
            if sim < 0 or hd < sim:
                sim = hd
        return sim

    def imagetype(self, img):
        '''
        get the type of this img
        :param img:
        :return: tuple
        '''

        pictype = -1
        hd = -1

        obs = self.similarity(img, self.obstacle)
        if hd < 0 or obs < hd:
            hd = obs
            pictype = self.OBSTACLE

        enemy = self.similarity(img, self.enemy)
        if hd < 0 or enemy < hd:
            hd = enemy
            pictype = self.ENEMY

        player = self.similarity(img, self.player)
        if hd < 0 or player < hd:
            hd = player
            pictype = self.PLAYER

        castle = self.similarity(img, self.castle)
        if hd < 0 or castle < hd:
            hd = castle
            pictype = self.CASTLE

        path = self.similarity(img, self.path)
        if hd < 0 or path < hd:
            hd = path
            pictype = self.PATH

        return pictype, hd

    def isGameStart(self, img):
        hd1 = self.hammingDistance(self.gamestart[0], img)
        hd2 = self.hammingDistance(self.gamestart[0], img)
        if hd1 < 1 or hd2 < 1:
            return True
        return False

    def isGameOver(self, img):
        hd = self.hammingDistance(self.gameover, img)
        if hd < 1:
            return True
        return False


class Map:
    def __init__(self):
        self.map = []
        for i in range(13*13):
            self.map.append(-1)

        self.calculator = Calculator()

        # x for cols number, y for rows number.
        # x, y for the location of the player.
        self.x = 4
        self.y = 12
        self.similarity = -1

        # four directions of the player
        self.UP = 0
        self.RIGHT = 1
        self.DOWN = 2
        self.LEFT = 3

    def mapConvert(self, piclist):
        '''
        convert image into matrix
        :param piclist: images
        :return:
        '''

        if len(piclist) != len(self.map):
            raise Exception("len(piclist) != len(self.map), len(piclist):{0}, len(self.map):{1}".format(len(piclist), len(self.map)))

        for i in range(13*13):
            temp = self.calculator.imagetype(piclist[i])
            self.map[i] = temp[0]
            if temp[1] == self.calculator.PLAYER:
                if self.similarity < 0 or self.similarity > temp[1]:
                    self.map[self.x + self.y*13] = self.calculator.ENEMY
                    self.x = i % 13
                    self.y = i / 13
                    self.similarity = temp[1]
                else:
                    self.map[i] = self.calculator.ENEMY

    def dangerous(self):
        '''
        get the most dangerous direction
        :return: int
        '''

        up, right, down, left = -1, -1, -1, -1

        # up
        if self.y > 0:
            for i in range(self.y):
                if self.map[i*13+self.x] == self.calculator.ENEMY:
                    up = self.y - i

        # right
        if self.x < 12:
            for i in range(self.x+1, 13):
                if self.map[self.y*13+i] == self.calculator.ENEMY:
                    right = i - self.x

        # down
        if self.y < 12:
            for i in range(self.y+1, 13):
                if self.map[i*13+self.x] == self.calculator.ENEMY:
                    down = i - self.y

        # left
        if self.x > 0:
            for i in range(self.x):
                if self.map[self.y*13+i] == self.calculator.ENEMY:
                    right = self.x - i

        if up < 0 and right < 0 and down < 0 and left < 0:
            # safe
            return -1

        min = up
        direction = self.UP
        if min < 0 or min > right:
            min = right
            direction = self.RIGHT
        if min < 0 or min > down:
            min = down
            direction = self.DOWN
        if min < 0 or min > left:
            min = left
            direction = self.LEFT
        return direction


class Player:
    '''
    simulate the actions of the player
    '''
    def __init__(self):
        self.keyboard = pykeyboard.PyKeyboard()

        # 0 for up, 1 for right, 2 for down, 3 for left.
        self.direction = 0

        self.map = Map()

    def fire(self):
        self.keyboard.tap_key(self.keyboard.space_key)

    def move(self):
        print("Move direction is {0}".format(self.direction))
        t = 0.333333333333333
        if self.direction == 0:
            if self.map.y > 0:
                self.keyboard.press_key(self.keyboard.up_key)
                time.sleep(t)
                self.keyboard.release_key(self.keyboard.up_key)
        elif self.direction == 1:
            if self.map.x < 12:
                self.keyboard.press_key(self.keyboard.right_key)
                time.sleep(t)
                self.keyboard.release_key(self.keyboard.right_key)
        elif self.direction == 2:
            if self.map.y < 12:
                self.keyboard.press_key(self.keyboard.down_key)
                time.sleep(t)
                self.keyboard.release_key(self.keyboard.down_key)
        elif self.direction == 3:
            if self.map.x > 0:
                self.keyboard.press_key(self.keyboard.left_key)
                time.sleep(t)
                self.keyboard.release_key(self.keyboard.left_key)

    def rotate(self):
        self.direction = random.randint(0, 4)
        '''
        if self.direction == 1 or self.direction == 3:
            rand = [2, 4]
            self.direction = rand[random.randint(0, 1)]
        elif self.direction == 2 or self.direction == 4:
            rand = [1, 3]
            self.direction = rand[random.randint(0, 1)]
        '''

    def restart(self):
        self.keyboard.tap_key(self.keyboard.return_key)


if __name__ == '__main__':

    wh = Windowhandle()
    found = wh.findBattleCity()
    while not found:
        found = wh.findBattleCity()

    hd = wh.hwnd
    calculator = Calculator()

    if hd < 0:
        raise Exception("Please start Battle City")
    else:
        wh.showGameWindowToTheTop()
        # A time interval to show the window.
        time.sleep(0.3)
        player = Player()
        while True:
            wh.cutWindow()
            if calculator.isGameOver(wh.window):
                player.restart()

            if not calculator.isGameStart(wh.window):
                pic_list = wh.cut()
                player.map.mapConvert(pic_list)
                print("x, y : {0}, {1}".format(player.map.x, player.map.y))
                danger = player.map.dangerous()

                if danger == 0:
                    player.direction = 0
                    player.move()
                    player.fire()
                elif danger == 1:
                    player.direction = 1
                    player.move()
                    player.fire()
                elif danger == 2:
                    player.direction = 2
                    player.move()
                    player.fire()
                else:
                    player.direction = 3
                    player.move()
                    player.fire()

                player.rotate()
                player.move()
