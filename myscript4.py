import tanks
import pygame
import random
import os
from Queue import deque
import heapq
import threading
import multiprocessing
import math
import time


def tanks_init():
    tanks.gtimer = tanks.Timer()

    tanks.sprites = pygame.transform.scale(pygame.image.load("images/sprites.gif"), [192, 224])
    tanks.screen = pygame.display.set_mode((480, 416))
    tanks.players = []
    tanks.enemies = []
    tanks.bullets = []
    tanks.bonuses = []
    tanks.labels = []

    tanks.play_sounds = True
    tanks.sounds = dict()
    pygame.mixer.init(44100, -16, 1, 512)
    tanks.sounds["start"] = pygame.mixer.Sound("sounds/gamestart.ogg")
    tanks.sounds["end"] = pygame.mixer.Sound("sounds/gameover.ogg")
    tanks.sounds["score"] = pygame.mixer.Sound("sounds/score.ogg")
    tanks.sounds["bg"] = pygame.mixer.Sound("sounds/background.ogg")
    tanks.sounds["fire"] = pygame.mixer.Sound("sounds/fire.ogg")
    tanks.sounds["bonus"] = pygame.mixer.Sound("sounds/bonus.ogg")
    tanks.sounds["explosion"] = pygame.mixer.Sound("sounds/explosion.ogg")
    tanks.sounds["brick"] = pygame.mixer.Sound("sounds/brick.ogg")
    tanks.sounds["steel"] = pygame.mixer.Sound("sounds/steel.ogg")


class PriorityQueue:
    def __init__(self):
        self.items = []

    def isEmpty(self):
        return len(self.items) == 0

    def put(self, priority, item):
        heapq.heappush(self.items, (priority, item))

    def get(self):
        return heapq.heappop(self.items)


class Robot(tanks.Player):
    def __init__(self, sprites, enemies, players, bonuses, level, side, bullets, castle, position=None, direction=None, filename=None):
        tanks.Player.__init__(self, level, side, position=position, direction=direction, filename=filename)

        self.sprites = sprites
        self.enemies = enemies
        self.players = players
        self.bonuses = bonuses
        self.bullets = bullets
        self.castle = castle
        self.filename = filename
        if filename is None:
            filename = (0, 0, 16 * 2, 16 * 2)

        self.start_position = position
        self.start_direction = direction

        self.lives = 99

        # total score
        self.score = 0

        # store how many bonuses in this stage this player has collected
        self.trophies = {
            "bonus": 0,
            "enemy0": 0,
            "enemy1": 0,
            "enemy2": 0,
            "enemy3": 0
        }

        self.image = self.sprites.subsurface(filename)
        self.image_up = self.image
        self.image_left = pygame.transform.rotate(self.image, 90)
        self.image_down = pygame.transform.rotate(self.image, 180)
        self.image_right = pygame.transform.rotate(self.image, 270)

        if direction is None:
            self.rotate(self.DIR_UP, False)
        else:
            self.rotate(direction, False)

        # a set of control instructions
        self.controls = multiprocessing.Queue

    def auto(self):
        while True:
            # sort enemies
            enemies = self.enemies
            sorted_enemy_to_castle = sorted(enemies, key=lambda e: self.manhattan_distance(self.castle.rect.center, e.rect.center))
            sorted_enemy_to_player = sorted(enemies, key=lambda e: self.manhattan_distance(self.rect.center, e.rect.center))

            if sorted_enemy_to_castle:
                # if enemy distance with castle < 150, chase it
                if self.manhattan_distance(sorted_enemy_to_castle[0].rect.center, self.castle.rect.center) < 150:
                    target_enemy = sorted_enemy_to_castle[0]
                # else chase the nearest enemy to player
                else:
                    target_enemy = sorted_enemy_to_player[0]

                # check if player is inline with enemy
                inline_direction = self.inline_with_enemy(target_enemy)

                # perform a star control instruction
                astar_direction = self.a_star(target_enemy.rect, self.speed)

                # perform dodge bullet instruction
                shoot, direction = self.dodge_bullets(self.mapinfo[3][0], 6, self.mapinfo[0], astar_direction, inline_direction)

                # update strategy
                self.update_strategy(c_control, shoot, direction)
                time.sleep(0.005)
            # go back to start position
            else:
                # perform a star
                birth_rect = pygame.Rect(self.start_position[0], self.start_position[1], 26, 26)
                astar_direction = self.a_star(birth_rect, self.speed)

                # update strategy
                if astar_direction is not None:
                    self.update_strategy(c_control, 0, astar_direction)
                    # time.sleep(0.001)
                else:
                    self.update_strategy(c_control, 0, 0)
                    # time.sleep(0.001)

    def manhattan_distance(self, pos1, pos2):
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

    def euclidean_distance(self, pos1, pos2):
        return math.sqrt((pos1[0]-pos2[0])**2 + (pos1[1]-pos2[1])**2)

    def update_strategy(self, control, shoot, move_dir):
        if self.controls.empty():
            self.controls.put([shoot, move_dir])

    def should_fire(self):
        for e in self.enemies:
            if self.inline_with_enemy(e) > -1:
                return True

    def inline_with_enemy(self, enemy):
        # vertical
        if enemy.rect.left <= self.rect.centerx <= enemy.rect.right and abs(self.rect.top - enemy.rect.bottom) <= 151:
            # enemy on top
            if enemy.rect.bottom <= self.rect.top:
                print('enemy on top')
                return self.DIR_UP
            # enemy on bottom
            elif self.rect.bottom <= enemy.rect.top:
                print('enemy on bottom')
                return self.DIR_DOWN
        # horizontal inline
        if enemy.rect.top <= self.rect.centery <= enemy.rect.bottom and abs(self.rect.left - enemy.rect.right) <= 151:
            # enemy on left
            if enemy.rect.right <= self.rect.left:
                print('enemy on left')
                return self.DIR_LEFT
            # enemy on right
            elif self.rect.right <= enemy.rect.left:
                print('enemy on right')
                return self.DIR_RIGHT
        return -1

    def a_star(self, target_rect, speed):
        '''
        track target by A star
        :param start_rect:
        :param goal_rect:
        :param speed:
        :return:
        '''

        # init list
        open_list = PriorityQueue()
        came_from = {}
        close_list = {}

        # init start
        start = (self.rect.left, self.rect.top)
        target_pos = (target_rect.left, target_rect.top)
        open_list.put(0, start)
        came_from[start] = None
        close_list[start] = 0 + self.manhattan_distance(start, target_pos)
        current = start

        while not open_list.isEmpty():
            current = open_list.get()[1]

            # if reach target, break
            temp_rect = pygame.Rect(current[0], current[1], 26, 26)
            if self.reach_target(temp_rect, target_rect):
                break

            # try neighbours
            for neighbour in self.find_neighbour(temp_rect, speed):
                new_cost = close_list[current] + speed + self.manhattan_distance(neighbour, target_pos)

                # if not visited or move cost less, add new step
                if neighbour not in close_list.keys() or new_cost < close_list[neighbour]:
                    close_list[neighbour] = new_cost
                    open_list.put(new_cost, neighbour)
                    came_from[neighbour] = current

            # return the first move
            next = None
            next_dir = None

            while current != start:
                next = current
                current = came_from[current]

            if next:
                next_left, next_top = next
                current_left, current_top = current
                # up
                if current_top > next_top:
                    next_dir = self.DIR_UP
                # down
                elif current_top < next_top:
                    next_dir = self.DIR_DOWN
                # left
                elif current_left > next_left:
                    next_dir = self.DIR_LEFT
                # right
                elif current_left < next_left:
                    next_dir = self.DIR_RIGHT
            return next_dir

    def find_neighbour(self, rect, step):
        neighbours = []
        for i in range(4):
            new_left, new_top = rect.left, rect.top
            if i == 0:
                # move up
                new_top = rect.top - step
                new_left = rect.left
            elif i == 1:
                # move down
                new_top = rect.top + step
                new_left = rect.left
            elif i == 2:
                # move left
                new_top = rect.top
                new_left = rect.left - step
            elif i == 3:
                # move right
                new_top = rect.top
                new_left = rect.left + step

            if 0 <= new_left <= (416 - 26) and 0 <= new_top <= (416 - 26):
                new_rect = pygame.Rect(new_left, new_top, 26, 26)

                # if reach castle or fortress
                castle_fortress = pygame.Rect(11 * 16, 23 * 16, 4 * 16, 3 * 16)
                if new_rect.colliderect(castle_fortress):
                    continue

                # collisions with tiles, except bricks
                collide_tile = new_rect.collidelistall(self.level.mapr)
                collied = False
                if len(collide_tile) > 0:
                    for tile_index in collide_tile:
                        tile = self.level.mapr[tile_index].type
                        if tile in (self.level.TILE_STEEL, self.level.TILE_WATER):
                            collied = True
                            break
                if not collied:
                    neighbours.append((new_left, new_top))
        return neighbours

    def reach_target(self, rect1, rect2):
        '''
        return true if two rects meet
        :param rect1:
        :param rect2:
        :return: bool
        '''
        center_x1, center_y1 = rect1.center
        center_x2, center_y2 = rect2.center
        if abs(center_x1 - center_x2) <= 7 and abs(center_y1 - center_y2) <= 7:
            return True
        else:
            return False

    def dodge_bullets(self, speed, direction_from_astar, inlined_with_enemy):
        # possible direction list
        directions = []

        # sort bullet by euclidean distance to player
        sorted_bullets = sorted(self.bullets, key=lambda x: self.euclidean_distance(x.rect.center, self.rect.center))

        # default shoot
        shoot = 0

        if sorted_bullets:
            min_distance = self.euclidean_distance(sorted_bullets[0].rect.center, self.rect.center)
        else:
            min_distance = 99999

        if min_distance < 150:
            bullet = sorted_bullets[0]

            if abs(self.rect.centerx - bullet.rect.centerx) < 26:
                # width of bullet is 6
                if abs(self.rect.centerx - bullet.rect.centerx) < 6:
                    # bullet direction to up, on player's bottom
                    # 0 up, 1 right, 2 down ,3 left
                    if bullet.direction == 0 and bullet.rect.top > self.rect.top:
                        # add direction to down
                        directions.append(2)
                        # shoot
                        shoot = 1
                        print('block bullet from down')
                    # direction to down, on player's top
                    if bullet.direction == 2 and bullet.rect.top < self.rect.top:
                        # add direction to up
                        directions.append(0)
                        # shoot
                        shoot = 1
                        print('block bullet from up')
                else:
                    # if bullet on player's right
                    if bullet.rect.left > self.rect.left:
                        # go left
                        directions.append(3)
                        print('go left, skip bullet')
                    else:
                        # go right
                        directions.append(1)
                        print('go right, skip bullet')
            elif abs(self.rect.centery - bullet.rect.centery) < 26:
                if abs(bullet.rect.centery - self.rect.centery) < 6:
                    # bullet direction to right, on player's left
                    if bullet.direction == 1 and bullet.rect.left < self.rect.left:
                        # go left
                        directions.append(3)
                        # shoot
                        shoot = 1
                        print('block bullet from left')
                    # bullet direction to left, on player's right
                    if bullet.direction == 3 and bullet.rect.left > self.rect.left:
                        # go right
                        directions.append(1)
                        # shoot
                        shoot = 1
                        print('block bullet from right')
            else:
                if inlined_with_enemy == direction_from_astar:
                    shoot = 1
                directions.append(direction_from_astar)

                # remove dangerous move
                # bullet direction down or up
                if bullet.direction == 0 or bullet.direction == 2:
                    # bullet on right hand side
                    if bullet.rect.left > self.rect.left:
                        if 1 in directions:
                            directions.remove(1)
                    else:
                        if 3 in directions:
                            directions.remove(3)
                # bullet direction to left or right
                if bullet.direction == 1 or bullet.direction == 3:
                    # bullet on bottom
                    if bullet.rect.top > self.rect.top:
                        if 2 in directions:
                            directions.remove(2)
                    else:
                        if 0 in directions:
                            directions.remove(0)
        else:
            if inlined_with_enemy == direction_from_astar:
                shoot = 1
            directions.append(direction_from_astar)

        if directions:
            for dir in directions:
                if dir == 0:
                    new_left = self.rect.left
                    new_top = self.rect.top - speed
                elif dir == 1:
                    new_left = self.rect.left + speed
                    new_top = self.rect.top
                elif dir == 2:
                    new_left = self.rect.left
                    new_top = self.rect.top + speed
                elif dir == 3:
                    new_left = self.rect.left - speed
                    new_top = self.rect.top
                else:
                    new_top = self.rect.top
                    new_left = self.rect.left

                temp_rect = pygame.Rect(new_left, new_top, 26, 26)
                if 0 <= new_top <= (416 - 26) and 0 <= new_left <= (416 - 26):
                    if temp_rect.colliderect(self.level.obstacle_rects):
                        if inlined_with_enemy == direction_from_astar:
                            shoot = 1
                            break
                    else:
                        return shoot, direction
        else:
            return shoot, 4
        return shoot, direction_from_astar

class Gameloader:

    (DIR_UP, DIR_RIGHT, DIR_DOWN, DIR_LEFT) = range(4)
    TILE_SIZE = 16

    def __init__(self, sprites, sounds, play_sounds, screen, players, enemies, bullets, bonuses, gtimer, castle, labels):

        # params from tanks.py
        self.sprites = sprites
        self.sounds = sounds
        self.play_sounds = play_sounds
        self.screen = screen
        self.players = players
        self.enemies = enemies
        self.bullets = bullets
        self.bonuses = bonuses
        self.gtimer = gtimer
        self.castle = castle
        self.labels = labels

        # center window
        os.environ['SDL_VIDEO_WINDOW_POS'] = 'center'

        if self.play_sounds:
            pygame.mixer.pre_init(44100, -16, 1, 512)

        pygame.init()
        pygame.display.set_caption("Battle City")

        self.clock = pygame.time.Clock()

        pygame.display.set_icon(self.sprites.subsurface(0, 0, 13 * 2, 13 * 2))

        self.enemy_life_image = self.sprites.subsurface(81 * 2, 57 * 2, 7 * 2, 7 * 2)
        self.player_life_image = self.sprites.subsurface(89 * 2, 56 * 2, 7 * 2, 8 * 2)
        self.flag_image = self.sprites.subsurface(64 * 2, 49 * 2, 16 * 2, 15 * 2)

        # this is used in intro screen
        self.player_image = pygame.transform.rotate(self.sprites.subsurface(0, 0, 13 * 2, 13 * 2), 270)

        # if true, no new enemies will be spawn during this time
        self.timefreeze = False

        # load custom font
        self.font = pygame.font.Font("fonts/prstart.ttf", 16)

        # pre-render game over text
        self.im_game_over = pygame.Surface((64, 40))
        self.im_game_over.set_colorkey((0, 0, 0))
        self.im_game_over.blit(self.font.render("GAME", False, (127, 64, 64)), [0, 0])
        self.im_game_over.blit(self.font.render("OVER", False, (127, 64, 64)), [0, 20])
        self.game_over_y = 416 + 40

        # number of players. here is defined preselected menu value
        self.nr_of_players = 1

        self.stage = 1
        self.level = None

        # if True, start "game over" animation
        self.game_over = False

        # if False, game will end w/o "game over" bussiness
        self.running = True

        # if False, players won't be able to do anything
        self.active = True

        # if True, Ai robot is active and battle automatically
        self.auto_active = True

        # if True, the status of enemies will show on screen
        self.show_status = False
        self.show_circle = 500

        del self.players[:]
        del self.bullets[:]
        del self.enemies[:]
        del self.bonuses[:]

    def showMenu(self):
        """
            Show game menu
        """
        # stop game main loop (if any)
        self.running = False

        # clear all timers
        del self.gtimer.timers[:]

        self.animateIntroScreen()

        # tick is to control animation of the instruction
        main_tick = 0
        interior_tick = 310

        main_loop = True
        while main_loop:
            time_passed = self.clock.tick(20)

            main_tick += 1
            tick_temp = main_tick % 10
            if tick_temp > 5:
                interior_tick = 310 + tick_temp - 5
            else:
                interior_tick = 310 - (5 - tick_temp)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    quit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        quit()
                    elif event.key == pygame.K_UP:
                        if self.nr_of_players == 2:
                            self.nr_of_players = 1
                            self.drawIntroScreen(tick=interior_tick)
                    elif event.key == pygame.K_DOWN:
                        if self.nr_of_players == 1:
                            self.nr_of_players = 2
                            self.drawIntroScreen(tick=interior_tick)
                    elif event.key == pygame.K_RETURN:
                        main_loop = False
            self.drawIntroScreen(tick=interior_tick)

        del self.players[:]
        self.nextLevel()

    def gameOverScreen(self):
        """ Show game over screen """
        # stop game main loop (if any)
        self.running = False

        self.screen.fill([0, 0, 0])

        self.writeInBricks("game", [125, 140])
        self.writeInBricks("over", [125, 220])
        pygame.display.flip()

        while 1:
            time_passed = self.clock.tick(50)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    quit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        self.showMenu()
                        return

    def gameOver(self):
        """ End game and return to menu """
        print "Game Over"
        if self.play_sounds:
            for sound in self.sounds:
                self.sounds[sound].stop()
            self.sounds["end"].play()

        self.game_over_y = 416 + 40

        self.game_over = True
        self.gtimer.add(3000, lambda: self.showScores(), 1)

    def loadHiscore(self):
        """
            Load hiscore Really primitive version =] If for some reason hiscore cannot be loaded, return 20000
            @return int
        """
        filename = ".hiscore"
        if (not os.path.isfile(filename)):
            return 20000

        f = open(filename, "r")
        hiscore = int(f.read())

        if 19999 < hiscore < 1000000:
            return hiscore
        else:
            print "cheater =["
            return 20000

    def saveHiscore(self, hiscore):
        """
            Save hiscore
            @return boolean
        """
        try:
            f = open(".hiscore", "w")
        except:
            print "Can't save hi-score"
            return False
        f.write(str(hiscore))
        f.close()
        return True

    def showScores(self):
        """ Show level scores """
        # stop game main loop (if any)
        self.running = False

        # clear all timers
        del self.gtimer.timers[:]

        if self.play_sounds:
            for sound in self.sounds:
                self.sounds[sound].stop()

        hiscore = self.loadHiscore()

        # update hiscore if needed
        if self.players[0].score > hiscore:
            hiscore = self.players[0].score
            self.saveHiscore(hiscore)
        if self.nr_of_players == 2 and self.players[1].score > hiscore:
            hiscore = self.players[1].score
            self.saveHiscore(hiscore)

        img_tanks = [
            self.sprites.subsurface(32 * 2, 0, 13 * 2, 15 * 2),
            self.sprites.subsurface(48 * 2, 0, 13 * 2, 15 * 2),
            self.sprites.subsurface(64 * 2, 0, 13 * 2, 15 * 2),
            self.sprites.subsurface(80 * 2, 0, 13 * 2, 15 * 2)
        ]

        img_arrows = [
            self.sprites.subsurface(81 * 2, 48 * 2, 7 * 2, 7 * 2),
            self.sprites.subsurface(88 * 2, 48 * 2, 7 * 2, 7 * 2)
        ]

        self.screen.fill([0, 0, 0])

        # colors
        black = pygame.Color("black")
        white = pygame.Color("white")
        purple = pygame.Color(127, 64, 64)
        pink = pygame.Color(191, 160, 128)

        self.screen.blit(self.font.render("HI-SCORE", False, purple), [105, 35])
        self.screen.blit(self.font.render(str(hiscore), False, pink), [295, 35])

        self.screen.blit(self.font.render("STAGE" + str(self.stage).rjust(3), False, white), [170, 65])

        self.screen.blit(self.font.render("I-PLAYER", False, purple), [25, 95])

        # player 1 global score
        self.screen.blit(self.font.render(str(self.players[0].score).rjust(8), False, pink), [25, 125])

        if self.nr_of_players == 2:
            self.screen.blit(self.font.render("II-PLAYER", False, purple), [310, 95])

            # player 2 global score
            self.screen.blit(self.font.render(str(self.players[1].score).rjust(8), False, pink), [325, 125])

        # tanks and arrows
        for i in range(4):
            self.screen.blit(img_tanks[i], [226, 160 + (i * 45)])
            self.screen.blit(img_arrows[0], [206, 168 + (i * 45)])
            if self.nr_of_players == 2:
                self.screen.blit(img_arrows[1], [258, 168 + (i * 45)])

        self.screen.blit(self.font.render("TOTAL", False, white), [70, 335])

        # total underline
        pygame.draw.line(self.screen, white, [170, 330], [307, 330], 4)

        pygame.display.flip()

        self.clock.tick(2)

        interval = 5

        # points and kills
        for i in range(4):

            # total specific tanks
            tanks = self.players[0].trophies["enemy" + str(i)]

            for n in range(tanks + 1):
                if n > 0 and self.play_sounds:
                    self.sounds["score"].play()

                # erase previous text
                self.screen.blit(self.font.render(str(n - 1).rjust(2), False, black), [170, 168 + (i * 45)])
                # print new number of enemies
                self.screen.blit(self.font.render(str(n).rjust(2), False, white), [170, 168 + (i * 45)])
                # erase previous text
                self.screen.blit(self.font.render(str((n - 1) * (i + 1) * 100).rjust(4) + " PTS", False, black),
                            [25, 168 + (i * 45)])
                # print new total points per enemy
                self.screen.blit(self.font.render(str(n * (i + 1) * 100).rjust(4) + " PTS", False, white),
                            [25, 168 + (i * 45)])
                pygame.display.flip()
                self.clock.tick(interval)

            if self.nr_of_players == 2:
                tanks = self.players[1].trophies["enemy" + str(i)]

                for n in range(tanks + 1):

                    if n > 0 and self.play_sounds:
                        self.sounds["score"].play()

                    self.screen.blit(self.font.render(str(n - 1).rjust(2), False, black), [277, 168 + (i * 45)])
                    self.screen.blit(self.font.render(str(n).rjust(2), False, white), [277, 168 + (i * 45)])

                    self.screen.blit(self.font.render(str((n - 1) * (i + 1) * 100).rjust(4) + " PTS", False, black),
                                [325, 168 + (i * 45)])
                    self.screen.blit(self.font.render(str(n * (i + 1) * 100).rjust(4) + " PTS", False, white),
                                     [325, 168 + (i * 45)])

                    pygame.display.flip()
                    self.clock.tick(interval)

            self.clock.tick(interval)

        # total tanks
        tanks = sum([i for i in self.players[0].trophies.values()]) - self.players[0].trophies["bonus"]
        self.screen.blit(self.font.render(str(tanks).rjust(2), False, white), [170, 335])
        if self.nr_of_players == 2:
            tanks = sum([i for i in self.players[1].trophies.values()]) - self.players[1].trophies["bonus"]
            self.screen.blit(self.font.render(str(tanks).rjust(2), False, white), [277, 335])

        pygame.display.flip()

        # do nothing for 2 seconds
        self.clock.tick(1)
        self.clock.tick(1)

        if self.game_over:
            self.gameOverScreen()
        else:
            self.nextLevel()

    def chunks(self, l, n):
        """
            Split text string in chunks of specified size
            @param string l Input string
            @param int n Size (number of characters) of each chunk
            @return list
        """
        return [l[i:i + n] for i in range(0, len(l), n)]

    def writeInBricks(self, text, pos):
        """
            Write specified text in "brick font"
            @return None
        """
        bricks = self.sprites.subsurface(56 * 2, 64 * 2, 8 * 2, 8 * 2)
        brick1 = bricks.subsurface((0, 0, 8, 8))
        brick2 = bricks.subsurface((8, 0, 8, 8))
        brick3 = bricks.subsurface((8, 8, 8, 8))
        brick4 = bricks.subsurface((0, 8, 8, 8))

        alphabet = {
            "a": "0071b63c7ff1e3",
            "b": "01fb1e3fd8f1fe",
            "c": "00799e0c18199e",
            "e": "01fb060f98307e",
            "g": "007d860cf8d99f",
            "i": "01f8c183060c7e",
            "l": "0183060c18307e",
            "m": "018fbffffaf1e3",
            "o": "00fb1e3c78f1be",
            "r": "01fb1e3cff3767",
            "t": "01f8c183060c18",
            "v": "018f1e3eef8e08",
            "y": "019b3667860c18"
        }

        abs_x, abs_y = pos

        for letter in text.lower():

            binstr = ""
            for h in self.chunks(alphabet[letter], 2):
                binstr += str(bin(int(h, 16)))[2:].rjust(8, "0")
            binstr = binstr[7:]

            x, y = 0, 0
            letter_w = 0
            surf_letter = pygame.Surface((56, 56))
            for j, row in enumerate(self.chunks(binstr, 7)):
                for i, bit in enumerate(row):
                    if bit == "1":
                        if i % 2 == 0 and j % 2 == 0:
                            surf_letter.blit(brick1, [x, y])
                        elif i % 2 == 1 and j % 2 == 0:
                            surf_letter.blit(brick2, [x, y])
                        elif i % 2 == 1 and j % 2 == 1:
                            surf_letter.blit(brick3, [x, y])
                        elif i % 2 == 0 and j % 2 == 1:
                            surf_letter.blit(brick4, [x, y])
                        if x > letter_w:
                            letter_w = x
                    x += 8
                x = 0
                y += 8
            self.screen.blit(surf_letter, [abs_x, abs_y])
            abs_x += letter_w + 16

    def drawIntroScreen(self, put_on_surface=True, tick=310):
        """
            Draw intro (menu) screen
            @param boolean put_on_surface If True, flip display after drawing
            @return None
        """
        self.screen.fill([0, 0, 0])

        if pygame.font.get_init():
            hiscore = self.loadHiscore()

            self.screen.blit(self.font.render("HI- " + str(hiscore), True, pygame.Color('white')), [170, 35])

            self.screen.blit(self.font.render("1 PLAYER", True, pygame.Color('white')), [165, 250])
            self.screen.blit(self.font.render("2 PLAYERS", True, pygame.Color('white')), [165, 275])

            # insert instruction
            insert_word = pygame.font.Font(None, 24)
            insert_word.set_italic(True)
            self.screen.blit(
                insert_word.render("Press P to switch control. Press O to show status.", True, pygame.Color(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))),
                [50, tick])

            self.screen.blit(self.font.render("(c) 1980 1985 NAMCO LTD.", True, pygame.Color('white')), [50, 350])
            self.screen.blit(self.font.render("ALL RIGHTS RESERVED", True, pygame.Color('white')), [85, 380])

        if self.nr_of_players == 1:
            self.screen.blit(self.player_image, [125, 245])
        elif self.nr_of_players == 2:
            self.screen.blit(self.player_image, [125, 270])

        self.writeInBricks("battle", [65, 80])
        self.writeInBricks("city", [129, 160])

        if put_on_surface:
            pygame.display.flip()

    def animateIntroScreen(self):
        # Opening Cinematic
        self.drawIntroScreen(False)
        screen_cp = self.screen.copy()

        self.screen.fill([0, 0, 0])

        y = 416
        while y > 0:
            time_passed = self.clock.tick(50)
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        y = 0
                        break

            self.screen.blit(screen_cp, [0, y])
            pygame.display.flip()
            y -= 5

        self.screen.blit(screen_cp, [0, 0])
        pygame.display.flip()

    def shieldPlayer(self, player, shield=True, duration=None):
        """
            Add/remove shield
            player: player (not enemy)
            shield: true/false
            duration: in ms. if none, do not remove shield automatically
        """
        player.shielded = shield
        if shield:
            player.timer_uuid_shield = self.gtimer.add(100, lambda: player.toggleShieldImage())
        else:
            self.gtimer.destroy(player.timer_uuid_shield)

        if shield and duration is not None:
            self.gtimer.add(duration, lambda: self.shieldPlayer(player, False), 1)

    def respawnPlayer(self, player, clear_scores=False):
        """ Respawn player """

        player.reset()

        # clear player path
        player.path = []

        if clear_scores:
            player.trophies = {
                "bonus": 0, "enemy0": 0, "enemy1": 0, "enemy2": 0, "enemy3": 0
            }

        self.shieldPlayer(player, True, 4000)

    def reloadPlayers(self):
        """ Init robots.
            If robots already exist, just reset them.
        """
        if len(self.players) == 0:
            # first player
            x = 8 * self.TILE_SIZE + (self.TILE_SIZE * 2 - 26) / 2
            y = 24 * self.TILE_SIZE + (self.TILE_SIZE * 2 - 26) / 2

            robot1 = Robot(
                self.sprites, self.enemies, self.players, self.bonuses, self.level, 0, self.bullets, self.castle, [x, y], self.DIR_UP, (0, 0, 13 * 2, 13 * 2)
            )
            self.players.append(robot1)

            # second player
            if self.nr_of_players == 2:
                x = 16 * self.TILE_SIZE + (self.TILE_SIZE * 2 - 26) / 2
                y = 24 * self.TILE_SIZE + (self.TILE_SIZE * 2 - 26) / 2
                robot2 = Robot(
                    self.sprites, self.enemies, self.players, self.bonuses, self.level, 0, self.bullets, self.castle, [x, y], self.DIR_UP, (16 * 2, 0, 13 * 2, 13 * 2)
                )
                robot2.controls = [102, 119, 100, 115, 97]
                self.players.append(robot2)

        for player in self.players:
            player.level = self.level
            player.lives = 99
            self.respawnPlayer(player, True)

    def spawnEnemy(self):
        """
            Spawn new enemy if needed
            Only add enemy if:
                - there are at least one in queue
                - map capacity hasn't exceeded its quota
                - now isn't timefreeze
        """
        if len(self.enemies) >= self.level.max_active_enemies:
            return
        if len(self.level.enemies_left) < 1 or self.timefreeze:
            return
        enemy = tanks.Enemy(self.level, 1)

        self.enemies.append(enemy)

    def drawSidebar(self):
        x = 416
        y = 0
        self.screen.fill([100, 100, 100], pygame.Rect([416, 0], [64, 416]))

        xpos = x + 16
        ypos = y + 16

        # draw enemy lives
        for n in range(len(self.level.enemies_left) + len(self.enemies)):
            self.screen.blit(self.enemy_life_image, [xpos, ypos])
            if n % 2 == 1:
                xpos = x + 16
                ypos += 17
            else:
                xpos += 17

        # players' lives
        if pygame.font.get_init():
            text_color = pygame.Color('black')
            for n in range(len(self.players)):
                if n == 0:
                    self.screen.blit(self.font.render(str(n + 1) + "P", False, text_color), [x + 16, y + 200])
                    self.screen.blit(self.font.render(str(self.players[n].lives), False, text_color), [x + 31, y + 215])
                    self.screen.blit(self.player_life_image, [x + 17, y + 215])
                else:
                    self.screen.blit(self.font.render(str(n + 1) + "P", False, text_color), [x + 16, y + 240])
                    self.screen.blit(self.font.render(str(self.players[n].lives), False, text_color), [x + 31, y + 255])
                    self.screen.blit(self.player_life_image, [x + 17, y + 255])

            self.screen.blit(self.flag_image, [x + 17, y + 280])
            self.screen.blit(self.font.render(str(self.stage), False, text_color), [x + 17, y + 312])

    def draw(self):
        self.screen.fill([0, 0, 0])

        self.level.draw([self.level.TILE_EMPTY, self.level.TILE_BRICK, self.level.TILE_STEEL, self.level.TILE_FROZE,
                         self.level.TILE_WATER])

        self.castle.draw()

        for enemy in self.enemies:
            enemy.draw()

        for label in self.labels:
            label.draw()

        for player in self.players:
            player.draw()

        for bullet in self.bullets:
            bullet.draw()

        for bonus in self.bonuses:
            bonus.draw()

        self.level.draw([self.level.TILE_GRASS])

        if self.game_over:
            if self.game_over_y > 188:
                self.game_over_y -= 4
            self.screen.blit(self.im_game_over, [176, self.game_over_y])  # 176=(416-64)/2

        self.drawSidebar()

        pygame.display.flip()

    def toggleEnemyFreeze(self, freeze=True):
        """ Freeze/defreeze all enemies """
        for enemy in self.enemies:
            enemy.paused = freeze
        self.timefreeze = freeze

    def triggerBonus(self, bonus, player):
        """ Execute bonus powers """
        if self.play_sounds:
            self.sounds["bonus"].play()

        player.trophies["bonus"] += 1
        player.score += 500

        if bonus.bonus == bonus.BONUS_GRENADE:
            for enemy in self.enemies:
                enemy.explode()
        elif bonus.bonus == bonus.BONUS_HELMET:
            self.shieldPlayer(player, True, 10000)
        elif bonus.bonus == bonus.BONUS_SHOVEL:
            self.level.buildFortress(self.level.TILE_STEEL)
            self.gtimer.add(10000, lambda: self.level.buildFortress(self.level.TILE_BRICK), 1)
        elif bonus.bonus == bonus.BONUS_STAR:
            player.superpowers += 1
            if player.superpowers == 2:
                player.max_active_bullets = 2
        elif bonus.bonus == bonus.BONUS_TANK:
            player.lives += 1
        elif bonus.bonus == bonus.BONUS_TIMER:
            self.toggleEnemyFreeze(True)
            self.gtimer.add(10000, lambda: self.toggleEnemyFreeze(False), 1)
        self.bonuses.remove(bonus)

        self.labels.append(tanks.Label(bonus.rect.topleft, "500", 500))

    def finishLevel(self):
        """
            Finish current level
            Show earned scores and advance to the next stage
        """
        if self.play_sounds:
            self.sounds["bg"].stop()

        self.active = False
        self.gtimer.add(3000, lambda: self.showScores(), 1)

        print "Stage " + str(self.stage) + " completed"

    def nextLevel(self):
        """ Start next level """
        del self.bullets[:]
        del self.enemies[:]
        del self.bonuses[:]

        del self.labels[:]
        self.castle.rebuild()
        del self.gtimer.timers[:]

        # load level
        self.stage += 1
        self.level = tanks.Level(self.stage)
        self.timefreeze = False

        # set number of enemies by types (basic, fast, power, armor) according to level
        levels_enemies = (
            (18, 2, 0, 0), (14, 4, 0, 2), (14, 4, 0, 2), (2, 5, 10, 3), (8, 5, 5, 2),
            (9, 2, 7, 2), (7, 4, 6, 3), (7, 4, 7, 2), (6, 4, 7, 3), (12, 2, 4, 2),
            (5, 5, 4, 6), (0, 6, 8, 6), (0, 8, 8, 4), (0, 4, 10, 6), (0, 2, 10, 8),
            (16, 2, 0, 2), (8, 2, 8, 2), (2, 8, 6, 4), (4, 4, 4, 8), (2, 8, 2, 8),
            (6, 2, 8, 4), (6, 8, 2, 4), (0, 10, 4, 6), (10, 4, 4, 2), (0, 8, 2, 10),
            (4, 6, 4, 6), (2, 8, 2, 8), (15, 2, 2, 1), (0, 4, 10, 6), (4, 8, 4, 4),
            (3, 8, 3, 6), (6, 4, 2, 8), (4, 4, 4, 8), (0, 10, 4, 6), (0, 6, 4, 10)
        )

        if self.stage <= 35:
            enemies_l = levels_enemies[self.stage - 1]
        else:
            enemies_l = levels_enemies[34]

        # self.level.enemies_left = [0] * enemies_l[0] + [1] * enemies_l[1] + [2] * enemies_l[2] + [3] * enemies_l[3]
        self.level.enemies_left = [0] * 10
        random.shuffle(self.level.enemies_left)
        self.level.enemies_left = self.level.enemies_left[0: len(self.level.enemies_left)/2]

        if self.play_sounds:
            self.sounds["start"].play()
            self.gtimer.add(4330, lambda: self.sounds["bg"].play(-1), 1)

        self.reloadPlayers()

        self.gtimer.add(3000, lambda: self.spawnEnemy())

        self.game_over = False
        self.running = True
        self.active = True
        self.show_status = False
        self.show_circle = 500

        self.draw()

        while self.running:

            time_passed = self.clock.tick(50)

            for event in pygame.event.get():
                if event.type == pygame.MOUSEBUTTONDOWN:
                    pass
                elif event.type == pygame.QUIT:
                    quit()
                elif event.type == pygame.KEYDOWN and not self.game_over and self.active:

                    if event.key == pygame.K_q:
                        quit()
                    # toggle sounds
                    elif event.key == pygame.K_m:
                        self.play_sounds = not self.play_sounds
                        if not self.play_sounds:
                            pygame.mixer.stop()
                        else:
                            self.sounds["bg"].play(-1)
                    # active AI robot or shut down
                    elif event.key == pygame.K_p:
                        self.auto_active = not self.auto_active
                    # show enemies status
                    elif event.key == pygame.K_o:
                        self.show_status = True

                    for player in self.players:
                        if player.state == player.STATE_ALIVE and self.auto_active is False:
                            try:
                                index = player.controls.index(event.key)
                            except:
                                pass
                            else:
                                if index == 0:
                                    if player.fire() and self.play_sounds:
                                        self.sounds["fire"].play()
                                elif index == 1:
                                    player.pressed[0] = True
                                elif index == 2:
                                    player.pressed[1] = True
                                elif index == 3:
                                    player.pressed[2] = True
                                elif index == 4:
                                    player.pressed[3] = True
                elif event.type == pygame.KEYUP and not self.game_over and self.active:
                    for player in self.players:
                        if player.state == player.STATE_ALIVE:
                            try:
                                index = player.controls.index(event.key)
                            except:
                                pass
                            else:
                                if index == 1:
                                    player.pressed[0] = False
                                elif index == 2:
                                    player.pressed[1] = False
                                elif index == 3:
                                    player.pressed[2] = False
                                elif index == 4:
                                    player.pressed[3] = False

            for player in self.players:
                if player.state == player.STATE_ALIVE and not self.game_over:
                    if self.auto_active is False:
                        if player.pressed[0]:
                            player.move(self.DIR_UP)
                            player.path = []
                        elif player.pressed[1]:
                            player.move(self.DIR_RIGHT)
                            player.path = []
                        elif player.pressed[2]:
                            player.move(self.DIR_DOWN)
                            player.path = []
                        elif player.pressed[3]:
                            player.move(self.DIR_LEFT)
                            player.path = []
                if self.auto_active:
                    player.ai_update(time_passed)
                else:
                    player.update(time_passed)
            for enemy in self.enemies:
                if enemy.state == enemy.STATE_DEAD and not self.game_over and self.active:
                    self.enemies.remove(enemy)
                    if len(self.level.enemies_left) == 0 and len(self.enemies) == 0:
                        self.finishLevel()
                else:
                    enemy.update(time_passed)

                    if self.show_status is True:
                        if self.show_circle > 0:
                            show_x = tanks.Label((enemy.rect.left, enemy.rect.bottom), "X:{0}".format(enemy.rect.centerx), 1)
                            show_y = tanks.Label((enemy.rect.left, enemy.rect.bottom+13), "Y:{0}".format(enemy.rect.centery), 1)
                            show_health = tanks.Label((enemy.rect.left, enemy.rect.bottom+26), "HEALTH:{0}".format(enemy.health), 1)
                            self.labels.append(show_x)
                            self.labels.append(show_y)
                            self.labels.append(show_health)
                            self.show_circle -= 1
                        else:
                            self.show_status = False
                            self.show_circle = 500

            if not self.game_over and self.active:
                for player in self.players:
                    if player.state == player.STATE_ALIVE:
                        if player.bonus is not None and player.side == player.SIDE_PLAYER:
                            self.triggerBonus(player.bonus, player)
                            player.bonus = None
                    elif player.state == player.STATE_DEAD:
                        player.superpowers = 0
                        player.lives -= 1
                        if player.lives > 0:
                            self.respawnPlayer(player)
                        else:
                            self.gameOver()

            for bullet in self.bullets:
                if bullet.state == bullet.STATE_REMOVED:
                    self.bullets.remove(bullet)
                else:
                    bullet.update()

            for bonus in self.bonuses:
                if bonus.active is False:
                    self.bonuses.remove(bonus)

            for label in self.labels:
                if not label.active:
                    self.labels.remove(label)

            if not self.game_over:
                if not self.castle.active:
                    self.gameOver()

            self.gtimer.update(time_passed)

            self.draw()


if __name__ == '__main__':

    tanks_init()

    game = Gameloader(
        sprites=tanks.sprites,
        sounds=tanks.sounds,
        play_sounds=tanks.play_sounds,
        screen=tanks.screen,
        players=tanks.players,
        enemies=tanks.enemies,
        bullets=tanks.bullets,
        bonuses=tanks.bonuses,
        gtimer=tanks.gtimer,
        castle=None,
        labels=tanks.labels
    )
    tanks.castle = tanks.Castle()
    game.castle = tanks.castle
    game.showMenu()
