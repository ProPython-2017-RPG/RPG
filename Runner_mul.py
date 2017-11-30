import pygame
import pyganim
import tiledtmxloader
import math
import socket
import threading
import multiprocessing as mp

FPS = 0
WIDTH = 1024
HEIGHT = 768
CEN_X = WIDTH // 2 - 16
CEN_Y = HEIGHT // 2 - 16
STACK = []
FLAG = [True]

PATH_TO_MAP = 'TilesMap/'

HOST_SERV = "127.0.0.1" # "188.226.185.13"
PORT_SERV = 17070


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
    def __init__(self, img: str, width=32, height=32, num=3, st=0, rect_coll=(16, 0, 2, 2)):
        super().__init__(img, width, height, num, st)

        self.UP = rect_coll[0]
        self.DOWN = self.img_height - rect_coll[1]
        self.LEFT = rect_coll[2]
        self.RIGHT = self.img_width - rect_coll[3]

        self.center_x_const = self.LEFT + (self.RIGHT - self.LEFT) // 2
        self.center_y_const = self.UP + (self.DOWN - self.UP) // 2

        self.run_rate = 0.45
        self.walk_rate = 0.15

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

    def encode(self, flag: bool) -> bytes:
        d = len(LOGGIN).to_bytes(length=1, byteorder='big', signed=False)
        loggin = bytes(LOGGIN, encoding='utf-8')
        x = round(self.pos_x).to_bytes(length=4, byteorder='big', signed=False)
        y = round(self.pos_y).to_bytes(length=4, byteorder='big', signed=False)
        dir_and_flag = (self.direction * 2 + flag).to_bytes(length=1, byteorder='big', signed=False)
        level = self.level.to_bytes(length=1, byteorder='big', signed=True)
        return d + loggin + x + y + dir_and_flag + level


class Friend(Life):
    def __init__(self, img: str, width=32, height=32, num=3, st=0):
        super().__init__(img, width, height, num, st)

        self.pos_x = mp.Value('i', 0)
        self.pos_y = mp.Value('i', 0)

        self.direction = mp.Value('i', 0)
        self.level = mp.Value('i', 0)

        self.flag = mp.Value('b', False)

    def move(self, dx, dy):
        self.pos_x.value += dx
        self.pos_y.value += dy

    def get_pos(self):
        return self.pos_x.value, self.pos_y.value

    def cord(self, player: Player):
        return CEN_X - (player.pos_x - self.pos_x.value), CEN_Y - (player.pos_y - self.pos_y.value)

    def update(self, data: bytes):
        self.pos_x.value = int.from_bytes(bytes=data[0:4], byteorder='big', signed=False)
        self.pos_y.value = int.from_bytes(bytes=data[4:8], byteorder='big', signed=False)
        dir_and_flag = int.from_bytes(bytes=data[8:9], byteorder='big', signed=False)
        self.direction.value = dir_and_flag // 2
        self.flag.value = dir_and_flag % 2
        self.level.value = int.from_bytes(bytes=data[9:10], byteorder='big', signed=True)

    @staticmethod
    def decode(data: bytes, dic: dict):
        d = int(data[0])
        loggin = data[1:d+1]
        dic.setdefault(loggin, Friend('IMG/Hero/Healer.png', 32, 32, 3, 1)).update(data[d+1:])


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

    def check_obj(self, player: Player, friends: dict):
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
                    Map(PATH_TO_MAP+name, self.surface).run(player, friends)
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

    def run(self, player: Player, friends: dict):
        self.start_pos_hero(player)
        clock = pygame.time.Clock()
        pygame.time.set_timer(pygame.USEREVENT, 1000)
        running = False
        direction_x = direction_y = 0
        self.done = True
        while self.done:
            dt = clock.tick(FPS)

            # Отправка
            sock.sendto(player.encode(not direction_x == direction_y == 0), (HOST_SERV, PORT_SERV))

            # event handing
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.done = False
                    FLAG[0] = False
                elif event.type == pygame.USEREVENT:
                    print("FPS: ", clock.get_fps())
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.done = False
                        FLAG[0] = False
                    if event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
                        running = True

                elif event.type == pygame.KEYUP:
                    if event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
                        running = False
            if running:
                rate = player.run_rate
            else:
                rate = player.walk_rate

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

            self.check_obj(player, friends)

            self.surface.fill((0, 0, 0))
            i = 0
            for layer in self.layers:
                self.renderer.render_layer(self.surface, layer)
                if i == self.layer_player:

                    for friend in friends.values():
                        if friend.level.value == player.level:
                            if friend.flag.value:
                                friend.move_conductor.play()
                                friend.anim_objs[friend.direction.value].blit(self.surface, friend.cord(player))
                            else:
                                friend.move_conductor.stop()
                                self.surface.blit(friend.standing[friend.direction.value], friend.cord(player))

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

            pygame.display.flip()


# <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>

def Listen(friends: dict, sock: socket.socket):
    print('Start Listen')
    sock.settimeout(1)
    while FLAG[0]:
        try:
            data, _ = sock.recvfrom(1024)
        except:
            continue
        Friend.decode(data, friends)


if __name__ == "__main__":
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # sock.bind(('127.0.0.1', int(input())))
    LOGGIN = input()

    pygame.init()
    pygame.display.set_caption('RPG')
    screen_width = WIDTH
    screen_height = HEIGHT
    screen = pygame.display.set_mode((screen_width, screen_height))
    INN = Map('TilesMap/Inn.tmx', screen)

    P = Player('IMG/Hero/Healer.png', 32, 32, 3, 1)

    friends = {}
    listen_UDP = threading.Thread(target=Listen, args=(friends, sock))
    # game = threading.Thread(target=Test_1.run, args=(P, friends))

    listen_UDP.start()
    INN.run(P, friends)
    # game.start()

    # game.join()
    sock.close()
    FLAG[0] = False
