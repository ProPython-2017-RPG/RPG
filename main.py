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


class BattleEnemy:
    def __init__(self, img, position=(16, 16), width=32, height=32, num=3, lines=1):
        self.img_width = width
        self.img_height = height

        rects = []
        for i in range(lines):
            for n in range(num):
                rects.append((n * width, i * height, width, height))

        all_images = pyganim.getImagesFromSpriteSheet(img, rects=rects)
        frames = list(zip(all_images, [100] * len(all_images)))
        self.anim_objs = pyganim.PygAnimation(frames)

        self.move_conductor = pyganim.PygConductor(self.anim_objs)

        self.pos_x, self.pos_y = position
        self.pos_x -= all_images[0].get_width() / 2
        self.pos_y -= all_images[0].get_height() / 2


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
        # Actions menu
        self.buttons_state = 'hero' # 'hero', 'action', 'target'
        self.buttons = ('Attack', 'Magic', 'Suicide', 'Kill\'um all')
        # Cursor position
        self.cursor_hero = 0
        self.cursor_action = 0
        self.cursor_enemies = 0

        # Heros
        self.heros = {'usagi': None, 'healer': None, 'neko': None, 'snake': None}
        self.hero_states = {'usagi': 'wait',
                            'healer': 'wait',
                            'neko': 'wait',
                            'snake': 'wait'}
        # Turn was made or not
        self.hero_turn = {'usagi': False,
                           'healer': False,
                           'neko': False,
                           'snake': False}

        # Create heros
        for hero in heros:
            if hero:
                if hero['name'] == 'usagi':
                    self.heros['usagi'] = BattlePlayer('images/heros/Usagi.png',
                                                       (screen.get_size()[0] - 190,
                                                        screen.get_size()[1] / 2),
                                                       32, 48, 4, 0)
                elif hero['name'] == 'healer':
                    self.heros['healer'] = BattlePlayer('images/heros/Healer.png',
                                                        (screen.get_size()[0] - 160,
                                                         screen.get_size()[1] / 2 + 25),
                                                        32, 32, 3, 1)
                elif hero['name'] == 'neko':
                    self.heros['neko'] = BattlePlayer('images/heros/Neko.png',
                                                      (screen.get_size()[0] - 130,
                                                       screen.get_size()[1] / 2 + 50),
                                                      32, 48, 4, 0)
                elif hero['name'] == 'snake':
                    self.heros['snake'] = BattlePlayer('images/heros/Snake.png',
                                                       (screen.get_size()[0] - 90,
                                                        screen.get_size()[1] / 2 + 85),
                                                       48, 48, 4, 0)

        # Create enemies
        self.enemies = {1: None,
                        2: None,
                        3: None,
                        4: None}
        DEFAULT_POS = {1: (200, screen.get_size()[1] / 2 - 20),
                       2: (170, screen.get_size()[1] / 2 + 5),
                       3: (140, screen.get_size()[1] / 2 + 30),
                       4: (110, screen.get_size()[1] / 2 + 55)}
        ENEMY_IMG = {'reddragon': 'images/enemies/reddragonfly.png',
                     'yellowdragon': 'images/enemies/yellowdragonfly.png'}
        if len(enemies) <= 4:
            i = 0
            for enemy in enemies:
                i += 1
                if enemy:
                    self.enemies[i] = BattleEnemy(ENEMY_IMG[enemy['type']],
                                                  DEFAULT_POS[i],
                                                  200, 160, 4, 4)
                    self.enemies[i].move_conductor.play()


        # Objects for heros and enemies (for HP, 'alive', ...)
        self.heros_obj = {'usagi': None, 'healer': None, 'neko': None, 'snake': None}
        self.start_heros_hp = {'usagi': None, 'healer': None, 'neko': None, 'snake': None}
        self.enemies_obj = {1: None, 2: None, 3: None, 4: None}
        for hero in heros:
            if hero:
                self.heros_obj[hero['name']] = hero['object']
                self.start_heros_hp[hero['name']] = hero['object'].hp
        i = 0
        for enemy in enemies:
            i += 1
            if enemy:
                self.enemies_obj[i] = enemy['object']

        # Visual effects
        self.death_act = False
        self.death_animation = BattleEnemy('images/death.png', (100, 100), 96, 96, 12, 1)

        self.attack_act_hero = False
        self.attack_animation_hero = BattleEnemy('images/fireball.png', (100, 100), 64, 64, 8, 1)

        self.attack_act_enemy = False
        self.attack_animation_enemy = BattleEnemy('images/fireball_right.png', (100, 100), 64, 64, 8, 1)

        self.magic_act = False
        self.magic_animation = BattleEnemy('images/magic.png', (100, 100), 128, 128, 8, 7)

        # Pictures
        self.img_l = pygame.image.load(self.img_lower)
        self.img_l = pygame.transform.scale(self.img_l, self.screen.get_size())
        self.img_u = pygame.image.load(self.img_upper)
        self.img_u = pygame.transform.scale(self.img_u, self.screen.get_size())
        self.img_menu = pygame.image.load('images/menu_1.png')
        self.img_menu = pygame.transform.scale(self.img_menu, (self.screen.get_size()[0], 130))
        self.img_cur = pygame.image.load('images/right_small.png')
        self.img_cur = pygame.transform.scale(self.img_cur, (35, 35))
        self.img_cur_left = pygame.image.load('images/left_small.png')
        self.img_cur_left = pygame.transform.scale(self.img_cur_left, (35, 35))

        self.background = pygame.Surface(self.screen.get_size())


    def render(self):
        self.background.blit(self.img_l, (0, 0))
        self.background.blit(self.img_u, (0, 0))
        self.background.blit(self.img_menu, (0, self.screen.get_size()[1] - 130))

        # Cursor
        if self.buttons_state == 'hero' and self.cursor_hero != 4: # != 4 - Except done button
            self.background.blit(self.img_cur, (self.screen.get_size()[0] - 290,
                                                self.screen.get_size()[1] - 125 + self.cursor_hero * 25))

        if self.buttons_state == 'hero' and self.cursor_hero == 4: # Done button
            self.background.blit(self.img_cur, (self.screen.get_size()[0] - 105, 25))

        elif self.buttons_state == 'action':
            self.background.blit(self.img_cur, (10,
                                                self.screen.get_size()[1] - 125 + self.cursor_action * 25))

        elif self.buttons_state == 'target':
            # ~
            value = 0
            for enemy in self.enemies:
                if self.enemies[enemy]:
                    value += 1
                    if value == (self.cursor_enemies + 1):
                        value = enemy
                        break

            self.background.blit(self.img_cur_left, (self.enemies[value].get_pos()[0] + 200,
                                                     self.enemies[value].get_pos()[1] + 75))

        self.screen.blit(self.background, (0, 0))

        font = pygame.font.SysFont('Lucida Console', 25)
        i = 0
        for hero in self.heros:
            if self.hero_turn[hero]:
                color = (210, 105, 30)
            else:
                color = (0, 0, 0)
            # Menu (heros)
            # Hero names
            text_surface = font.render(hero.capitalize(),True, color, None)
            self.screen.blit(text_surface, (self.screen.get_size()[0] - 250,
                                            self.screen.get_size()[1] - 118 + 25 * i))
            # Hero health
            if self.heros[hero]:
                text_surface = font.render('{}/{}'.format(self.heros_obj[hero].hp, self.start_heros_hp[hero]),
                                                          True,
                                                          (0, 0, 0),
                                                          None)
                self.screen.blit(text_surface, (self.screen.get_size()[0] - 130,
                                                self.screen.get_size()[1] - 118 + 25 * i))
            i += 1

            if self.heros[hero]:
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

        # Done button
        done_button_surface = pygame.image.load('images/done_button.png')
        self.screen.blit(done_button_surface, (self.screen.get_size()[0] - 64, 20))

        # Enemies
        for enemy in self.enemies:
            if self.enemies[enemy]:
                self.enemies[enemy].anim_objs.blit(self.screen, self.enemies[enemy].get_pos())

        # Death animation
        if self.death_act:
            self.death_animation.move_conductor.play()
            self.death_animation.anim_objs.blit(self.screen, self.death_animation.get_pos())
        else:
            self.death_animation.move_conductor.stop()

        # Attack animation
        if self.attack_act_hero:
            self.attack_animation_hero.move_conductor.play()
            self.attack_animation_hero.anim_objs.blit(self.screen,
                                                      self.attack_animation_hero.get_pos())
        else:
            self.attack_animation_hero.move_conductor.stop()

        if self.attack_act_enemy:
            self.attack_animation_enemy.move_conductor.play()
            self.attack_animation_enemy.anim_objs.blit(self.screen,
                                                       self.attack_animation_enemy.get_pos())
        else:
            self.attack_animation_enemy.move_conductor.stop()

        # Magic animation
        if self.magic_act:
            self.magic_animation.move_conductor.play()
            self.magic_animation.anim_objs.blit(self.screen, self.magic_animation.get_pos())
        else:
            self.magic_animation.move_conductor.stop()


def simple_move(scene, hero):
    timer = pygame.time.Clock()

    if hero in ('usagi', 'healer', 'neko', 'snake'):
        scene.hero_states[hero] = 'move'
        for step in range(25):
            scene.heros[hero].move(-2, 0)
            scene.render()
            pygame.display.update()
            timer.tick(60)

        scene.hero_states[hero] = 'wait'
        scene.render()
        pygame.display.update()
        for step in range(30):  # Simple delay
            scene.render()
            pygame.display.update()
            timer.tick(60)

        scene.hero_states[hero] = 'move'
        for step in range(25):
            scene.heros[hero].move(2, 0)
            scene.render()
            pygame.display.update()
            timer.tick(60)

        scene.hero_states[hero] = 'wait'
        scene.render()
        pygame.display.update()

    else:
        for step in range(25):
            scene.enemies[hero].move(2, 0)
            scene.render()
            pygame.display.update()
            timer.tick(60)

        for step in range(30):  # Simple delay
            scene.render()
            pygame.display.update()
            timer.tick(60)

        for step in range(25):
            scene.enemies[hero].move(-2, 0)
            scene.render()
            pygame.display.update()
            timer.tick(60)


def move(scene, hero, direction):
    timer = pygame.time.Clock()

    if hero in ('usagi', 'healer', 'neko', 'snake'):
        if direction == 'left':
            scene.hero_states[hero] = 'move'
            for step in range(25):
                scene.heros[hero].move(-2, 0)
                scene.render()
                pygame.display.update()
                timer.tick(60)
            scene.hero_states[hero] = 'wait'
            scene.render()
            pygame.display.update()

        if direction == 'right':
            scene.hero_states[hero] = 'move'
            for step in range(25):
                scene.heros[hero].move(2, 0)
                scene.render()
                pygame.display.update()
                timer.tick(60)
            scene.hero_states[hero] = 'wait'
            scene.render()
            pygame.display.update()

    elif hero == 'attack_animation':
        if direction == 'left':
            for step in range(40):
                scene.attack_animation_enemy.move(-2, 0)
                scene.attack_animation_hero.move(-2, 0)
                scene.render()
                pygame.display.update()
                timer.tick(60)

        if direction == 'right':
            for step in range(40):
                scene.attack_animation_enemy.move(2, 0)
                scene.attack_animation_hero.move(2, 0)
                scene.render()
                pygame.display.update()
                timer.tick(60)

    elif hero == 'magic_animation':
        if direction == 'left':
            for step in range(40):
                scene.magic_animation.move(-2, 0)
                scene.render()
                pygame.display.update()
                timer.tick(60)

        if direction == 'right':
            for step in range(40):
                scene.magic_animation.move(2, 0)
                scene.render()
                pygame.display.update()
                timer.tick(60)

    else:
        if direction == 'left':
            for step in range(40):
                scene.enemies[hero].move(-2, 0)
                scene.render()
                pygame.display.update()
                timer.tick(60)

        if direction == 'right':
            for step in range(40):
                scene.enemies[hero].move(2, 0)
                scene.render()
                pygame.display.update()
                timer.tick(60)


def vis_attack(scene, hero):
    if hero in ('usagi', 'healer', 'neko', 'snake'):
        move(scene, hero, 'left')

        scene.attack_animation_hero.pos_x = scene.heros[hero].get_pos()[0] - 40
        scene.attack_animation_hero.pos_y = scene.heros[hero].get_pos()[1] - 5
        scene.attack_act_hero = True
        move(scene, 'attack_animation', 'left')
        scene.attack_act_hero = False

        move(scene, hero, 'right')

    else:
        move(scene, hero, 'right')

        scene.attack_animation_enemy.pos_x = scene.enemies[hero].get_pos()[0] + 150
        scene.attack_animation_enemy.pos_y = scene.enemies[hero].get_pos()[1] + 60
        scene.attack_act_enemy = True
        move(scene, 'attack_animation', 'right')
        scene.attack_act_enemy = False

        move(scene, hero, 'left')

def vis_magic(scene, hero):
    if hero in ('usagi', 'healer', 'neko', 'snake'):
        move(scene, hero, 'left')

        scene.magic_animation.pos_x = scene.heros[hero].get_pos()[0] - 70
        scene.magic_animation.pos_y = scene.heros[hero].get_pos()[1] - 45
        scene.magic_act = True
        move(scene, 'magic_animation', 'left')
        scene.magic_act = False

        move(scene, hero, 'right')

    else:
        move(scene, hero, 'right')

        scene.magic_animation.pos_x = scene.enemies[hero].get_pos()[0] + 140
        scene.magic_animation.pos_y = scene.enemies[hero].get_pos()[1] + 20
        scene.magic_act = True
        move(scene, 'magic_animation', 'right')
        scene.magic_act = False

        move(scene, hero, 'left')


def vis_dead(scene, hero):
    timer = pygame.time.Clock()

    if hero in ('usagi', 'healer', 'neko', 'snake'):
        scene.death_animation.pos_x = scene.heros[hero].get_pos()[0] - 32
        scene.death_animation.pos_y = scene.heros[hero].get_pos()[1] - 32

        scene.death_act = True
        for step in range(8):  # Simple delay
            scene.render()
            pygame.display.update()
            timer.tick(60)
        scene.heros[hero] = None
        for step in range(20):  # Simple delay
            scene.render()
            pygame.display.update()
            timer.tick(60)
        scene.death_act = False
        scene.render()
        pygame.display.update()

    else:
        scene.death_animation.pos_x = scene.enemies[hero].get_pos()[0] + 70
        scene.death_animation.pos_y = scene.enemies[hero].get_pos()[1] + 40

        scene.death_act = True
        for step in range(8):  # Simple delay
            scene.render()
            pygame.display.update()
            timer.tick(60)
        scene.enemies[hero] = None
        for step in range(20):  # Simple delay
            scene.render()
            pygame.display.update()
            timer.tick(60)
        scene.death_act = False
        scene.render()
        pygame.display.update()


def choice(scene):

    result = {'usagi': {'action': None, 'target': None},
              'healer': {'action': None, 'target': None},
              'neko': {'action': None, 'target': None},
              'snake': {'action': None, 'target': None}
              }
    names = ['usagi', 'healer', 'neko', 'snake']

    # Check alive heroes
    for hero in scene.heros:
        if scene.heros[hero]:
            scene.hero_turn[hero] = False
        else:
            scene.hero_turn[hero] = True

    # Check alive enemies
    num_enemies = 0
    for enemy in scene.enemies:
        if scene.enemies[enemy]:
            num_enemies += 1


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
                            scene.cursor_hero = 4
                    elif scene.buttons_state == 'action':
                        scene.cursor_action -= 1
                        if scene.cursor_action == -1:
                            scene.cursor_action = 3
                    elif scene.buttons_state == 'target':
                        scene.cursor_enemies -= 1
                        if scene.cursor_enemies == -1:
                            scene.cursor_enemies = num_enemies - 1

                if event.key == pygame.K_DOWN:
                    if scene.buttons_state == 'hero':
                        scene.cursor_hero += 1
                        if scene.cursor_hero == 5:
                            scene.cursor_hero = 0
                    elif scene.buttons_state == 'action':
                        scene.cursor_action += 1
                        if scene.cursor_action == 4:
                            scene.cursor_action = 0
                    elif scene.buttons_state == 'target':
                        scene.cursor_enemies += 1
                        if scene.cursor_enemies == num_enemies:
                            scene.cursor_enemies = 0

                if event.key == pygame.K_RETURN:
                    if scene.cursor_hero == 4:
                        done = True
                    elif not scene.hero_turn[names[scene.cursor_hero]]: # Hasn't made his turn yet
                        if scene.buttons_state == 'hero':
                            scene.buttons_state = 'action'
                            scene.cursor_action = 0

                        elif scene.buttons_state == 'action':
                            if scene.cursor_action == 0:
                                result[names[scene.cursor_hero]]['action'] = 'attack'
                            if scene.cursor_action == 1:
                                result[names[scene.cursor_hero]]['action'] = 'magic'
                            if scene.cursor_action == 2:
                                result[names[scene.cursor_hero]]['action'] = 'something'
                            if scene.cursor_action == 3:
                                result[names[scene.cursor_hero]]['action'] = 'something else'
                            scene.buttons_state = 'target'
                            scene.cursor_enemies = 0

                        elif scene.buttons_state == 'target':
                            value = 0
                            for enemy in scene.enemies:
                                if scene.enemies[enemy]:
                                    value += 1
                                    if value == (scene.cursor_enemies + 1):
                                        value = enemy
                                        break
                            result[names[scene.cursor_hero]]['target'] = value
                            scene.buttons_state = 'hero'
                            scene.hero_turn[names[scene.cursor_hero]] = True

                if event.key == pygame.K_RIGHT:
                    if scene.buttons_state == 'action':
                        scene.buttons_state = 'hero'
                    if scene.buttons_state == 'target':
                        scene.buttons_state = 'action'


        scene.render()
        pygame.display.update()
    return result
