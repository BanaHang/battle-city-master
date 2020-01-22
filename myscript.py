import win32con
import win32gui
import win32process
import win32api


def findBattleCity():
    '''
    find the window of Battle City
    :return: hwnd
    '''
    handle_window = -1
    hWndList = []
    win32gui.EnumWindows(lambda hwnd, param: param.append(hwnd), hWndList)
    for h in hWndList:
        # find window by WindowText
        if win32gui.GetWindowText(h) == "Battle City":
            left, top, right, bottom = win32gui.GetWindowRect(h)
            print("{0}, {1}, {2}, {3}".format(left, top, right, bottom))
            handle_window = h
    return handle_window


def showGameWindowToTheTop(hwnd):
    '''
    show the window of Battle City
    based on pywin32
    :return:
    '''

    # show the window, if the window is minimized
    if win32gui.IsIconic(hwnd):
        win32gui.ShowWindow(hwnd, win32con.SW_SHOWNORMAL)

    # let the window on the top
    # win32gui.SetWindowPos(h, win32con.HWND_TOPMOST, 438, 170, 924-438, 615-170, win32con.SW_SHOWNORMAL)
    win32gui.SetForegroundWindow(hwnd)


def findProcess(hwnd):
    tid, pid = win32process.GetWindowThreadProcessId(hwnd)
    phandler = win32api.OpenProcess(win32con.PROCESS_ALL_ACCESS, False, pid)
    print("{0}, {1}, {2}".format(tid, pid, phandler))
    print(win32process.GetProcessMemoryInfo(phandler))

if __name__ == '__main__':

    hwnd = findBattleCity()
    print(hwnd)
    if hwnd < 0:
        print("Please start Battle City")
    else:
        showGameWindowToTheTop(hwnd)
        findProcess(hwnd)
