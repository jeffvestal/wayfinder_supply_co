import json
import os
from typing import Dict, Optional


def get_customer_profile(user_id: str, crm_data_path: str) -> Dict:
    """
    Get customer profile from mock CRM data.
    """
    if not os.path.exists(crm_data_path):
        raise FileNotFoundError(f"CRM data file not found: {crm_data_path}")
    
    with open(crm_data_path, 'r') as f:
        crm_data = json.load(f)
    
    if user_id not in crm_data:
        # Return default new user profile
        return {
            "user_id": user_id,
            "name": "Unknown User",
            "email": f"{user_id}@example.com",
            "loyalty_tier": "none",
            "account_type": "individual",
            "lifetime_value": 0.0,
            "purchase_history": [],
            "preferences": {}
        }
    
    return crm_data[user_id]


