"""
Comprehensive tests for app/core/combat.py — damage calculation, damage
application, and full combat resolution including equipment modifiers.
"""
import pytest
from app.core.combat import calculate_damage, apply_damage, resolve_combat
from app.core.models import Player, Enemy, Item


# ---------------------------------------------------------------------------
# calculate_damage
# ---------------------------------------------------------------------------

def test_calculate_damage_positive():
    assert calculate_damage(10, 4) == 6

def test_calculate_damage_zero_when_defense_higher():
    assert calculate_damage(3, 10) == 0

def test_calculate_damage_zero_when_equal():
    assert calculate_damage(5, 5) == 0

def test_calculate_damage_one():
    assert calculate_damage(6, 5) == 1

def test_calculate_damage_large_attacker():
    assert calculate_damage(100, 0) == 100

# ---------------------------------------------------------------------------
# apply_damage
# ---------------------------------------------------------------------------

def test_apply_damage_reduces_hp():
    e = Enemy("Bat", hp=10, attack=2, defense=1, xp_value=3, position=(0, 0))
    died = apply_damage(e, 4)
    assert e.hp == 6
    assert died is False
    assert e.is_alive is True

def test_apply_damage_kills_enemy():
    e = Enemy("Emu", hp=3, attack=2, defense=0, xp_value=2, position=(0, 0))
    died = apply_damage(e, 3)
    assert e.hp == 0
    assert died is True
    assert e.is_alive is False

def test_apply_damage_overkill():
    """Damage exceeding current HP brings HP to 0, not negative."""
    e = Enemy("Emu", hp=1, attack=2, defense=0, xp_value=2, position=(0, 0))
    died = apply_damage(e, 100)
    assert e.hp == 0
    assert died is True

def test_apply_damage_player_no_is_alive():
    """Players don't have is_alive; apply_damage should not raise."""
    p = Player("Hero")
    p.hp = 5
    died = apply_damage(p, 3)
    assert p.hp == 2
    assert died is False

def test_apply_damage_kills_player():
    p = Player("Hero")
    p.hp = 1
    died = apply_damage(p, 10)
    assert p.hp == 0
    assert died is True

# ---------------------------------------------------------------------------
# resolve_combat
# ---------------------------------------------------------------------------

def test_resolve_combat_player_hits_enemy():
    p = Player("Hero")   # attack=4, defense=1
    e = Enemy("Emu", hp=10, attack=2, defense=0, xp_value=2, position=(1, 0))

    damage, events = resolve_combat(p, e)
    assert damage == 4  # 4 - 0
    assert e.hp == 6
    assert any('hits' in ev for ev in events)

def test_resolve_combat_enemy_hits_player():
    e = Enemy("Dragon", hp=40, attack=15, defense=8, xp_value=50, position=(1, 0))
    p = Player("Hero")  # defense=1

    damage, events = resolve_combat(e, p)
    assert damage == 14  # 15 - 1
    # HP is capped at 0 by apply_damage
    assert p.hp == 0

def test_resolve_combat_miss():
    """When attacker attack <= defender defense damage is 0 and 'misses' is logged."""
    p = Player("Hero")  # attack=4
    e = Enemy("Tank", hp=20, attack=0, defense=10, xp_value=0, position=(1, 0))

    damage, events = resolve_combat(p, e)
    assert damage == 0
    assert any('misses' in ev for ev in events)

def test_resolve_combat_kill_generates_defeated_event():
    p = Player("Hero")  # attack=4
    e = Enemy("Weakling", hp=1, attack=0, defense=0, xp_value=1, position=(1, 0))

    damage, events = resolve_combat(p, e)
    assert e.is_alive is False
    assert any('defeated' in ev for ev in events)

def test_resolve_combat_with_weapon_bonus():
    """Equipped weapon value is added to attacker's attack."""
    p = Player("Hero")  # base attack=4
    weapon = Item("Long Sword", "weapon", 5, "A long sword (+5 attack)")
    p.equipped_weapon = weapon

    e = Enemy("Emu", hp=20, attack=2, defense=0, xp_value=2, position=(1, 0))
    damage, events = resolve_combat(p, e)
    assert damage == 9  # (4 + 5) - 0

def test_resolve_combat_with_armor_bonus():
    """Equipped armor value is added to defender's defense."""
    p = Player("Hero")  # attack=4
    e = Enemy("Emu", hp=20, attack=2, defense=0, xp_value=2, position=(1, 0))
    armor = Item("Chain Mail", "armor", 4, "Chain mail armor (+4 defense)")
    e_player = Player("Defended")  # defense=1
    e_player.equipped_armor = armor

    damage, events = resolve_combat(p, e_player)
    assert damage == 0  # 4 - (1 + 4) = -1 → 0

def test_resolve_combat_events_not_empty():
    p = Player("Hero")
    e = Enemy("Bat", hp=10, attack=2, defense=1, xp_value=3, position=(1, 0))
    _, events = resolve_combat(p, e)
    assert len(events) >= 1
