import logging
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

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
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:5173", 
        "http://localhost:5174", 
        "http://localhost:3000"
    ]

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
