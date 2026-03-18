from app.core.map_gen import generate_map
from app.core.models import Tile

def test_map_dimensions():
    tiles, player_pos, enemy_positions, item_positions = generate_map(80, 24, 42, 1)
    assert len(tiles) == 24
    assert all(len(row) == 80 for row in tiles)

def test_player_spawn_on_floor():
    tiles, player_pos, enemy_positions, item_positions = generate_map(80, 24, 42, 1)
    px, py = player_pos
    assert tiles[py][px] == Tile.FLOOR

def test_stairs_exist():
    tiles, player_pos, enemy_positions, item_positions = generate_map(80, 24, 42, 1)
    found = any(tiles[y][x] == Tile.STAIRS for y in range(24) for x in range(80))
    assert found

def test_same_seed_same_map():
    tiles1, pos1, _, _ = generate_map(80, 24, 99, 1)
    tiles2, pos2, _, _ = generate_map(80, 24, 99, 1)
    assert pos1 == pos2
    assert all(tiles1[y][x] == tiles2[y][x] for y in range(24) for x in range(80))
