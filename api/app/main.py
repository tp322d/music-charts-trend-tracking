"""
Main FastAPI application.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.routers import auth, charts, trends, websocket, data_sync
from app.database.postgres import engine, Base

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Music Charts Tracking API - RESTful API for tracking daily music chart data",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    swagger_ui_init_oauth={
        "usePkceWithAuthorizationCodeGrant": False,
    }
)

cors_origins = [origin.strip() for origin in settings.BACKEND_CORS_ORIGINS.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(charts.router, prefix=settings.API_V1_STR)
app.include_router(trends.router, prefix=settings.API_V1_STR)
app.include_router(data_sync.router, prefix=settings.API_V1_STR)
app.include_router(websocket.router)


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Music Charts Tracking API",
        "version": settings.VERSION,
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "music-charts-api"}


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown."""
    from app.database.mongodb import close_mongodb_connection
    from app.database.redis_client import close_redis_connection
    
    close_mongodb_connection()
    close_redis_connection()

