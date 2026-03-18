import pytest
import json
from app.app import create_app
from app.storage.memory_store import MemoryStore
from app.core.models import Item

@pytest.fixture
def client():
    app = create_app({'TESTING': True})
    # Clear storage between tests
    store = MemoryStore()
    store.clear()
    with app.test_client() as c:
        yield c

def test_create_game(client):
    resp = client.post('/api/v1/games', json={'player_name': 'TestHero', 'seed': 42})
    assert resp.status_code == 201
    data = resp.get_json()
    assert 'game_id' in data
    assert 'state' in data
    assert data['state']['player']['name'] == 'TestHero'

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

def test_get_inventory_empty(client):
    resp = client.post('/api/v1/games', json={'seed': 42})
    game_id = resp.get_json()['game_id']

    resp = client.get(f'/api/v1/games/{game_id}/inventory')
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'inventory' in data
    assert 'equipped_weapon' in data
    assert 'equipped_armor' in data
    assert 'equipped_rings' in data
    assert isinstance(data['inventory'], list)

def test_get_inventory_with_items(client):
    resp = client.post('/api/v1/games', json={'seed': 42})
    game_id = resp.get_json()['game_id']

    store = MemoryStore()
    game_state = store.load(game_id)
    potion = Item("Potion of Healing", "potion", 6, "Restores 6 HP")
    sword = Item("Short Sword", "weapon", 3, "A short sword")
    game_state.player.inventory.extend([potion, sword])
    store.save(game_id, game_state)

    resp = client.get(f'/api/v1/games/{game_id}/inventory')
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data['inventory']) == 2
    assert data['inventory'][0]['key'] == 'a'
    assert data['inventory'][0]['name'] == 'Potion of Healing'
    assert data['inventory'][1]['key'] == 'b'
    assert data['inventory'][1]['name'] == 'Short Sword'

def test_get_inventory_unknown_game(client):
    resp = client.get('/api/v1/games/nonexistent-game-id/inventory')
    assert resp.status_code == 404

def test_inventory_keys_in_game_state(client):
    resp = client.post('/api/v1/games', json={'seed': 42})
    game_id = resp.get_json()['game_id']

    store = MemoryStore()
    game_state = store.load(game_id)
    potion = Item("Potion of Healing", "potion", 6, "Restores 6 HP")
    game_state.player.inventory.append(potion)
    store.save(game_id, game_state)

    resp = client.get(f'/api/v1/games/{game_id}')
    assert resp.status_code == 200
    data = resp.get_json()
    inv = data['player']['inventory']
    assert len(inv) == 1
    assert inv[0]['key'] == 'a'

def test_use_item_by_key(client):
    resp = client.post('/api/v1/games', json={'seed': 42})
    game_id = resp.get_json()['game_id']

    store = MemoryStore()
    game_state = store.load(game_id)
    game_state.player.hp = 1
    potion = Item("Potion of Healing", "potion", 6, "Restores 6 HP")
    game_state.player.inventory.append(potion)
    store.save(game_id, game_state)

    resp = client.post(f'/api/v1/games/{game_id}/action', json={'action': 'use_item', 'item_key': 'a'})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True
    assert any('drink' in e for e in data['events'])

def test_use_item_missing_key(client):
    resp = client.post('/api/v1/games', json={'seed': 42})
    game_id = resp.get_json()['game_id']

    resp = client.post(f'/api/v1/games/{game_id}/action', json={'action': 'use_item'})
    assert resp.status_code == 400

def test_perform_action_move(client):
    resp = client.post('/api/v1/games', json={'seed': 42})
    game_id = resp.get_json()['game_id']
    
    resp = client.post(f'/api/v1/games/{game_id}/action', json={'action': 'move', 'direction': 'north'})
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'success' in data
    assert 'events' in data
    assert 'state' in data

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

def test_get_unknown_game(client):
    resp = client.get('/api/v1/games/nonexistent-game-id')
    assert resp.status_code == 404

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
