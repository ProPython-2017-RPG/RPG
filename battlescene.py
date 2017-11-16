
import pygame
import time

# Структура меню:основная часть кода здесь это меню: выбор игроком героя ,затем выбор атаки из тех которые
# у этого героя есть, и выбор атакуемого монстра противника


class Action:           # это архитектура из той статьи что я скидывал в вк
    def __init__(self):
        self.next = self

    def SwitchToScene(self, next_scene):
        self.next = next_scene

    def Terminate(self):
        self.SwitchToScene(None)


class BattleScene(Action):
    def __init__(self, player, enemy, first_step):
        self.player = player
        self.enemy = enemy
        self.step = first_step  # ход игрок или комп
        self.hero_pos = 0  # индекс выбранного героя из живых
        self.attack_pos = 0  # индекс выбранного типа атаки из существующих
        self.enemy_pos = 0 # индекс выбранного противника
        self.func_pos = 0
        self.pressed = False
        self.menu_res = {'hero': None, 'atk': None, 'monster': None}
        self.flag = None  # указавает текущий пункт меню
        self.done = False  # True если выбор в меню окончен(клавиша d) и затем переход к расчету битвы
        Action.__init__(self)

    def hero_choice(self, events):  # выбор атакующего героя
        choice = self.player.get_alive_heroes()[self.hero_pos]
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_DOWN and self.hero_pos < len(self.player.heroes) - 1:
                self.hero_pos += 1
                choice = self.player.heroes[self.hero_pos]
            if event.type == pygame.KEYDOWN and event.key == pygame.K_UP and abs(self.hero_pos) < len(self.player.heroes):
                self.hero_pos -= 1
                choice = self.player.heroes[self.hero_pos]
        choice.attack_list_filter()
        return choice

    def attack_choice(self, events, hero):  # выбор типа атаки
        choice = list(hero.at_list.keys())[self.attack_pos]
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_DOWN and self.attack_pos < len(list(hero.at_list.keys())) - 1:
                self.attack_pos += 1
                choice = list(hero.at_list.keys())[self.attack_pos]

            if event.type == pygame.KEYDOWN and event.key == pygame.K_UP and abs(self.attack_pos) < len(list(hero.at_list.keys())):
                self.attack_pos -= 1
                choice = list(hero.at_list.keys())[self.attack_pos]
        return choice

    def monster_choice(self, events):  # выбор монстра для атаки

        monsters = self.enemy.get_alive_monsters()
        choice = monsters[self.enemy_pos]
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_DOWN and self.enemy_pos < len(monsters) - 1:
                self.enemy_pos += 1
                choice = monsters[self.enemy_pos]
            if event.type == pygame.KEYDOWN and event.key == pygame.K_UP and abs(self.enemy_pos) < len(monsters):
                self.enemy_pos -= 1
                choice = monsters[self.enemy_pos]
        return choice

    def menu(self, events, pressed):
        if self.func_pos == 0 and self.flag != 'hero':
            self.menu_res['hero'] = self.hero_choice(events)

        if (pressed[pygame.K_LEFT] and self.func_pos == 0 and self.pressed is False ) or (self.flag == 'atk'
                 and pressed[pygame.K_LEFT] != 1 and pressed[pygame.K_RIGHT] != 1 and pressed[pygame.K_d] != 1):
            self.func_pos = 1
            self.pressed = True
            if self.flag == 'atk':
                self.pressed = False
            self.flag = 'atk'
            self.menu_res['atk'] = self.attack_choice(events, self.menu_res['hero'])

        if (pressed[pygame.K_LEFT] and self.func_pos == 1 and self.pressed is False ) \
                or (self.flag == 'mns' and pressed[pygame.K_RIGHT] != 1 and pressed[pygame.K_d] != 1):
            self.func_pos = 2
            self.pressed = True
            if self.flag == 'mns':
                self.pressed = False
            self.flag = 'mns'
            self.menu_res['monster'] = self.monster_choice(events)
        if (pressed[pygame.K_RIGHT] and self.func_pos == 2 and self.pressed is False ) or (self.flag == 'atk'
                and pressed[pygame.K_LEFT] is False and pressed[pygame.K_RIGHT] != 1 and pressed[pygame.K_d] != 1):
            self.func_pos = 1
            self.pressed = True
            if self.flag == 'atk':
                self.pressed = False
            self.flag = 'atk'
            self.menu_res['atk'] = self.attack_choice(events, self.menu_res['hero'])

        if (pressed[pygame.K_RIGHT] and self.func_pos == 1 and self.pressed is False) \
                or (self.flag == 'hero' and pressed[pygame.K_LEFT] != 1 and pressed[pygame.K_d] != 1):
            self.func_pos = 0
            self.pressed = True
            if self.flag == 'hero':
                self.pressed = False
            self.flag = 'hero'
            self.menu_res['hero'] = self.hero_choice(events)

        if pressed[pygame.K_d]:
            if None not in self.menu_res.values() and self.menu_res['atk'] in self.menu_res['hero'].at_list:
                self.done = True

    def process_input(self, events, pressed):
        # логика меню
        for event in events:
            if event.type != pygame.KEYDOWN:
                events.remove(event)
        self.menu(events, pressed)
        print('{}  {}  {}'.format(self.menu_res['hero'], self.menu_res['atk'], self.menu_res['monster']))

    def update(self, events):  # атака

        if self.step == 'player' and self.done is True:
            self.menu_res['hero'].attack(self.menu_res['monster'], self.menu_res['atk'])
            print('hero ', self.menu_res['hero'])
            print('hero attack ', self.menu_res['atk'])
            print('hero sp ', self.menu_res['hero'].sp)
            print('hero mp ', self.menu_res['hero'].mp)
            print('monster ', self.menu_res['monster'])
            print('monster hp ', self.menu_res['monster'].hp)
            print('monster sp ', self.menu_res['monster'].sp)
            print('monster mp ', self.menu_res['monster'].mp)

            time.sleep(3)  # где то здесь должна быть анимация
            self.next = None
            #self.menu_res = {'hero': None, 'atk': None, 'monster': None}
        # if self.step == 'enemy':
        #     monster = self.enemy.choose_random_monster()    # ход компа
        #     monster.attack(self.player.get_alive_heroes())

    def render(self, screen):
        screen.fill((100, 100, 100))
        i = 0
        for hero in self.player.get_alive_heroes():
            font = pygame.font.SysFont("comicsansms", 40)
            text = font.render(hero.name, True, (0, 0, 0))
            if hero == self.menu_res['hero']:
                text = font.render(hero.name, True, (0, 255, 0))
            screen.blit(text, (450 - text.get_width() // 2, 600 + i - text.get_height() // 2))
            i += 30
        j = 0
        for attack in self.menu_res['hero'].at_list.items():
            font = pygame.font.SysFont("comicsansms", 40)
            text = font.render(attack[0]+'  '+str(attack[1]['size']), True, (0, 0, 0))
            if attack[0] == self.menu_res['atk']:
                text = font.render(attack[0]+'  '+str(attack[1]['size']), True, (0, 0, 255))
            screen.blit(text, (300 - text.get_width() // 2, 600 + j - text.get_height() // 2))
            j += 30
        k = 0
        for monster in self.enemy.get_alive_monsters():
            font = pygame.font.SysFont("comicsansms", 40)
            text = font.render(monster.name+' '+str(monster.hp), True, (0, 0, 0))
            if monster == self.menu_res['monster']:
                text = font.render(monster.name+' '+str(monster.hp), True, (255, 0, 0))
            screen.blit(text, (150 - text.get_width() // 2, 600 + k - text.get_height() // 2))
            k += 30

        # здесь идет отрисовка сцены с соотв менюхой и персонажами




