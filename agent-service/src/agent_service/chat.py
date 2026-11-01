from collections.abc import Sequence

from .models import Product


def compose_reply(message: str, products: Sequence[Product]) -> str:
    """Generate a deterministic reply until a model-backed implementation is added."""
    if not products:
        return "商城目录暂时没有可推荐的商品，请稍后再试。"

    names = "、".join(product.name for product in products[:3])
    lowered = message.lower()
    if any(greeting in lowered for greeting in ("你好", "hello", "hi")):
        return f"你好，我是商城导购。今天可以先看看 {names}。"

    return f"我查看了商城目录，{names} 都值得看看。你更偏好饮品、家居还是文创？"
