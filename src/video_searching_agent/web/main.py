"""Entry point for the API server."""

import logging

import uvicorn

from video_searching_agent.config.settings import get_settings
from video_searching_agent.web.app import create_app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Create app instance for uvicorn
app = create_app()


def main() -> None:
    """Run the API server."""
    settings = get_settings()

    uvicorn.run(
        "video_searching_agent.web.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_debug,
        log_level="debug" if settings.api_debug else "info",
    )


if __name__ == "__main__":
    main()
