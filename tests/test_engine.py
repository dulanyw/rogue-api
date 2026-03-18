import pytest
from app.core.engine import GameEngine
from app.core.models import Tile, Item, Enemy, Player
from app.config import Config

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

def test_descend_action():
    state = engine.create_game(seed=42, player_name="Hero")
    # Place stairs at player position
    px, py = state.player.position
    state.map[py][px] = Tile.STAIRS
    
    initial_level = state.dungeon_level
    success, events, new_state = engine.process_action(state, {'action': 'descend'})
    assert success
    assert new_state.dungeon_level == initial_level + 1

# ---------------------------------------------------------------------------
# Additional engine tests — actions, edge cases, game-over scenarios
# ---------------------------------------------------------------------------

def test_wait_action():
    """Wait action always succeeds and produces a 'You wait.' event."""
    state = engine.create_game(seed=42)
    success, events, new_state = engine.process_action(state, {'action': 'wait'})
    assert success is True
    assert any('wait' in e.lower() for e in events)
    assert new_state.turn == 1

def test_attack_no_enemy():
    """Attacking a direction with no enemy returns success=False."""
    state = engine.create_game(seed=42)
    state.enemies = []
    success, events, _ = engine.process_action(state, {'action': 'attack', 'direction': 'north'})
    assert success is False
    assert any('no enemy' in e.lower() for e in events)

def test_attack_kills_enemy():
    """Attacking an enemy with enough damage marks it as dead and grants XP."""
    state = engine.create_game(seed=42)
    px, py = state.player.position
    state.enemies = []

    weak_enemy = Enemy("Emu", hp=1, attack=0, defense=0, xp_value=5, position=(px + 1, py))
    state.enemies.append(weak_enemy)
    state.map[py][px + 1] = Tile.FLOOR

    initial_xp = state.player.xp
    success, events, new_state = engine.process_action(state, {'action': 'attack', 'direction': 'east'})
    assert success is True
    assert new_state.player.xp > initial_xp
    assert len(new_state.enemies) == 0

def test_pickup_gold():
    """Picking up gold adds to the player's gold and removes the item from the map."""
    state = engine.create_game(seed=42)
    gold_item = Item("Gold", "gold", 30, "Shiny gold coins")
    gold_item.position = list(state.player.position)
    state.items = [gold_item]

    success, events, new_state = engine.process_action(state, {'action': 'pickup'})
    assert success is True
    assert new_state.player.gold >= 30
    assert len(new_state.items) == 0

def test_pickup_nothing():
    """Pickup when no item at player position returns success=False."""
    state = engine.create_game(seed=42)
    state.items = []
    success, events, _ = engine.process_action(state, {'action': 'pickup'})
    assert success is False

def test_pickup_full_inventory():
    """Pickup fails when inventory is at the limit."""
    state = engine.create_game(seed=42)
    # Fill inventory to the limit
    for _ in range(Config.INVENTORY_LIMIT):
        state.player.inventory.append(Item("Sword", "weapon", 3, "Weapon"))

    item = Item("Long Sword", "weapon", 5, "A long sword")
    item.position = list(state.player.position)
    state.items = [item]

    success, events, _ = engine.process_action(state, {'action': 'pickup'})
    assert success is False
    assert any('full' in e.lower() for e in events)

def test_use_item_potion():
    """Using a potion heals the player and removes it from inventory."""
    state = engine.create_game(seed=42)
    state.player.hp = 5
    potion = Item("Potion of Healing", "potion", 6, "Restores 6 HP")
    state.player.inventory.append(potion)

    success, events, new_state = engine.process_action(
        state, {'action': 'use_item', 'item_id': potion.id}
    )
    assert success is True
    assert new_state.player.hp == 11  # 5 + 6
    assert potion not in new_state.player.inventory

def test_use_item_potion_caps_at_max_hp():
    """Using a potion does not exceed max HP."""
    state = engine.create_game(seed=42)
    state.player.hp = state.player.max_hp  # already at max
    potion = Item("Potion of Extra Healing", "potion", 15, "Restores 15 HP")
    state.player.inventory.append(potion)

    success, events, new_state = engine.process_action(
        state, {'action': 'use_item', 'item_id': potion.id}
    )
    assert success is True
    assert new_state.player.hp == new_state.player.max_hp

def test_use_item_not_found():
    """Trying to use a non-existent item_id returns success=False."""
    state = engine.create_game(seed=42)
    success, events, _ = engine.process_action(
        state, {'action': 'use_item', 'item_id': 'ghost-item-id'}
    )
    assert success is False

def test_use_non_potion_item():
    """Using a non-potion item (e.g., weapon) from inventory returns success=False."""
    state = engine.create_game(seed=42)
    sword = Item("Long Sword", "weapon", 5, "A long sword")
    state.player.inventory.append(sword)

    success, events, _ = engine.process_action(
        state, {'action': 'use_item', 'item_id': sword.id}
    )
    assert success is False

def test_don_armor():
    """Equipping armor from inventory puts it in the equipped_armor slot."""
    state = engine.create_game(seed=42)
    armor = Item("Leather Armor", "armor", 2, "Leather armor (+2 defense)")
    state.player.inventory.append(armor)

    success, events, new_state = engine.process_action(
        state, {'action': 'don_armor', 'item_id': armor.id}
    )
    assert success is True
    assert new_state.player.equipped_armor is not None
    assert new_state.player.equipped_armor.id == armor.id
    assert armor not in new_state.player.inventory

def test_don_armor_swaps_existing():
    """Equipping a new armor when one is already equipped swaps them."""
    state = engine.create_game(seed=42)
    old_armor = Item("Ring Mail", "armor", 3, "Ring mail armor")
    new_armor = Item("Chain Mail", "armor", 4, "Chain mail armor")
    state.player.equipped_armor = old_armor
    state.player.inventory.append(new_armor)

    success, events, new_state = engine.process_action(
        state, {'action': 'don_armor', 'item_id': new_armor.id}
    )
    assert success is True
    assert new_state.player.equipped_armor.id == new_armor.id
    assert any(i.id == old_armor.id for i in new_state.player.inventory)

def test_don_armor_not_found():
    """don_armor with an invalid item_id returns success=False."""
    state = engine.create_game(seed=42)
    success, events, _ = engine.process_action(
        state, {'action': 'don_armor', 'item_id': 'bad-id'}
    )
    assert success is False

def test_remove_armor():
    """Removing equipped armor adds it to inventory."""
    state = engine.create_game(seed=42)
    armor = Item("Leather Armor", "armor", 2, "Leather armor")
    state.player.equipped_armor = armor

    success, events, new_state = engine.process_action(state, {'action': 'remove_armor'})
    assert success is True
    assert new_state.player.equipped_armor is None
    assert any(i.id == armor.id for i in new_state.player.inventory)

def test_remove_armor_when_none():
    """Removing armor when none is equipped returns success=False."""
    state = engine.create_game(seed=42)
    assert state.player.equipped_armor is None
    success, events, _ = engine.process_action(state, {'action': 'remove_armor'})
    assert success is False

def test_don_ring():
    """Equipping a ring from inventory adds it to equipped_rings."""
    state = engine.create_game(seed=42)
    ring = Item("Ring of Strength", "ring", 2, "Increases attack by 2")
    state.player.inventory.append(ring)

    success, events, new_state = engine.process_action(
        state, {'action': 'don_ring', 'item_id': ring.id}
    )
    assert success is True
    assert any(r.id == ring.id for r in new_state.player.equipped_rings)
    assert ring not in new_state.player.inventory

def test_don_ring_not_found():
    """don_ring with an invalid item_id returns success=False."""
    state = engine.create_game(seed=42)
    success, events, _ = engine.process_action(
        state, {'action': 'don_ring', 'item_id': 'bad-ring-id'}
    )
    assert success is False

def test_remove_ring():
    """Removing an equipped ring moves it back to inventory."""
    state = engine.create_game(seed=42)
    ring = Item("Ring of Strength", "ring", 2, "Increases attack by 2")
    state.player.equipped_rings.append(ring)

    success, events, new_state = engine.process_action(
        state, {'action': 'remove_ring', 'ring_id': ring.id}
    )
    assert success is True
    assert not any(r.id == ring.id for r in new_state.player.equipped_rings)
    assert any(i.id == ring.id for i in new_state.player.inventory)

def test_remove_ring_not_found():
    """Removing a ring that is not equipped returns success=False."""
    state = engine.create_game(seed=42)
    success, events, _ = engine.process_action(
        state, {'action': 'remove_ring', 'ring_id': 'nonexistent-ring-id'}
    )
    assert success is False

def test_switch_weapon():
    """Switching to a weapon from inventory equips it."""
    state = engine.create_game(seed=42)
    sword = Item("Long Sword", "weapon", 5, "A long sword (+5 attack)")
    state.player.inventory.append(sword)

    success, events, new_state = engine.process_action(
        state, {'action': 'switch_weapon', 'item_id': sword.id}
    )
    assert success is True
    assert new_state.player.equipped_weapon is not None
    assert new_state.player.equipped_weapon.id == sword.id
    assert sword not in new_state.player.inventory

def test_switch_weapon_swaps_existing():
    """Switching weapon when one is already equipped moves old one to inventory."""
    state = engine.create_game(seed=42)
    old_sword = Item("Short Sword", "weapon", 3, "A short sword")
    new_sword = Item("Long Sword", "weapon", 5, "A long sword")
    state.player.equipped_weapon = old_sword
    state.player.inventory.append(new_sword)

    success, events, new_state = engine.process_action(
        state, {'action': 'switch_weapon', 'item_id': new_sword.id}
    )
    assert success is True
    assert new_state.player.equipped_weapon.id == new_sword.id
    assert any(i.id == old_sword.id for i in new_state.player.inventory)

def test_switch_weapon_not_found():
    """switch_weapon with an invalid item_id returns success=False."""
    state = engine.create_game(seed=42)
    success, events, _ = engine.process_action(
        state, {'action': 'switch_weapon', 'item_id': 'bad-weapon-id'}
    )
    assert success is False

def test_player_death():
    """When player HP drops to 0 the game status becomes 'dead'."""
    state = engine.create_game(seed=42)
    px, py = state.player.position
    state.enemies = []

    # Place a powerful enemy that will certainly kill a player with 1 HP
    state.player.hp = 1
    killer = Enemy("Dragon", hp=40, attack=100, defense=0, xp_value=50, position=(px + 1, py))
    state.enemies.append(killer)
    state.map[py][px + 1] = Tile.FLOOR

    # Move into the enemy (triggers combat). The enemy then attacks back.
    _, _, new_state = engine.process_action(state, {'action': 'move', 'direction': 'east'})
    # After the player's attack and the enemy's counter-attack the player should be dead
    # (dragon has 100 attack — even if the player survives the first round, their 1 HP is gone)
    assert new_state.status == 'dead'

def test_descend_not_on_stairs():
    """Descend fails when the player is not on a stairs tile."""
    state = engine.create_game(seed=42)
    px, py = state.player.position
    state.map[py][px] = Tile.FLOOR  # ensure it's floor, not stairs

    success, events, _ = engine.process_action(state, {'action': 'descend'})
    assert success is False
    assert any('stairs' in e.lower() for e in events)

def test_level_up():
    """Killing enemies accumulates XP and triggers level-up."""
    state = engine.create_game(seed=42)
    px, py = state.player.position
    state.enemies = []

    initial_level = state.player.level
    # Give plenty of XP directly to force a level-up
    state.player.xp = state.player.xp_next - 1
    weak_enemy = Enemy("Emu", hp=1, attack=0, defense=0, xp_value=5, position=(px + 1, py))
    state.enemies.append(weak_enemy)
    state.map[py][px + 1] = Tile.FLOOR

    _, _, new_state = engine.process_action(state, {'action': 'attack', 'direction': 'east'})
    assert new_state.player.level > initial_level

def test_process_action_dead_game():
    """process_action on an already-dead game state returns success=False."""
    state = engine.create_game(seed=42)
    state.status = 'dead'
    success, events, returned_state = engine.process_action(state, {'action': 'wait'})
    assert success is False
    assert returned_state.status == 'dead'

def test_move_out_of_bounds():
    """Moving into a boundary outside the map is blocked."""
    state = engine.create_game(seed=42)
    # Place player at top-left corner and try to move north/west
    state.player.position = [0, 0]
    state.map[0][0] = Tile.FLOOR

    success_n, events_n, new_state_n = engine.process_action(state, {'action': 'move', 'direction': 'north'})
    assert new_state_n.player.position[1] >= 0  # did not go negative

    state.player.position = [0, 0]
    success_w, events_w, new_state_w = engine.process_action(state, {'action': 'move', 'direction': 'west'})
    assert new_state_w.player.position[0] >= 0

def test_enemy_ai_attacks_adjacent_player():
    """An enemy adjacent to the player should attack during the enemy turn."""
    state = engine.create_game(seed=42)
    px, py = state.player.position
    state.enemies = []

    # Place a powerful enemy adjacent to the player
    attacker = Enemy("Dragon", hp=40, attack=50, defense=0, xp_value=50, position=(px + 1, py))
    state.enemies.append(attacker)
    state.map[py][px + 1] = Tile.FLOOR

    initial_hp = state.player.hp
    # Wait so no player action removes the enemy; enemy AI fires
    _, events, new_state = engine.process_action(state, {'action': 'wait'})
    # Dragon has 50 attack vs player 1 defense → 49 damage. Player should have taken damage.
    assert new_state.player.hp < initial_hp
