import random
# в качестве структур данных я брал словари
atk_def = {'ph_atk': 'ph_def', 'mag_atk': 'mag_def', 'fr_atk': 'mag_def'}  # создано для определения типа защиты при данном типе атаки


class Player:
    def __init__(self, **kwargs):
        # self.login = kwargs['login']
        # self.money = kwargs['money']
        # self.inventory = kwargs['inventory']
        self.heroes = kwargs['heroes']
        # self.x = kwargs['x0']
        # self.y = kwargs['y0']

    # def move_player(self, x, y):
    #     self.x = x
    #     self.y = y

    # def set_money(self, delta_money):
    #     self.money += delta_money

    # def append_inventory(self, item):
    #     if item in self.inventory.keys():
    #         self.inventory[item] += 1
    #     else:
    #         self.inventory += {item: 1}

    def get_alive_heroes(self):
        return [i for i in self.heroes if i.alive is True]


class Hero:
    def __init__(self, **kwargs):
        self.name = kwargs['name']
        self.hp = kwargs['hp']
        self.mp = kwargs['mp']
        self.sp = kwargs['sp']
        self.ph_atk = kwargs['ph_atk']
        self.mag_atk = kwargs['mag_atk']
        self.fr_atk = kwargs['fr_atk']
        self.ph_def = kwargs['ph_def']
        self.mag_def = kwargs['mag_def']
        self.at_list = {'ph_atk': self.ph_atk, 'mag_atk': self.mag_atk, 'fr_atk': self.fr_atk} # ph_atk:{'size':5,'cost':2,'type':'ph'}
        self.df_list = {'ph_def': self.ph_def, 'mag_def': self.mag_def}
        self.alive = True

    def attack_list_filter(self):
        for i in list(self.at_list.items()):  # удаляем из at_list несуществующие типы атак для данного героя
            if i[1] is None:
                self.at_list.pop(i[0])

    def __str__(self):
        return '{}'.format(self.name)

    def get_hp(self):
        return self.hp

    def hp_change(self, impact_type, impact_size):
        self.hp -= (1 - self.df_list[atk_def[impact_type]]) * impact_size
        if self.hp <= 0:
            self.alive = False

    # непосредственно расчет атаки,пока добавлены только два типа атаки
    def attack(self, monster, attack_type):
        if self.at_list[attack_type]['type'] == 'sp' and self.at_list[attack_type]['cost'] <= self.sp:
            self.sp -= self.at_list[attack_type]['cost']
            monster.hp_change(attack_type, self.at_list[attack_type]['size'])
        if self.at_list[attack_type]['type'] == 'mp' and self.at_list[attack_type]['cost'] <= self.mp:
            self.mp -= self.at_list[attack_type]['cost']
            monster.hp_change(attack_type, self.at_list[attack_type]['size'])


class Enemy:
    def __init__(self, **kwargs):
        # self.inventory = kwargs['inventory']
        self.monsters = kwargs['monsters']
        # self.x = kwargs['x0']
        # self.y = kwargs['y0']
        pass

    # def move_enemy(self, x, y):
    #     # self.x = x
    #     # self.y = y

    def get_alive_monsters(self):
        return [i for i in self.monsters if i.alive is True]

    def choose_random_monster(self):
        return random.choice(self.get_alive_monsters())


class Monster:
    def __init__(self, **kwargs):
        self.name = kwargs['name']
        self.hp = kwargs['hp']
        self.mp = kwargs['mp']
        self.sp = kwargs['sp']
        self.ph_atk = kwargs['ph_atk']
        self.mag_atk = kwargs['mag_atk']
        self.ph_def = kwargs['ph_def']
        self.mag_def = kwargs['mag_def']
        self.at_list = {'ph_atk': self.ph_atk, 'mag_atk': self.mag_atk}
        self.df_list = {'ph_def': self.ph_def, 'mag_def': self.mag_def}
        self.alive = True

    def __str__(self):
        return '{}'.format(self.name)

    def get_hp(self):
        return self.hp

    def choose_random_attack(self):
        i = random.choice(self.at_list.values())
        while i is None:
            i = random.choice(self.at_list.values())
        return i

    def hp_change(self, impact_type, impact_size):
        self.hp -= (1 - self.df_list[atk_def[impact_type]] * 0.01) * impact_size
        if self.hp <= 0:
            self.alive = False

    def attack(self, heroes):
        hero = sorted(heroes, key=lambda hro: hro.get_hp())[0]
        attack_type = self.choose_random_attack()
        if self.at_list[attack_type]['type'] == 'sp' and self.at_list[attack_type]['cost'] >= self.sp:
            self.sp -= self.at_list[attack_type]['cost']
            hero.hp_change(attack_type, self.at_list[attack_type]['size'])
        if self.at_list[attack_type]['type'] == 'mp' and self.at_list[attack_type]['cost'] >= self.mp:
            self.mp -= self.at_list[attack_type]['cost']
            hero.hp_change(attack_type, self.at_list[attack_type]['size'])











