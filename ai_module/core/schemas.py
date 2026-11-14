
from typing import Optional, Literal
from pydantic import BaseModel, Field, ConfigDict
#settings

class BaseSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")
#данные
class Message(BaseSchema):
    message_id: Optional[str] = None

    role: Literal[
        "client",
        "bot",
        "dispatcher"
    ]

    text: str

    created_at: Optional[str] = None


class Attachment(BaseSchema):
    attachment_id: str

    type: Literal[
        "image",
        "audio",
        "document"
    ]

    storage_path: str

    mime_type: Optional[str] = None

    description: Optional[str] = None


#category справочник

class TaxonomySubcategory(BaseSchema):
    id: int
    code: str
    name: str

    description: Optional[str] = None

    required_fields: list[str] = Field(
        default_factory=list
    )


class TaxonomyCategory(BaseSchema):
    id: int
    code: str
    name: str

    description: Optional[str] = None

    required_fields: list[str] = Field(
        default_factory=list
    )

    subcategories: list[TaxonomySubcategory] = Field(
        default_factory=list
    )


#Исправление диспетчера

class OperatorOverrides(BaseSchema):
    """
    Ручные исправления диспетчера.

    Backend передаёт сюда только те значения,
    которые диспетчер уже подтвердил или исправил.
    """

    fields: dict = Field(
        default_factory=dict
    )


# вход для ai

class AnalysisRequest(BaseSchema):

    schema_version: str = "1.0"

    ticket_id: str

    source: Literal[
        "chat",
        "web",
        "phone"
    ]

    messages: list[Message] = Field(
        min_length=1
    )

    taxonomy_version: str

    taxonomy: list[TaxonomyCategory]

    attachments: list[Attachment] = Field(
        default_factory=list
    )

    operator_overrides: OperatorOverrides = Field(
        default_factory=OperatorOverrides
    )


#класификация

class Classification(BaseSchema):

    category_id: Optional[int] = None

    category_code: str = "none"

    subcategory_id: Optional[int] = None

    subcategory_code: str = "none"

    status: Literal[
        "matched",
        "category_only",
        "unclassified"
    ]


#полученные данные

class Location(BaseSchema):

    building: Optional[str] = None

    floor: Optional[str] = None

    room: Optional[str] = None


class ExtractedFields(BaseSchema):

    object: Optional[str] = None

    location: Location = Field(
        default_factory=Location
    )

    device: Optional[str] = None

    ip_address: Optional[str] = None

    serial_number: Optional[str] = None

    hostname: Optional[str] = None


#определения маштаба и типа проблеммы

class Impact(BaseSchema):

    scope: Literal[
        "single_device",
        "single_user",
        "department",
        "building",
        "multiple_buildings",
        "unknown"
    ] = "unknown"

    affected_users_count: Optional[int] = Field(
        default=None,
        ge=0
    )

    service_unavailable: Optional[bool] = None


class Issue(BaseSchema):

    description: Optional[str] = None

    symptoms: list[str] = Field(
        default_factory=list
    )

    attempted_actions: list[str] = Field(
        default_factory=list
    )

    impact: Impact = Field(
        default_factory=Impact
    )


#приорететы

class Priority(BaseSchema):

    suggested: Literal[
        "low",
        "medium",
        "high",
        "critical",
        "needs_review"
    ]

    reasons: list[str] = Field(
        default_factory=list
    )


#уточняющие вопросы

class ClarificationQuestion(BaseSchema):

    field: str

    question: str


class Intake(BaseSchema):

    state: Literal[
        "collecting_info",
        "ready_for_dispatcher",
        "urgent_escalation"
    ]

    ready_for_dispatcher: bool

    missing_fields: list[str] = Field(
        default_factory=list
    )

    questions_to_client: list[ClarificationQuestion] = Field(
        default_factory=list
    )


#оценка уверенности

class Confidence(BaseSchema):

    classification: float = Field(
        ge=0,
        le=1
    )

    extraction: float = Field(
        ge=0,
        le=1
    )

    overall: float = Field(
        ge=0,
        le=1
    )


#info img

class VisualObservation(BaseSchema):

    attachment_id: str

    description: str

    related_symptoms: list[str] = Field(
        default_factory=list
    )

    confidence: Optional[float] = Field(
        default=None,
        ge=0,
        le=1
    )


#final result

class TicketAIResult(BaseSchema):

    schema_version: str = "1.0"

    ticket_id: str

    intake: Intake

    classification: Classification

    extracted_fields: ExtractedFields

    issue: Issue

    priority: Priority

    confidence: Confidence

    requires_clarification: bool

    needs_human_review: bool = True

    decision_notes: list[str] = Field(
        default_factory=list
    )

    visual_observations: list[VisualObservation] = Field(
        default_factory=list
    )
