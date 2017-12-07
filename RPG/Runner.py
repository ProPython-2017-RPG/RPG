import pygame
import pyganim

from RPG import tiledtmxloader
from RPG.input_pygame import pygame_textinput
from RPG import sql

import textwrap
import math
import socket
import threading
import os
import logging

FPS = 0
DELAY_SEND = 100
WIDTH = 1024
HEIGHT = 768
CEN_X = WIDTH // 2 - 16
CEN_Y = HEIGHT // 2 - 16

RUN = True

PATH_TO_MAP = 'TilesMap/'
PATH_TO_LOG = 'game.log'

HOST = "127.0.0.1"  # "188.226.185.13"
PORT_UDP = 17070
PORT_TCP = 17071

SPECIAL_ID = ['asuka',
              'katsuragi',
              'shinji']


class Message:
    """
    Класс для рамки сообщений
    """

    def __init__(self, font_path: str, font_size: int, frame: str, w=WIDTH // 4, h=HEIGHT):
        """
        :param font_path: Путь к шрифту
        :param font_size: Размер текста
        :param frame: Путь к изображению рамки
        :param w: Длина рамки
        :param h: Высота рамки
        """
        self.colors = []
        self.strings = []
        if not os.path.isfile(font_path): font_path = pygame.font.match_font(font_path)
        self.font_object = pygame.font.Font(font_path, font_size)
        self.frame = pygame.transform.scale(pygame.image.load(frame), (w, h))
        self.surface = self.frame.copy()
        self.w = w
        self.wch = (w - 40) // self.font_object.size('a')[0]
        self.h = h
        self.hch = (h - 40) // self.font_object.size('a')[1]

    @staticmethod
    def login_to_rpg(login: str) -> (int, int, int):
        """
        Функция возвращает цвет для логина
        У каждого пользователя свой цвет сообщения
        :param login: Логин игрока
        :return: Цвет в RGB
        """
        r, g, b = 0, 0, 0
        for i in range(len(login) // 3):
            r += ord(login[i])
            g += ord(login[i + 1])
            b += ord(login[i + 2])
        r = 255 - r % 230
        g = 255 - r % 150
        b = 255 - r % 230
        return r, g, b

    def add(self, login: str, msg: str):
        """
        Метод добавления соощения в класс
        :param login: логин пользователя
        :param msg: тест сообщения
        :return: None
        """
        msg = textwrap.fill('{0}> {1}\n'.format(login, msg), self.wch)
        lines = msg.split('\n')
        self.colors += [(Message.login_to_rpg(login))] * len(lines)
        self.strings += lines
        self.render_lines()

    def render_lines(self):
        """
        Обновляет Surface
        :return: None
        """
        self.surface = self.frame.copy()
        up = -self.font_object.get_height() + 20
        down = self.surface.get_height() - self.font_object.get_height() - 20
        dy = -self.font_object.get_height()
        i = -1
        for y in range(down, up, dy):
            if i < -len(self.strings):
                break
            else:
                self.surface.blit(
                    self.font_object.render(self.strings[i], True, self.colors[i]),
                    (20, y))
            i -= 1

    def get_surface(self) -> pygame.Surface:
        """
        Возвращает рамку
        :return: Рамка
        """
        return self.surface


class Life:
    """
    Класс Life - базовый класс для всех живых объектов:
    Player;
    Friend;
    NPC; (Пока в разарботке)
    """

    def __init__(self, id: str, DB_C: sql.DB):
        """
        Инициализет анимацию объекта
        :param id: ID анимации в базе данных
        :param DB_C: Объект для работы с базой данных
        """
        try:
            img, width, height, num, st, x, y = DB_C.search(id)
        except ValueError:
            logging.error("ID=%s not found" % (id,))
            return
        self.img_width = width
        self.img_height = height

        self.anim_objs = [None] * 4
        self.standing = [None] * 4
        # 0-front, 1-left, 2-right, 3-back
        for i in range(4):
            rects = [(x+num * width, y+i * height, width, height) for num in range(num)]
            all_images = pyganim.getImagesFromSpriteSheet(img, rects=rects)
            all_images = list(map(lambda x: x.convert_alpha(), all_images))
            self.standing[i] = all_images[st]
            frames = list(zip(all_images, [120] * len(all_images)))
            self.anim_objs[i] = pyganim.PygAnimation(frames)
        self.move_conductor = pyganim.PygConductor(self.anim_objs)

        self.pos_x = 0
        self.pos_y = 0

        self.run_rate = 0.45
        self.walk_rate = 0.15

        self.id = id

        self.direction = 0
        self.level = 0

    def move(self, dx, dy):
        """
        Метод обновления координат
        :param dx: Дельта X
        :param dy: Дельта Y
        :return: None
        """
        self.pos_x += dx
        self.pos_y += dy

    def get_pos(self):
        """
        Возвращает позицию объекта
        :return: Позиция объекта
        """
        return self.pos_x, self.pos_y


class Player(Life):
    """
    Класс основного игрока
    """

    def __init__(self, login: str, id: str, DB_C: sql.DB, rect_coll=(16, 0, 2, 2)):
        """
        :param login: Логин игрока
        :param id: ID анимации в базе данных
        :param DB_C: Объект для работы с базой данных
        :param rect_coll: Отступ сверху, снизу, слева и справа соответсвенно. Для обработки столкновений
        """
        super().__init__(id, DB_C)
        self.face = self.load_face()

        self.UP = rect_coll[0]
        self.DOWN = self.img_height - rect_coll[1]
        self.LEFT = rect_coll[2]
        self.RIGHT = self.img_width - rect_coll[3]

        self.center_x_const = self.LEFT + (self.RIGHT - self.LEFT) // 2
        self.center_y_const = self.UP + (self.DOWN - self.UP) // 2

        self.login = login

        self._stack = []

    def load_face(self) -> list:
        """
        Загружает изображения лиц персонажа.
        :return: Список лиц
        """
        if self.id in SPECIAL_ID:
            files = list(map(lambda x: 'IMG/Hero/Face/'+self.id+x, os.listdir('IMG/Hero/Face/'+self.id)))
            files = list(filter(os.path.isfile, files))
            return list(map(lambda x: pygame.image.load(x), files))
        else:
            n = int(self.id[-2:])
            path = 'IMG/Hero/Face/'+self.id[:-2]+'.png'
            rect = ((n % 4)*96, (n // 4)*96, 96, 96)
            return list(pyganim.getImagesFromSpriteSheet(path, rects=[rect]))

    def get_pos_cam(self):
        """
        Возвращает позицию для камеры
        :return: Позиция камеры
        """
        return self.pos_x + 16, self.pos_y + 16

    def _help_func(self, dx, dy) -> (float, float, float, float):
        """
        Вспомогательная функция для обработки столкновений
        :param dx: Дельта X
        :param dy: Дельта Y
        :return: X слева, справа, Y сверху, снизу
        """
        left = self.pos_x + dx + self.LEFT
        right = self.pos_x + dx + self.RIGHT
        up = self.pos_y + dy + self.UP
        down = self.pos_y + dy + self.DOWN
        return left, right, up, down

    def push(self, x, y):
        """
        Добовляет в стек информацию.
        Срабатывает при входе в помещение
        :param x: Позиция X
        :param y: Позиция Y
        :return: None
        """
        self._stack.append((x, y, self.level))

    def pop(self):
        """
        Обновляет координаты из стека.
        Срабатывает при выходе из помещения
        :return: None
        """
        self.pos_x, self.pos_y, self.level = self._stack.pop()

    def encode_udp(self, flag: bool) -> bytes:
        """
        Кодирует позицию игрока для отпраки.
        :param flag: Состояние игрока (в движении или нет).
        :return: Байты для отправки
        """
        d = len(self.login).to_bytes(length=1, byteorder='big', signed=False)
        login = bytes(self.login, encoding='utf-8')
        x = round(self.pos_x).to_bytes(length=4, byteorder='big', signed=False)
        y = round(self.pos_y).to_bytes(length=4, byteorder='big', signed=False)
        dir_and_flag = (self.direction * 2 + flag).to_bytes(length=1, byteorder='big', signed=False)
        level = self.level.to_bytes(length=1, byteorder='big', signed=True)
        return d + login + x + y + dir_and_flag + level

    def encode_tcp(self, label: int, *args) -> bytes:
        """
        Кодирует сообщение в байты для отправки.
        :param args: Само сообщение
        :param label: Указывает на тип сообщения
                0 - Текстовое сообщение
                1 - Сообщение о новом игроке
        :return: Байты для отправки
        """
        d = len(self.login).to_bytes(length=1, byteorder='big', signed=False)
        login = bytes(self.login, encoding='utf-8')
        flag = label.to_bytes(length=1, byteorder='big', signed=False)
        if label == 0:
            message = bytes(args[0], encoding='utf-8')
            return d + login + flag + message
        elif label == 1:
            id = bytes(self.id, encoding='utf-8')
            return d + login + flag + id


class Friend(Life):
    """
    Класс других игроков.
    """

    def __init__(self, id: str, DB_C: sql.DB):
        """
        :param id: ID анимации в базе данных
        :param DB_C: Объект для работы с базой данных
        """
        super().__init__(id, DB_C)
        self.show = False

    def cord(self, player: Player):
        """
        Возвращает координаты относительно основного игрока
        :param player: Ссылка на онсовного игрока
        :return: Координата в X и Y
        """
        return CEN_X - (player.pos_x - self.pos_x), CEN_Y - (player.pos_y - self.pos_y)

    def update(self, data: bytes):
        """
        Обновление позиции, по пришедшему сообщению.
        :param data: Байты с информацией
        :return: None
        """
        self.pos_x = int.from_bytes(bytes=data[0:4], byteorder='big', signed=False)
        self.pos_y = int.from_bytes(bytes=data[4:8], byteorder='big', signed=False)
        dir_and_flag = int.from_bytes(bytes=data[8:9], byteorder='big', signed=False)
        self.direction = dir_and_flag // 2
        self.show = dir_and_flag % 2
        self.level = int.from_bytes(bytes=data[9:10], byteorder='big', signed=True)

    @staticmethod
    def decode_udp(data: bytes, dic: dict):
        """
        Декодирует пришедшее по UDP сообщение
        Ищет в словаре игрока с таким же логином и обновляет для него координтаы
        :param data: Пришедщее сообщение
        :param dic: Словарь с игроками по логину
        :return: None
        """
        d = int(data[0])
        login = data[1:d + 1]
        fr = dic.get(login, None)
        if fr is not None:
            fr.update(data[d + 1:])

    @staticmethod
    def decode_tcp(data: bytes, dic: dict, mf: Message, DB_C: sql.DB):
        """
        Декодирует пришедшее по TCP сообщение
        Смотрит на метку и выполняет соответвующую операцию:
        0 - пишет соощение в Message
        1 - добовляет нового игрока
        :param data: Пришедшее сообщение
        :param dic: Словарь с игроками по логину
        :param mf: Рамка с сообщениями
        :return: None
        """
        d = int(data[0])
        login = data[1:d + 1]
        label = int(data[d + 1])
        data = data[d + 2:]
        if label == 0:
            mf.add(login.decode(), data.decode())
        elif label == 1:
            dic[login] = Friend(data.decode(), DB_C)


class Map:
    """
    Класс работаюзий с картами
    """
    def __init__(self, file_name):
        """
        :param file_name: Путь к карте
        """
        # self.surface = surface
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
        """
        Провряет столкновение
        :param player: Основной игрок
        :param dx: Дельта X
        :param dy: Дельта Y
        :return: Обновленные dx, dy
        """
        if dx >= 32 or dy >= 32:
            return 0, 0

        left, right, up, down = map(lambda x: int(x) // 32, player._help_func(dx, 0))
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

        left, right, up, down = map(lambda x: int(x) // 32, player._help_func(0, dy))
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

    def check_wall(self, player: Player, dx: float, dy: float) -> (float, float):
        """
        Также проверяет столкновение, только теперь с объектами.
        (Просто не все стены можно сделать из кубиков карты.
        :param player: Основной игрок
        :param dx: Дельта X
        :param dy: Дельта Y
        :return: Обновленные dx, dy
        """
        if not self.wall:
            return dx, dy

        left, right, up, down = player._help_func(dx, 0)
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

        left, right, up, down = player._help_func(0, dy)
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
        """
        Ставит игрока на начальную позицию.
        :param player: Основной игрок
        :return: None
        """
        player.pos_x = self.start_x
        player.pos_y = self.start_y
        player.level = self.level


class Game:
    """
    Основной класс игры.
    """
    def __init__(self):
        """
        Pass
        """
        # База данных с информацией для анимации персонажей
        self.DB_C = sql.DB('DataBase/Characters.sqlite')
        # Флаг работы игры
        self.RUN = False

        # Соккет для UDP соединения
        self.sock_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock_udp.settimeout(1)
        self.run_udp = False

        # Соккет для TCP соединения
        self.sock_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock_tcp.settimeout(1)
        self.run_tcp = False

        # Вспомогательные "Флаги"
        self.show_message_frame = True
        self.show_glow = False

        # Окно сообщений
        self.message_frame = Message(font_path='Font/UbuntuMono-R.ttf',
                                     font_size=12,
                                     frame='IMG/Frames/Frame_message.png')

        # Окно настроек
        self.option_frame = pygame.image.load('IMG/Frames/Options.png')

        # Изображение иконок
        self.icon = Game.icon_init()

        # Основное игровое окно
        self.screen = Game.pygame_init()

        # Окно ввода
        self.dial_frame = pygame.image.load('IMG/Frames/Frame_dial.png')

        # Другие игроки
        self.friends = {}

        # Основной игрок
        self.player = Game.player_init(self.DB_C)

    def option(self):
        """
        Открывает окно настроек.
        (Включается при нажатии ESC).
        :return: None
        """
        check_pos = [(835, 242),
                     (835, 285)]
        check = self.icon['check']
        arrow = self.icon['arrow']
        arrow_pos = [(560, 233),
                     (560, 279),
                     (560, 320),
                     (560, 362),
                     (560, 404),
                     (560, 448)]
        i_a = 0
        donne = True
        while donne and self.RUN:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.RUN = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        donne = False
                    elif event.key == pygame.K_RETURN:
                        if i_a == 0:
                            # Окно сообщений
                            self.show_message_frame = not self.show_message_frame
                        elif i_a == 1:
                            # Свечение
                            self.show_glow = not self.show_glow
                        elif i_a == 2:
                            # Сохранить
                            pass
                        elif i_a == 3:
                            # Загрузить
                            pass
                        elif i_a == 4:
                            # Титры
                            pass
                        elif i_a == 5:
                            # Выход
                            self.RUN = False

                    elif event.key == pygame.K_DOWN:
                        i_a += 1
                        if i_a >= len(arrow_pos):
                            i_a = 0
                        pygame.time.delay(30)
                    elif event.key == pygame.K_UP:
                        i_a -= 1
                        if i_a < 0:
                            i_a = len(arrow_pos) - 1
                        pygame.time.delay(30)
            self.screen.fill((0, 0, 0))
            self.screen.blit(self.option_frame, (0, 0))
            if self.show_message_frame:
                self.screen.blit(check, check_pos[0])
            if self.show_glow:
                self.screen.blit(check, check_pos[1])
            self.screen.blit(arrow, arrow_pos[i_a])
            pygame.display.flip()

    def check_obj(self, map: Map):
        """
        Проверяет объекты на карте.
        Gate-вход куда либо.
        Exit-выход из помещения.
        :param map: Текущая карта
        :return: None
        """
        if not map.obj:
            return

        x = self.player.pos_x + self.player.center_x_const
        y = self.player.pos_y + self.player.center_y_const
        for obj in map.obj.objects:
            if obj.x < x < obj.x + obj.width and obj.y < y < obj.y + obj.height:
                if obj.type == "Gate":
                    self.player.push(int(obj.properties["pos_x"]),
                                     int(obj.properties["pos_y"]))
                    name = obj.properties["path"]
                    self.map_run(Map(PATH_TO_MAP + name))
                    break
                if obj.type == "Exit":
                    map.done = False
                    self.player.pop()
                    break

    def map_run(self, map: Map):
        """
        Основной игровой цикл на карте.
        :param map: Текущая карта
        :return: None
        """
        map.start_pos_hero(self.player)
        clock = pygame.time.Clock()
        pygame.time.set_timer(pygame.USEREVENT + 0, 1000)
        pygame.time.set_timer(pygame.USEREVENT + 1, DELAY_SEND)
        running = False
        direction_x = direction_y = 0

        dial_flag = False
        msg_input = Game.new_msg()

        map.done = True
        while map.done and self.RUN:
            dt = clock.tick(FPS)
            # event handing
            events = pygame.event.get()
            if dial_flag:
                if msg_input.update(events):
                    msg = msg_input.get_text()
                    if self.run_tcp:
                        self.sock_tcp.send(self.player.encode_tcp(msg))
                    self.message_frame.add(self.player.login, msg)
                    dial_flag = False
                    msg_input = Game.new_msg()

            for event in events:
                if event.type == pygame.QUIT:
                    self.RUN = False
                elif event.type == pygame.USEREVENT + 0:
                    pass
                    # print("FPS: ", clock.get_fps())
                elif event.type == pygame.USEREVENT + 1 and self.run_udp:
                    self.sock_udp.sendto(self.player.encode_udp(not direction_x == direction_y == 0), (HOST, PORT_UDP))

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.option()
                    elif event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
                        running = True
                    elif event.key == pygame.K_q:
                        dial_flag = True

                elif event.type == pygame.KEYUP:
                    if event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
                        running = False

            if running:
                rate = self.player.run_rate
            else:
                rate = self.player.walk_rate

            if dial_flag:
                direction_x = 0
                direction_y = 0
            else:
                direction_x = pygame.key.get_pressed()[pygame.K_RIGHT] - \
                              pygame.key.get_pressed()[pygame.K_LEFT]
                direction_y = pygame.key.get_pressed()[pygame.K_DOWN] - \
                              pygame.key.get_pressed()[pygame.K_UP]

            if direction_y == 1:
                self.player.direction = 0
            elif direction_y == -1:
                self.player.direction = 3
            if direction_x == 1:
                self.player.direction = 2
            elif direction_x == -1:
                self.player.direction = 1

            dir_len = math.hypot(direction_x, direction_y)
            dir_len = dir_len if dir_len else 1.0
            # update position
            dx = rate * dt * direction_x / dir_len
            dy = rate * dt * direction_y / dir_len
            dx, dy = map.check_collision(self.player, dx, dy)
            dx, dy = map.check_wall(self.player, dx, dy)

            self.check_obj(map)

            self.screen.fill((0, 0, 0))
            i = 0
            for layer in map.layers:
                map.renderer.render_layer(self.screen, layer)
                if i == map.layer_player:

                    for friend in self.friends.values():
                        if friend.level == self.player.level:
                            if friend.show:
                                friend.move_conductor.play()
                                friend.anim_objs[friend.direction].blit(self.screen, friend.cord(self.player))
                            else:
                                friend.move_conductor.stop()
                                self.screen.blit(friend.standing[friend.direction], friend.cord(self.player))

                    if direction_x or direction_y:
                        self.player.move_conductor.play()
                        self.player.move(dx, dy)
                        self.player.anim_objs[self.player.direction].blit(self.screen, (CEN_X, CEN_Y))
                    else:
                        self.player.move_conductor.stop()
                        self.screen.blit(self.player.standing[self.player.direction], (CEN_X, CEN_Y))
                i += 1
            cam_pos_x, cam_pos_y = self.player.get_pos_cam()
            # map.renderer.set_camera_position(cam_pos_x, cam_pos_y)
            map.renderer.set_camera_position(*self.player.get_pos_cam())

            if dial_flag:
                self.screen.blit(self.dial_frame, (0, 642))
                self.screen.blit(msg_input.get_surface(), (10, 697))

            if self.show_message_frame:
                frame = self.message_frame.get_surface()
                self.screen.blit(frame, (WIDTH * 3 // 4, 0))
            if self.show_glow:
                self.screen.blit(self.icon['glow'], (CEN_X, CEN_Y))

            pygame.display.flip()

    @staticmethod
    def player_init(DB_C: sql.DB) -> Player:
        """
        Статический метод создания игрока.
        :return: Объект игрока
        """
        login = ''
        while len(login) < 6:
            print('Длина логина должна быть не менее 6 символов.')
            login = input('Введите логин: ')
        id = input('Введите ID персонажа: ').lower()
        return Player(login, id, DB_C)

    @staticmethod
    def pygame_init() -> pygame.Surface:
        """
        Статический метод для создания основного окна и инициализации Pygame
        :return: Основное окно
        """
        pygame.init()
        pygame.font.init()
        pygame.display.set_caption('RPG')
        screen_width = WIDTH
        screen_height = HEIGHT
        return pygame.display.set_mode((screen_width, screen_height))

    @staticmethod
    def icon_init() -> dict:
        """
        Статический метод для создания словаря мелких изображений.
        :return: Словарь изображений по названию
        """
        paths = list(filter(os.path.isfile, map(lambda x: 'IMG/Icon/' + x, os.listdir('IMG/Icon'))))
        keys = list(map(lambda x: x[9:-4], paths))
        items = list(zip(keys, list(map(lambda x: pygame.image.load(x), paths))))
        return dict(items)

    @staticmethod
    def settings_init() -> dict:
        """
        Статический метод для создания словаря "флагов".
        :return: Словарь флагов по названию
        """
        return {
            'message_frame': True,
            'glow': False,
        }

    def listen_udp(self):
        """
        Цикл пролушки UDP соединения
        :return: None
        """
        self.run_udp = True
        while self.run_udp and self.RUN:
            try:
                data, _ = self.sock_udp.recvfrom(1024)
            except socket.timeout:
                continue
            except ConnectionResetError:
                break
            Friend.decode_udp(data, self.friends)

    def listen_tcp(self):
        """
        Цикл прослушки TCP соединения
        :return: None
        """
        self.run_tcp = True
        self.sock_tcp.connect((HOST, PORT_TCP))
        self.sock_tcp.send(Player.encode_tcp(1))
        while self.run_tcp and self.RUN:
            try:
                data = self.sock_tcp.recv(1024)
            except socket.timeout:
                continue
            Friend.decode_tcp(data, self.friends, self.message_frame, self.DB_C)

    @staticmethod
    def new_msg() -> pygame_textinput.TextInput:
        """
        Статический метод возвращающий новую строку ввода.
        :return: Новая строка ввода
        """
        return pygame_textinput.TextInput(font_family='Font/UbuntuMono-R.ttf',
                                          font_size=18,
                                          antialias=True,
                                          text_color=(255, 255, 255),
                                          cursor_color=(255, 255, 255),
                                          max_len=100)

    def start(self, udp: bool, tcp: bool):
        """
        Запуск всей игры.
        :param udp: "Флаг" для UDP соединения
        :param tcp: "Флаг" для TCP соединения
        :return: None
        """
        self.RUN = True
        self.run_udp = udp
        self.run_tcp = tcp
        if udp:
            listen_UDP = threading.Thread(target=self.listen_udp, args=())
            listen_UDP.start()
        if tcp:
            listen_TCP = threading.Thread(target=self.listen_tcp, args=())
            listen_TCP.start()

        self.map_run(Map('TilesMap/Inn.tmx'))

        self.RUN = False
        self.sock_tcp.close()
        self.sock_udp.close()
        pygame.font.quit()
        pygame.quit()


# <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>

if __name__ == "__main__":
    Game().start(False, False)
