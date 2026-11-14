"""Валидация и нормализация ответа ИИ.

Модель может вернуть лишние поля, неверные коды или неполный JSON.
Здесь всё приводится к единому контракту ``TicketAIResult``.
"""

import json
from typing import Any

from ai_module.core.clarification import build_intake
from ai_module.core.schemas import (
    ClarificationQuestion,
    Classification,
    Confidence,
    ExtractedFields,
    Impact,
    Issue,
    Priority,
    TicketAIResult,
    VisualObservation,
)
from ai_module.core.taxonomy import (
    IMPACT_SCOPES,
    PRIORITIES,
    action_codes,
    category_by_code,
    is_valid_category,
    is_valid_subcategory,
    symptom_codes,
)


def clamp01(value: Any, default: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return max(0.0, min(1.0, number))


def as_text(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def text_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    result: list[str] = []
    for item in value:
        text = as_text(item)
        if text and text not in result:
            result.append(text)
    return result


def filter_codes(values: Any, allowed: set[str]) -> list[str]:
    return [code for code in text_list(values) if code in allowed]


def extract_json_object(raw: str) -> dict:
    """Достаёт JSON-объект из ответа модели, даже если он в ```-блоке."""

    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
        text = text.strip()

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end < start:
        raise ValueError("В ответе модели нет JSON-объекта")

    return json.loads(text[start : end + 1])


def _parse_questions(raw: Any) -> list[ClarificationQuestion]:
    if not isinstance(raw, list):
        return []

    questions: list[ClarificationQuestion] = []
    for item in raw:
        if isinstance(item, str):
            text = as_text(item)
            if text:
                questions.append(
                    ClarificationQuestion(field="clarification", question=text)
                )
        elif isinstance(item, dict):
            question = as_text(item.get("question"))
            field = as_text(item.get("field")) or "clarification"
            if question:
                questions.append(
                    ClarificationQuestion(field=field, question=question)
                )
    return questions


def extract_extra_questions(
    payload: dict | None,
) -> list[ClarificationQuestion]:
    """Достаёт вопросы модели из нового или старого формата ответа."""

    if not isinstance(payload, dict):
        return []

    questions = _parse_questions(payload.get("clarification_questions"))
    intake_source = payload.get("intake")
    if isinstance(intake_source, dict):
        questions.extend(
            _parse_questions(intake_source.get("questions_to_client"))
        )
    return questions


def _merge_classification(
    result: TicketAIResult, payload: dict
) -> None:
    source = payload.get("classification")
    if not isinstance(source, dict):
        source = {
            "category_code": payload.get("category"),
            "subcategory_code": payload.get("subcategory"),
        }

    category_code = as_text(source.get("category_code"))
    subcategory_code = as_text(source.get("subcategory_code"))

    if not is_valid_category(category_code):
        # Категория не определена — оставляем базовую (обычно "none").
        return

    if not is_valid_subcategory(category_code, subcategory_code):
        subcategory_code = None

    category = category_by_code(category_code)
    subcategory = None
    if category and subcategory_code:
        subcategory = next(
            (
                item
                for item in category.subcategories
                if item.code == subcategory_code
            ),
            None,
        )

    status = "matched" if subcategory else "category_only"
    if category_code == "other":
        status = "unclassified"

    result.classification = Classification(
        category_id=category.id if category else None,
        category_code=category_code,
        subcategory_id=subcategory.id if subcategory else None,
        subcategory_code=subcategory_code or "none",
        status=status,  # type: ignore[arg-type]
    )


def _merge_extracted(result: TicketAIResult, payload: dict) -> None:
    source = payload.get("extracted_fields")
    if not isinstance(source, dict):
        source = payload

    location = source.get("location")
    if not isinstance(location, dict):
        location = {}

    extracted: ExtractedFields = result.extracted_fields

    for field in ("building", "floor", "room"):
        value = as_text(location.get(field)) or as_text(source.get(field))
        if value:
            setattr(extracted.location, field, value)

    for field in ("device", "ip_address", "serial_number", "hostname", "object"):
        value = as_text(source.get(field))
        if value:
            setattr(extracted, field, value)

    # Серийный номер и IP из плоского старого контракта.
    if not extracted.serial_number:
        extracted.serial_number = as_text(payload.get("serial_number"))
    if not extracted.ip_address:
        extracted.ip_address = as_text(payload.get("ip_address"))


def _merge_issue(result: TicketAIResult, payload: dict) -> None:
    source = payload.get("issue")
    if not isinstance(source, dict):
        source = {}

    description = as_text(source.get("description"))
    if description:
        result.issue.description = description[:1000]

    symptoms = source.get("symptoms", payload.get("symptoms"))
    cleaned_symptoms = filter_codes(symptoms, symptom_codes())
    if cleaned_symptoms:
        result.issue.symptoms = cleaned_symptoms

    actions = source.get(
        "attempted_actions", payload.get("attempted_actions")
    )
    cleaned_actions = filter_codes(actions, action_codes())
    if cleaned_actions:
        result.issue.attempted_actions = cleaned_actions

    impact_source = source.get("impact")
    if not isinstance(impact_source, dict):
        impact_source = payload.get("impact")
    if isinstance(impact_source, dict):
        scope = as_text(impact_source.get("scope"))
        if scope in IMPACT_SCOPES:
            result.issue.impact.scope = scope
        count = impact_source.get("affected_users_count")
        if isinstance(count, int) and count >= 0:
            result.issue.impact.affected_users_count = count
        unavailable = impact_source.get("service_unavailable")
        if isinstance(unavailable, bool):
            result.issue.impact.service_unavailable = unavailable


def _merge_priority(result: TicketAIResult, payload: dict) -> None:
    source = payload.get("priority")
    if not isinstance(source, dict):
        source = {}

    suggested = as_text(source.get("suggested")) or as_text(
        payload.get("suggested_priority")
    )
    if suggested in PRIORITIES:
        result.priority.suggested = suggested  # type: ignore[assignment]

    reasons = text_list(source.get("reasons"))
    if reasons:
        result.priority.reasons = reasons


def _merge_confidence(result: TicketAIResult, payload: dict) -> None:
    source = payload.get("confidence")

    if isinstance(source, (int, float)):
        result.confidence = Confidence(
            classification=clamp01(source, result.confidence.classification),
            extraction=clamp01(source, result.confidence.extraction),
            overall=clamp01(source, result.confidence.overall),
        )
        return

    if isinstance(source, dict):
        result.confidence = Confidence(
            classification=clamp01(
                source.get("classification"),
                result.confidence.classification,
            ),
            extraction=clamp01(
                source.get("extraction"),
                result.confidence.extraction,
            ),
            overall=clamp01(
                source.get("overall"),
                result.confidence.overall,
            ),
        )


def _merge_visual(
    result: TicketAIResult, payload: dict
) -> None:
    source = payload.get("visual_observations")
    if not isinstance(source, list):
        return

    observations: list[VisualObservation] = []
    for item in source:
        if not isinstance(item, dict):
            continue
        attachment_id = as_text(item.get("attachment_id"))
        description = as_text(item.get("description"))
        if not attachment_id or not description:
            continue
        observations.append(
            VisualObservation(
                attachment_id=attachment_id,
                description=description[:1000],
                related_symptoms=filter_codes(
                    item.get("related_symptoms"), symptom_codes()
                ),
                confidence=(
                    clamp01(item.get("confidence"))
                    if item.get("confidence") is not None
                    else None
                ),
            )
        )

    if observations:
        result.visual_observations = observations


def merge_payload(
    baseline: TicketAIResult,
    payload: dict | None,
    extra_questions: list[ClarificationQuestion] | None = None,
) -> TicketAIResult:
    """Совмещает проверенный базовый результат с ответом модели."""

    result = baseline.model_copy(deep=True)
    if not isinstance(payload, dict):
        return finalize_result(result, extra_questions)

    _merge_classification(result, payload)
    _merge_extracted(result, payload)
    _merge_issue(result, payload)
    _merge_priority(result, payload)
    _merge_confidence(result, payload)
    _merge_visual(result, payload)

    if isinstance(payload.get("needs_human_review"), bool):
        result.needs_human_review = payload["needs_human_review"]

    reasoning = as_text(payload.get("reasoning"))
    if reasoning:
        note = f"Модель: {reasoning}"
        if note not in result.decision_notes:
            result.decision_notes.append(note)

    return finalize_result(result, extract_extra_questions(payload))


def finalize_result(
    result: TicketAIResult,
    extra_questions: list[ClarificationQuestion] | None = None,
) -> TicketAIResult:
    """Пересчитывает intake и защитные флаги по фактическим данным."""

    classification = result.classification
    if classification.status == "unclassified":
        result.confidence.overall = min(result.confidence.overall, 0.4)

    result.intake = build_intake(
        extracted=result.extracted_fields,
        category_code=classification.category_code,
        subcategory_code=classification.subcategory_code,
        impact=result.issue.impact,
        priority=result.priority,
        overall_confidence=result.confidence.overall,
        classification_status=classification.status,
        extra_questions=extra_questions,
    )

    result.requires_clarification = bool(
        result.intake.questions_to_client
    ) or not result.intake.ready_for_dispatcher

    risky_scope = result.issue.impact.scope in (
        "department",
        "building",
        "multiple_buildings",
    )
    if (
        result.confidence.overall < 0.65
        or classification.status == "unclassified"
        or result.priority.suggested in ("critical", "needs_review")
        or risky_scope
    ):
        result.needs_human_review = True

    result.decision_notes = list(dict.fromkeys(result.decision_notes))
    return result


def apply_operator_overrides(
    result: TicketAIResult,
    overrides: dict,
    extra_questions: list[ClarificationQuestion] | None = None,
) -> TicketAIResult:
    """Применяет подтверждённые диспетчером значения."""

    if not overrides:
        return result

    result = result.model_copy(deep=True)
    extracted = result.extracted_fields

    flat_fields = {
        "building": ("location", "building"),
        "floor": ("location", "floor"),
        "room": ("location", "room"),
        "device": (None, "device"),
        "ip_address": (None, "ip_address"),
        "serial_number": (None, "serial_number"),
        "hostname": (None, "hostname"),
        "object": (None, "object"),
    }

    for key, (location_field, field) in flat_fields.items():
        if key not in overrides:
            continue
        value = as_text(overrides[key])
        if not value:
            continue
        if location_field:
            setattr(extracted.location, field, value)
        else:
            setattr(extracted, field, value)

    category_code = as_text(overrides.get("category_code"))
    if is_valid_category(category_code):
        subcategory_code = as_text(overrides.get("subcategory_code"))
        if not is_valid_subcategory(category_code, subcategory_code):
            subcategory_code = None
        category = category_by_code(category_code)
        subcategory = None
        if category and subcategory_code:
            subcategory = next(
                (
                    item
                    for item in category.subcategories
                    if item.code == subcategory_code
                ),
                None,
            )
        result.classification = Classification(
            category_id=category.id if category else None,
            category_code=category_code,
            subcategory_id=subcategory.id if subcategory else None,
            subcategory_code=subcategory_code or "none",
            status=(
                "unclassified"
                if category_code == "other"
                else "matched" if subcategory else "category_only"
            ),
        )

    priority = as_text(overrides.get("priority"))
    if priority in PRIORITIES:
        result.priority.suggested = priority  # type: ignore[assignment]

    return finalize_result(result, extra_questions)
