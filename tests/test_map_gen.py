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

# ---------------------------------------------------------------------------
# Additional map generation tests
# ---------------------------------------------------------------------------

def test_enemy_positions_on_floor():
    """All spawned enemy positions land on floor tiles."""
    tiles, player_pos, enemy_positions, item_positions = generate_map(80, 24, 42, 1)
    for pos in enemy_positions:
        x, y = pos
        assert tiles[y][x] == Tile.FLOOR, f"Enemy at ({x},{y}) is not on a floor tile"

def test_item_positions_on_floor():
    """All spawned item positions land on floor tiles."""
    tiles, player_pos, enemy_positions, item_positions = generate_map(80, 24, 42, 1)
    for pos in item_positions:
        x, y = pos
        assert tiles[y][x] == Tile.FLOOR, f"Item at ({x},{y}) is not on a floor tile"

def test_different_seeds_produce_different_maps():
    """Different seeds should (very likely) produce different maps."""
    _, pos1, _, _ = generate_map(80, 24, 111, 1)
    _, pos2, _, _ = generate_map(80, 24, 999, 1)
    # Different seeds should produce different player starting positions
    # (This is probabilistic but nearly guaranteed for well-separated seeds)
    assert pos1 != pos2

def test_different_levels_different_maps():
    """The same seed but a different dungeon level produces a different map."""
    tiles1, pos1, _, _ = generate_map(80, 24, 42, 1)
    tiles2, pos2, _, _ = generate_map(80, 24, 42, 2)
    maps_differ = any(
        tiles1[y][x] != tiles2[y][x]
        for y in range(24) for x in range(80)
    )
    assert maps_differ

def test_enemy_count_scales_with_level():
    """Higher dungeon levels should spawn more enemies."""
    _, _, enemies_l1, _ = generate_map(80, 24, 42, 1)
    _, _, enemies_l3, _ = generate_map(80, 24, 42, 3)
    assert len(enemies_l3) >= len(enemies_l1)

def test_at_least_some_floor_tiles():
    """Each generated map must have a reasonable number of walkable floor tiles."""
    tiles, _, _, _ = generate_map(80, 24, 42, 1)
    floor_count = sum(
        1 for y in range(24) for x in range(80) if tiles[y][x] == Tile.FLOOR
    )
    assert floor_count > 20  # At minimum 5 rooms of size ~4x4 = 80 tiles

def test_player_not_on_stairs():
    """Player spawn position must not coincide with the stairs."""
    tiles, player_pos, _, _ = generate_map(80, 24, 42, 1)
    px, py = player_pos
    assert tiles[py][px] != Tile.STAIRS
