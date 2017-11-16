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

import threading
import socket
import json

HOST = "127.0.0.1"
PORT = 9999

def handle_client(sock, world_map, resources, renderer, screen_width, screen_height, screen):

    P = Player('IMG/Hero/Healer.png', (world_map.pixel_width // 2, world_map.pixel_height // 2), 32, 32, 3, 1)
    center_x = (screen_width - P.img_width) // 2
    center_y = (screen_height - P.img_height) // 2

    cam_pos_x = screen_width // 2
    cam_pos_y = screen_height // 2
    renderer.set_camera_position_and_size(cam_pos_x, cam_pos_y, screen_width, screen_height)

    # retrieve the layers
    sprite_layers = tiledtmxloader.helperspygame.get_layers_from_map(resources)

    # filter layers
    sprite_layers = [layer for layer in sprite_layers if not layer.is_object_group]

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

        if not done:
            sock.close()
            return

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
                # отсылаем координаты игрока через сервер другим клиентам
                data = json.dumps([direction_x, direction_y, dx, dy])
                sock.send(data.encode())

                if direction_x or direction_y:
                    P.move(dx, dy)
                    P.move_conductor.play()
                    P.anim_objs[direction].blit(screen, (center_x, center_y))
                    # P.anim_objs[direction].blit(screen, P.get_pos())
                else:
                    P.move_conductor.stop()
                    screen.blit(P.standing[direction], (center_x, center_y))
                    # screen.blit(P.standing[direction], P.get_pos())
            i += 1

        # adjust camera according to the hero's position, follow him
        cam_pos_x, cam_pos_y = P.get_pos_cam()
        renderer.set_camera_position(cam_pos_x, cam_pos_y)

        pygame.display.update()
        
#  ----------------------------------------------------------------------------------------
# описываем подключенного соперника
def new_player(sock, players, addr, world_map, resources, renderer, screen_width, screen_height, screen):

    P = Player('IMG/Hero/Neko.png', (world_map.pixel_width // 2 - 50, world_map.pixel_height // 2), 32, 48, 4, 0)
    center_x = (screen_width - P.img_width) // 2
    center_y = (screen_height - P.img_height) // 2
    # retrieve the layers
    sprite_layers = tiledtmxloader.helperspygame.get_layers_from_map(resources)

    # filter layers
    sprite_layers = [layer for layer in sprite_layers if not layer.is_object_group]


    direction = 'front'
    # playerloop
    done = True
    while done:

        while True:
            data = sock.recv(4096)
            if not data:  # если главный игрок вышел из игры
                players.discard(addr)
                return
            struct = json.loads(data.decode())
            if struct[0] == addr and struct[1] == 'disconnected':  # если соперник отключился
                players.discard(addr)
                return
            elif struct[0] == addr:
                break

        direction_x = struct[1]
        direction_y = struct[2]
        dx = struct[3]
        dy = struct[4]

        if direction_y == 1:
            direction = 'front'
        elif direction_y == -1:
            direction = 'back'
        if direction_x == 1:
            direction = 'right'
        elif direction_x == -1:
            direction = 'left'
        # render the map
        screen.fill((0, 0, 0))
        i = 0
        for sprite_layer in sprite_layers:
            renderer.render_layer(screen, sprite_layer)
            if i == 4:
                if direction_x or direction_y:
                    P.move(dx, dy)
                    P.move_conductor.play()
                    P.anim_objs[direction].blit(screen, (center_x - 50, center_y))
                    # P.anim_objs[direction].blit(screen, P.get_pos())
                else:
                    P.move_conductor.stop()
                    screen.blit(P.standing[direction], (center_x - 50, center_y))
                    # screen.blit(P.standing[direction], P.get_pos())

            i += 1

        pygame.display.flip()
#  ----------------------------------------------------------------------------------------


def main(file_name):
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

    client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_sock.connect((HOST, PORT))

    # # отправили информацию, что игрок подключился
    # data = json.dumps('connected')
    # client_sock.send(data.encode())

    # отправили главного игрока крутиться в отдельном потоке
    threading.Thread(
        target=handle_client,
        args=[client_sock, world_map, resources, renderer, screen_width, screen_height, screen], daemon=True
    ).start()

    # следим за подключением остальных игроков
    players = list()  # здесь будут храниться адреса подключенных игроков
    while True:
        data = client_sock.recv(4096)
        if not data:
            break
        st = json.loads(data.decode())
        if st[1] == 'connected':
            addr = st[0]
            if addr not in players:
                players.append(addr)
                # создаем поток для подсоединившегося игрока
                threading.Thread(
                    target=new_player,
                    args=[client_sock, players, world_map, resources, renderer, screen_width, screen_height, screen], daemon=True
                ).start()

    client_sock.close()

# <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
if __name__ == '__main__':
    main('TilesMap/Test_1.tmx')

