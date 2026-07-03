from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str = ""
    priority: str = Field(default="normal", pattern="^(low|normal|high)$")


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    status: str | None = Field(default=None, pattern="^(pending|done)$")
    priority: str | None = Field(default=None, pattern="^(low|normal|high)$")


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    status: str
    priority: str
    created_at: datetime


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    session_id: str = "default"


class ChatResponse(BaseModel):
    reply: str
    tools_used: list[str] = []
