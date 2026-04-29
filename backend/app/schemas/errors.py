from typing import Dict, Any, Optional
from pydantic import BaseModel

class ErrorResponse(BaseModel):
    """
    Standardized error response for the NeuroSafe API.
    """
    error: str
    message: str
    status_code: int
    details: Optional[Dict[str, Any]] = None
