import enum
import uuid

class Tile(enum.Enum):
    FLOOR = '.'
    WALL = '#'
    STAIRS = '>'
    EMPTY = ' '

class Item:
    def __init__(self, name, item_type, value=0, description=""):
        self.id = str(uuid.uuid4())
        self.name = name
        self.type = item_type  # 'potion', 'weapon', 'armor', 'ring', 'gold'
        self.value = value
        self.description = description

class Enemy:
    def __init__(self, name, hp, attack, defense, xp_value, position=(0, 0)):
        self.id = str(uuid.uuid4())
        self.name = name
        self.hp = hp
        self.max_hp = hp
        self.attack = attack
        self.defense = defense
        self.position = list(position)
        self.is_alive = True
        self.xp_value = xp_value

class Player:
    def __init__(self, name="Player"):
        self.name = name
        self.hp = 12
        self.max_hp = 12
        self.attack = 4
        self.defense = 1
        self.position = [1, 1]
        self.inventory = []
        self.level = 1
        self.xp = 0
        self.xp_next = 10
        self.gold = 0
        self.equipped_weapon = None
        self.equipped_armor = None
        self.equipped_rings = []

class GameState:
    def __init__(self, game_id, seed, player, enemies, items, dungeon_level, map_tiles, width, height):
        self.game_id = game_id
        self.seed = seed
        self.turn = 0
        self.player = player
        self.enemies = enemies
        self.items = items
        self.dungeon_level = dungeon_level
        self.map = map_tiles  # 2D list of Tile
        self.log = []
        self.status = 'ongoing'
        self.width = width
        self.height = height
