from myscript2 import *


def cutWindow(hwnd):
    '''
    cut the window of Battlc City
    :return:
    '''
    wh = Windowhandle()
    h = win32gui.GetForegroundWindow()
    if hwnd != h or win32gui.IsIconic(hwnd):
        wh.showGameWindowToTheTop()
        # A time interval to show the window.
        time.sleep(0.3)

    left, top, right, bottom = win32gui.GetWindowRect(self.hwnd)
    gap = (right - left - 480) / 2
    gap_top = bottom - top - 416 - gap
    # print("{0}, {1}, {2}, {3}".format(left, top, right, bottom))
    # print("{0}, {1}, {2}, {3}".format(left+gap, top+gap_top, right-gap, bottom-gap))
    # window = ImageGrab.grab(bbox=(left+gap, top+gap_top, right-gap, bottom-gap)).show()
    self.window = ImageGrab.grab(bbox=(left + gap, top + gap_top, left + gap + 416, bottom - gap)).save("C:/Users/Hangge/Desktop/pic/window.png")

def cut(window):
    '''
    cut and save the current window of Battle City into 13*13 pictures
    :return:
    '''
    for i in range(13):
        for j in range(13):
            window.crop((32 * j, 32 * i, 32 * (j + 1), 32 * (i + 1))).save("C:/Users/Hangge/Desktop/pic/{0}-{1}.png".format(i, j))


if __name__ == '__main__':
    wh = Windowhandle()
    found = wh.findBattleCity()
    while not found:
        found = wh.findBattleCity()

    hwnd = wh.hwnd

    if hwnd < 0:
        raise Exception("Please start Battle City")
    else:
        wh.showGameWindowToTheTop()
        # A time interval to show the window.
        time.sleep(0.3)

        wh.cutWindow()
        wh.window.save("C:/Users/Hangge/Desktop/pic/window.png")
        #cut(wh.window)
