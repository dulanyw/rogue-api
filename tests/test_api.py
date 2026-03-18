import pytest
import json
import tempfile
import os
from app.app import create_app
from app.storage.db_store import SQLiteStore

@pytest.fixture
def client():
    # Use a temporary database file for test isolation
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(db_fd)
    SQLiteStore().init_db(db_path)
    app = create_app({'TESTING': True})
    store = SQLiteStore()
    store.clear()
    with app.test_client() as c:
        yield c
    os.unlink(db_path)

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
    store = SQLiteStore()
    game_state = store.load(game_id)
    game_state.status = 'dead'
    store.save(game_id, game_state)
    
    resp = client.post(f'/api/v1/games/{game_id}/action', json={'action': 'move', 'direction': 'north'})
    assert resp.status_code == 409
