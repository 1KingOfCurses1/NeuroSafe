from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    APP_ENV: str = "development"
    MODEL_PROVIDER: str = "demo"
    HF_API_URL: str = ""
    HF_API_TOKEN: str = ""
    GEMINI_API_KEY: str = ""
    UPLOAD_DIR: str = "./uploads"
    ALLOWED_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:5174", "http://localhost:3000"]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
