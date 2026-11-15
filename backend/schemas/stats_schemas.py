from datetime import datetime

from pydantic import BaseModel, Field


class CountItem(BaseModel):
    name: str
    count: int


class HourlyItem(BaseModel):
    time: str
    tickets: int


class DailyItem(BaseModel):
    date: str
    created: int
    closed: int


class EngineersStats(BaseModel):
    total: int = 0
    available: int = 0
    load: int = 0


class EngineerLoadItem(BaseModel):
    id: int
    name: str
    competencies: list[str] = Field(default_factory=list)
    load: int = 0
    available: bool = True
    open_tickets: int = 0


class CallsStats(BaseModel):
    total: int = 0
    today: int = 0
    with_recording: int = 0
    with_transcript: int = 0


class AttachmentsStats(BaseModel):
    total: int = 0
    images: int = 0
    audio: int = 0
    video: int = 0
    documents: int = 0


class StatsResponse(BaseModel):
    total_tickets: int = 0
    new_tickets: int = 0
    draft_tickets: int = 0
    in_progress_tickets: int = 0
    resolved_tickets: int = 0
    closed_tickets: int = 0
    high_priority_tickets: int = 0
    unassigned_tickets: int = 0
    ai_review_tickets: int = 0
    mass_incident_tickets: int = 0
    sla_risks: int = 0
    completion_rate: float = 0.0
    avg_ai_confidence: float = 0.0
    avg_resolution_hours: float = 0.0
    manual_edits: int = 0
    by_status: list[CountItem] = Field(default_factory=list)
    by_priority: list[CountItem] = Field(default_factory=list)
    by_category: list[CountItem] = Field(default_factory=list)
    by_subcategory: list[CountItem] = Field(default_factory=list)
    by_channel: list[CountItem] = Field(default_factory=list)
    hourly: list[HourlyItem] = Field(default_factory=list)
    daily: list[DailyItem] = Field(default_factory=list)
    engineers: EngineersStats = Field(default_factory=EngineersStats)
    engineers_detail: list[EngineerLoadItem] = Field(default_factory=list)
    calls: CallsStats = Field(default_factory=CallsStats)
    attachments: AttachmentsStats = Field(default_factory=AttachmentsStats)
    knowledge_articles: int = 0
    generated_at: datetime
