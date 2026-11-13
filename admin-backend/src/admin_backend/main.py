import os

import uvicorn


def run() -> None:
    uvicorn.run(
        "admin_backend.api:app",
        host=os.getenv("ADMIN_BACKEND_HOST", "127.0.0.1"),
        port=int(os.getenv("ADMIN_BACKEND_PORT", "8003")),
    )
