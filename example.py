import random
from classes import *

warden_mag_atk = Attack(name='mag_atk', size=15, cost=20, atr_type='mp', defense='mag_def')
warden_ph_atk = Attack(name='ph_atk', size=10, cost=8, atr_type='sp', defense='ph_def')

warden_fire_def = Defence(name='fire_def', size=20)
warden_ph_def = Defence(name='ph_def', size=10)

warden = Hero(name='Warden', hp=100, mp=200, sp=70, at_list=(warden_mag_atk, warden_ph_atk,),
              df_list=(warden_fire_def, warden_ph_def,))

dragon_fire_atk = Attack(name='fire_atk', size=20, cost=10, atr_type='mp', defense='fire_def')
dragon_ph_atk = Attack(name='ph_atk', size=5, cost=20, atr_type='sp', defense='ph_def')

dragon_mag_def = Defence(name='mag_def', size=20)
dragon_ph_def = Defence(name='ph_def', size=10)

dragon = Monster(name='Dragon', hp=150, mp=120, sp=100, at_list=(dragon_fire_atk, dragon_ph_atk,),
              df_list=(dragon_ph_def, dragon_mag_def,))

#warden.attack(monster=dragon, attack=warden_mag_atk)

dragon.attack(heroes=(warden,))
