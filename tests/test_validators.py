"""
Comprehensive tests for app/utils/validators.py — all valid and invalid
action payloads.
"""
import pytest
from app.utils.validators import validate_action

# ---------------------------------------------------------------------------
# Valid actions — each should return (True, None)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("direction", ["north", "south", "east", "west"])
def test_valid_move(direction):
    valid, error = validate_action({'action': 'move', 'direction': direction})
    assert valid is True
    assert error is None

@pytest.mark.parametrize("direction", ["north", "south", "east", "west"])
def test_valid_attack(direction):
    valid, error = validate_action({'action': 'attack', 'direction': direction})
    assert valid is True
    assert error is None

def test_valid_wait():
    valid, error = validate_action({'action': 'wait'})
    assert valid is True
    assert error is None

def test_valid_pickup():
    valid, error = validate_action({'action': 'pickup'})
    assert valid is True
    assert error is None

def test_valid_descend():
    valid, error = validate_action({'action': 'descend'})
    assert valid is True
    assert error is None

def test_valid_use_item():
    valid, error = validate_action({'action': 'use_item', 'item_id': 'some-uuid'})
    assert valid is True
    assert error is None

def test_valid_remove_armor():
    valid, error = validate_action({'action': 'remove_armor'})
    assert valid is True
    assert error is None

def test_valid_don_armor():
    valid, error = validate_action({'action': 'don_armor', 'item_id': 'some-uuid'})
    assert valid is True
    assert error is None

def test_valid_remove_ring():
    valid, error = validate_action({'action': 'remove_ring', 'ring_id': 'some-uuid'})
    assert valid is True
    assert error is None

def test_valid_don_ring():
    valid, error = validate_action({'action': 'don_ring', 'item_id': 'some-uuid'})
    assert valid is True
    assert error is None

def test_valid_switch_weapon():
    valid, error = validate_action({'action': 'switch_weapon', 'item_id': 'some-uuid'})
    assert valid is True
    assert error is None

# ---------------------------------------------------------------------------
# Invalid: missing or unknown 'action' field
# ---------------------------------------------------------------------------

def test_invalid_missing_action():
    valid, error = validate_action({'direction': 'north'})
    assert valid is False
    assert error is not None
    assert 'action' in error.lower()

def test_invalid_empty_dict():
    valid, error = validate_action({})
    assert valid is False
    assert error is not None

def test_invalid_unknown_action():
    valid, error = validate_action({'action': 'cast_fireball'})
    assert valid is False
    assert error is not None
    assert 'cast_fireball' in error

def test_invalid_action_spell():
    valid, error = validate_action({'action': 'spell'})
    assert valid is False

def test_invalid_action_empty_string():
    valid, error = validate_action({'action': ''})
    assert valid is False

# ---------------------------------------------------------------------------
# Invalid: directional actions missing/invalid direction
# ---------------------------------------------------------------------------

def test_invalid_move_missing_direction():
    valid, error = validate_action({'action': 'move'})
    assert valid is False
    assert 'direction' in error.lower()

def test_invalid_attack_missing_direction():
    valid, error = validate_action({'action': 'attack'})
    assert valid is False
    assert 'direction' in error.lower()

@pytest.mark.parametrize("bad_dir", ["up", "down", "diagonal", "northwest", "12", ""])
def test_invalid_move_bad_direction(bad_dir):
    valid, error = validate_action({'action': 'move', 'direction': bad_dir})
    assert valid is False, f"Expected failure for direction='{bad_dir}'"
    assert error is not None

@pytest.mark.parametrize("bad_dir", ["up", "down", "diagonal", "northwest"])
def test_invalid_attack_bad_direction(bad_dir):
    valid, error = validate_action({'action': 'attack', 'direction': bad_dir})
    assert valid is False, f"Expected failure for direction='{bad_dir}'"

# ---------------------------------------------------------------------------
# Invalid: use_item missing item_id
# ---------------------------------------------------------------------------

def test_invalid_use_item_missing_item_id():
    valid, error = validate_action({'action': 'use_item'})
    assert valid is False
    assert 'item_id' in error.lower()

def test_invalid_use_item_empty_item_id():
    valid, error = validate_action({'action': 'use_item', 'item_id': ''})
    assert valid is False
    assert 'item_id' in error.lower()

# ---------------------------------------------------------------------------
# Invalid: action_data is not a dict
# ---------------------------------------------------------------------------

def test_invalid_not_dict_string():
    valid, error = validate_action("move north")
    assert valid is False
    assert error is not None

def test_invalid_not_dict_none():
    valid, error = validate_action(None)
    assert valid is False

def test_invalid_not_dict_list():
    valid, error = validate_action([{'action': 'wait'}])
    assert valid is False
