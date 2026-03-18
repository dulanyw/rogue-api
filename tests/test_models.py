from app.core.models import Player, Enemy, Item, GameState, Tile

def test_player_creation():
    p = Player("TestHero")
    assert p.name == "TestHero"
    assert p.hp == p.max_hp
    assert p.hp > 0
    assert p.level == 1
    assert p.xp == 0
    assert p.gold == 0
    assert p.inventory == []
    assert p.equipped_weapon is None
    assert p.equipped_armor is None
    assert p.equipped_rings == []

def test_enemy_creation():
    e = Enemy("Dragon", hp=40, attack=15, defense=8, xp_value=50, position=(5, 5))
    assert e.name == "Dragon"
    assert e.hp == 40
    assert e.max_hp == 40
    assert e.attack == 15
    assert e.defense == 8
    assert e.xp_value == 50
    assert e.is_alive is True
    assert e.position == [5, 5]

def test_item_creation():
    item = Item("Potion of Healing", "potion", 6, "Restores 6 HP")
    assert item.name == "Potion of Healing"
    assert item.type == "potion"
    assert item.value == 6
    assert item.description == "Restores 6 HP"
    assert item.id is not None
