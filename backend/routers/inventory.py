from fastapi import APIRouter
from pydantic import BaseModel
from services import inventory_service

router = APIRouter()


class ReserveRequest(BaseModel):
    product_id: str
    quantity: int
    user_id: str


class ReserveResponse(BaseModel):
    reserved: bool
    quantity_available: int
    reservation_id: str | None


@router.post("/v1/checkout/reserve", response_model=ReserveResponse)
async def reserve_inventory(body: ReserveRequest):
    result = await inventory_service.reserve(
        product_id=body.product_id,
        quantity=body.quantity,
        user_id=body.user_id,
    )
    return ReserveResponse(**result)
