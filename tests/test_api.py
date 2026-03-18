import pytest
import json
from app.app import create_app
from app.storage.memory_store import MemoryStore
from app.core.models import Item, Tile

@pytest.fixture
def client():
    app = create_app({'TESTING': True})
    # Clear storage between tests
    store = MemoryStore()
    store.clear()
    with app.test_client() as c:
        yield c

# ---------------------------------------------------------------------------
# POST /games — create a new game
# ---------------------------------------------------------------------------

def test_create_game(client):
    resp = client.post('/api/v1/games', json={'player_name': 'TestHero', 'seed': 42})
    assert resp.status_code == 201
    data = resp.get_json()
    assert 'game_id' in data
    assert 'state' in data
    assert data['state']['player']['name'] == 'TestHero'

def test_create_game_no_body(client):
    """POST with no body should use defaults (Player, random seed)."""
    resp = client.post('/api/v1/games')
    assert resp.status_code == 201
    data = resp.get_json()
    assert 'game_id' in data
    assert 'state' in data
    assert data['state']['player']['name'] == 'Player'

def test_create_game_seed_only(client):
    resp = client.post('/api/v1/games', json={'seed': 99})
    assert resp.status_code == 201
    data = resp.get_json()
    assert data['state']['seed'] == 99
    assert data['state']['player']['name'] == 'Player'

def test_create_game_player_name_only(client):
    resp = client.post('/api/v1/games', json={'player_name': 'Rogue'})
    assert resp.status_code == 201
    data = resp.get_json()
    assert data['state']['player']['name'] == 'Rogue'

def test_create_game_full_state_structure(client):
    """Verify that the created game state contains all expected fields."""
    resp = client.post('/api/v1/games', json={'seed': 42, 'player_name': 'Hero'})
    assert resp.status_code == 201
    state = resp.get_json()['state']
    for field in ('game_id', 'seed', 'turn', 'dungeon_level', 'status',
                  'player', 'enemies', 'items', 'visible_map', 'log',
                  'width', 'height'):
        assert field in state, f"Missing field: {field}"
    assert state['turn'] == 0
    assert state['dungeon_level'] == 1
    assert state['status'] == 'ongoing'
    assert isinstance(state['log'], list)
    assert isinstance(state['enemies'], list)
    assert isinstance(state['items'], list)

def test_create_game_player_structure(client):
    """Verify that the player object contains all expected fields."""
    resp = client.post('/api/v1/games', json={'seed': 42})
    player = resp.get_json()['state']['player']
    for field in ('name', 'hp', 'max_hp', 'attack', 'defense', 'position',
                  'level', 'xp', 'xp_next', 'gold', 'inventory',
                  'equipped_weapon', 'equipped_armor', 'equipped_rings'):
        assert field in player, f"Missing player field: {field}"
    assert player['hp'] > 0
    assert player['level'] == 1
    assert player['xp'] == 0
    assert player['gold'] == 0
    assert player['equipped_weapon'] is None
    assert player['equipped_armor'] is None
    assert player['equipped_rings'] == []

def test_create_game_visible_map_structure(client):
    """Verify that visible_map contains rows, width, height, player_position."""
    resp = client.post('/api/v1/games', json={'seed': 42})
    vm = resp.get_json()['state']['visible_map']
    assert 'rows' in vm
    assert 'width' in vm
    assert 'height' in vm
    assert 'player_position' in vm
    assert vm['width'] == 80
    assert vm['height'] == 24
    assert len(vm['rows']) == 24

def test_create_game_deterministic_seed(client):
    """Two games with the same seed should start with the same player position."""
    resp1 = client.post('/api/v1/games', json={'seed': 777})
    resp2 = client.post('/api/v1/games', json={'seed': 777})
    pos1 = resp1.get_json()['state']['player']['position']
    pos2 = resp2.get_json()['state']['player']['position']
    assert pos1 == pos2

# ---------------------------------------------------------------------------
# GET /games/{game_id} — retrieve game state
# ---------------------------------------------------------------------------

def test_get_game(client):
    # Create first
    resp = client.post('/api/v1/games', json={'seed': 42})
    game_id = resp.get_json()['game_id']
    
    resp = client.get(f'/api/v1/games/{game_id}')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['game_id'] == game_id
    assert 'player' in data
    assert 'visible_map' in data
    assert 'log' in data
    assert 'status' in data

def test_get_game_response_structure(client):
    """GET response must include game_id, turn, player, visible_map, log, status."""
    resp = client.post('/api/v1/games', json={'seed': 42})
    game_id = resp.get_json()['game_id']

    resp = client.get(f'/api/v1/games/{game_id}')
    assert resp.status_code == 200
    data = resp.get_json()
    for field in ('game_id', 'turn', 'player', 'visible_map', 'log', 'status'):
        assert field in data, f"Missing field: {field}"
    assert data['status'] == 'ongoing'
    assert data['turn'] == 0

def test_get_game_player_fields(client):
    resp = client.post('/api/v1/games', json={'seed': 42})
    game_id = resp.get_json()['game_id']

    player = client.get(f'/api/v1/games/{game_id}').get_json()['player']
    for field in ('name', 'hp', 'max_hp', 'attack', 'defense', 'position',
                  'level', 'xp', 'xp_next', 'gold', 'inventory'):
        assert field in player, f"Missing player field: {field}"

def test_get_game_visible_map_fields(client):
    resp = client.post('/api/v1/games', json={'seed': 42})
    game_id = resp.get_json()['game_id']

    vm = client.get(f'/api/v1/games/{game_id}').get_json()['visible_map']
    assert 'rows' in vm
    assert 'width' in vm
    assert 'height' in vm
    assert 'player_position' in vm

def test_get_unknown_game(client):
    resp = client.get('/api/v1/games/nonexistent-game-id')
    assert resp.status_code == 404
    assert 'error' in resp.get_json()

def test_get_game_random_string_id(client):
    resp = client.get('/api/v1/games/this-is-definitely-not-a-valid-id-12345')
    assert resp.status_code == 404

# ---------------------------------------------------------------------------
# POST /games/{game_id}/action — perform an action (valid cases)
# ---------------------------------------------------------------------------

def test_perform_action_move(client):
    resp = client.post('/api/v1/games', json={'seed': 42})
    game_id = resp.get_json()['game_id']
    
    resp = client.post(f'/api/v1/games/{game_id}/action', json={'action': 'move', 'direction': 'north'})
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'success' in data
    assert 'events' in data
    assert 'state' in data

def test_perform_action_move_response_structure(client):
    """Action response must include success, events (list), and state."""
    resp = client.post('/api/v1/games', json={'seed': 42})
    game_id = resp.get_json()['game_id']

    resp = client.post(f'/api/v1/games/{game_id}/action',
                       json={'action': 'move', 'direction': 'south'})
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data['success'], bool)
    assert isinstance(data['events'], list)
    assert isinstance(data['state'], dict)

def test_perform_action_move_all_directions(client):
    """All four valid directions should be accepted (200 even if blocked)."""
    for direction in ('north', 'south', 'east', 'west'):
        resp = client.post('/api/v1/games', json={'seed': 42})
        game_id = resp.get_json()['game_id']
        resp = client.post(f'/api/v1/games/{game_id}/action',
                           json={'action': 'move', 'direction': direction})
        assert resp.status_code == 200, f"Expected 200 for direction={direction}"

def test_perform_action_wait(client):
    resp = client.post('/api/v1/games', json={'seed': 42})
    game_id = resp.get_json()['game_id']

    resp = client.post(f'/api/v1/games/{game_id}/action', json={'action': 'wait'})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True
    assert any('wait' in e.lower() for e in data['events'])

def test_perform_action_pickup_nothing(client):
    """Pickup when no item is at the player position returns success=False."""
    resp = client.post('/api/v1/games', json={'seed': 42})
    game_id = resp.get_json()['game_id']

    store = MemoryStore()
    game_state = store.load(game_id)
    game_state.items = []  # clear all items on the map
    store.save(game_id, game_state)

    resp = client.post(f'/api/v1/games/{game_id}/action', json={'action': 'pickup'})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is False

def test_perform_action_pickup_item(client):
    """Pickup succeeds when an item is at the player position."""
    resp = client.post('/api/v1/games', json={'seed': 42})
    game_id = resp.get_json()['game_id']

    store = MemoryStore()
    game_state = store.load(game_id)
    potion = Item('Potion of Healing', 'potion', 6, 'Restores 6 HP')
    potion.position = list(game_state.player.position)
    game_state.items = [potion]
    store.save(game_id, game_state)

    resp = client.post(f'/api/v1/games/{game_id}/action', json={'action': 'pickup'})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True
    assert len(data['state']['player']['inventory']) == 1

def test_perform_action_pickup_gold(client):
    """Picking up gold adds to the player gold total."""
    resp = client.post('/api/v1/games', json={'seed': 42})
    game_id = resp.get_json()['game_id']

    store = MemoryStore()
    game_state = store.load(game_id)
    gold = Item('Gold', 'gold', 25, 'Shiny gold coins')
    gold.position = list(game_state.player.position)
    game_state.items = [gold]
    store.save(game_id, game_state)

    resp = client.post(f'/api/v1/games/{game_id}/action', json={'action': 'pickup'})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True
    assert data['state']['player']['gold'] >= 25

def test_perform_action_use_item_potion(client):
    """Using a potion from inventory restores HP."""
    resp = client.post('/api/v1/games', json={'seed': 42})
    game_id = resp.get_json()['game_id']

    store = MemoryStore()
    game_state = store.load(game_id)
    # Damage player so potion can heal
    game_state.player.hp = 5
    potion = Item('Potion of Healing', 'potion', 6, 'Restores 6 HP')
    game_state.player.inventory.append(potion)
    store.save(game_id, game_state)

    resp = client.post(f'/api/v1/games/{game_id}/action',
                       json={'action': 'use_item', 'item_id': potion.id})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True
    assert data['state']['player']['hp'] > 5

def test_perform_action_use_item_not_in_inventory(client):
    """Using an item_id that is not in inventory returns success=False."""
    resp = client.post('/api/v1/games', json={'seed': 42})
    game_id = resp.get_json()['game_id']

    resp = client.post(f'/api/v1/games/{game_id}/action',
                       json={'action': 'use_item', 'item_id': 'nonexistent-item-id'})
    assert resp.status_code == 200
    assert resp.get_json()['success'] is False

def test_perform_action_attack_no_enemy(client):
    """Attacking an empty tile returns success=False."""
    resp = client.post('/api/v1/games', json={'seed': 42})
    game_id = resp.get_json()['game_id']

    store = MemoryStore()
    game_state = store.load(game_id)
    game_state.enemies = []
    store.save(game_id, game_state)

    resp = client.post(f'/api/v1/games/{game_id}/action',
                       json={'action': 'attack', 'direction': 'north'})
    assert resp.status_code == 200
    assert resp.get_json()['success'] is False

def test_perform_action_attack_all_directions(client):
    """All four attack directions are accepted (200 even if no enemy)."""
    for direction in ('north', 'south', 'east', 'west'):
        resp = client.post('/api/v1/games', json={'seed': 42})
        game_id = resp.get_json()['game_id']
        store = MemoryStore()
        game_state = store.load(game_id)
        game_state.enemies = []
        store.save(game_id, game_state)
        resp = client.post(f'/api/v1/games/{game_id}/action',
                           json={'action': 'attack', 'direction': direction})
        assert resp.status_code == 200, f"Expected 200 for attack direction={direction}"

def test_perform_action_descend_not_on_stairs(client):
    """Descending when not on stairs returns success=False."""
    resp = client.post('/api/v1/games', json={'seed': 42})
    game_id = resp.get_json()['game_id']

    store = MemoryStore()
    game_state = store.load(game_id)
    px, py = game_state.player.position
    # Ensure player is on FLOOR, not STAIRS
    game_state.map[py][px] = Tile.FLOOR
    store.save(game_id, game_state)

    resp = client.post(f'/api/v1/games/{game_id}/action', json={'action': 'descend'})
    assert resp.status_code == 200
    assert resp.get_json()['success'] is False

def test_perform_action_descend_on_stairs(client):
    """Descending on stairs advances dungeon level."""
    resp = client.post('/api/v1/games', json={'seed': 42})
    game_id = resp.get_json()['game_id']

    store = MemoryStore()
    game_state = store.load(game_id)
    px, py = game_state.player.position
    game_state.map[py][px] = Tile.STAIRS
    store.save(game_id, game_state)

    resp = client.post(f'/api/v1/games/{game_id}/action', json={'action': 'descend'})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True
    assert data['state']['dungeon_level'] == 2

def test_perform_action_don_armor(client):
    """Equipping armor from inventory works."""
    resp = client.post('/api/v1/games', json={'seed': 42})
    game_id = resp.get_json()['game_id']

    store = MemoryStore()
    game_state = store.load(game_id)
    armor = Item('Leather Armor', 'armor', 2, 'Leather armor (+2 defense)')
    game_state.player.inventory.append(armor)
    store.save(game_id, game_state)

    resp = client.post(f'/api/v1/games/{game_id}/action',
                       json={'action': 'don_armor', 'item_id': armor.id})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True
    assert data['state']['player']['equipped_armor'] is not None

def test_perform_action_remove_armor(client):
    """Removing equipped armor works."""
    resp = client.post('/api/v1/games', json={'seed': 42})
    game_id = resp.get_json()['game_id']

    store = MemoryStore()
    game_state = store.load(game_id)
    armor = Item('Leather Armor', 'armor', 2, 'Leather armor')
    game_state.player.equipped_armor = armor
    store.save(game_id, game_state)

    resp = client.post(f'/api/v1/games/{game_id}/action', json={'action': 'remove_armor'})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True
    assert data['state']['player']['equipped_armor'] is None

def test_perform_action_remove_armor_when_none(client):
    """Removing armor when none equipped returns success=False."""
    resp = client.post('/api/v1/games', json={'seed': 42})
    game_id = resp.get_json()['game_id']

    resp = client.post(f'/api/v1/games/{game_id}/action', json={'action': 'remove_armor'})
    assert resp.status_code == 200
    assert resp.get_json()['success'] is False

def test_perform_action_switch_weapon(client):
    """Equipping a weapon from inventory works."""
    resp = client.post('/api/v1/games', json={'seed': 42})
    game_id = resp.get_json()['game_id']

    store = MemoryStore()
    game_state = store.load(game_id)
    sword = Item('Long Sword', 'weapon', 5, 'A long sword (+5 attack)')
    game_state.player.inventory.append(sword)
    store.save(game_id, game_state)

    resp = client.post(f'/api/v1/games/{game_id}/action',
                       json={'action': 'switch_weapon', 'item_id': sword.id})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True
    assert data['state']['player']['equipped_weapon'] is not None

def test_perform_action_don_ring(client):
    """Equipping a ring from inventory works."""
    resp = client.post('/api/v1/games', json={'seed': 42})
    game_id = resp.get_json()['game_id']

    store = MemoryStore()
    game_state = store.load(game_id)
    ring = Item('Ring of Strength', 'ring', 2, 'Increases attack by 2')
    game_state.player.inventory.append(ring)
    store.save(game_id, game_state)

    resp = client.post(f'/api/v1/games/{game_id}/action',
                       json={'action': 'don_ring', 'item_id': ring.id})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True
    assert len(data['state']['player']['equipped_rings']) == 1

def test_perform_action_remove_ring(client):
    """Removing an equipped ring works."""
    resp = client.post('/api/v1/games', json={'seed': 42})
    game_id = resp.get_json()['game_id']

    store = MemoryStore()
    game_state = store.load(game_id)
    ring = Item('Ring of Strength', 'ring', 2, 'Increases attack by 2')
    game_state.player.equipped_rings.append(ring)
    store.save(game_id, game_state)

    resp = client.post(f'/api/v1/games/{game_id}/action',
                       json={'action': 'remove_ring', 'ring_id': ring.id})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True
    assert len(data['state']['player']['equipped_rings']) == 0

def test_perform_action_turn_increments(client):
    """Each action increments the turn counter by 1."""
    resp = client.post('/api/v1/games', json={'seed': 42})
    game_id = resp.get_json()['game_id']

    for expected_turn in range(1, 4):
        resp = client.post(f'/api/v1/games/{game_id}/action', json={'action': 'wait'})
        assert resp.get_json()['state']['turn'] == expected_turn

# ---------------------------------------------------------------------------
# POST /games/{game_id}/action — invalid data / error cases
# ---------------------------------------------------------------------------

def test_action_on_dead_game(client):
    resp = client.post('/api/v1/games', json={'seed': 42})
    game_id = resp.get_json()['game_id']
    
    # Manually set game to dead by loading and modifying
    store = MemoryStore()
    game_state = store.load(game_id)
    game_state.status = 'dead'
    store.save(game_id, game_state)
    
    resp = client.post(f'/api/v1/games/{game_id}/action', json={'action': 'move', 'direction': 'north'})
    assert resp.status_code == 409
    assert 'error' in resp.get_json()

def test_action_on_won_game(client):
    """Actions on a won game return 409 Conflict."""
    resp = client.post('/api/v1/games', json={'seed': 42})
    game_id = resp.get_json()['game_id']

    store = MemoryStore()
    game_state = store.load(game_id)
    game_state.status = 'won'
    store.save(game_id, game_state)

    resp = client.post(f'/api/v1/games/{game_id}/action', json={'action': 'wait'})
    assert resp.status_code == 409
    assert 'error' in resp.get_json()

def test_action_on_nonexistent_game(client):
    resp = client.post('/api/v1/games/no-such-game/action', json={'action': 'wait'})
    assert resp.status_code == 404
    assert 'error' in resp.get_json()

def test_action_missing_action_field(client):
    resp = client.post('/api/v1/games', json={'seed': 42})
    game_id = resp.get_json()['game_id']

    resp = client.post(f'/api/v1/games/{game_id}/action', json={'direction': 'north'})
    assert resp.status_code == 400
    assert 'error' in resp.get_json()

def test_action_invalid_action_name(client):
    resp = client.post('/api/v1/games', json={'seed': 42})
    game_id = resp.get_json()['game_id']

    resp = client.post(f'/api/v1/games/{game_id}/action', json={'action': 'cast_fireball'})
    assert resp.status_code == 400
    assert 'error' in resp.get_json()

def test_action_move_missing_direction(client):
    resp = client.post('/api/v1/games', json={'seed': 42})
    game_id = resp.get_json()['game_id']

    resp = client.post(f'/api/v1/games/{game_id}/action', json={'action': 'move'})
    assert resp.status_code == 400
    assert 'error' in resp.get_json()

def test_action_move_invalid_direction(client):
    resp = client.post('/api/v1/games', json={'seed': 42})
    game_id = resp.get_json()['game_id']

    resp = client.post(f'/api/v1/games/{game_id}/action',
                       json={'action': 'move', 'direction': 'up'})
    assert resp.status_code == 400
    assert 'error' in resp.get_json()

def test_action_attack_missing_direction(client):
    resp = client.post('/api/v1/games', json={'seed': 42})
    game_id = resp.get_json()['game_id']

    resp = client.post(f'/api/v1/games/{game_id}/action', json={'action': 'attack'})
    assert resp.status_code == 400
    assert 'error' in resp.get_json()

def test_action_attack_invalid_direction(client):
    resp = client.post('/api/v1/games', json={'seed': 42})
    game_id = resp.get_json()['game_id']

    resp = client.post(f'/api/v1/games/{game_id}/action',
                       json={'action': 'attack', 'direction': 'diagonal'})
    assert resp.status_code == 400
    assert 'error' in resp.get_json()

def test_action_use_item_missing_item_id(client):
    resp = client.post('/api/v1/games', json={'seed': 42})
    game_id = resp.get_json()['game_id']

    resp = client.post(f'/api/v1/games/{game_id}/action', json={'action': 'use_item'})
    assert resp.status_code == 400
    assert 'error' in resp.get_json()

def test_action_empty_body(client):
    """Empty body (no action field) returns 400."""
    resp = client.post('/api/v1/games', json={'seed': 42})
    game_id = resp.get_json()['game_id']

    resp = client.post(f'/api/v1/games/{game_id}/action', json={})
    assert resp.status_code == 400
    assert 'error' in resp.get_json()

def test_action_non_json_body(client):
    """Non-JSON body is treated as empty and returns 400 (missing action)."""
    resp = client.post('/api/v1/games', json={'seed': 42})
    game_id = resp.get_json()['game_id']

    resp = client.post(f'/api/v1/games/{game_id}/action',
                       data='not-json', content_type='text/plain')
    assert resp.status_code == 400

# ---------------------------------------------------------------------------
# DELETE /games/{game_id} — delete a game
# ---------------------------------------------------------------------------

def test_delete_game(client):
    resp = client.post('/api/v1/games', json={'seed': 42})
    game_id = resp.get_json()['game_id']
    
    resp = client.delete(f'/api/v1/games/{game_id}')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['deleted'] is True
    
    # Should 404 now
    resp = client.get(f'/api/v1/games/{game_id}')
    assert resp.status_code == 404

def test_delete_nonexistent_game(client):
    resp = client.delete('/api/v1/games/this-game-does-not-exist')
    assert resp.status_code == 404
    assert 'error' in resp.get_json()

def test_delete_game_double(client):
    """Deleting a game twice: first returns 200, second returns 404."""
    resp = client.post('/api/v1/games', json={'seed': 42})
    game_id = resp.get_json()['game_id']

    resp1 = client.delete(f'/api/v1/games/{game_id}')
    assert resp1.status_code == 200

    resp2 = client.delete(f'/api/v1/games/{game_id}')
    assert resp2.status_code == 404
