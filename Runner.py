import pygame
import pyganim

import tiledtmxloader

import math


class Player:
    def __init__(self, img, position=(16, 16)):
        anim_types = ['front', 'left', 'right', 'back']
        self.anim_objs = {}
        self.standing = {}
        i = 0
        for anim_type in anim_types:
            rects = [(num * 32, i * 32, 32, 32) for num in range(3)]
            all_images = pyganim.getImagesFromSpriteSheet(img, rects=rects)
            self.standing[anim_type] = all_images[1]
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
        return self.pos_x + 16, self.pos_y + 16

    def check_pos(self, width, height, dx, dy):
        if self.pos_x + dx < 0:
            self.pos_x = 0
            dx = 0
        elif self.pos_x + dx + 32 > width:
            self.pos_x = width - 32
            dx = 0
        if self.pos_y + dy < 0:
            self.pos_y = 0
            dy = 0
        elif self.pos_y + dy + 32 > height:
            self.pos_y = height - 32
            dy = 0

        return dx, dy

    def check_collision(self, dx, dy, coll_layer):

        step_dx = (int((self.pos_x + dx) // 32), int(self.pos_y // 32))
        if dx > 0:
            if coll_layer.content2D[step_dx[1]][step_dx[0] + 1] is not None or \
                            coll_layer.content2D[step_dx[1] + 1][step_dx[0] + 1] is not None:
                dx = 0
                self.pos_x = step_dx[0] * 32 - 1
        elif dx < 0:
            if coll_layer.content2D[step_dx[1]][step_dx[0]] is not None or \
                            coll_layer.content2D[step_dx[1] + 1][step_dx[0]] is not None:
                dx = 0
                self.pos_x = step_dx[0] * 32 + 32 + 1

        step_dy = (int(self.pos_x // 32), int((self.pos_y + dy) // 32))
        if dy > 0:
            if coll_layer.content2D[step_dy[1] + 1][step_dy[0]] is not None or \
                            coll_layer.content2D[step_dy[1] + 1][step_dy[0] + 1] is not None:
                dy = 0
                self.pos_y = step_dy[1] * 32 - 1
        elif dy < 0:
            if coll_layer.content2D[step_dy[1]][step_dy[0]] is not None or \
                            coll_layer.content2D[step_dy[1]][step_dy[0] + 1] is not None:
                dy = 0
                self.pos_y = step_dy[1] * 32 + 32 + 1

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

    P = Player('IMG/Hero/ch1.png', (screen_width // 2, screen_height // 2))
    P.move_conductor.play()

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
    run_rate = 10
    walk_rate = 4
    dx = dy = 0

    move_up = move_down = move_left = move_right = False
    direction = 'front'

    # mainloop
    done = True
    while done:
        screen.fill((0, 0, 0))
        # event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    done = False
                if event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
                    running = True
                if event.key == pygame.K_UP:
                    move_up = True
                    move_down = False
                    if not move_left and not move_right:
                        direction = 'back'
                elif event.key == pygame.K_DOWN:
                    move_up = False
                    move_down = True
                    if not move_left and not move_right:
                        direction = 'front'
                elif event.key == pygame.K_LEFT:
                    move_left = True
                    move_right = False
                    if not move_up and not move_down:
                        direction = 'left'
                elif event.key == pygame.K_RIGHT:
                    move_left = False
                    move_right = True
                    if not move_up and not move_down:
                        direction = 'right'

            elif event.type == pygame.KEYUP:
                if event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
                    running = False
                if event.key == pygame.K_UP:
                    move_up = False
                    if move_left:
                        direction = 'left'
                    if move_right:
                        direction = 'right'
                elif event.key == pygame.K_DOWN:
                    move_down = False
                    if move_left:
                        direction = 'left'
                    if move_right:
                        direction = 'right'
                elif event.key == pygame.K_LEFT:
                    move_left = False
                    if move_up:
                        direction = 'back'
                    if move_down:
                        direction = 'front'
                elif event.key == pygame.K_RIGHT:
                    move_right = False
                    if move_up:
                        direction = 'back'
                    if move_down:
                        direction = 'front'

        # render the map
        i = 0
        for sprite_layer in sprite_layers:
            renderer.render_layer(screen, sprite_layer)
            if i == 3:
                if move_up or move_down or move_left or move_right:
                    P.move(dx, dy)
                    P.move_conductor.play()
                    P.anim_objs[direction].blit(screen, (304, 304))
                    # P.anim_objs[direction].blit(screen, P.get_pos())

                    if running:
                        rate = run_rate
                    else:
                        rate = walk_rate

                    dx = dy = 0
                    if move_up:
                        dy -= rate
                    if move_down:
                        dy += rate
                    if move_left:
                        dx -= rate
                    if move_right:
                        dx += rate

                    dx, dy = P.check_collision(dx, dy, sprite_layers[5])

                else:
                    P.move_conductor.stop()
                    screen.blit(P.standing[direction], (304, 304))
                    # screen.blit(P.standing[direction], P.get_pos())
            i += 1

        # adjust camera according to the hero's position, follow him
        cam_pos_x, cam_pos_y = P.get_pos_cam()
        renderer.set_camera_position(cam_pos_x, cam_pos_y)

        pygame.display.update()
        clock.tick(60)


# <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>

demo('TilesMap/Test_1.tmx')
