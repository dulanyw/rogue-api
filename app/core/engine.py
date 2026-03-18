import uuid
import random
from .models import GameState, Player, Enemy, Item, Tile
from .map_gen import generate_map
from .combat import resolve_combat

ENEMY_TYPES = [
    # (name, hp, attack, defense, xp_value, min_level)
    ("Emu", 3, 2, 0, 2, 1),
    ("Bat", 4, 2, 1, 3, 1),
    ("Kestrel", 4, 3, 1, 3, 1),
    ("Snake", 6, 3, 1, 5, 1),
    ("Hobgoblin", 10, 4, 2, 8, 2),
    ("Orc", 12, 5, 2, 10, 2),
    ("Zombie", 14, 5, 3, 12, 3),
    ("Aquator", 15, 6, 3, 14, 3),
    ("Centaur", 18, 7, 4, 18, 4),
    ("Griffin", 22, 9, 5, 25, 5),
    ("Troll", 24, 10, 5, 28, 5),
    ("Ogre", 26, 10, 6, 30, 6),
    ("Dragon", 40, 15, 8, 50, 8),
]

ITEM_TYPES = [
    ("Potion of Healing", "potion", 6, "Restores 6 HP"),
    ("Potion of Extra Healing", "potion", 15, "Restores 15 HP"),
    ("Short Sword", "weapon", 3, "A short sword (+3 attack)"),
    ("Long Sword", "weapon", 5, "A long sword (+5 attack)"),
    ("Mace", "weapon", 4, "A heavy mace (+4 attack)"),
    ("Ring Mail", "armor", 3, "Ring mail armor (+3 defense)"),
    ("Leather Armor", "armor", 2, "Leather armor (+2 defense)"),
    ("Chain Mail", "armor", 4, "Chain mail armor (+4 defense)"),
    ("Ring of Strength", "ring", 2, "Increases attack by 2"),
    ("Gold", "gold", 0, "Shiny gold coins"),
]

class GameEngine:
    def create_game(self, seed=None, player_name="Player"):
        if seed is None:
            seed = random.randint(0, 999999)
        
        game_id = str(uuid.uuid4())
        rng = random.Random(seed)
        
        dungeon_level = 1
        from ..config import Config
        width = Config.MAP_WIDTH
        height = Config.MAP_HEIGHT
        
        tiles, player_pos, enemy_positions, item_positions = generate_map(width, height, seed, dungeon_level)
        
        player = Player(name=player_name)
        player.position = player_pos[:]
        
        enemies = self._spawn_enemies(enemy_positions, dungeon_level, rng)
        items = self._spawn_items(item_positions, rng)
        
        state = GameState(
            game_id=game_id,
            seed=seed,
            player=player,
            enemies=enemies,
            items=items,
            dungeon_level=dungeon_level,
            map_tiles=tiles,
            width=width,
            height=height,
        )
        state.log.append(f"Welcome, {player_name}! The dungeon awaits.")
        return state

    def _spawn_enemies(self, positions, dungeon_level, rng):
        eligible = [e for e in ENEMY_TYPES if e[5] <= dungeon_level]
        if not eligible:
            eligible = ENEMY_TYPES[:3]
        
        enemies = []
        for pos in positions:
            etype = rng.choice(eligible)
            name, base_hp, base_atk, base_def, xp, _ = etype
            # Scale with level
            hp = base_hp + (dungeon_level - 1) * 2
            atk = base_atk + (dungeon_level - 1)
            e = Enemy(name=name, hp=hp, attack=atk, defense=base_def, xp_value=xp, position=pos)
            enemies.append(e)
        return enemies

    def _spawn_items(self, positions, rng):
        items = []
        for pos in positions:
            itype = rng.choice(ITEM_TYPES)
            name, type_, value, desc = itype
            item = Item(name=name, item_type=type_, value=value, description=desc)
            item.position = list(pos)
            items.append(item)
        return items

    def process_action(self, game_state, action_data):
        if game_state.status != 'ongoing':
            return False, ["Game is over."], game_state
        
        action = action_data.get('action')
        events = []
        success = True
        
        if action == 'move':
            success, action_events = self._handle_move(game_state, action_data)
            events.extend(action_events)
        elif action == 'attack':
            success, action_events = self._handle_attack(game_state, action_data)
            events.extend(action_events)
        elif action == 'pickup':
            success, action_events = self._handle_pickup(game_state)
            events.extend(action_events)
        elif action == 'use_item':
            success, action_events = self._handle_use_item(game_state, action_data)
            events.extend(action_events)
        elif action == 'descend':
            success, action_events = self._handle_descend(game_state)
            events.extend(action_events)
        elif action == 'wait':
            events.append("You wait.")
        elif action == 'remove_armor':
            success, action_events = self._handle_remove_armor(game_state)
            events.extend(action_events)
        elif action == 'don_armor':
            success, action_events = self._handle_don_armor(game_state, action_data)
            events.extend(action_events)
        elif action == 'remove_ring':
            success, action_events = self._handle_remove_ring(game_state, action_data)
            events.extend(action_events)
        elif action == 'don_ring':
            success, action_events = self._handle_don_ring(game_state, action_data)
            events.extend(action_events)
        elif action == 'switch_weapon':
            success, action_events = self._handle_switch_weapon(game_state, action_data)
            events.extend(action_events)
        
        if game_state.status == 'ongoing':
            enemy_events = self._enemy_turn(game_state)
            events.extend(enemy_events)
        
        game_state.turn += 1
        game_state.log.extend(events)
        
        return success, events, game_state

    def _direction_to_delta(self, direction):
        return {
            'north': (0, -1),
            'south': (0, 1),
            'east': (1, 0),
            'west': (-1, 0),
        }.get(direction, (0, 0))

    def _handle_move(self, game_state, action_data):
        direction = action_data.get('direction', '')
        dx, dy = self._direction_to_delta(direction)
        
        px, py = game_state.player.position
        nx, ny = px + dx, py + dy
        
        # Bounds check
        if not (0 <= nx < game_state.width and 0 <= ny < game_state.height):
            return False, ["You can't move there."]
        
        tile = game_state.map[ny][nx]
        if tile == Tile.WALL or tile == Tile.EMPTY:
            return False, ["You bump into a wall."]
        
        # Check for enemy
        for enemy in game_state.enemies:
            if enemy.is_alive and enemy.position == [nx, ny]:
                damage, combat_events = resolve_combat(game_state.player, enemy)
                if not enemy.is_alive:
                    game_state.enemies = [e for e in game_state.enemies if e.is_alive]
                    xp_gain = enemy.xp_value
                    game_state.player.xp += xp_gain
                    combat_events.append(f"You gain {xp_gain} XP.")
                    self._check_level_up(game_state)
                return True, combat_events
        
        game_state.player.position = [nx, ny]
        return True, [f"You move {direction}."]

    def _handle_attack(self, game_state, action_data):
        direction = action_data.get('direction', '')
        dx, dy = self._direction_to_delta(direction)
        px, py = game_state.player.position
        nx, ny = px + dx, py + dy
        
        for enemy in game_state.enemies:
            if enemy.is_alive and enemy.position == [nx, ny]:
                damage, combat_events = resolve_combat(game_state.player, enemy)
                if not enemy.is_alive:
                    game_state.enemies = [e for e in game_state.enemies if e.is_alive]
                    xp_gain = enemy.xp_value
                    game_state.player.xp += xp_gain
                    combat_events.append(f"You gain {xp_gain} XP.")
                    self._check_level_up(game_state)
                return True, combat_events
        
        return False, ["No enemy there."]

    def _handle_pickup(self, game_state):
        player_pos = game_state.player.position
        for item in game_state.items:
            if hasattr(item, 'position') and item.position == player_pos:
                if item.type == 'gold':
                    gold = item.value if item.value > 0 else random.randint(10, 50)
                    game_state.player.gold += gold
                    game_state.items.remove(item)
                    return True, [f"You pick up {gold} gold pieces."]
                
                from ..config import Config
                if len(game_state.player.inventory) >= Config.INVENTORY_LIMIT:
                    return False, ["Your inventory is full."]
                
                game_state.player.inventory.append(item)
                game_state.items.remove(item)
                return True, [f"You pick up {item.name}."]
        
        return False, ["Nothing to pick up here."]

    def _handle_use_item(self, game_state, action_data):
        item_id = action_data.get('item_id')
        for item in game_state.player.inventory:
            if item.id == item_id:
                if item.type == 'potion':
                    heal = item.value
                    game_state.player.hp = min(game_state.player.max_hp, game_state.player.hp + heal)
                    game_state.player.inventory.remove(item)
                    return True, [f"You drink {item.name} and recover {heal} HP."]
                else:
                    return False, ["You can't use that item directly."]
        return False, ["Item not found in inventory."]

    def _handle_descend(self, game_state):
        px, py = game_state.player.position
        if game_state.map[py][px] != Tile.STAIRS:
            return False, ["There are no stairs here."]
        
        game_state.dungeon_level += 1
        rng = random.Random(game_state.seed + game_state.dungeon_level)
        
        from ..config import Config
        tiles, player_pos, enemy_positions, item_positions = generate_map(
            Config.MAP_WIDTH, Config.MAP_HEIGHT, game_state.seed, game_state.dungeon_level
        )
        
        game_state.map = tiles
        game_state.width = Config.MAP_WIDTH
        game_state.height = Config.MAP_HEIGHT
        game_state.player.position = player_pos[:]
        game_state.enemies = self._spawn_enemies(enemy_positions, game_state.dungeon_level, rng)
        game_state.items = self._spawn_items(item_positions, rng)
        
        return True, [f"You descend to dungeon level {game_state.dungeon_level}."]

    def _handle_remove_armor(self, game_state):
        if game_state.player.equipped_armor is None:
            return False, ["You're not wearing any armor."]
        armor = game_state.player.equipped_armor
        game_state.player.equipped_armor = None
        game_state.player.inventory.append(armor)
        return True, [f"You remove {armor.name}."]

    def _handle_don_armor(self, game_state, action_data):
        item_id = action_data.get('item_id')
        for item in game_state.player.inventory:
            if item.id == item_id and item.type == 'armor':
                if game_state.player.equipped_armor:
                    game_state.player.inventory.append(game_state.player.equipped_armor)
                game_state.player.inventory.remove(item)
                game_state.player.equipped_armor = item
                return True, [f"You put on {item.name}."]
        return False, ["Armor not found."]

    def _handle_remove_ring(self, game_state, action_data):
        ring_id = action_data.get('ring_id')
        for ring in game_state.player.equipped_rings:
            if ring.id == ring_id:
                game_state.player.equipped_rings.remove(ring)
                game_state.player.inventory.append(ring)
                return True, [f"You remove {ring.name}."]
        return False, ["Ring not found."]

    def _handle_don_ring(self, game_state, action_data):
        item_id = action_data.get('item_id')
        for item in game_state.player.inventory:
            if item.id == item_id and item.type == 'ring':
                game_state.player.inventory.remove(item)
                game_state.player.equipped_rings.append(item)
                return True, [f"You put on {item.name}."]
        return False, ["Ring not found."]

    def _handle_switch_weapon(self, game_state, action_data):
        item_id = action_data.get('item_id')
        for item in game_state.player.inventory:
            if item.id == item_id and item.type == 'weapon':
                if game_state.player.equipped_weapon:
                    game_state.player.inventory.append(game_state.player.equipped_weapon)
                game_state.player.inventory.remove(item)
                game_state.player.equipped_weapon = item
                return True, [f"You wield {item.name}."]
        return False, ["Weapon not found."]

    def _enemy_turn(self, game_state):
        events = []
        player = game_state.player
        
        for enemy in game_state.enemies:
            if not enemy.is_alive:
                continue
            
            ex, ey = enemy.position
            px, py = player.position
            
            # Adjacent to player?
            if abs(ex - px) <= 1 and abs(ey - py) <= 1 and (ex != px or ey != py):
                damage, combat_events = resolve_combat(enemy, player)
                events.extend(combat_events)
                if player.hp <= 0:
                    game_state.status = 'dead'
                    events.append("You have died!")
                    return events
            else:
                # Move toward player
                dx = 0 if ex == px else (1 if px > ex else -1)
                dy = 0 if ey == py else (1 if py > ey else -1)
                
                # Try to move
                nx, ny = ex + dx, ey + dy
                if self._can_move_to(game_state, nx, ny):
                    enemy.position = [nx, ny]
                else:
                    # Try horizontal or vertical only
                    if dx != 0 and self._can_move_to(game_state, ex + dx, ey):
                        enemy.position = [ex + dx, ey]
                    elif dy != 0 and self._can_move_to(game_state, ex, ey + dy):
                        enemy.position = [ex, ey + dy]
        
        return events

    def _can_move_to(self, game_state, x, y):
        if not (0 <= x < game_state.width and 0 <= y < game_state.height):
            return False
        tile = game_state.map[y][x]
        if tile in (Tile.WALL, Tile.EMPTY):
            return False
        # Check no other enemy at position
        for e in game_state.enemies:
            if e.is_alive and e.position == [x, y]:
                return False
        # Don't move onto player
        if game_state.player.position == [x, y]:
            return False
        return True

    def _check_level_up(self, game_state):
        player = game_state.player
        while player.xp >= player.xp_next:
            player.level += 1
            player.xp -= player.xp_next
            player.xp_next = int(player.xp_next * 1.5)
            player.max_hp += 4
            player.hp = min(player.hp + 4, player.max_hp)
            player.attack += 1
            game_state.log.append(f"You advance to level {player.level}!")
