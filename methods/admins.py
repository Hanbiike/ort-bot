import json
import os
from typing import List, Set
import logging
from config import HAN_ID

logger = logging.getLogger(__name__)

# Path to the admins file
ADMINS_FILE = 'admins.json'

def load_admins() -> Set[int]:
    """
    Load admin IDs from the JSON file.
    Always includes the main admin (HAN_ID).
    """
    admins = {HAN_ID}  # Always include the main admin
    
    if os.path.exists(ADMINS_FILE):
        try:
            with open(ADMINS_FILE, 'r') as file:
                data = json.load(file)
                admins.update(int(admin_id) for admin_id in data['admins'])
        except Exception as e:
            logger.error(f"Error loading admins: {e}")
    
    return admins

def save_admins(admins: Set[int]) -> bool:
    """
    Save admin IDs to the JSON file.
    HAN_ID is not saved as it's always included by default.
    """
    # Remove HAN_ID as it's added automatically when loading
    admins_to_save = {admin_id for admin_id in admins if admin_id != HAN_ID}
    
    try:
        with open(ADMINS_FILE, 'w') as file:
            json.dump({'admins': list(admins_to_save)}, file)
        return True
    except Exception as e:
        logger.error(f"Error saving admins: {e}")
        return False

def is_admin(user_id: int) -> bool:
    """Check if user is an admin."""
    if user_id == HAN_ID:  # Main admin check
        return True
    
    admins = load_admins()
    return user_id in admins

def add_admin(user_id: int) -> bool:
    """Add a new admin."""
    admins = load_admins()
    if user_id in admins:
        return False  # Already an admin
    
    admins.add(user_id)
    return save_admins(admins)

def remove_admin(user_id: int) -> bool:
    """Remove an admin."""
    if user_id == HAN_ID:
        return False  # Cannot remove the main admin
    
    admins = load_admins()
    if user_id not in admins:
        return False  # Not an admin
    
    admins.remove(user_id)
    return save_admins(admins)

def get_all_admins() -> List[int]:
    """Get list of all admins."""
    return list(load_admins())
