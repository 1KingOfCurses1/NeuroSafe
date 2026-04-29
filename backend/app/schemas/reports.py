from typing import List
from pydantic import BaseModel

class GeminiReport(BaseModel):
    headline: str
    findings: List[str]
    recommended_actions: List[str]
