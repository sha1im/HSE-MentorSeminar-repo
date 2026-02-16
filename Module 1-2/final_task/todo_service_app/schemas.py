from pydantic import BaseModel, Field
from typing import Optional


class ItemCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)
    priority: int = Field(default=3, ge=1, le=5)


class ItemUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)
    priority: Optional[int] = Field(default=None, ge=1, le=5)
    completed: Optional[bool] = None


class ItemOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    priority: int
    completed: bool
    archived: bool
    created_at: str