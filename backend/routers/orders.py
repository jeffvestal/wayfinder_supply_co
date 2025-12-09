from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from services.elastic_client import get_elastic_client
from datetime import datetime
import uuid
import random
import string

router = APIRouter()


class OrderCreate(BaseModel):
    user_id: str
    shipping_address: dict
    payment_info: dict


@router.post("/orders")
async def create_order(order: OrderCreate):
    """
    Create an order from the user's cart.
    Returns order ID and confirmation number.
    """
    es = get_elastic_client()
    
    # Get user's cart (simplified - in production would use cart service)
    # For now, we'll just generate an order ID
    order_id = str(uuid.uuid4())
    confirmation_number = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    
    # In a real system, we would:
    # 1. Get cart items
    # 2. Calculate totals
    # 3. Create order document
    # 4. Clear cart
    # 5. Send confirmation email
    
    # For workshop purposes, just return order info
    order_doc = {
        "order_id": order_id,
        "confirmation_number": confirmation_number,
        "user_id": order.user_id,
        "shipping_address": order.shipping_address,
        "payment_info": {
            "last4": order.payment_info.get("card_number", "0000")[-4:] if order.payment_info.get("card_number") else "0000",
            "card_type": order.payment_info.get("card_type", "Visa")
        },
        "status": "confirmed",
        "created_at": datetime.now().isoformat()
    }
    
    # Store order (optional - for demo purposes)
    try:
        es.index(index="orders", id=order_id, document=order_doc)
    except Exception:
        # Index might not exist, that's okay for workshop
        pass
    
    return {
        "order_id": order_id,
        "confirmation_number": confirmation_number,
        "status": "confirmed",
        "message": "Order placed successfully"
    }


