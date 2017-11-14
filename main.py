import pygame
from pygame import *
import pyganim


class BattlePlayer:
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


class BattleScene:
    def __init__(self, screen, img_lower, img_upper, heros = (None, ), enemies = (None, )):
        # Background pictures
        self.img_lower = img_lower
        self.img_upper = img_upper
        self.screen = screen
        # Actions memu
        self.buttons_state = 'hero' # 'hero', 'action', 'target'
        self.buttons = ('Attack', 'Magic', 'Something', 'Something else')
        # Cursor position
        self.cursor_hero = 0
        self.cursor_action = 0

        self.heros = {'usagi': None, 'healer': None, 'neko': None, 'snake': None}
        self.hero_states = {'usagi': 'wait',
                            'healer': 'wait',
                            'neko': 'wait',
                            'snake': 'wait'}
        for hero in heros:
            if hero == 'usagi':
                self.heros['usagi'] = BattlePlayer('images/heros/Usagi.png',
                                                   (screen.get_size()[0] - 190,
                                                    screen.get_size()[1] / 2),
                                                   32, 48, 4, 0)
            elif hero == 'healer':
                self.heros['healer'] = BattlePlayer('images/heros/Healer.png',
                                                    (screen.get_size()[0] - 160,
                                                     screen.get_size()[1] / 2 + 25),
                                                    32, 32, 3, 1)
            elif hero == 'neko':
                self.heros['neko'] = BattlePlayer('images/heros/Neko.png',
                                                  (screen.get_size()[0] - 130,
                                                   screen.get_size()[1] / 2 + 50),
                                                  32, 48, 4, 0)
            elif hero == 'snake':
                self.heros['snake'] = BattlePlayer('images/heros/Snake.png',
                                                   (screen.get_size()[0] - 90,
                                                    screen.get_size()[1] / 2 + 85),
                                                   48, 48, 4, 0)

        # Pictures
        self.img_l = pygame.image.load(self.img_lower)
        self.img_l = pygame.transform.scale(self.img_l, self.screen.get_size())
        self.img_u = pygame.image.load(self.img_upper)
        self.img_u = pygame.transform.scale(self.img_u, self.screen.get_size())
        self.img_menu = pygame.image.load('images/menu_1.png')
        self.img_menu = pygame.transform.scale(self.img_menu, (self.screen.get_size()[0], 130))
        self.img_cur = pygame.image.load('images/play.png')
        self.img_cur = pygame.transform.scale(self.img_cur, (20, 20))

        self.background = pygame.Surface(self.screen.get_size())


    def render(self):
        self.background.blit(self.img_l, (0, 0))
        self.background.blit(self.img_u, (0, 0))
        self.background.blit(self.img_menu, (0, self.screen.get_size()[1] - 130))

        # Cursor
        if self.buttons_state == 'hero':
            self.background.blit(self.img_cur, (self.screen.get_size()[0] - 275,
                                                self.screen.get_size()[1] - 115 + self.cursor_hero * 25))
        elif self.buttons_state == 'action':
            self.background.blit(self.img_cur, (25,
                                                self.screen.get_size()[1] - 115 + self.cursor_action * 25))

        self.screen.blit(self.background, (0, 0))

        font = pygame.font.SysFont('Lucida Console', 25)
        i = 0
        for hero in self.heros:
            if self.heros[hero]:
                # Menu (heros)
                text_surface = font.render(hero.capitalize(),True, (0, 0, 0), None)
                self.screen.blit(text_surface, (self.screen.get_size()[0] - 250,
                                                self.screen.get_size()[1] - 118 + 25 * i))
                text_surface = font.render('100/100', True, (0, 0, 0), None)
                self.screen.blit(text_surface, (self.screen.get_size()[0] - 130,
                                                self.screen.get_size()[1] - 118 + 25 * i))
                i += 1

                if self.hero_states[hero] == 'wait':
                    self.heros[hero].move_conductor.stop()
                    self.screen.blit(self.heros[hero].standing['left'],
                                     self.heros[hero].get_pos())

                elif self.hero_states[hero] == 'move':
                    self.heros[hero].move_conductor.play()
                    self.heros[hero].anim_objs['left'].blit(self.screen, self.heros[hero].get_pos())

        # Menu
        i = 0
        if self.buttons_state == 'action':
            for button in self.buttons:
                text_surface = font.render(button, True, (0, 0, 0), None)
                self.screen.blit(text_surface, (50, self.screen.get_size()[1] - 118 + 25 * i))
                i += 1


def move(scene, hero):
    timer = pygame.time.Clock()

    scene.hero_states[hero] = 'move'
    for step in range(10):
        scene.heros[hero].move(-5, 0)
        scene.render()
        pygame.display.update()
        timer.tick(60)

    scene.hero_states[hero] = 'wait'
    scene.render()
    pygame.display.update()
    timer.tick(2)

    scene.hero_states[hero] = 'move'
    for step in range(10):
        scene.heros[hero].move(5, 0)
        scene.render()
        pygame.display.update()
        timer.tick(60)

    scene.hero_states[hero] = 'wait'
    scene.render()
    pygame.display.update()


def choice(scene):
    result = {'usagi': {'action': None, 'target': None},
               'healer': {'action': None, 'target': None},
               'neko': {'action': None, 'target': None},
               'snake': {'action': None, 'target': None}
               }
    names = ['usagi', 'healer', 'neko', 'snake']

    done = False
    while not done:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                raise SystemExit('QUIT')
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    if scene.buttons_state == 'hero':
                        scene.cursor_hero -= 1
                        if scene.cursor_hero == -1:
                            scene.cursor_hero = 3
                    elif scene.buttons_state == 'action':
                        scene.cursor_action -= 1
                        if scene.cursor_action == -1:
                            scene.cursor_action = 3

                if event.key == pygame.K_DOWN:
                    if scene.buttons_state == 'hero':
                        scene.cursor_hero += 1
                        if scene.cursor_hero == 4:
                            scene.cursor_hero = 0
                    elif scene.buttons_state == 'action':
                        scene.cursor_action += 1
                        if scene.cursor_action == 4:
                            scene.cursor_action = 0

                if event.key == pygame.K_RETURN:
                    if scene.heros[names[scene.cursor_hero]]:
                        if scene.buttons_state == 'hero':
                            scene.buttons_state = 'action'
                            scene.cursor_action = 0
                        elif scene.buttons_state == 'action':
                            if scene.cursor_action == 0:
                                done = True
                                result[names[scene.cursor_hero]]['action'] = 'attack'
                            scene.buttons_state = 'hero'

        scene.render()
        pygame.display.update()

    return result


def test_main():
    SCREEN_WIDTH = 640
    SCREEN_HEIGHT = 490

    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption('RPG Battle')

    scene = BattleScene(screen, 'images/background/lower/Castle.png',
                        'images/background/upper/Castle1.png',
                        ('healer', 'snake', 'neko', 'usagi'))
    scene.render()
    pygame.display.update()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                raise SystemExit('QUIT')
        result = choice(scene)
        for hero in scene.heros:
            if result[hero]['action'] == 'attack':
                move(scene, hero)


test_main()

