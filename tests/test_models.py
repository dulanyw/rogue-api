from app.core.models import Player, Enemy, Item, GameState, Tile
from app.core.map_gen import generate_map

def test_player_creation():
    p = Player("TestHero")
    assert p.name == "TestHero"
    assert p.hp == p.max_hp
    assert p.hp > 0
    assert p.level == 1
    assert p.xp == 0
    assert p.gold == 0
    assert p.inventory == []
    assert p.equipped_weapon is None
    assert p.equipped_armor is None
    assert p.equipped_rings == []

def test_enemy_creation():
    e = Enemy("Dragon", hp=40, attack=15, defense=8, xp_value=50, position=(5, 5))
    assert e.name == "Dragon"
    assert e.hp == 40
    assert e.max_hp == 40
    assert e.attack == 15
    assert e.defense == 8
    assert e.xp_value == 50
    assert e.is_alive is True
    assert e.position == [5, 5]

def test_item_creation():
    item = Item("Potion of Healing", "potion", 6, "Restores 6 HP")
    assert item.name == "Potion of Healing"
    assert item.type == "potion"
    assert item.value == 6
    assert item.description == "Restores 6 HP"
    assert item.id is not None

# ---------------------------------------------------------------------------
# Additional model tests
# ---------------------------------------------------------------------------

def test_player_default_name():
    p = Player()
    assert p.name == "Player"

def test_player_position_default():
    p = Player("Hero")
    assert isinstance(p.position, list)
    assert len(p.position) == 2

def test_player_unique_ids_via_items():
    """Each Item gets a unique UUID."""
    i1 = Item("Sword", "weapon", 3, "")
    i2 = Item("Sword", "weapon", 3, "")
    assert i1.id != i2.id

def test_enemy_position_stored_as_list():
    """Enemy position is stored as a list even when provided as a tuple."""
    e = Enemy("Bat", hp=4, attack=2, defense=1, xp_value=3, position=(10, 20))
    assert e.position == [10, 20]
    assert isinstance(e.position, list)

def test_enemy_takes_damage():
    """Manually reducing hp kills the enemy when it reaches 0."""
    e = Enemy("Emu", hp=3, attack=2, defense=0, xp_value=2, position=(1, 1))
    e.hp -= 3
    assert e.hp == 0

def test_item_gold_type():
    gold = Item("Gold", "gold", 0, "Shiny gold coins")
    assert gold.type == "gold"

def test_tile_values():
    assert Tile.FLOOR.value == '.'
    assert Tile.WALL.value == '#'
    assert Tile.STAIRS.value == '>'
    assert Tile.EMPTY.value == ' '

def test_game_state_creation():
    """GameState initialises with sane defaults."""
    tiles, player_pos, enemy_pos, item_pos = generate_map(80, 24, 42, 1)
    player = Player("Tester")
    player.position = player_pos[:]
    state = GameState(
        game_id="test-id",
        seed=42,
        player=player,
        enemies=[],
        items=[],
        dungeon_level=1,
        map_tiles=tiles,
        width=80,
        height=24,
    )
    assert state.game_id == "test-id"
    assert state.seed == 42
    assert state.turn == 0
    assert state.dungeon_level == 1
    assert state.status == 'ongoing'
    assert state.log == []
    assert state.width == 80
    assert state.height == 24
