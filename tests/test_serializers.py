"""
Comprehensive tests for app/utils/serializers.py — item, enemy, player,
map, and full game-state serialization.
"""
import pytest
from app.core.models import Player, Enemy, Item, GameState, Tile
from app.core.map_gen import generate_map
from app.utils.serializers import (
    serialize_item,
    serialize_enemy,
    serialize_player,
    serialize_map,
    serialize_game_state,
)


def _make_state(seed=42):
    """Helper: build a minimal GameState for testing."""
    tiles, player_pos, _, _ = generate_map(80, 24, seed, 1)
    player = Player("Tester")
    player.position = player_pos[:]
    return GameState(
        game_id="test-id",
        seed=seed,
        player=player,
        enemies=[],
        items=[],
        dungeon_level=1,
        map_tiles=tiles,
        width=80,
        height=24,
    )


# ---------------------------------------------------------------------------
# serialize_item
# ---------------------------------------------------------------------------

def test_serialize_item_fields():
    item = Item("Long Sword", "weapon", 5, "A long sword (+5 attack)")
    result = serialize_item(item)
    assert result['id'] == item.id
    assert result['name'] == "Long Sword"
    assert result['type'] == "weapon"
    assert result['value'] == 5
    assert result['description'] == "A long sword (+5 attack)"

def test_serialize_item_potion():
    potion = Item("Potion of Healing", "potion", 6, "Restores 6 HP")
    result = serialize_item(potion)
    assert result['type'] == "potion"
    assert result['value'] == 6

def test_serialize_item_gold():
    gold = Item("Gold", "gold", 0, "Shiny gold coins")
    result = serialize_item(gold)
    assert result['type'] == "gold"

# ---------------------------------------------------------------------------
# serialize_enemy
# ---------------------------------------------------------------------------

def test_serialize_enemy_fields():
    e = Enemy("Dragon", hp=40, attack=15, defense=8, xp_value=50, position=(5, 10))
    result = serialize_enemy(e)
    assert result['id'] == e.id
    assert result['name'] == "Dragon"
    assert result['hp'] == 40
    assert result['max_hp'] == 40
    assert result['attack'] == 15
    assert result['defense'] == 8
    assert result['position'] == [5, 10]
    assert result['is_alive'] is True
    assert result['xp_value'] == 50

def test_serialize_enemy_dead():
    e = Enemy("Bat", hp=4, attack=2, defense=1, xp_value=3, position=(1, 1))
    e.hp = 0
    e.is_alive = False
    result = serialize_enemy(e)
    assert result['hp'] == 0
    assert result['is_alive'] is False

# ---------------------------------------------------------------------------
# serialize_player
# ---------------------------------------------------------------------------

def test_serialize_player_basic():
    p = Player("Hero")
    result = serialize_player(p)
    assert result['name'] == "Hero"
    assert result['hp'] == 12
    assert result['max_hp'] == 12
    assert result['attack'] == 4
    assert result['defense'] == 1
    assert result['level'] == 1
    assert result['xp'] == 0
    assert result['gold'] == 0
    assert result['inventory'] == []
    assert result['equipped_weapon'] is None
    assert result['equipped_armor'] is None
    assert result['equipped_rings'] == []

def test_serialize_player_with_inventory():
    p = Player("Hero")
    sword = Item("Short Sword", "weapon", 3, "A short sword")
    p.inventory.append(sword)
    result = serialize_player(p)
    assert len(result['inventory']) == 1
    assert result['inventory'][0]['name'] == "Short Sword"

def test_serialize_player_with_equipped_weapon():
    p = Player("Hero")
    sword = Item("Long Sword", "weapon", 5, "A long sword")
    p.equipped_weapon = sword
    result = serialize_player(p)
    assert result['equipped_weapon'] is not None
    assert result['equipped_weapon']['name'] == "Long Sword"

def test_serialize_player_with_equipped_armor():
    p = Player("Hero")
    armor = Item("Leather Armor", "armor", 2, "Leather armor")
    p.equipped_armor = armor
    result = serialize_player(p)
    assert result['equipped_armor'] is not None
    assert result['equipped_armor']['name'] == "Leather Armor"

def test_serialize_player_with_rings():
    p = Player("Hero")
    ring = Item("Ring of Strength", "ring", 2, "Increases attack by 2")
    p.equipped_rings.append(ring)
    result = serialize_player(p)
    assert len(result['equipped_rings']) == 1
    assert result['equipped_rings'][0]['name'] == "Ring of Strength"

# ---------------------------------------------------------------------------
# serialize_map
# ---------------------------------------------------------------------------

def test_serialize_map_structure():
    state = _make_state()
    result = serialize_map(state)
    assert 'rows' in result
    assert 'width' in result
    assert 'height' in result
    assert 'player_position' in result

def test_serialize_map_dimensions():
    state = _make_state()
    result = serialize_map(state)
    assert result['width'] == 80
    assert result['height'] == 24
    assert len(result['rows']) == 24
    assert all(len(row) == 80 for row in result['rows'])

def test_serialize_map_player_position():
    state = _make_state()
    result = serialize_map(state)
    assert result['player_position'] == state.player.position

def test_serialize_map_fog_of_war_hides_distant_tiles():
    """With fog of war enabled, tiles far from the player should be spaces."""
    state = _make_state()
    # Place player at a corner so distant tiles are definitely hidden
    state.player.position = [0, 0]
    result = serialize_map(state, fog_of_war=True)
    # Tile at (79, 23) should be hidden (distance >> vision radius)
    assert result['rows'][23][79] == ' '

def test_serialize_map_no_fog_reveals_all():
    """With fog of war disabled, no tile should be a space (unless it's EMPTY tile type)."""
    state = _make_state()
    result = serialize_map(state, fog_of_war=False)
    # Every tile should be one of '.', '#', '>', ' ' (where ' ' is Tile.EMPTY)
    valid_chars = {'.', '#', '>', ' '}
    for row in result['rows']:
        for ch in row:
            assert ch in valid_chars

# ---------------------------------------------------------------------------
# serialize_game_state
# ---------------------------------------------------------------------------

def test_serialize_game_state_fields():
    state = _make_state()
    result = serialize_game_state(state)
    for field in ('game_id', 'seed', 'turn', 'dungeon_level', 'status',
                  'player', 'enemies', 'items', 'visible_map', 'log',
                  'width', 'height'):
        assert field in result, f"Missing field: {field}"

def test_serialize_game_state_values():
    state = _make_state(seed=77)
    result = serialize_game_state(state)
    assert result['game_id'] == "test-id"
    assert result['seed'] == 77
    assert result['turn'] == 0
    assert result['dungeon_level'] == 1
    assert result['status'] == 'ongoing'
    assert result['log'] == []
    assert result['enemies'] == []
    assert result['items'] == []
    assert result['width'] == 80
    assert result['height'] == 24

def test_serialize_game_state_with_enemies_and_items():
    state = _make_state()
    e = Enemy("Bat", hp=4, attack=2, defense=1, xp_value=3, position=(5, 5))
    item = Item("Potion of Healing", "potion", 6, "Restores 6 HP")
    item.position = [6, 6]
    state.enemies = [e]
    state.items = [item]

    result = serialize_game_state(state)
    assert len(result['enemies']) == 1
    assert result['enemies'][0]['name'] == "Bat"
    assert len(result['items']) == 1
    assert result['items'][0]['name'] == "Potion of Healing"
