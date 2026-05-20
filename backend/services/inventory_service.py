import asyncio
import uuid
from services.telemetry import get_tracer

tracer = get_tracer("wayfinder.inventory")

# Simulated in-memory stock store
_stock: dict[str, int] = {}
_DEFAULT_STOCK = 50


def _get_stock(product_id: str) -> int:
    return _stock.get(product_id, _DEFAULT_STOCK)


def _apply_reservation(product_id: str, quantity: int) -> bool:
    """Atomic check-and-decrement. Returns True if reservation succeeded."""
    current = _stock.get(product_id, _DEFAULT_STOCK)
    if current < quantity:
        return False
    _stock[product_id] = current - quantity
    return True


async def reserve(product_id: str, quantity: int, user_id: str) -> dict:
    with tracer.start_as_current_span("inventory.reserve") as span:
        span.set_attribute("inventory.quantity_requested", quantity)
        span.set_attribute("http.route", "/api/v1/checkout/reserve")
        span.set_attribute("inventory.product_id", product_id)
        span.set_attribute("inventory.user_id", user_id)

        with tracer.start_as_current_span("db.query") as query_span:
            query_span.set_attribute(
                "db.statement",
                f"SELECT quantity FROM inventory WHERE product_id = '{product_id}'"
            )
            await asyncio.sleep(0.01)
            available = _get_stock(product_id)

        span.set_attribute("inventory.quantity_available", available)

        if available < quantity:
            return {
                "reserved": False,
                "quantity_available": available,
                "reservation_id": None,
            }

        with tracer.start_as_current_span("db.write") as write_span:
            # Atomic: single conditional UPDATE — only decrements if stock still sufficient
            write_span.set_attribute(
                "db.statement",
                f"UPDATE inventory SET quantity = quantity - {quantity} "
                f"WHERE product_id = '{product_id}' AND quantity >= {quantity} "
                f"RETURNING reservation_id"
            )
            await asyncio.sleep(0.01)
            succeeded = _apply_reservation(product_id, quantity)

        if not succeeded:
            return {
                "reserved": False,
                "quantity_available": _get_stock(product_id),
                "reservation_id": None,
            }

        reservation_id = str(uuid.uuid4())
        span.set_attribute("inventory.reservation_id", reservation_id)

        return {
            "reserved": True,
            "quantity_available": _get_stock(product_id),
            "reservation_id": reservation_id,
        }
