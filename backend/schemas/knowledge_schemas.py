from pydantic import BaseModel, Field


class KnowledgeArticleRead(BaseModel):
    id: int
    code: str
    title: str
    body: str
    keywords: list[str] = Field(default_factory=list)
    score: float | None = None


class KnowledgeStatus(BaseModel):
    enabled: bool
    qdrant_available: bool
    indexed: bool
    collection: str
    embedding_model: str
    articles: int
