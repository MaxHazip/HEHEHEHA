from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    text: str = Field(default="", max_length=20_000)
    attachment_ids: list[int] = Field(default_factory=list)


class ChatReply(BaseModel):
    reply: str
    ticket_id: int
