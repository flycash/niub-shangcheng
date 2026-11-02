from datetime import datetime, timedelta, timezone
from threading import RLock
from uuid import uuid4

from .catalog import get_product
from .mock_data import ORDERS
from .models import CreateOrderItem, Order, OrderItem, ShippingAddress


class OrderNotFound(Exception):
    """Raised when an order does not exist for the current user."""


class OrderConflict(Exception):
    """Raised when an order cannot move to the requested state."""


class InsufficientStock(Exception):
    """Raised when a product does not have enough stock."""


MOCK_ADDRESS = ShippingAddress(
    recipient="演示用户",
    phone_masked="138****0001",
    region="上海市 浦东新区",
    detail="演示路 88 号",
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _order_key(user_id: int, idempotency_key: str) -> tuple[int, str]:
    return user_id, idempotency_key


_LOCK = RLock()
_ORDERS: dict[str, Order] = {
    order.order_id: order
    for user_orders in ORDERS.values()
    for order in user_orders
}
_INITIAL_ORDER_IDS = frozenset(_ORDERS)
_IDEMPOTENCY_INDEX: dict[tuple[int, str], str] = {}


def _check_stock(product_id: str, quantity: int) -> None:
    product = get_product(product_id)
    if product is None:
        raise OrderNotFound(f"商品 {product_id} 不存在")
    if product.stock is not None and product.stock < quantity:
        raise InsufficientStock(f"商品 {product_id} 库存不足")


def create_order(
    user_id: int,
    items: list[CreateOrderItem],
    idempotency_key: str,
) -> Order:
    with _LOCK:
        existing_id = _IDEMPOTENCY_INDEX.get(
            _order_key(user_id, idempotency_key)
        )
        if existing_id is not None:
            return _ORDERS[existing_id]

        quantities: dict[str, int] = {}
        for item in items:
            quantities[item.product_id] = (
                quantities.get(item.product_id, 0) + item.quantity
            )

        order_items: list[OrderItem] = []
        for product_id, quantity in quantities.items():
            product = get_product(product_id)
            if product is None:
                raise OrderNotFound(f"商品 {product_id} 不存在")
            _check_stock(product_id, quantity)
            subtotal = product.price_cents * quantity
            order_items.append(
                OrderItem(
                    product_id=product.id,
                    name=product.name,
                    image_url=product.image_url,
                    quantity=quantity,
                    unit_price_cents=product.price_cents,
                    subtotal_cents=subtotal,
                )
            )

        now = _now()
        order_id = f"order-{uuid4().hex}"
        subtotal_cents = sum(item.subtotal_cents for item in order_items)
        shipping_fee_cents = 0
        order = Order(
            order_id=order_id,
            user_id=user_id,
            status="pending_payment",
            ordered_at=now.isoformat(timespec="milliseconds"),
            address=MOCK_ADDRESS,
            subtotal_cents=subtotal_cents,
            shipping_fee_cents=shipping_fee_cents,
            total_cents=subtotal_cents + shipping_fee_cents,
            items=order_items,
            preview_path=f"/orders/{order_id}",
            expires_at=(now + timedelta(minutes=30)).isoformat(
                timespec="milliseconds"
            ),
        )
        _ORDERS[order_id] = order
        _IDEMPOTENCY_INDEX[_order_key(user_id, idempotency_key)] = order_id
        return order


def list_user_orders(user_id: int) -> list[Order]:
    with _LOCK:
        orders = [
            order for order in _ORDERS.values() if order.user_id == user_id
        ]
    return sorted(orders, key=lambda order: order.ordered_at, reverse=True)


def get_order(user_id: int, order_id: str) -> Order | None:
    with _LOCK:
        order = _ORDERS.get(order_id)
        if order is None or order.user_id != user_id:
            return None
        return order


def pay_order(user_id: int, order_id: str) -> Order:
    with _LOCK:
        order = _ORDERS.get(order_id)
        if order is None or order.user_id != user_id:
            raise OrderNotFound("订单不存在")
        if order.status == "paid":
            return order
        if order.status != "pending_payment":
            raise OrderConflict("当前订单状态不能支付")

        for item in order.items:
            _check_stock(item.product_id, item.quantity)
        for item in order.items:
            product = get_product(item.product_id)
            if product is not None and product.stock is not None:
                product.stock -= item.quantity

        paid_order = order.model_copy(
            update={
                "status": "paid",
                "paid_at": _now().isoformat(timespec="milliseconds"),
            }
        )
        _ORDERS[order_id] = paid_order
        return paid_order


def reset_order_store() -> None:
    """Reset dynamically created orders for deterministic tests."""
    with _LOCK:
        for order_id in set(_ORDERS) - _INITIAL_ORDER_IDS:
            del _ORDERS[order_id]
        _IDEMPOTENCY_INDEX.clear()
