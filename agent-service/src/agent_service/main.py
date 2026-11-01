import argparse
import os
from pathlib import Path

import uvicorn


def run() -> None:
    parser = argparse.ArgumentParser(description="Start the shopping agent service")
    parser.add_argument(
        "--config",
        help="Path to the LLM YAML config file",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Reload Python source code when files change",
    )
    args = parser.parse_args()

    if args.config:
        os.environ["LLM_CONFIG_FILE"] = str(Path(args.config).expanduser().resolve())

    uvicorn.run(
        "agent_service.api:app",
        host=os.getenv("AGENT_SERVICE_HOST", "0.0.0.0"),
        port=int(os.getenv("AGENT_SERVICE_PORT", "8002")),
        reload=args.reload,
        reload_dirs=[str(Path(__file__).resolve().parent)] if args.reload else None,
    )
