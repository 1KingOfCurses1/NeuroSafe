import logging
import os
from typing import List, Union, Any, Dict
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    APP_ENV: str = "development"
    
    # Mode Configuration: "demo", "tribev2", "tribe_v2", or "huggingface"
    MODEL_PROVIDER: str = "demo"

    # TRIBE v2 settings
    TRIBE_MODEL_ID: str = "facebook/tribev2"
    TRIBEV2_API_URL: str = ""
    TRIBEV2_API_TOKEN: str = ""
    TRIBEV2_LOCAL_REPO_PATH: str = "C:/Users/shanj/Downloads/Personal/tribev2"
    TRIBEV2_CACHE_DIR: str = "./cache"

    # External API Keys (optional in demo mode)
    HF_API_URL: str = ""
    HF_API_TOKEN: str = ""
    GEMINI_API_KEY: str = ""
    
    # Local Storage
    UPLOAD_DIR: str = "./uploads"
    
    # CORS Configuration
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
        return v

    @field_validator("MODEL_PROVIDER", mode="before")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        allowed = ["demo", "tribev2", "tribe_v2", "local_cv", "huggingface"]
        if v.lower() not in allowed:
            return "demo"
        return v.lower()

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def is_demo_mode(self) -> bool:
        return self.MODEL_PROVIDER == "demo"

    @property
    def is_tribev2_mode(self) -> bool:
        return self.MODEL_PROVIDER == "tribev2"

    @property
    def is_tribe_mode(self) -> bool:
        # Keep compatibility for both naming conventions
        return self.MODEL_PROVIDER in ["tribev2", "tribe_v2"]

    @property
    def is_huggingface_mode(self) -> bool:
        return self.MODEL_PROVIDER == "huggingface"

    def validate_runtime_config(self) -> Dict[str, Any]:
        """
        Performs lightweight runtime validation and returns a summary.
        Ensures UPLOAD_DIR exists and checks for missing optional keys.
        """
        warnings = []
        
        # 1. Check Model Provider
        if self.is_tribev2_mode:
            from importlib.util import find_spec
            has_tribe_pkg = find_spec("tribev2") is not None
            if not has_tribe_pkg:
                if not os.path.exists(self.TRIBEV2_LOCAL_REPO_PATH):
                    warnings.append(
                        f"MODEL_PROVIDER=tribev2 but 'tribev2' package is not installed "
                        f"and TRIBEV2_LOCAL_REPO_PATH ({self.TRIBEV2_LOCAL_REPO_PATH}) does not exist."
                    )
                else:
                    warnings.append(
                        f"MODEL_PROVIDER=tribev2 but 'tribev2' package is not installed. "
                        f"Will attempt to load from {self.TRIBEV2_LOCAL_REPO_PATH}."
                    )
        
        if self.MODEL_PROVIDER == "tribe_v2":
            from importlib.util import find_spec
            has_tribe_pkg = find_spec("tribev2") is not None
            if not has_tribe_pkg and (not self.HF_API_URL or not self.HF_API_TOKEN):
                warnings.append(
                    "MODEL_PROVIDER=tribe_v2 but neither the tribe_v2 package is installed "
                    "nor HF_API_URL/HF_API_TOKEN are configured. "
                )
        if self.is_huggingface_mode:
            if not self.HF_API_URL or not self.HF_API_TOKEN:
                warnings.append("MODEL_PROVIDER is set to 'huggingface' but HF_API_URL or HF_API_TOKEN is missing.")
        
        if self.MODEL_PROVIDER == "local_cv":
            from importlib.util import find_spec
            has_cv = find_spec("cv2") is not None or find_spec("imageio") is not None
            if not has_cv:
                warnings.append("MODEL_PROVIDER=local_cv but opencv or imageio are not installed.")
        
        # 2. Check Gemini
        if not self.GEMINI_API_KEY:
            warnings.append("GEMINI_API_KEY is missing. Clinical reports will use local fallback generator.")

        # 3. Check/Create Upload Dir
        try:
            if not os.path.exists(self.UPLOAD_DIR):
                os.makedirs(self.UPLOAD_DIR, exist_ok=True)
                logger.info(f"Created upload directory: {self.UPLOAD_DIR}")
        except Exception as e:
            warnings.append(f"Could not create/access UPLOAD_DIR '{self.UPLOAD_DIR}': {e}")

        # 4. Check Origins
        if not self.ALLOWED_ORIGINS:
            warnings.append("ALLOWED_ORIGINS is empty. CORS may block frontend requests.")

        return {
            "model_provider": self.MODEL_PROVIDER,
            "demo_mode": self.is_demo_mode,
            "huggingface_configured": bool(self.HF_API_URL and self.HF_API_TOKEN),
            "gemini_configured": bool(self.GEMINI_API_KEY),
            "upload_dir": self.UPLOAD_DIR,
            "warnings": warnings
        }

settings = Settings()
