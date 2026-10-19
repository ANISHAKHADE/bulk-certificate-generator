from pydantic import BaseModel, Field, field_validator
from typing import List, Any, Optional
from datetime import date
from .config import settings

class RecipientIn(BaseModel):
    name: Any = None
    email: Any = None
    model_config = {"extra": "allow"}

class JobCreate(BaseModel):
    course_name: str = Field(..., min_length=1, max_length=150)
    issuer_name: Optional[str] = None
    issue_date: Optional[date] = None
    recipients: List[RecipientIn] = Field(..., min_length=1, max_length=settings.MAX_RECIPIENTS)

    @field_validator("course_name")
    def not_blank(cls, v):
        if not v.strip(): raise ValueError("course_name must not be blank")
        return v
