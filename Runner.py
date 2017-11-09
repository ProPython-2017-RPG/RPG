import pygame
import pyganim

import tiledtmxloader

import math
import time

FPS = 0

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

    def move(self, dx, dy):
        self.pos_x += dx
        self.pos_y += dy

    def get_pos(self):
        return self.pos_x, self.pos_y

    def get_pos_cam(self):
        return self.pos_x + self.img_width/2, self.pos_y + self.img_height/2

    def check_collision(self, dx, dy, coll_layer):
        if dx >= 32 or dy >= 32:
            return 0, 0
        left = int((self.pos_x + dx) // 32)
        right = int((self.pos_x + dx + self.img_width) // 32)
        up = int(self.pos_y // 32)
        down = int((self.pos_y + self.img_height) // 32)

        if dx > 0:
            if coll_layer.content2D[up][right] is not None or \
                            coll_layer.content2D[down][right] is not None:
                dx = 0
                self.pos_x = right * 32 - self.img_width - 1
        elif dx < 0:
            if coll_layer.content2D[up][left] is not None or \
                            coll_layer.content2D[down][left] is not None:
                dx = 0
                self.pos_x = (left + 1) * 32 + 1

        left = int(self.pos_x // 32)
        right = int((self.pos_x + self.img_width) // 32)
        up = int((self.pos_y + dy) // 32)
        down = int((self.pos_y + dy + self.img_height) // 32)
        if dy > 0:
            if coll_layer.content2D[down][left] is not None or \
                            coll_layer.content2D[down][right] is not None:
                dy = 0
                self.pos_y = down * 32 - self.img_height - 1
        elif dy < 0:
            if coll_layer.content2D[up][left] is not None or \
                            coll_layer.content2D[up][right] is not None:
                dy = 0
                self.pos_y = (up + 1) * 32 + 1

        return dx, dy


def demo(file_name):
    # parser the map (it is done here to initialize the
    # window the same size as the map if it is small enough)
    world_map = tiledtmxloader.tmxreader.TileMapParser().parse_decode(file_name)

    # init pygame and set up a screen
    pygame.init()
    pygame.display.set_caption('RPG')
    screen_width = min(1024, world_map.pixel_width)
    screen_height = min(768, world_map.pixel_height)
    screen = pygame.display.set_mode((screen_width, screen_height))

    # load the images using pygame
    resources = tiledtmxloader.helperspygame.ResourceLoaderPygame()
    resources.load(world_map)

    # prepare map rendering
    assert world_map.orientation == "orthogonal"

    # renderer
    renderer = tiledtmxloader.helperspygame.RendererPygame()

    # P = Player('IMG/Hero/Neko.png', (world_map.pixel_width // 2, world_map.pixel_height // 2), 32, 48, 4, 0)
    # P = Player('IMG/Hero/Usagi.png', (world_map.pixel_width //2, world_map.pixel_height//2), 32, 48, 4, 0)
    # P = Player('IMG/Hero/Rect.png', (world_map.pixel_width // 2, world_map.pixel_height // 2), 32, 48, 4, 0)
    # P = Player('IMG/Hero/Snake.png', (world_map.pixel_width // 2, world_map.pixel_height // 2), 48, 48, 4, 0)
    P = Player('IMG/Hero/Healer.png', (world_map.pixel_width // 2, world_map.pixel_height // 2), 32, 32, 3, 1)
    # other_Players = [Player('IMG/Hero/Neko.png', (world_map.pixel_width//2 - 50, world_map.pixel_height//2), 32, 48, 4, 0)]
    # other_Players[0].move_conductor.play()
    center_x = (screen_width - P.img_width) // 2
    center_y = (screen_height - P.img_height) // 2
    # P.move_conductor.play()

    # set initial cam position and size
    cam_pos_x = screen_width // 2
    cam_pos_y = screen_height // 2
    renderer.set_camera_position_and_size(cam_pos_x, cam_pos_y, screen_width, screen_height)

    # retrieve the layers
    sprite_layers = tiledtmxloader.helperspygame.get_layers_from_map(resources)

    # filter layers
    sprite_layers = [layer for layer in sprite_layers if not layer.is_object_group]

    # add the hero the the right layer, it can be changed using 0-9 keys
    # sprite_layers[3].add_sprite(hero)

    clock = pygame.time.Clock()
    running = False
    run_rate = 0.45
    walk_rate = 0.15
    dx = dy = 0

    direction = 'front'
    pygame.time.set_timer(pygame.USEREVENT, 1000)
    # mainloop
    done = True
    while done:
        dt = clock.tick(FPS)

        # event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = False
            elif event.type == pygame.USEREVENT:
                print("fps: ", clock.get_fps())
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    done = False
                if event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
                    running = True

            elif event.type == pygame.KEYUP:
                if event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
                    running = False
        if running:
            rate = run_rate
        else:
            rate = walk_rate

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
        dx, dy = P.check_collision(dx, dy, sprite_layers[6])

        # render the map
        screen.fill((0, 0, 0))
        i = 0
        for sprite_layer in sprite_layers:
            renderer.render_layer(screen, sprite_layer)
            if i == 4:
                if direction_x or direction_y:
                    P.move(dx, dy)
                    P.move_conductor.play()
                    P.anim_objs[direction].blit(screen, (center_x, center_y))
                    # P.anim_objs[direction].blit(screen, P.get_pos())

                else:
                    P.move_conductor.stop()
                    screen.blit(P.standing[direction], (center_x, center_y))
                    # screen.blit(P.standing[direction], P.get_pos())

                # for op in other_Players:
                #     if direction_x or direction_y:
                #         op.move(dx, dy)
                #         op.move_conductor.play()
                #         op.anim_objs[direction].blit(screen, (center_x - 50, center_y))
                #         # P.anim_objs[direction].blit(screen, P.get_pos())
                #
                #     else:
                #         op.move_conductor.stop()
                #         screen.blit(op.standing[direction], (center_x - 50, center_y))
                #         # screen.blit(P.standing[direction], P.get_pos())
            i += 1

        # adjust camera according to the hero's position, follow him
        cam_pos_x, cam_pos_y = P.get_pos_cam()
        renderer.set_camera_position(cam_pos_x, cam_pos_y)

        pygame.display.flip()


# <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>

demo('TilesMap/Test_1.tmx')
