from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import health, analysis, websocket
from app.core.config import settings

app = FastAPI(
    title="NeuroSafe Backend",
    description="Seizure trigger analysis backend for NeuroSafe",
    version="0.1.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["health"])
app.include_router(analysis.router, prefix="/api/analyze", tags=["analysis"])
app.include_router(websocket.router, prefix="/ws/analyze", tags=["websocket"])

@app.get("/")
async def root():
    return {
        "service": "NeuroSafe Backend",
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }
