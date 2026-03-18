from flask import Blueprint, request, jsonify
from ..core.engine import GameEngine
from ..storage.db_store import SQLiteStore
from ..utils.serializers import serialize_game_state
from ..utils.validators import validate_action

bp = Blueprint('api', __name__, url_prefix='/api/v1')
engine = GameEngine()
store = SQLiteStore()

@bp.route('/games', methods=['POST'])
def create_game():
    data = request.get_json(silent=True) or {}
    seed = data.get('seed')
    player_name = data.get('player_name', 'Player')
    
    game_state = engine.create_game(seed=seed, player_name=player_name)
    store.save(game_state.game_id, game_state)
    
    return jsonify({
        'game_id': game_state.game_id,
        'state': serialize_game_state(game_state),
    }), 201

@bp.route('/games/<game_id>', methods=['GET'])
def get_game(game_id):
    game_state = store.load(game_id)
    if game_state is None:
        return jsonify({'error': 'Game not found.'}), 404
    
    serialized = serialize_game_state(game_state)
    return jsonify({
        'game_id': game_state.game_id,
        'turn': game_state.turn,
        'player': serialized['player'],
        'visible_map': serialized['visible_map'],
        'log': game_state.log,
        'status': game_state.status,
    })

@bp.route('/games/<game_id>/action', methods=['POST'])
def perform_action(game_id):
    game_state = store.load(game_id)
    if game_state is None:
        return jsonify({'error': 'Game not found.'}), 404
    
    if game_state.status != 'ongoing':
        return jsonify({'error': 'Game is over.'}), 409
    
    action_data = request.get_json(silent=True) or {}
    is_valid, error_msg = validate_action(action_data)
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    success, events, updated_state = engine.process_action(game_state, action_data)
    store.save(game_id, updated_state)
    
    return jsonify({
        'success': success,
        'events': events,
        'state': serialize_game_state(updated_state),
    })

@bp.route('/games/<game_id>', methods=['DELETE'])
def delete_game(game_id):
    if not store.exists(game_id):
        return jsonify({'error': 'Game not found.'}), 404
    
    store.delete(game_id)
    return jsonify({'deleted': True})
