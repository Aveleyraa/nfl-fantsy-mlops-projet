import logging
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.backend.config import settings
from src.backend.routers import players, stats, predict

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = FastAPI(
    title="NFL Stats API",
    description="API para estadísticas NFL usando nflreadpy. Alimenta el dashboard de Streamlit.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — permite que Streamlit (otro puerto) consuma la API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # en producción limitar a tu dominio
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(players.router)
app.include_router(stats.router)
app.include_router(predict.router)


@app.get("/", tags=["health"])
def root()-> dict:
    return {
        "status": "ok",
        "environment": settings.environment,
        "docs": "/docs",
    }


@app.get("/health", tags=["health"])
def health()-> dict:
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
    )