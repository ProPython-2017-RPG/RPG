
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
        self.next = self
        self.player = player
        self.enemy = enemy
        self.step = first_step  # ход игрок или комп
        self.hero_pos = 0  # индекс выбранного героя из живых
        self.attack_pos = 0  # индекс выбранного типа атаки из существующих
        self.enemy_pos = 0 # индекс выбранного противника
        self.func_pos = 0
        self.menu_res = [None, None, None]
        self.pressed = False
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
        return choice

    def attack_choice(self, events, hero):  # выбор типа атаки
        hero.attack_list_filter()
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
            self.menu_res[0] = self.hero_choice(events)
        for event in events:
            if (event.type == pygame.KEYDOWN and event.key == pygame.K_LEFT and self.func_pos == 0 and self.pressed is False) \
                 or (self.flag == 'atk' and event.key != pygame.K_LEFT and event.key != pygame.K_RIGHT and event.key != pygame.K_d):
                self.func_pos = 1
                self.pressed = True
                if self.flag == 'atk':
                    self.pressed = False
                self.flag = 'atk'
                self.menu_res[1] = self.attack_choice(events, self.menu_res[0])
                break
            if (event.type == pygame.KEYDOWN and event.key == pygame.K_LEFT and self.func_pos == 1 and self.pressed is False) \
                    or (self.flag == 'mns' and event.key != pygame.K_RIGHT and event.key != pygame.K_d ):
                self.func_pos = 2
                self.pressed = True
                if self.flag == 'mns':
                    self.pressed = False
                self.flag = 'mns'
                self.menu_res[2] = self.monster_choice(events)
                break
            if (event.type == pygame.KEYDOWN and event.key == pygame.K_RIGHT and self.func_pos == 2 and self.pressed is False) \
                    or (self.flag == 'atk' and event.key != pygame.K_LEFT and event.key != pygame.K_RIGHT and event.key != pygame.K_d):
                self.func_pos = 1
                self.pressed = True
                if self.flag == 'atk':
                    self.pressed = False
                self.flag = 'atk'
                self.menu_res[1] = self.attack_choice(events, self.menu_res[0])
                break
            if (event.type == pygame.KEYDOWN and event.key == pygame.K_RIGHT and self.func_pos == 1 and self.pressed is False) \
                    or (self.flag == 'hero' and event.key != pygame.K_LEFT and event.key != pygame.K_d):
                self.func_pos = 0
                self.pressed = True
                if self.flag == 'hero':
                    self.pressed = False
                self.flag = 'hero'
                self.menu_res[0] = self.hero_choice(events)
                break

            if event.type == pygame.KEYDOWN and event.key == pygame.K_d:
                if None not in self.menu_res and self.flag != 'hero':
                    self.done = True
                    break
        self.pressed = False

    def process_input(self, events, pressed):
        # логика меню
        for event in events:
            if event.type != pygame.KEYDOWN:
                events.remove(event)
        self.menu(events, pressed)
        print(self.menu_res,self.attack_pos)

    def update(self, events):  # атака

        if self.step == 'player' and self.done is True:
            self.player.get_alive_heroes()[self.hero_pos].attack(self.enemy.monsters[self.enemy_pos], self.menu_res[1])
            print('hero ', self.menu_res[0])
            print('hero attack ', self.menu_res[1])
            print('hero sp ', self.menu_res[0].sp)
            print('hero mp ', self.menu_res[0].mp)
            print('monster ', self.menu_res[2])
            print('monster hp ', self.menu_res[2].hp)
            print('monster sp ', self.menu_res[2].sp)
            print('monster mp ', self.menu_res[2].mp)

            time.sleep(5)  # где то здесь должна быть анимация

            self.next = None
        # if self.step == 'enemy':
        #     monster = self.enemy.choose_random_monster()    # ход компа
        #     monster.attack(self.player.get_alive_heroes())
            return

    def render(self, screen):
        screen.fill((0, 0, 255))  # здесь идет отрисовка сцены с соотв менюхой и персонажами




