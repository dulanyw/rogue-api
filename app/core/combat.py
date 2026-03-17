def calculate_damage(attacker_attack, defender_defense):
    return max(0, attacker_attack - defender_defense)

def apply_damage(entity, damage):
    entity.hp -= damage
    if entity.hp <= 0:
        entity.hp = 0
        if hasattr(entity, 'is_alive'):
            entity.is_alive = False
        return True
    return False

def resolve_combat(attacker, defender):
    attack_val = attacker.attack
    if hasattr(attacker, 'equipped_weapon') and attacker.equipped_weapon:
        attack_val += attacker.equipped_weapon.value
    
    defense_val = defender.defense
    if hasattr(defender, 'equipped_armor') and defender.equipped_armor:
        defense_val += defender.equipped_armor.value
    
    damage = calculate_damage(attack_val, defense_val)
    died = apply_damage(defender, damage)
    
    events = []
    if damage > 0:
        events.append(f"{attacker.name} hits {defender.name} for {damage} damage.")
    else:
        events.append(f"{attacker.name} misses {defender.name}.")
    
    if died:
        events.append(f"{defender.name} is defeated!")
    
    return damage, events
