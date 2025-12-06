from fastapi import APIRouter, HTTPException
from typing import List, Dict, Optional
from pydantic import BaseModel

router = APIRouter()

# In-memory cart storage (in production, use Redis or database)
carts: Dict[str, List[Dict]] = {}


class CartItem(BaseModel):
    product_id: str
    quantity: int = 1


class CartResponse(BaseModel):
    items: List[Dict]
    subtotal: float
    discount: float
    total: float
    loyalty_perks: List[str]


@router.post("/cart")
async def add_to_cart(user_id: str, item: CartItem):
    """
    Add item to cart.
    """
    if user_id not in carts:
        carts[user_id] = []
    
    # Check if item already in cart
    for cart_item in carts[user_id]:
        if cart_item["product_id"] == item.product_id:
            cart_item["quantity"] += item.quantity
            return {"message": "Item quantity updated", "cart": carts[user_id]}
    
    # Add new item
    carts[user_id].append({
        "product_id": item.product_id,
        "quantity": item.quantity
    })
    
    return {"message": "Item added to cart", "cart": carts[user_id]}


@router.get("/cart")
async def get_cart(user_id: str, loyalty_tier: Optional[str] = None):
    """
    Get cart contents with pricing.
    """
    if user_id not in carts or not carts[user_id]:
        return CartResponse(
            items=[],
            subtotal=0.0,
            discount=0.0,
            total=0.0,
            loyalty_perks=[]
        )
    
    from services.elastic_client import get_elastic_client
    es = get_elastic_client()
    
    items = []
    subtotal = 0.0
    
    for cart_item in carts[user_id]:
        try:
            product = es.get(index="product-catalog", id=cart_item["product_id"])
            product_data = product["_source"]
            
            item_total = product_data["price"] * cart_item["quantity"]
            subtotal += item_total
            
            items.append({
                "product_id": cart_item["product_id"],
                "title": product_data["title"],
                "price": product_data["price"],
                "quantity": cart_item["quantity"],
                "subtotal": item_total,
                "image_url": product_data.get("image_url", "")
            })
        except Exception as e:
            # Skip items that can't be found
            continue
    
    # Calculate discounts and perks
    discount = 0.0
    perks = []
    
    if loyalty_tier == "platinum":
        discount = subtotal * 0.10  # 10% discount
        perks.append("Free overnight shipping")
    elif loyalty_tier == "business":
        discount = subtotal * 0.15  # 15% bulk discount
        perks.append("Net-30 payment terms")
    
    total = subtotal - discount
    
    return CartResponse(
        items=items,
        subtotal=subtotal,
        discount=discount,
        total=total,
        loyalty_perks=perks
    )


@router.delete("/cart")
async def clear_cart(user_id: str):
    """
    Clear cart for user.
    """
    if user_id in carts:
        carts[user_id] = []
    return {"message": "Cart cleared"}


@router.delete("/cart/{product_id}")
async def remove_from_cart(user_id: str, product_id: str):
    """
    Remove item from cart.
    """
    if user_id not in carts:
        raise HTTPException(status_code=404, detail="Cart not found")
    
    carts[user_id] = [item for item in carts[user_id] if item["product_id"] != product_id]
    
    return {"message": "Item removed", "cart": carts[user_id]}


