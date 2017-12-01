"""
Скажу честно, с кодом в go.py и в battlescene.py не очень разобрался.
Предложение по объединению такое: так как все рисование картинок происходит у меня,
то выбор героев и их действий пусть тоже происходит у меня

Взаимодействие можно осуществить таким образом >

<< Получение информации от меня >>
Функция для осуществления выбора перед ходом игрока:
choice(scene)
Возвращает результат выбора игрока в таком формате:
result = {'usagi': {'action': None, 'target': None},
          'healer': {'action': None, 'target': None},
          'neko': {'action': None, 'target': None},
          'snake': {'action': None, 'target': None}
          }
Где 'action' может быть 'attack', 'magic' и что-нибудь еще, типа
атаки огнем, водой, землей и всякое такое
'target' - выбор атакуемого противника

Пока есть только функция move(scene, hero) для визуализации любого типа действий,
в перспективе добавлю следующие типы анимаций:
    vis_dead(scene, hero) - смерть героя или одного из противников
    vis_attack(scene, hero) - обычная физическая атака героя или одного из противников
    vis_magic(scene, hero) - магическая атака героя или одного из противников
    Опять же, в будущем можно будеть отдельные анимации для атаки огнем, водой, землей и всякое такое

<< Получение информации от тебя >>
Если придерживаться исходного описания классов, то я смогу получить всю информацию
из атрибутов классов Monster и Hero, таких как
    self.hp
    self.mp
    self.dead
"""

import pygame
from main import *
from classes import *
import os
import random
#from go import *
#from battlescene import *

#Предлагаю использовать такую функцию, где будет происходить вся движуха
def main_loop():
    # Размер экрана
    SCREEN_WIDTH = 640 #1024
    SCREEN_HEIGHT = 490 #768

    # Всякая ерунда со стартом pygame
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption('RPG Battle')

    # Создание объектов героев и врагов (если они еще не были созданы)
    example = {'name': None,
               'ph_atk': None,
               'mag_atk': {'size': 5,
                           'cost': 2,
                           'type': 'mp'},
               'fr_atk': {'size': 9,
                          'cost': 2,
                          'type': 'mp'},
               'ph_def': 10,
               'mag_def': 11,
               'hp': 50,
               'sp': 30,
               'mp': 60}

    healer = Hero(**example)
    snake = Hero(**example)
    neko = Hero(**example)
    usagi = Hero(**example)
    heros = ({'name': 'healer', 'object': healer},
             {'name': 'snake', 'object': snake},
             {'name': 'neko', 'object': neko},
             {'name': 'usagi', 'object': usagi})

    example = {'name': None,
               'ph_atk': {'size': 3,
                          'cost': 2,
                          'type': 'sp'},
               'mag_atk': {'size': 8,
                           'cost': 2,
                           'type': 'mp'},
               'ph_def': 14,
               'mag_def': 19,
               'hp': 50,
               'sp': 30,
               'mp': 60}

    monster_1 = Monster(**example)
    monster_2 = Monster(**example)
    enemies = (None,
               {'type': 'yellowdragon', 'object': monster_2},
               None,
               {'type': 'reddragon', 'object': monster_1})

    # Случайным образов выберем фон
    lower_bg = os.listdir(path='images/background/lower')
    upper_bg = os.listdir(path='images/background/upper')
    random_lower = 'images/background/lower/' + lower_bg[random.randint(0, len(lower_bg) - 1)]
    random_upper = 'images/background/upper/' + upper_bg[random.randint(0, len(upper_bg) - 1)]

    # Объявляем scene
    scene = BattleScene(screen,
                        random_lower,
                        random_upper,
                        heros, enemies)

    # Отрисовываем первый раз
    scene.render()
    pygame.display.update()

    #Бесконечный цикл, где все будет происходить
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                raise SystemExit('QUIT')

        # Здесь наконец-то начинается сам процесс битвы
        # Даем возможность игроку "походить" и забираем результат
        result = choice(scene)

        # Теперь, в зависимости от результата, можно смоделировать
        # ответную реакцию врагов и все отрисовать
        # Здесь как раз вступает в действие твой код с алгоритмом боя
        # И, используя мои заготовленнные функции vis_dead, vis_attack и т.д.,
        # ты делаешь бой боем

        # Пока это выглядит так
        for hero in scene.heros:
            if result[hero]['action'] == 'attack':
                vis_attack(scene, hero)
            if result[hero]['action'] == 'magic':
                vis_magic(scene, hero)
            if result[hero]['action'] == 'something':
                vis_dead(scene, hero)
            if result[hero]['action'] == 'something else':
                if scene.enemies[result[hero]['target']]:
                    vis_dead(scene, result[hero]['target'])

main_loop()
