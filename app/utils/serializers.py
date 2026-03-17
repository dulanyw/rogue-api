import math
from ..core.models import Tile
from ..config import Config

def serialize_item(item):
    return {
        'id': item.id,
        'name': item.name,
        'type': item.type,
        'value': item.value,
        'description': item.description,
    }

def serialize_enemy(enemy):
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

def serialize_player(player):
    result = {
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
        'inventory': [serialize_item(i) for i in player.inventory],
        'equipped_weapon': serialize_item(player.equipped_weapon) if player.equipped_weapon else None,
        'equipped_armor': serialize_item(player.equipped_armor) if player.equipped_armor else None,
        'equipped_rings': [serialize_item(r) for r in player.equipped_rings],
    }
    return result

def serialize_map(game_state, fog_of_war=True):
    vision_radius = Config.VISION_RADIUS
    px, py = game_state.player.position
    
    rows = []
    for y in range(game_state.height):
        row = []
        for x in range(game_state.width):
            dist = math.sqrt((x - px) ** 2 + (y - py) ** 2)
            if fog_of_war and dist > vision_radius:
                row.append(' ')
            else:
                row.append(game_state.map[y][x].value)
        rows.append(''.join(row))
    
    return {
        'rows': rows,
        'width': game_state.width,
        'height': game_state.height,
        'player_position': game_state.player.position,
    }

def serialize_game_state(game_state):
    return {
        'game_id': game_state.game_id,
        'seed': game_state.seed,
        'turn': game_state.turn,
        'dungeon_level': game_state.dungeon_level,
        'status': game_state.status,
        'player': serialize_player(game_state.player),
        'enemies': [serialize_enemy(e) for e in game_state.enemies],
        'items': [serialize_item(i) for i in game_state.items],
        'visible_map': serialize_map(game_state, fog_of_war=Config.FOG_OF_WAR),
        'log': game_state.log,
        'width': game_state.width,
        'height': game_state.height,
    }
