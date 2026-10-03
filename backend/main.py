"""
Project AETHER - Main FastAPI Application
A time-aware, multi-agent decision intelligence system
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api.routes import debate_router
from app.api.auth_routes import auth_router
from app.core.config import settings
from app.core.database import connect_db, close_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    print("🚀 AETHER System Initializing...")
    await connect_db()
    yield
    await close_db()
    print("🛑 AETHER System Shutting Down...")


app = FastAPI(
    title="Project AETHER",
    description="Time-Aware Multi-Agent Decision Intelligence System",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware — must be before routers
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # Vite dev server
        "http://localhost:3000",   # fallback
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(debate_router, prefix="/api/v1", tags=["debate"])


@app.get("/")
async def root():
    return {
        "status": "operational",
        "system": "AETHER v1.0",
        "description": "Time-Aware Multi-Agent Decision Intelligence System",
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "agents": {
            "factor_extraction": "ready",
            "pro_agent": "ready",
            "con_agent": "ready",
            "moderator": "ready",
            "synthesizer": "ready",
        },
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)