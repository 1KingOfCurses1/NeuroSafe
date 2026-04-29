from typing import Optional, Dict, Any

class NeuroSafeError(Exception):
    """
    Base exception for all NeuroSafe-specific errors.
    """
    def __init__(
        self, 
        error_code: str, 
        message: str, 
        status_code: int = 500, 
        details: Optional[Dict[str, Any]] = None
    ):
        self.error_code = error_code
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(self.message)

class JobNotFoundAPIError(NeuroSafeError):
    """
    Raised when an analysis job is not found.
    """
    def __init__(self, job_id: str):
        super().__init__(
            error_code="job_not_found",
            message=f"Analysis job '{job_id}' was not found.",
            status_code=404,
            details={"job_id": job_id}
        )

class ValidationAPIError(NeuroSafeError):
    """
    Raised when request validation fails.
    """
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            error_code="validation_error",
            message=message,
            status_code=400,
            details=details
        )

class UploadAPIError(NeuroSafeError):
    """
    Raised when a video upload fails.
    """
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            error_code="upload_error",
            message=message,
            status_code=400,
            details=details
        )

class ExternalServiceAPIError(NeuroSafeError):
    """
    Raised when an external service (HF, Gemini, YouTube) fails.
    """
    def __init__(self, service: str, message: str):
        super().__init__(
            error_code="external_service_error",
            message=f"External service '{service}' error: {message}",
            status_code=502,
            details={"service": service}
        )
