import pygame
import pyganim
import tiledtmxloader
import math
import socket
import threading

FPS = 60
WIDTH = 1024
HEIGHT = 768
CEN_X = WIDTH // 2 - 16
CEN_Y = HEIGHT // 2 - 16
STACK = []
FLAG = [True]


class Player:
    def __init__(self, img: str, position=(16, 16), width=32, height=32, num=3, st=0, rect_coll=(16, 0, 2, 2)):
        self.img_width = width
        self.img_height = height

        self.UP = rect_coll[0]
        self.DOWN = rect_coll[1]
        self.LEFT = rect_coll[2]
        self.RIGHT = rect_coll[3]

        self.anim_objs = [None]*4
        self.standing = [None]*4
        # 0-front, 1-left, 2-right, 3-back
        for i in range(4):
            rects = [(num * width, i * height, width, height) for num in range(num)]
            all_images = pyganim.getImagesFromSpriteSheet(img, rects=rects)
            all_images = list(map(lambda x: x.convert_alpha(), all_images))
            self.standing[i] = all_images[st]
            frames = list(zip(all_images, [120] * len(all_images)))
            self.anim_objs[i] = pyganim.PygAnimation(frames)

        self.move_conductor = pyganim.PygConductor(self.anim_objs)

        self.pos_x, self.pos_y = position
        self.pos_x -= self.img_width / 2
        self.pos_y -= self.img_height / 2

        self.center_x_const = self.LEFT + (self.img_width - self.LEFT - self.RIGHT) // 2
        self.center_y_const = self.UP + (self.img_height - self.UP - self.DOWN) // 2

        self.run_rate = 0.45
        self.walk_rate = 0.15

        self.level = 0

    def move(self, dx, dy):
        self.pos_x += dx
        self.pos_y += dy

    def get_pos(self):
        return self.pos_x, self.pos_y

    def get_pos_cam(self):
        return self.pos_x + self.img_width / 2, self.pos_y + self.img_height / 2

    def check_collision(self, dx, dy, coll_layer):
        if dx >= 32 or dy >= 32:
            return 0, 0

        left = int((self.pos_x + dx + self.LEFT) // 32)
        right = int((self.pos_x + dx + self.img_width - self.RIGHT) // 32)
        up = int((self.pos_y + self.UP) // 32)
        down = int((self.pos_y + self.img_height - self.DOWN) // 32)

        if dx > 0:
            if coll_layer.content2D[up][right] is not None or \
                            coll_layer.content2D[down][right] is not None:
                dx = 0
                self.pos_x = right * 32 - self.img_width - 1 + self.RIGHT
        elif dx < 0:
            if coll_layer.content2D[up][left] is not None or \
                            coll_layer.content2D[down][left] is not None:
                dx = 0
                self.pos_x = (left + 1) * 32 + 0 - self.LEFT

        left = int((self.pos_x + self.LEFT) // 32)
        right = int((self.pos_x + self.img_width - self.RIGHT) // 32)
        up = int((self.pos_y + dy + self.UP) // 32)
        down = int((self.pos_y + dy + self.img_height - self.DOWN) // 32)

        if dy > 0:
            if coll_layer.content2D[down][left] is not None or \
                            coll_layer.content2D[down][right] is not None:
                dy = 0
                self.pos_y = down * 32 - self.img_height - 1 + self.DOWN
        elif dy < 0:
            if coll_layer.content2D[up][left] is not None or \
                            coll_layer.content2D[up][right] is not None:
                dy = 0
                self.pos_y = (up + 1) * 32 + 0 - self.UP

        return dx, dy

    def encode(self, direction: int, flag: bool):
        x = round(self.pos_x).to_bytes(length=4, byteorder='big', signed=False)
        y = round(self.pos_y).to_bytes(length=4, byteorder='big', signed=False)
        dir_and_flag = (direction*2+flag).to_bytes(length=1, byteorder='big', signed=False)
        level = self.level.to_bytes(length=1, byteorder='big', signed=True)
        return x+y+dir_and_flag+level


class Friend(Player):
    def __init__(self, img, position=(16, 16), width=32, height=32, num=3, st=0):
        super().__init__(img, position, width, height, num, st)
        self.dir = 0
        self.flag = False

    def cord(self, player: Player):
        return CEN_X - (player.pos_x - self.pos_x), CEN_Y - (player.pos_y - self.pos_y)

    def decode(self, data: bytes):
        self.pos_x = int.from_bytes(bytes=data[0:4], byteorder='big', signed=False)
        self.pos_y = int.from_bytes(bytes=data[4:8], byteorder='big', signed=False)
        dir_and_flag = int.from_bytes(bytes=data[8:9], byteorder='big', signed=False)
        self.dir = dir_and_flag // 2
        self.flag = dir_and_flag % 2
        self.level = int.from_bytes(bytes=data[9:10], byteorder='big', signed=True)


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

        self.obj_layers = []
        self.layers = []
        for layer in tiledtmxloader.helperspygame.get_layers_from_map(self.resources):
            if layer.is_object_group:
                self.obj_layers.append(layer)
            else:
                self.layers.append(layer)
        self.collision = self.layers.pop(n_coll)

        self.done = False

    def check_obj(self, player: Player, other: Friend):
        x = player.pos_x + player.center_x_const
        y = player.pos_y + player.center_y_const
        for obj in self.obj_layers[0].objects:
            if x > obj.x and x < obj.x + obj.width and y > obj.y and y < obj.y + obj.height:
                if obj.type == "Gate":
                    player.level += 1
                    STACK.append((int(obj.properties["pos_x"]) * self.tile_width,
                                  int(obj.properties["pos_y"]) * self.tile_height))
                    Tent.run(player, other)
                    break
                if obj.type == "Exit":
                    player.level -= 1
                    self.done = False
                    player.pos_x, player.pos_y = STACK.pop()
                    break

    def start_pos_hero(self, player: Player):
        player.pos_x = self.start_x * self.tile_width
        player.pos_y = self.start_y * self.tile_height

    def run(self, player: Player, other: Friend):
        self.start_pos_hero(player)
        clock = pygame.time.Clock()
        pygame.time.set_timer(pygame.USEREVENT, 1000)
        running = False
        direction = 0
        direction_x = direction_y = 0
        self.done = True
        while self.done:
            dt = clock.tick(FPS)

            # Отправка
            sock.sendto(player.encode(direction, not direction_x == direction_y == 0), (HOST, 8080))

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
                direction = 0
            elif direction_y == -1:
                direction = 3
            if direction_x == 1:
                direction = 2
            elif direction_x == -1:
                direction = 1

            dir_len = math.hypot(direction_x, direction_y)
            dir_len = dir_len if dir_len else 1.0
            # update position
            dx = rate * dt * direction_x / dir_len
            dy = rate * dt * direction_y / dir_len
            dx, dy = player.check_collision(dx, dy, self.collision)

            self.check_obj(player, other)

            self.surface.fill((0, 0, 0))
            i = 0
            for layer in self.layers:
                self.renderer.render_layer(self.surface, layer)
                if i == self.layer_player:
                    if other.level == player.level:
                        if other.flag:
                            other.move_conductor.play()
                            other.anim_objs[other.dir].blit(self.surface, other.cord(player))
                        else:
                            other.move_conductor.stop()
                            self.surface.blit(other.standing[other.dir], other.cord(player))
                    if direction_x or direction_y:
                        player.move_conductor.play()
                        player.move(dx, dy)
                        player.anim_objs[direction].blit(self.surface, (CEN_X, CEN_Y))
                    else:
                        player.move_conductor.stop()
                        self.surface.blit(player.standing[direction], (CEN_X, CEN_Y))
                i += 1
            cam_pos_x, cam_pos_y = player.get_pos_cam()
            self.renderer.set_camera_position(cam_pos_x, cam_pos_y)

            pygame.display.flip()


# <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>

def Listen(other: Friend):
    while FLAG[0]:
        try:
            data, _ = sock.recvfrom(1024)
        except:
            continue
        other.decode(data)


if __name__ == "__main__":
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    HOST = "127.0.0.1"
    PORT = int(input('Введите порт для соединения с сервером: '))
    sock.bind((HOST, PORT))
    sock.settimeout(1)

    pygame.init()
    pygame.display.set_caption('RPG')
    screen_width = WIDTH
    screen_height = HEIGHT
    screen = pygame.display.set_mode((screen_width, screen_height))
    P = Player('IMG/Hero/Healer.png', (0, 0), 32, 32, 3, 1)

    F = Friend('IMG/Hero/Healer.png', (0, 0), 32, 32, 3, 1)

    Tent = Map('TilesMap/Tent.tmx', screen)
    Test_1 = Map('TilesMap/Test_1.tmx', screen)

    threading.Thread(target=Listen, args=(F,)).start()
    Test_1.run(P, F)

    sock.close()
    FLAG[0] = False
