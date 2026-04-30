from app.adapters.base import BaseModelAdapter, RawModelOutput
from app.adapters.demo_adapter import demo_model_adapter
from app.adapters.huggingface_adapter import huggingface_model_adapter
from app.adapters.tribev2_adapter import tribe_v2_adapter
from app.adapters.local_cv_adapter import local_cv_adapter

__all__ = [
    "BaseModelAdapter",
    "RawModelOutput",
    "demo_model_adapter",
    "huggingface_model_adapter",
    "tribe_v2_adapter",
    "local_cv_adapter",
]
