import json
from ..core.models import GameState, Player, Enemy, Item, Tile


def _item_to_dict(item):
    return {
        'id': item.id,
        'name': item.name,
        'type': item.type,
        'value': item.value,
        'description': item.description,
        'position': getattr(item, 'position', None),
    }


def _dict_to_item(d):
    if d is None:
        return None
    item = Item(name=d['name'], item_type=d['type'], value=d['value'], description=d['description'])
    item.id = d['id']
    if d.get('position') is not None:
        item.position = d['position']
    return item


def _enemy_to_dict(enemy):
    return {
        'id': enemy.id,
        'name': enemy.name,
        'hp': enemy.hp,
        'max_hp': enemy.max_hp,
        'attack': enemy.attack,
        'defense': enemy.defense,
        'position': enemy.position,
        'is_alive': enemy.is_alive,
        'xp_value': enemy.xp_value,
    }


def _dict_to_enemy(d):
    enemy = Enemy(
        name=d['name'],
        hp=d['max_hp'],
        attack=d['attack'],
        defense=d['defense'],
        xp_value=d['xp_value'],
        position=tuple(d['position']),
    )
    enemy.id = d['id']
    enemy.hp = d['hp']
    enemy.is_alive = d['is_alive']
    return enemy


def _player_to_dict(player):
    return {
        'name': player.name,
        'hp': player.hp,
        'max_hp': player.max_hp,
        'attack': player.attack,
        'defense': player.defense,
        'position': player.position,
        'level': player.level,
        'xp': player.xp,
        'xp_next': player.xp_next,
        'gold': player.gold,
        'inventory': [_item_to_dict(i) for i in player.inventory],
        'equipped_weapon': _item_to_dict(player.equipped_weapon) if player.equipped_weapon else None,
        'equipped_armor': _item_to_dict(player.equipped_armor) if player.equipped_armor else None,
        'equipped_rings': [_item_to_dict(r) for r in player.equipped_rings],
    }


def _dict_to_player(d):
    player = Player(name=d['name'])
    player.hp = d['hp']
    player.max_hp = d['max_hp']
    player.attack = d['attack']
    player.defense = d['defense']
    player.position = d['position']
    player.level = d['level']
    player.xp = d['xp']
    player.xp_next = d['xp_next']
    player.gold = d['gold']
    player.inventory = [_dict_to_item(i) for i in d['inventory']]
    player.equipped_weapon = _dict_to_item(d['equipped_weapon'])
    player.equipped_armor = _dict_to_item(d['equipped_armor'])
    player.equipped_rings = [_dict_to_item(r) for r in d['equipped_rings']]
    return player


def serialize_state(game_state):
    """Serialize a GameState to a JSON string for database storage."""
    map_data = [[tile.value for tile in row] for row in game_state.map]
    state_dict = {
        'game_id': game_state.game_id,
        'seed': game_state.seed,
        'turn': game_state.turn,
        'dungeon_level': game_state.dungeon_level,
        'status': game_state.status,
        'width': game_state.width,
        'height': game_state.height,
        'log': game_state.log,
        'player': _player_to_dict(game_state.player),
        'enemies': [_enemy_to_dict(e) for e in game_state.enemies],
        'items': [_item_to_dict(i) for i in game_state.items],
        'map': map_data,
    }
    return json.dumps(state_dict)


def deserialize_state(json_str):
    """Deserialize a JSON string back to a GameState object."""
    data = json.loads(json_str)
    map_data = [[Tile(cell) for cell in row] for row in data['map']]
    game_state = GameState(
        game_id=data['game_id'],
        seed=data['seed'],
        player=_dict_to_player(data['player']),
        enemies=[_dict_to_enemy(e) for e in data['enemies']],
        items=[_dict_to_item(i) for i in data['items']],
        dungeon_level=data['dungeon_level'],
        map_tiles=map_data,
        width=data['width'],
        height=data['height'],
    )
    game_state.turn = data['turn']
    game_state.status = data['status']
    game_state.log = data['log']
    return game_state
