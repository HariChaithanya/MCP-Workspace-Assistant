from typing import Any, Literal

from pydantic import BaseModel, Field


class ToolCall(BaseModel):
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    status: Literal["pending", "running", "success", "error"] = "pending"
    result: Any | None = None


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    conversation_id: str | None = None


class ChatResponse(BaseModel):
    answer: str
    tools_used: list[ToolCall] = Field(default_factory=list)
    files_referenced: list[str] = Field(default_factory=list)
    status: Literal["completed", "error"] = "completed"
    conversation_id: str | None = None


class WorkspaceUpdateRequest(BaseModel):
    workspace_path: str = Field(..., min_length=1)


class SettingsResponse(BaseModel):
    workspace_path: str
    workspace_exists: bool
    github_configured: bool


class ErrorResponse(BaseModel):
    detail: str
