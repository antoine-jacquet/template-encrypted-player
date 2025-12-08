#!/usr/bin/env python3
"""Your encrypted strategy - edit this file, then encrypt it with setup_encryption.py"""

from typing import Any, Dict

import numpy as np


def strategy(state: Dict[str, Any]) -> Dict[str, Dict[str, int]]:
    """
    Your strategy function.
    
    Args:
        state: Game state dictionary containing:
            - playerIds: list of all player IDs
            - myPlayerId: your player ID
            - opponentsIds: list of opponent IDs
            - state: list of completed turns
            - turnId: current turn number
    
    Returns:
        Dictionary with 'shoot' and 'keep' maps:
        {
            "shoot": {opponent_id: direction (0-2), ...},
            "keep": {opponent_id: direction (0-2), ...}
        }
    """
    my_id = state.get("myPlayerId")
    opponents = state.get("opponentsIds") or []

    if not my_id or not opponents:
        return {"shoot": {}, "keep": {}}

    # Example: random strategy
    # Replace this with your actual strategy logic
    shoot = np.random.randint(0, 3, len(opponents)).tolist()
    keep = np.random.randint(0, 3, len(opponents)).tolist()

    return {
        "shoot": {pid: int(direction) for pid, direction in zip(opponents, shoot)},
        "keep": {pid: int(direction) for pid, direction in zip(opponents, keep)},
    }
