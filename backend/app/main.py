from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.middleware.logging_middleware import LoggingMiddleware
from app.middleware.auth_middleware import APIKeyMiddleware
from app.middleware.error_handler import setup_error_handlers
from app.core.logging import setup_logging
import logging

setup_logging()
logger = logging.getLogger("ai_workforce.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    try:
        from app.database.session import engine, Base
        from app.database import models
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"DB Error: {e}")
    yield
    logger.info("Shutting down...")

app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION, lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.add_middleware(LoggingMiddleware)
app.add_middleware(APIKeyMiddleware)
setup_error_handlers(app)

from app.routers import chat, health, agents, voice, pipeline, auth
app.include_router(health.router)
app.include_router(chat.router)
app.include_router(agents.router)
app.include_router(agents.director_router)
app.include_router(voice.router)
app.include_router(pipeline.router)
app.include_router(auth.router)

@app.get("/")
async def root():
    return {"message": "AI Workforce OS is running", "database": "Active", "logging": "Active"}
