import string

VALID_ACTIONS = {
    'move', 'attack', 'pickup', 'use_item', 'descend',
    'wait', 'remove_armor', 'don_armor', 'remove_ring', 'don_ring', 'switch_weapon'
}
VALID_DIRECTIONS = {'north', 'south', 'east', 'west'}
VALID_INVENTORY_KEYS = set(string.ascii_lowercase)

def validate_action(action_data):
    if not isinstance(action_data, dict):
        return False, "Action data must be a JSON object."
    
    action = action_data.get('action')
    if not action:
        return False, "Missing 'action' field."
    
    if action not in VALID_ACTIONS:
        return False, f"Invalid action '{action}'. Valid actions: {', '.join(sorted(VALID_ACTIONS))}"
    
    if action in ('move', 'attack'):
        direction = action_data.get('direction')
        if not direction:
            return False, f"Action '{action}' requires 'direction' field."
        if direction not in VALID_DIRECTIONS:
            return False, f"Invalid direction '{direction}'. Valid: {', '.join(sorted(VALID_DIRECTIONS))}"
    
    if action in ('use_item', 'don_armor', 'don_ring', 'switch_weapon'):
        item_key = action_data.get('item_key')
        if item_key not in VALID_INVENTORY_KEYS:
            return False, f"Action '{action}' requires 'item_key' field (a single letter a-z)."
    
    if action == 'remove_ring':
        ring_key = action_data.get('ring_key')
        if ring_key not in VALID_INVENTORY_KEYS:
            return False, "Action 'remove_ring' requires 'ring_key' field (a single letter a-z)."
    
    return True, None
