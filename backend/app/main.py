import logging
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.api.routes import health, analysis, websocket
from app.core.config import settings
from app.core.exceptions import NeuroSafeError
from app.schemas.errors import ErrorResponse

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

@app.on_event("startup")
async def startup_event():
    """
    Validate environment and log configuration on startup.
    """
    config_summary = settings.validate_runtime_config()
    
    logger.info("=" * 50)
    logger.info(f"🚀 NeuroSafe Backend Starting...")
    logger.info(f"Mode: {config_summary['model_provider'].upper()} (Demo: {config_summary['demo_mode']})")
    logger.info(f"Hugging Face Configured: {config_summary['huggingface_configured']}")
    logger.info(f"Gemini Configured: {config_summary['gemini_configured']}")
    
    if config_summary["warnings"]:
        logger.warning(f"⚠️ Configuration Warnings ({len(config_summary['warnings'])}):")
        for warning in config_summary["warnings"]:
            logger.warning(f"  - {warning}")
    else:
        logger.info("✅ Configuration valid and ready.")
    logger.info("=" * 50)

# --- Exception Handlers ---

@app.exception_handler(NeuroSafeError)
async def neurosafe_exception_handler(request: Request, exc: NeuroSafeError):
    """
    Handle custom NeuroSafe backend errors.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.error_code,
            message=exc.message,
            status_code=exc.status_code,
            details=exc.details
        ).dict()
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle FastAPI validation errors and wrap them in standard format.
    """
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            error="validation_error",
            message="Request validation failed.",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details={"errors": exc.errors()}
        ).dict()
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """
    Catch-all for unexpected server errors to prevent leaking stack traces.
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="internal_server_error",
            message="An unexpected error occurred on the server.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        ).dict()
    )

# --- Routes ---

from fastapi.staticfiles import StaticFiles

import os
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/video", StaticFiles(directory=settings.UPLOAD_DIR), name="video")

app.include_router(health.router, tags=["Health"])
app.include_router(analysis.router, prefix="/api/analyze", tags=["Analysis"])
app.include_router(websocket.router, prefix="/ws/analyze", tags=["WebSocket"])

@app.get("/")
async def root():
    return {
        "app": "NeuroSafe Backend",
        "version": "0.1.0",
        "docs": "/docs"
    }
