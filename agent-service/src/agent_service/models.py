from typing import Literal

from pydantic import BaseModel, Field, field_validator


class Product(BaseModel):
    id: str
    name: str
    description: str
    price_cents: int
    category: str
    badge: str | None = None
    stock: int | None = None
    tags: list[str] = Field(default_factory=list)
    image_url: str | None = None


class ProductList(BaseModel):
    items: list[Product]
    total: int


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2_000)

    @field_validator("message")
    @classmethod
    def message_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("message must not be blank")
        return value


class ChatResponse(BaseModel):
    reply: str
    products: list[Product]


class ConversationMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=10_000)

    @field_validator("content")
    @classmethod
    def content_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("content must not be blank")
        return value


class StreamChatRequest(BaseModel):
    conversation_id: str | None = Field(default=None, max_length=64)
    message: str = Field(min_length=1, max_length=10_000)

    @field_validator("message")
    @classmethod
    def stream_message_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("message must not be blank")
        return value


class ToolTrace(BaseModel):
    call_id: str | None = None
    tool: str
    arguments: str = ""
    status: Literal["started", "completed", "failed"] = "started"
    summary: str | None = None


class StoredMessage(BaseModel):
    id: str
    role: Literal["user", "assistant"]
    content: str
    status: Literal["streaming", "completed", "failed"]
    created_at: str
    recommendations: list[Product] = Field(default_factory=list)
    tool_trace: list[ToolTrace] = Field(default_factory=list)


class ConversationSummary(BaseModel):
    id: str
    title: str
    message_count: int
    created_at: str
    updated_at: str


class ConversationDetail(ConversationSummary):
    messages: list[StoredMessage]


class ConversationList(BaseModel):
    items: list[ConversationSummary]
