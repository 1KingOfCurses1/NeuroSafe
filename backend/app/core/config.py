import logging
from typing import List, Union, Any
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator

# Setup basic logging to show mode on startup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    APP_ENV: str = "development"
    
    # Mode Configuration: "demo" or "huggingface"
    MODEL_PROVIDER: str = "demo"
    
    # External API Keys (Optional in demo mode)
    HF_API_URL: str = ""
    HF_API_TOKEN: str = ""
    GEMINI_API_KEY: str = ""
    
    # Local Storage
    UPLOAD_DIR: str = "./uploads"
    
    # CORS Configuration
    # We use Union[List[str], str] to allow comma-separated strings from env vars
    ALLOWED_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173", 
        "http://localhost:5174", 
        "http://localhost:3000"
    ]

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        return v # Let pydantic handle other cases or throw error

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def is_demo_mode(self) -> bool:
        return self.MODEL_PROVIDER.lower() == "demo"

    @property
    def is_huggingface_mode(self) -> bool:
        return self.MODEL_PROVIDER.lower() == "huggingface"

settings = Settings()

# Log active provider on startup
logger.info(f"NeuroSafe Backend initialized with MODEL_PROVIDER={settings.MODEL_PROVIDER}")
if settings.is_demo_mode:
    logger.info("Demo mode is ACTIVE. External API keys are not required.")
