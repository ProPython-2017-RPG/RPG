
from classes import *
from battlescene import *


def run_game(width, height, fps, starting_scene):
    pygame.init()
    screen = pygame.display.set_mode((width, height))
    clock = pygame.time.Clock()

    active_scene = starting_scene

    while active_scene is not None:
        pressed_keys = pygame.key.get_pressed()

        # Event filtering
        filtered_events = []
        for event in pygame.event.get():
            quit_attempt = False
            if event.type == pygame.QUIT:
                quit_attempt = True
            elif event.type == pygame.KEYDOWN:
                alt_pressed = pressed_keys[pygame.K_LALT] or \
                              pressed_keys[pygame.K_RALT]
                if event.key == pygame.K_ESCAPE:
                    quit_attempt = True
                elif event.key == pygame.K_F4 and alt_pressed:
                    quit_attempt = True

            if quit_attempt:
                active_scene.Terminate()
            else:
                filtered_events.append(event)

        active_scene.process_input(filtered_events, pressed_keys)
        active_scene.update(filtered_events)
        active_scene.render(screen)

        active_scene = active_scene.next

        pygame.display.flip()
        clock.tick(fps)


c = {'name': 'cat', 'ph_atk': None, 'mag_atk': {'size': 5, 'cost': 2, 'type': 'mp'},
     'fr_atk': {'size': 9, 'cost': 2, 'type': 'mp'}, 'ph_def': 10, 'mag_def': 11, 'hp': 50, 'sp': 30, 'mp': 60}

d = {'name': 'dog', 'ph_atk': {'size': 3, 'cost': 2, 'type': 'sp'}, 'mag_atk': {'size': 8, 'cost': 2, 'type': 'mp'},
     'ph_def': 14, 'mag_def': 19, 'hp': 50, 'sp': 30, 'mp': 60}

g = {'name': 'gato', 'ph_atk': {'size': 6, 'cost': 2, 'type': 'sp'}, 'mag_atk': {'size': 3, 'cost': 4, 'type': 'mp'},
     'fr_atk': {'size': 9, 'cost': 2, 'type': 'mp'}, 'ph_def': 99, 'mag_def': 11, 'hp': 50, 'sp': 30, 'mp': 60}

m = {'name': 'moo', 'ph_atk': {'size': 6, 'cost': 2, 'type': 'sp'}, 'mag_atk': {'size': 3, 'cost': 4, 'type': 'mp'},
     'fr_atk': {'size': 9, 'cost': 2, 'type': 'mp'}, 'ph_def': 99, 'mag_def': 11, 'hp': 50, 'sp': 30, 'mp': 60}

cat = Hero(**c)
gato = Hero(**g)
ser = Player(heroes=[cat, gato])
dog = Monster(**d)
moo = Monster(**m)
phil = Enemy(monsters=[dog, moo])
battle = BattleScene(ser, phil, 'player')
run_game(600, 800, 60, battle)
