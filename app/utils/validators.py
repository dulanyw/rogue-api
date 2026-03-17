VALID_ACTIONS = {
    'move', 'attack', 'pickup', 'use_item', 'descend',
    'wait', 'remove_armor', 'don_armor', 'remove_ring', 'don_ring', 'switch_weapon'
}
VALID_DIRECTIONS = {'north', 'south', 'east', 'west'}

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
    
    if action == 'use_item':
        if not action_data.get('item_id'):
            return False, "Action 'use_item' requires 'item_id' field."
    
    return True, None
