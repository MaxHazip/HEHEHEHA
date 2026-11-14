from typing import Literal

from pydantic import BaseModel, Field


class AnalyzeTextRequest(BaseModel):
    """Анализ произвольного текста без сохранения заявки."""

    text: str = Field(min_length=1, max_length=20_000)
    source: Literal["chat", "web", "phone"] = "chat"


class AnalyzeTicketRequest(BaseModel):
    """Повторный анализ заявки. force=True запускает модель заново."""

    force: bool = False
