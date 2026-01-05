"""Main FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from app.core.telegram_client import telegram_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.app_debug else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    Manages Telegram client lifecycle.
    """
    # Startup
    logger.info("Starting Telegram Channel Message Receiver API")
    try:
        await telegram_manager.start()
        logger.info("Telegram client started successfully")
    except Exception as e:
        logger.error(f"Failed to start Telegram client: {e}")
        logger.warning("Application starting without Telegram connection")

    yield

    # Shutdown
    logger.info("Shutting down Telegram client")
    try:
        await telegram_manager.stop()
        logger.info("Telegram client stopped successfully")
    except Exception as e:
        logger.error(f"Error during Telegram client shutdown: {e}")


# Create FastAPI application
app = FastAPI(
    title="Telegram Channel Message Receiver",
    description="REST API for receiving messages from Telegram channels via MTProto",
    version="1.0.0",
    lifespan=lifespan,
    debug=settings.app_debug
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for media serving
try:
    app.mount(
        "/media",
        StaticFiles(directory=settings.media_cache_dir),
        name="media"
    )
    logger.info(f"Media directory mounted at /media from {settings.media_cache_dir}")
except Exception as e:
    logger.warning(f"Failed to mount media directory: {e}")


# Import and include routers (will be created next)
# Note: Import here to avoid circular dependencies
try:
    from app.api.routes import auth, channels, messages, media

    app.include_router(
        auth.router,
        prefix=f"{settings.api_prefix}/auth",
        tags=["Authentication"]
    )

    app.include_router(
        channels.router,
        prefix=f"{settings.api_prefix}/channels",
        tags=["Channels"]
    )

    app.include_router(
        messages.router,
        prefix=f"{settings.api_prefix}/messages",
        tags=["Messages"]
    )

    app.include_router(
        media.router,
        prefix=f"{settings.api_prefix}/media",
        tags=["Media"]
    )

    logger.info("API routes registered successfully")

except ImportError as e:
    logger.warning(f"Some routes not available yet: {e}")


@app.get("/health", tags=["System"])
async def health_check():
    """
    Health check endpoint.

    Returns service status and Telegram connection state.
    """
    is_connected = telegram_manager.is_connected()
    is_authorized = await telegram_manager.is_authorized() if is_connected else False

    return {
        "status": "healthy",
        "telegram_connected": is_connected,
        "telegram_authorized": is_authorized,
        "version": "1.0.0"
    }


@app.get("/", tags=["System"])
async def root():
    """Root endpoint with API information."""
    return {
        "service": "Telegram Channel Message Receiver",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_debug,
        log_level="debug" if settings.app_debug else "info"
    )
