from typing import Dict, List

# Define valid state transitions for orders
# This is a classic finite state machine pattern.
VALID_TRANSITIONS: Dict[str, List[str]] = {
    "PENDING": ["CONFIRMED", "CANCELLED"],
    "CONFIRMED": ["PROCESSING", "CANCELLED"],
    "PROCESSING": ["SHIPPED", "CANCELLED"],
    "SHIPPED": ["DELIVERED"],
    "DELIVERED": [],    # Terminal state
    "CANCELLED": []     # Terminal state
}

def is_valid_status_transition(current_status: str, new_status: str) -> bool:
    """
    Checks if a transition from current_status to new_status is permitted.
    If the status is unchanged, returns True.
    """
    current = current_status.upper()
    new = new_status.upper()
    
    if current == new:
        return True
        
    return new in VALID_TRANSITIONS.get(current, [])
