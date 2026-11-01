from typing import Annotated

from fastapi import FastAPI, HTTPException, Query

from .catalog import PRODUCTS, search_products
from .models import Product, ProductList

app = FastAPI(title="Mall Service", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "mall-service"}


@app.get("/api/products", response_model=ProductList)
def list_products(
    q: Annotated[str | None, Query(max_length=100)] = None,
) -> ProductList:
    products = search_products(q)
    return ProductList(items=products, total=len(products))


@app.get("/api/products/{product_id}", response_model=Product)
def get_product(product_id: str) -> Product:
    for product in PRODUCTS:
        if product.id == product_id:
            return product
    raise HTTPException(status_code=404, detail="商品不存在")
