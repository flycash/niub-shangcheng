import os

import uvicorn


def run() -> None:
    uvicorn.run(
        "mall_service.api:app",
        host=os.getenv("MALL_SERVICE_HOST", "0.0.0.0"),
        port=int(os.getenv("MALL_SERVICE_PORT", "8001")),
    )
