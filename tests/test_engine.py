import pytest
from app.core.engine import GameEngine
from app.core.models import Tile, Item, Enemy

engine = GameEngine()

def test_create_game():
    state = engine.create_game(seed=42, player_name="Hero")
    assert state is not None
    assert state.game_id is not None
    assert state.player.name == "Hero"
    assert state.dungeon_level == 1
    assert state.status == 'ongoing'
    assert state.map is not None

def test_move_updates_position():
    state = engine.create_game(seed=42, player_name="Hero")
    px, py = state.player.position
    
    # Find a direction we can move
    directions = [('east', 1, 0), ('west', -1, 0), ('south', 0, 1), ('north', 0, -1)]
    moved = False
    for direction, dx, dy in directions:
        nx, ny = px + dx, py + dy
        if (0 <= nx < state.width and 0 <= ny < state.height and
                state.map[ny][nx] in (Tile.FLOOR, Tile.STAIRS)):
            # Make sure no enemy there
            enemy_there = any(e.position == [nx, ny] and e.is_alive for e in state.enemies)
            if not enemy_there:
                success, events, new_state = engine.process_action(state, {'action': 'move', 'direction': direction})
                if success:
                    assert new_state.player.position == [nx, ny]
                    moved = True
                    break
    assert moved, "Player should be able to move in at least one direction"

def test_move_into_wall_blocked():
    state = engine.create_game(seed=42, player_name="Hero")
    
    # Find a wall adjacent to the player
    px, py = state.player.position
    directions = [('east', 1, 0), ('west', -1, 0), ('south', 0, 1), ('north', 0, -1)]
    blocked = False
    for direction, dx, dy in directions:
        nx, ny = px + dx, py + dy
        if (0 <= nx < state.width and 0 <= ny < state.height and
                state.map[ny][nx] == Tile.WALL):
            success, events, new_state = engine.process_action(state, {'action': 'move', 'direction': direction})
            assert not success or new_state.player.position == [px, py]
            blocked = True
            break
    
    # If no wall adjacent, manually place player next to wall
    if not blocked:
        # Find a wall tile
        for y in range(state.height):
            for x in range(state.width):
                if state.map[y][x] == Tile.WALL:
                    # Try to find a floor tile adjacent
                    # Map from (floor_x, floor_y) relative to wall (x, y) to direction
                    # If floor is at (x+1, y), moving 'west' from floor hits wall at (x, y)
                    # If floor is at (x-1, y), moving 'east' from floor hits wall at (x, y)
                    # If floor is at (x, y+1), moving 'north' from floor hits wall at (x, y)
                    # If floor is at (x, y-1), moving 'south' from floor hits wall at (x, y)
                    adjacents = [
                        (x + 1, y, 'west'),   # floor east of wall -> move west into wall
                        (x - 1, y, 'east'),   # floor west of wall -> move east into wall
                        (x, y + 1, 'north'),  # floor south of wall -> move north into wall
                        (x, y - 1, 'south'),  # floor north of wall -> move south into wall
                    ]
                    for fx, fy, dir_name in adjacents:
                        if (0 <= fx < state.width and 0 <= fy < state.height and
                                state.map[fy][fx] == Tile.FLOOR):
                            state.player.position = [fx, fy]
                            success, events, new_state = engine.process_action(
                                state, {'action': 'move', 'direction': dir_name}
                            )
                            assert new_state.player.position != [x, y]
                            blocked = True
                            break
                    if blocked:
                        break
            if blocked:
                break
    
    assert blocked

def test_pickup_item():
    state = engine.create_game(seed=42, player_name="Hero")
    # Place an item at player position
    item = Item("Test Potion", "potion", 6, "Test")
    item.position = list(state.player.position)
    state.items.append(item)
    
    initial_inv_size = len(state.player.inventory)
    success, events, new_state = engine.process_action(state, {'action': 'pickup'})
    assert success
    assert len(new_state.player.inventory) == initial_inv_size + 1

def test_combat_moving_into_enemy():
    state = engine.create_game(seed=42, player_name="Hero")
    px, py = state.player.position
    
    # Clear existing enemies
    state.enemies = []
    
    # Place enemy east of player
    enemy = Enemy("TestBat", hp=5, attack=1, defense=0, xp_value=3, position=(px + 1, py))
    state.enemies.append(enemy)
    state.map[py][px + 1] = Tile.FLOOR  # Ensure floor tile
    
    success, events, new_state = engine.process_action(state, {'action': 'move', 'direction': 'east'})
    assert success
    # Either enemy is dead or took damage
    assert any("hits" in e or "misses" in e or "defeated" in e for e in events)

def test_use_item_by_key():
    state = engine.create_game(seed=42, player_name="Hero")
    state.player.hp = 1
    potion = Item("Potion of Healing", "potion", 6, "Restores HP")
    potion.position = list(state.player.position)
    state.items.append(potion)

    # Pick up the potion so it gets an inventory key
    engine.process_action(state, {'action': 'pickup'})
    assert len(state.player.inventory) >= 1

    hp_before = state.player.hp
    success, events, new_state = engine.process_action(state, {'action': 'use_item', 'item_key': 'a'})
    assert success
    assert new_state.player.hp > hp_before

def test_switch_weapon_by_key():
    state = engine.create_game(seed=42, player_name="Hero")
    sword = Item("Short Sword", "weapon", 3, "A short sword")
    state.player.inventory.append(sword)

    success, events, new_state = engine.process_action(state, {'action': 'switch_weapon', 'item_key': 'a'})
    assert success
    assert new_state.player.equipped_weapon is not None
    assert new_state.player.equipped_weapon.name == "Short Sword"

def test_don_and_remove_ring_by_key():
    state = engine.create_game(seed=42, player_name="Hero")
    ring = Item("Ring of Strength", "ring", 2, "Increases attack")
    state.player.inventory.append(ring)

    success, events, new_state = engine.process_action(state, {'action': 'don_ring', 'item_key': 'a'})
    assert success
    assert len(new_state.player.equipped_rings) == 1

    success, events, new_state = engine.process_action(new_state, {'action': 'remove_ring', 'ring_key': 'a'})
    assert success
    assert len(new_state.player.equipped_rings) == 0

def test_don_armor_by_key():
    state = engine.create_game(seed=42, player_name="Hero")
    armor = Item("Leather Armor", "armor", 2, "Leather armor")
    state.player.inventory.append(armor)

    success, events, new_state = engine.process_action(state, {'action': 'don_armor', 'item_key': 'a'})
    assert success
    assert new_state.player.equipped_armor is not None
    assert new_state.player.equipped_armor.name == "Leather Armor"

def test_invalid_item_key_returns_failure():
    state = engine.create_game(seed=42, player_name="Hero")
    success, events, new_state = engine.process_action(state, {'action': 'use_item', 'item_key': 'a'})
    assert not success
    assert any("not found" in e.lower() for e in events)

def test_descend_action():
    state = engine.create_game(seed=42, player_name="Hero")
    # Place stairs at player position
    px, py = state.player.position
    state.map[py][px] = Tile.STAIRS
    
    initial_level = state.dungeon_level
    success, events, new_state = engine.process_action(state, {'action': 'descend'})
    assert success
    assert new_state.dungeon_level == initial_level + 1
