import pygame
import pyganim

import tiledtmxloader

import math
import time

FPS = 0

UP = 16
DOWN = 0
LEFT = 2
RIGHT = 2

WIDTH = 1024
HEIGHT = 768
CEN_X = WIDTH // 2 - 16
CEN_Y = HEIGHT // 2 - 16

STACK = []

class Player:
    def __init__(self, img, position=(16, 16), width=32, height=32, num=3, st=0):
        self.img_width = width
        self.img_height = height
        anim_types = ['front', 'left', 'right', 'back']
        self.anim_objs = {}
        self.standing = {}
        i = 0
        for anim_type in anim_types:
            rects = [(num * width, i * height, width, height) for num in range(num)]
            all_images = pyganim.getImagesFromSpriteSheet(img, rects=rects)
            self.standing[anim_type] = all_images[st]
            frames = list(zip(all_images, [100] * len(all_images)))
            self.anim_objs[anim_type] = pyganim.PygAnimation(frames)
            i += 1

        self.move_conductor = pyganim.PygConductor(self.anim_objs)

        self.pos_x, self.pos_y = position
        self.pos_x -= self.standing['front'].get_width() / 2
        self.pos_y -= self.standing['front'].get_height() / 2

        self.center_x_const = LEFT + (self.img_width - LEFT - RIGHT) // 2
        self.center_y_const = UP + (self.img_height - UP - DOWN) // 2

        self.run_rate = 0.45
        self.walk_rate = 0.15

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
        left = int((self.pos_x + dx + LEFT) // 32)
        right = int((self.pos_x + dx + self.img_width - RIGHT) // 32)
        up = int((self.pos_y + UP) // 32)
        down = int((self.pos_y + self.img_height - DOWN) // 32)
        if dx > 0:
            if coll_layer.content2D[up][right] is not None or \
                            coll_layer.content2D[down][right] is not None:
                dx = 0
                self.pos_x = right * 32 - self.img_width - 1 + RIGHT
        elif dx < 0:
            if coll_layer.content2D[up][left] is not None or \
                            coll_layer.content2D[down][left] is not None:
                dx = 0
                self.pos_x = (left + 1) * 32 + 0 - LEFT

        left = int((self.pos_x + LEFT) // 32)
        right = int((self.pos_x + self.img_width - RIGHT) // 32)
        up = int((self.pos_y + dy + UP) // 32)
        down = int((self.pos_y + dy + self.img_height - DOWN) // 32)
        if dy > 0:
            if coll_layer.content2D[down][left] is not None or \
                            coll_layer.content2D[down][right] is not None:
                dy = 0
                self.pos_y = down * 32 - self.img_height - 1 + DOWN
        elif dy < 0:
            if coll_layer.content2D[up][left] is not None or \
                            coll_layer.content2D[up][right] is not None:
                dy = 0
                self.pos_y = (up + 1) * 32 + 0 - UP

        return dx, dy


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

    def check_obj(self, player: Player):
        x = player.pos_x + player.center_x_const
        y = player.pos_y + player.center_y_const
        for obj in self.obj_layers[0].objects:
            if x > obj.x and x < obj.x + obj.width and y > obj.y and y < obj.y + obj.height:
                if obj.type == "Gate":
                    print("Gate")
                    STACK.append((int(obj.properties["pos_x"]) * self.tile_width,
                                  int(obj.properties["pos_y"]) * self.tile_height))
                    Tent.run(player)
                    break
                if obj.type == "Exit":
                    print("Exit")
                    self.done = False
                    player.pos_x, player.pos_y = STACK.pop()
                    break

    def start_pos_hero(self, player: Player):
        player.pos_x = self.start_x * self.tile_width
        player.pos_y = self.start_y * self.tile_height

    def run(self, player: Player):
        self.start_pos_hero(player)
        clock = pygame.time.Clock()
        pygame.time.set_timer(pygame.USEREVENT, 1000)
        running = False
        direction = 'front'
        self.done = True
        while self.done:
            dt = clock.tick(FPS)

            # event handing
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.done = False
                elif event.type == pygame.USEREVENT:
                    print("FPS: ", clock.get_fps())
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.done = False
                    if event.key == (pygame.K_LSHIFT, pygame.K_RSHIFT):
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
                direction = 'front'
            elif direction_y == -1:
                direction = 'back'
            if direction_x == 1:
                direction = 'right'
            elif direction_x == -1:
                direction = 'left'

            dir_len = math.hypot(direction_x, direction_y)
            dir_len = dir_len if dir_len else 1.0
            # update position
            dx = rate * dt * direction_x / dir_len
            dy = rate * dt * direction_y / dir_len
            dx, dy = player.check_collision(dx, dy, self.collision)

            self.check_obj(player)

            self.surface.fill((0, 0, 0))
            i = 0
            for layer in self.layers:
                self.renderer.render_layer(self.surface, layer)
                if i == self.layer_player:
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

if __name__ == "__main__":
    pygame.init()
    pygame.display.set_caption('RPG')
    screen_width = WIDTH
    screen_height = HEIGHT
    screen = pygame.display.set_mode((screen_width, screen_height))
    P = Player('IMG/Hero/Healer.png', (0, 0), 32, 32, 3, 1)
    Tent = Map('TilesMap/Tent.tmx', screen)
    Test_1 = Map('TilesMap/Test_1.tmx', screen)
    Test_1.run(P)
