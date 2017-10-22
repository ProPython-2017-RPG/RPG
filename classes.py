#1) Класс игрока.
class Player:
	
	def __init__(self, *args, **kwargs):
		
		self.login
		self.money
		self.inventory
		
		self.heroes
		
		self.active_missions
		self.completed_missions
		
		self.x
		self.y

#2) Класс героя.
class Hero:
	
	def __init__(self, *args, **kwargs):
		
		self.name
		#Слово class уже зарезервировано за Python
		self.kind
		self.profession
		self.level
		self.info
		self.dead
		
		#Очки здоровья
		self.hp
		#Очки маны
		self.mp
		#Очки опыта
		self.exp
		#Очки воли (Только после того, как CP иссякнут, у персонажа начнут уменьшаться HP)
		self.cp
		
		#Физическая атака
		self.p_atk
		#Критическая атака
		self.c_atk
		#Атака огнем
		self.f_atk
		#Атака водой
		self.w_atk
		#Атака землей
		self.e_atk
		#Атака воздухом
		self.a_atk
		#Атака светом
		self.l_atk
		#Атака тьмой
		self.d_atk
		
		#Физическая защита
		self.p_def
		#Защита от огня
		self.f_def
		#Защита от воды
		self.w_def
		#Защита от земли
		self.e_def
		#Защита от воздуха
		self.a_def
		#Защита от света
		self.l_def
		#Защита от тьмы
		self.d_def
		
		#Меткость (Частота успешных попаданий по противнику)
		self.accuracy
		#Шанс избежать удара (Частота уклонения от ударов противника)
		self.evasion
		#Шанс критического урона
		self.critical
		#Сила духа (Сопротивляемость заклинаниям, уменьшающим характеристики (дебаффам), а также сну, параличу и прочему)
		self.wit
		
		self.skills
		self.buff
		self.debuff
		
		self.weapons
		self.armor
		self.items

#3) Класс врагов, которые в свою очередь состоят из классов монстров.
class Enemies:
	
	def __init__(self, *args, **kwargs):
		
		self.name
		self.level
		self.info
		
		self.count
		self.monsters
		
		self.loot

#4) Класс монстров.
class Monster:
	
	def __init__(self, *args, **kwargs):
		
		self.dead
		
		#Очки здоровья
		self.hp
		#Очки маны
		self.mp
		#Очки воли (Только после того, как CP иссякнут, у персонажа начнут уменьшаться HP)
		self.cp
		
		#Физическая атака
		self.p_atk
		#Критическая атака
		self.c_atk
		#Атака огнем
		self.f_atk
		#Атака водой
		self.w_atk
		#Атака землей
		self.e_atk
		#Атака воздухом
		self.a_atk
		#Атака светом
		self.l_atk
		#Атака тьмой
		self.d_atk
		
		#Физическая защита
		self.p_def
		#Защита от огня
		self.f_def
		#Защита от воды
		self.w_def
		#Защита от земли
		self.e_def
		#Защита от воздуха
		self.a_def
		#Защита от света
		self.l_def
		#Защита от тьмы
		self.d_def
		
		#Меткость (Частота успешных попаданий по противнику)
		self.accuracy
		#Шанс избежать удара (Частота уклонения от ударов противника)
		self.evasion
		#Шанс критического урона
		self.critical
		#Сила духа (Сопротивляемость заклинаниям, уменьшающим характеристики (дебаффам), а также сну, параличу и прочему)
		self.wit
		
		self.skills
		self.buff
		self.debuff
		
		self.weapons
		self.armor
		self.items

#5) Класс умений.
class Skills:
	
	def __init__(self, *args, **kwargs):
		
		self.name
		self.level
		#Подразумевается использовать hash для различия навыков, предметов и прочего
		self.hash
		self.info

#6) Класс предмета.		
class Item:
	
	def __init__(self, *args, **kwargs):
		
		self.name
		#Прочность
		self.strength
		self.level
		#Допустимый класс. Не все классы смогут воспользоваться данным предметом.
		self.allowable_class
		self.hash
		self.info

#7) Класс оружия. Наследник класса Item.
class Weapons(Item):
	
	def __init__(self, *args, **kwargs):
		
		super().__init__(*args, **kwargs)
		
		#Физическая атака
		self.p_atk
		#Критическая атака
		self.c_atk
		#Атака огнем
		self.f_atk
		#Атака водой
		self.w_atk
		#Атака землей
		self.e_atk
		#Атака воздухом
		self.a_atk
		#Атака светом
		self.l_atk
		#Атака тьмой
		self.d_atk
		
		self.skills

#8) Класс брони. Наследник класса Item.
class Armor(Item):
	
	def __init__(self, *args, **kwargs):
		
		super().__init__(*args, **kwargs)
		
		#Физическая защита
		self.p_def
		#Защита от огня
		self.f_def
		#Защита от воды
		self.w_def
		#Защита от земли
		self.e_def
		#Защита от воздуха
		self.a_def
		#Защита от света
		self.l_def
		#Защита от тьмы
		self.d_def
		
		self.skills

#9) Класс вспомогательных предметов. Наследник класса Item.
#Название можно изменить, сейчас я не смог придумать лучше.
class HelpItem(Item):
	
	def __init__(self, *args, **kwargs):
		
		super().__init__(*args, **kwargs)
		
		#Функция от Hero увеличивающая какие-либо характеристики.
		self.action