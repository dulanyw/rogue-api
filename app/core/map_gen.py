import random
from .models import Tile

def generate_map(width, height, seed, level):
    rng = random.Random(seed + level * 1000)
    
    # Initialize map with walls
    tiles = [[Tile.WALL for _ in range(width)] for _ in range(height)]
    
    rooms = []
    attempts = 0
    while len(rooms) < 5 and attempts < 200:
        attempts += 1
        w = rng.randint(4, 8)
        h = rng.randint(4, 8)
        x = rng.randint(1, width - w - 1)
        y = rng.randint(1, height - h - 1)
        
        # Check overlap with padding
        overlap = False
        for rx, ry, rw, rh in rooms:
            if (x < rx + rw + 1 and x + w + 1 > rx and
                    y < ry + rh + 1 and y + h + 1 > ry):
                overlap = True
                break
        
        if not overlap:
            rooms.append((x, y, w, h))
            # Carve room
            for dy in range(h):
                for dx in range(w):
                    tiles[y + dy][x + dx] = Tile.FLOOR
    
    # Connect rooms with L-shaped corridors
    for i in range(1, len(rooms)):
        x1, y1, w1, h1 = rooms[i - 1]
        x2, y2, w2, h2 = rooms[i]
        cx1 = x1 + w1 // 2
        cy1 = y1 + h1 // 2
        cx2 = x2 + w2 // 2
        cy2 = y2 + h2 // 2
        
        # Horizontal then vertical
        if rng.random() < 0.5:
            for x in range(min(cx1, cx2), max(cx1, cx2) + 1):
                tiles[cy1][x] = Tile.FLOOR
            for y in range(min(cy1, cy2), max(cy1, cy2) + 1):
                tiles[y][cx2] = Tile.FLOOR
        else:
            for y in range(min(cy1, cy2), max(cy1, cy2) + 1):
                tiles[y][cx1] = Tile.FLOOR
            for x in range(min(cx1, cx2), max(cx1, cx2) + 1):
                tiles[cy2][x] = Tile.FLOOR
    
    # Place stairs in last room
    last_room = rooms[-1]
    sx = last_room[0] + last_room[2] // 2
    sy = last_room[1] + last_room[3] // 2
    tiles[sy][sx] = Tile.STAIRS
    
    # Player starts in center of first room
    first_room = rooms[0]
    player_pos = [first_room[0] + first_room[2] // 2, first_room[1] + first_room[3] // 2]
    
    # Collect floor positions (exclude player start and stairs)
    floor_positions = []
    for y in range(height):
        for x in range(width):
            if tiles[y][x] == Tile.FLOOR:
                if [x, y] != player_pos:
                    floor_positions.append([x, y])
    
    rng.shuffle(floor_positions)
    
    # Spawn enemies: 3-5 for level 1, +1-2 per additional level
    base_enemies = 3 + (level - 1) * 2
    num_enemies = rng.randint(base_enemies, base_enemies + 2)
    num_enemies = min(num_enemies, len(floor_positions) // 2)
    
    enemy_positions = floor_positions[:num_enemies]
    
    # Spawn items: 2-4 per level
    num_items = rng.randint(2, 4)
    num_items = min(num_items, len(floor_positions) - num_enemies)
    item_positions = floor_positions[num_enemies:num_enemies + num_items]
    
    return tiles, player_pos, enemy_positions, item_positions
