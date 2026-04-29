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

# --- Exception Handlers ---

@app.exception_handler(NeuroSafeError)
async def neurosafe_exception_handler(request: Request, exc: NeuroSafeError):
    """
    Handle custom NeuroSafe exceptions and return standardized ErrorResponse.
    """
    error_data = ErrorResponse(
        error=exc.error_code,
        message=exc.message,
        status_code=exc.status_code,
        details=exc.details
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=error_data.model_dump()
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle FastAPI validation errors and return standardized ErrorResponse.
    """
    error_data = ErrorResponse(
        error="validation_error",
        message="Request validation failed.",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        details={"errors": exc.errors()}
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_data.model_dump()
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """
    Handle unexpected errors and return a generic ErrorResponse to avoid leaking info.
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    error_data = ErrorResponse(
        error="internal_server_error",
        message="An unexpected backend error occurred.",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_data.model_dump()
    )

# --- Routers ---

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
