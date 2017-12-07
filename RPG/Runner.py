import pygame
import pyganim

from RPG import tiledtmxloader
from RPG import input_pygame

import textwrap
import math
import socket
import threading
import os

FPS = 0
DELAY_SEND = 100
WIDTH = 1024
HEIGHT = 768
CEN_X = WIDTH // 2 - 16
CEN_Y = HEIGHT // 2 - 16
STACK = []

RUN = True
DIAL_FLAG = False
MSG = ''

PATH_TO_MAP = 'TilesMap/'

HOST = "127.0.0.1"  # "188.226.185.13"
PORT_UDP = 17070
PORT_TCP = 17071


class Message:
    def __init__(self, font_path: str, font_size: int, frame: str, color=(255, 255, 255), w=WIDTH//4, h=HEIGHT):
        self.color = color
        self.strings = []
        if not os.path.isfile(font_path): font_path = pygame.font.match_font(font_path)
        self.font_object = pygame.font.Font(font_path, font_size)
        self.frame = pygame.transform.scale(pygame.image.load(frame), (w, h))
        self.surface = self.frame.copy()
        self.w = w
        # self.wch = (w-40) // font_size
        self.wch = 35
        self.h = h
        self.hch = (h-40) // self.font_object.get_height()

    def add(self, loggin: str, msg: str):
        msg = textwrap.fill('{0}> {1}\n'.format(loggin, msg), self.wch)
        self.strings += msg.split('\n')
        self.render_lines()

    def render_lines(self):
        self.surface = self.frame.copy()
        up = -self.font_object.get_height()+20
        down = self.surface.get_height()-self.font_object.get_height()-20
        dy = -self.font_object.get_height()
        i = -1
        for y in range(down, up, dy):
            if i < -len(self.strings):
                break
            else:
                self.surface.blit(
                    self.font_object.render(self.strings[i], True, self.color),
                    (20, y))
            i -= 1

    def get_surface(self) -> pygame.Surface:
        return self.surface

class Life:
    def __init__(self, img: str, width=32, height=32, num=3, st=0):
        self.img_width = width
        self.img_height = height

        self.anim_objs = [None] * 4
        self.standing = [None] * 4
        # 0-front, 1-left, 2-right, 3-back
        for i in range(4):
            rects = [(num * width, i * height, width, height) for num in range(num)]
            all_images = pyganim.getImagesFromSpriteSheet(img, rects=rects)
            all_images = list(map(lambda x: x.convert_alpha(), all_images))
            self.standing[i] = all_images[st]
            frames = list(zip(all_images, [120] * len(all_images)))
            self.anim_objs[i] = pyganim.PygAnimation(frames)
        self.move_conductor = pyganim.PygConductor(self.anim_objs)

        self.pos_x = 0
        self.pos_y = 0

        self.direction = 0
        self.level = 0

    def move(self, dx, dy):
        self.pos_x += dx
        self.pos_y += dy

    def get_pos(self):
        return self.pos_x, self.pos_y


class Player(Life):
    def __init__(self, loggin: str, img: str, width=32, height=32, num=3, st=0, rect_coll=(16, 0, 2, 2)):
        super().__init__(img, width, height, num, st)

        self.UP = rect_coll[0]
        self.DOWN = self.img_height - rect_coll[1]
        self.LEFT = rect_coll[2]
        self.RIGHT = self.img_width - rect_coll[3]

        self.center_x_const = self.LEFT + (self.RIGHT - self.LEFT) // 2
        self.center_y_const = self.UP + (self.DOWN - self.UP) // 2

        self.run_rate = 0.45
        self.walk_rate = 0.15

        self.loggin = loggin

        self._stack = []

    def get_pos_cam(self):
        # return self.pos_x + self.center_x_const, self.pos_y + self.center_y_const
        return self.pos_x + 16, self.pos_y + 16

    def help_func(self, dx, dy) -> (float, float, float, float):
        left = self.pos_x + dx + self.LEFT
        right = self.pos_x + dx + self.RIGHT
        up = self.pos_y + dy + self.UP
        down = self.pos_y + dy + self.DOWN
        return left, right, up, down

    def Push(self, x, y):
        self._stack.append((x, y, self.level))

    def Pop(self):
        self.pos_x, self.pos_y, self.level = self._stack.pop()

    def encode_udp(self, flag: bool) -> bytes:
        d = len(self.loggin).to_bytes(length=1, byteorder='big', signed=False)
        loggin = bytes(self.loggin, encoding='utf-8')
        x = round(self.pos_x).to_bytes(length=4, byteorder='big', signed=False)
        y = round(self.pos_y).to_bytes(length=4, byteorder='big', signed=False)
        dir_and_flag = (self.direction * 2 + flag).to_bytes(length=1, byteorder='big', signed=False)
        level = self.level.to_bytes(length=1, byteorder='big', signed=True)
        return d + loggin + x + y + dir_and_flag + level

    def encode_tcp(self, msg) -> bytes:
        d = len(self.loggin).to_bytes(length=1, byteorder='big', signed=False)
        loggin = bytes(self.loggin, encoding='utf-8')
        message = bytes(msg, encoding='utf-8')
        return d + loggin + message


class Friend(Life):
    def __init__(self, img: str, width=32, height=32, num=3, st=0):
        super().__init__(img, width, height, num, st)
        self.show = False

    def cord(self, player: Player):
        return CEN_X - (player.pos_x - self.pos_x), CEN_Y - (player.pos_y - self.pos_y)

    def update(self, data: bytes):
        self.pos_x = int.from_bytes(bytes=data[0:4], byteorder='big', signed=False)
        self.pos_y = int.from_bytes(bytes=data[4:8], byteorder='big', signed=False)
        dir_and_flag = int.from_bytes(bytes=data[8:9], byteorder='big', signed=False)
        self.direction = dir_and_flag // 2
        self.show = dir_and_flag % 2
        self.level = int.from_bytes(bytes=data[9:10], byteorder='big', signed=True)

    @staticmethod
    def decode_pos(data: bytes, dic: dict):
        d = int(data[0])
        loggin = data[1:d + 1]
        dic.setdefault(loggin, Friend('IMG/Hero/Healer.png', 32, 32, 3, 1)).update(data[d + 1:])

    @staticmethod
    def decode_msg(data: bytes, dic: dict, mf: Message):
        d = int(data[0])
        loggin = data[1:d + 1]
        mf.add(loggin.decode(), data[d+1:].decode())
        # dic.setdefault(loggin, Friend('IMG/Hero/Healer.png', 32, 32, 3, 1)).update(data[d + 1:])


class Map:
    def __init__(self, file_name, surface):
        self.surface = surface
        world_map = tiledtmxloader.tmxreader.TileMapParser().parse_decode(file_name)
        self.resources = tiledtmxloader.helperspygame.ResourceLoaderPygame()
        self.resources.load(world_map)

        assert world_map.orientation == "orthogonal"
        self.layer_player = int(world_map.properties["layer_player"])
        n_coll = int(world_map.properties["layer_coll"])
        self.start_x = int(world_map.properties["start_x"])
        self.start_y = int(world_map.properties["start_y"])
        self.level = int(world_map.properties["level"])
        self.flag = world_map.properties["flag"] == "true"

        self.tile_width = world_map.tilewidth
        self.tile_height = world_map.tileheight

        self.renderer = tiledtmxloader.helperspygame.RendererPygame()

        if self.flag:
            cam_pos_x = int(world_map.properties["cam_pos_x"]) * world_map.tilewidth + world_map.tilewidth // 2
            cam_pos_y = int(world_map.properties["cam_pos_y"]) * world_map.tileheight + world_map.tileheight // 2
            cam_size_x = int(world_map.properties["cam_size_x"]) * world_map.tilewidth
            cam_size_y = int(world_map.properties["cam_size_y"]) * world_map.tileheight
        else:
            cam_pos_x = self.start_x * world_map.tilewidth + world_map.tilewidth // 2
            cam_pos_y = self.start_y * world_map.tileheight + world_map.tileheight // 2
            cam_size_x = WIDTH
            cam_size_y = HEIGHT

        self.renderer.set_camera_position_and_size(cam_pos_x, cam_pos_y, cam_size_x, cam_size_y)

        obj_layers = []
        self.layers = []
        for layer in tiledtmxloader.helperspygame.get_layers_from_map(self.resources):
            if layer.is_object_group:
                obj_layers.append(layer)
            else:
                self.layers.append(layer)
        self.obj = None
        self.wall = None
        for layer in obj_layers:
            if layer.name == "Wall":
                self.wall = layer
            elif layer.name == "Obj":
                self.obj = layer

        self.collision = self.layers.pop(n_coll)
        self.done = False

    def check_collision(self, player, dx, dy):
        if dx >= 32 or dy >= 32:
            return 0, 0

        left, right, up, down = map(lambda x: int(x) // 32, player.help_func(dx, 0))
        if dx > 0:
            if self.collision.content2D[up][right] is not None or \
                            self.collision.content2D[down][right] is not None:
                dx = 0
                player.pos_x = right * 32 - player.RIGHT - 1
        elif dx < 0:
            if self.collision.content2D[up][left] is not None or \
                            self.collision.content2D[down][left] is not None:
                dx = 0
                player.pos_x = (left + 1) * 32 - player.LEFT + 0

        left, right, up, down = map(lambda x: int(x) // 32, player.help_func(0, dy))
        if dy > 0:
            if self.collision.content2D[down][left] is not None or \
                            self.collision.content2D[down][right] is not None:
                dy = 0
                player.pos_y = down * 32 - player.DOWN - 1
        elif dy < 0:
            if self.collision.content2D[up][left] is not None or \
                            self.collision.content2D[up][right] is not None:
                dy = 0
                player.pos_y = (up + 1) * 32 - player.UP + 0

        return dx, dy

    def check_obj(self, sock_udp: socket.socket, sock_tcp: socket.socket, player: Player, friends: dict):
        if not self.obj:
            return

        x = player.pos_x + player.center_x_const
        y = player.pos_y + player.center_y_const
        for obj in self.obj.objects:
            if obj.x < x < obj.x + obj.width and obj.y < y < obj.y + obj.height:
                if obj.type == "Gate":
                    player.Push(int(obj.properties["pos_x"]) * self.tile_width,
                                int(obj.properties["pos_y"]) * self.tile_height)
                    name = obj.properties["path"]
                    Map(PATH_TO_MAP + name, self.surface).run(sock_udp, sock_tcp, player, friends)
                    break
                if obj.type == "Exit":
                    self.done = False
                    player.Pop()
                    break

    def check_wall(self, player: Player, dx: float, dy: float) -> (float, float):
        if not self.wall:
            return dx, dy

        left, right, up, down = player.help_func(dx, 0)
        if dx > 0:
            for wall in self.wall.objects:
                if wall.x < right < wall.x + wall.width and \
                        (wall.y < up < wall.y + wall.height or wall.y < down < wall.y + wall.height):
                    dx = 0
                    player.pos_x = wall.x - player.RIGHT - 1
                    break
        elif dx < 0:
            for wall in self.wall.objects:
                if wall.x < left < wall.x + wall.width and \
                        (wall.y < up < wall.y + wall.height or wall.y < down < wall.y + wall.height):
                    dx = 0
                    player.pos_x = wall.x + wall.width - player.LEFT + 0
                    break

        left, right, up, down = player.help_func(0, dy)
        if dy > 0:
            for wall in self.wall.objects:
                if wall.y < down < wall.y + wall.height and \
                        (wall.x < left < wall.x + wall.width or wall.x < right < wall.x + wall.width):
                    dy = 0
                    player.pos_y = wall.y - player.DOWN - 1
                    break
        elif dy < 0:
            for wall in self.wall.objects:
                if wall.y < up < wall.y + wall.height and \
                        (wall.x < left < wall.x + wall.width or wall.x < right < wall.x + wall.width):
                    dy = 0
                    player.pos_y = wall.y + wall.height - player.UP + 0
                    break

        return dx, dy

    def start_pos_hero(self, player: Player):
        player.pos_x = self.start_x
        player.pos_y = self.start_y
        player.level = self.level

    def run(self, sock_udp: socket.socket, sock_tcp: socket.socket, player: Player, friends: dict):
        self.start_pos_hero(player)
        clock = pygame.time.Clock()
        pygame.time.set_timer(pygame.USEREVENT + 0, 1000)
        pygame.time.set_timer(pygame.USEREVENT + 1, DELAY_SEND)
        running = False
        direction_x = direction_y = 0

        dial_flag = False
        msg_input = new_msg()

        self.done = True
        while self.done:
            dt = clock.tick(FPS)
            # event handing
            events = pygame.event.get()
            if dial_flag:
                if msg_input.update(events):
                    msg = msg_input.get_text()
                    sock_tcp.send(player.encode_tcp(msg))
                    message_frame.add(LOGGIN, msg)
                    dial_flag = False
                    msg_input = new_msg()

            for event in events:
                if event.type == pygame.QUIT:
                    self.done = False
                elif event.type == pygame.USEREVENT + 0:
                    print("FPS: ", clock.get_fps())
                elif event.type == pygame.USEREVENT + 1:
                    sock_udp.sendto(player.encode_udp(not direction_x == direction_y == 0), (HOST, PORT_UDP))

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.done = False
                    elif event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
                        running = True
                    elif event.key == pygame.K_q:
                        dial_flag = True

                elif event.type == pygame.KEYUP:
                    if event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
                        running = False

            if running:
                rate = player.run_rate
            else:
                rate = player.walk_rate

            if dial_flag:
                direction_x = 0
                direction_y = 0
            else:
                direction_x = pygame.key.get_pressed()[pygame.K_RIGHT] - \
                              pygame.key.get_pressed()[pygame.K_LEFT]
                direction_y = pygame.key.get_pressed()[pygame.K_DOWN] - \
                              pygame.key.get_pressed()[pygame.K_UP]

            if direction_y == 1:
                player.direction = 0
            elif direction_y == -1:
                player.direction = 3
            if direction_x == 1:
                player.direction = 2
            elif direction_x == -1:
                player.direction = 1

            dir_len = math.hypot(direction_x, direction_y)
            dir_len = dir_len if dir_len else 1.0
            # update position
            dx = rate * dt * direction_x / dir_len
            dy = rate * dt * direction_y / dir_len
            dx, dy = self.check_collision(player, dx, dy)
            dx, dy = self.check_wall(player, dx, dy)

            self.check_obj(sock_udp, sock_tcp, player, friends)

            self.surface.fill((0, 0, 0))
            i = 0
            for layer in self.layers:
                self.renderer.render_layer(self.surface, layer)
                if i == self.layer_player:

                    for friend in friends.values():
                        if friend.level == player.level:
                            if friend.show:
                                friend.move_conductor.play()
                                friend.anim_objs[friend.direction].blit(self.surface, friend.cord(player))
                            else:
                                friend.move_conductor.stop()
                                self.surface.blit(friend.standing[friend.direction], friend.cord(player))

                    if direction_x or direction_y:
                        player.move_conductor.play()
                        player.move(dx, dy)
                        player.anim_objs[player.direction].blit(self.surface, (CEN_X, CEN_Y))
                    else:
                        player.move_conductor.stop()
                        self.surface.blit(player.standing[player.direction], (CEN_X, CEN_Y))
                i += 1
            cam_pos_x, cam_pos_y = player.get_pos_cam()
            self.renderer.set_camera_position(cam_pos_x, cam_pos_y)

            if dial_flag:
                self.surface.blit(dial_frame, (0, 642))
                self.surface.blit(msg_input.get_surface(), (10, 697))

            frame = message_frame.get_surface()
            self.surface.blit(frame, (WIDTH*3//4, 0))

            pygame.display.flip()


# <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>

def new_msg():
    return input_pygame.pygame_textinput.TextInput(font_family='Font/v_Dadhand_ItchyFeet4_v1.02.ttf',
                                            font_size=18,
                                            antialias=True,
                                            text_color=(255, 255, 255),
                                            cursor_color=(255, 255, 255),
                                            max_len=100)


def listen_udp(sock: socket.socket, friends: dict):
    while RUN:
        try:
            data, _ = sock.recvfrom(1024)
        except socket.timeout:
            continue
        except ConnectionResetError:
            break
        Friend.decode_pos(data, friends)


def listen_tcp(sock: socket.socket, friends: dict, mf: Message):
    while RUN:
        try:
            data = sock.recv(1024)
        except socket.timeout:
            continue
        Friend.decode_msg(data, friends, mf)


def main():
    os.chdir(os.path.dirname(__file__))
    global RUN
    global LOGGIN
    global message_frame
    global dial_frame
    sock_UDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock_UDP.settimeout(1)

    sock_TCP = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock_TCP.connect((HOST, PORT_TCP))
    sock_TCP.settimeout(1)

    LOGGIN = input('Введите логин: ')
    # LOGGIN = 'User'

    pygame.init()
    pygame.font.init()
    pygame.display.set_caption('RPG')
    screen_width = WIDTH
    screen_height = HEIGHT
    screen = pygame.display.set_mode((screen_width, screen_height))

    message_frame = Message('Font/v_GorillaMilkshake_v1.5.ttf',
                            12,
                            'IMG/Frames/Frame_message.png')

    dial_frame = pygame.image.load('IMG/Frames/Frame_dial.png')

    Inn = Map('TilesMap/Inn.tmx', screen)
    P = Player(LOGGIN, 'IMG/Hero/Healer.png', 32, 32, 3, 1)

    friends = {}

    listen_UDP = threading.Thread(target=listen_udp, args=(sock_UDP, friends))
    listen_TCP = threading.Thread(target=listen_tcp, args=(sock_TCP, friends, message_frame))
    listen_UDP.start()
    listen_TCP.start()

    Inn.run(sock_UDP, sock_TCP, P, friends)
    RUN = False
    listen_UDP.join()
    sock_UDP.close()
    listen_TCP.join()
    sock_TCP.close()


if __name__ == "__main__":
    main()

