from pydantic import BaseModel, Field


class TTSRequest(BaseModel):
    text: str = Field(min_length=1, max_length=5000)
    speaker: str | None = None
    language: str | None = None


class TranscriptionResponse(BaseModel):
    text: str
    provider: str
    language: str | None = None
    segments: list[dict] = Field(default_factory=list)


class VoiceChatResponse(BaseModel):
    transcript: str | None = None
    reply_text: str
    audio_base64: str | None = None
    audio_mime: str | None = None
    provider: str | None = None
