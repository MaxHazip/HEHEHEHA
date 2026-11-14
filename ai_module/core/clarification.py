"""Формирование недостающих полей и уточняющих вопросов.

Логика вынесена отдельно от модели: даже если LLM вернул вопросы,
backend получает согласованный и проверяемый набор missing_fields.
"""

from ai_module.core.schemas import (
    ClarificationQuestion,
    ExtractedFields,
    Impact,
    Intake,
    Priority,
)
from ai_module.core.taxonomy import required_fields

FIELD_LABELS: dict[str, str] = {
    "building": "Здание",
    "floor": "Этаж",
    "room": "Кабинет",
    "device": "Устройство",
    "ip_address": "IP-адрес",
    "serial_number": "Серийный номер",
    "hostname": "Имя компьютера",
    "object": "Объект",
}

_SCOPE_QUESTIONS = {
    "single_device": "Проблема наблюдается на одном устройстве?",
    "single_user": "Проблема только у вас или у коллег тоже?",
    "department": "Проблема наблюдается у всего отдела?",
    "building": "Проблема затрагивает всё здание?",
}


def get_field_value(extracted: ExtractedFields, field: str) -> str | None:
    """Достаёт значение по пути вида ``location.room``."""

    current = extracted
    for part in field.split("."):
        current = getattr(current, part, None)
        if current is None:
            return None
    if isinstance(current, str):
        value = current.strip()
        return value or None
    return None


def missing_field_paths(
    extracted: ExtractedFields,
    category_code: str,
    subcategory_code: str | None = None,
) -> list[str]:
    return [
        field
        for field in required_fields(category_code, subcategory_code)
        if get_field_value(extracted, field) is None
    ]


def _question_for(field: str, extracted: ExtractedFields) -> str:
    room = extracted.location.room
    building = extracted.location.building

    if field == "location.building":
        if room:
            return f"В каком здании находится кабинет {room}?"
        return "В каком здании находится проблема?"
    if field == "location.floor":
        return "На каком этаже находится проблема?"
    if field == "location.room":
        if building:
            return f"Уточните, пожалуйста, номер кабинета в {building}."
        return "Уточните, пожалуйста, номер кабинета."
    if field == "device":
        return "Какое устройство затронуто: компьютер, принтер, телефон или другое?"
    if field == "ip_address":
        return (
            "Какой IP-адрес у устройства? Если не знаете — напишите «не знаю»."
        )
    if field == "serial_number":
        return "Укажите серийный номер устройства, если он есть."
    if field == "hostname":
        return "Какое имя (hostname) у компьютера?"
    if field == "object":
        return "Какой объект или оборудование затронут?"
    return f"Уточните, пожалуйста, поле «{field}»."


def build_questions(
    extracted: ExtractedFields,
    missing_paths: list[str],
    impact: Impact,
    priority: Priority | None = None,
) -> list[ClarificationQuestion]:
    questions: list[ClarificationQuestion] = []

    for path in missing_paths:
        questions.append(
            ClarificationQuestion(
                field=path.split(".")[-1],
                question=_question_for(path, extracted),
            )
        )

    # Масштаб проблемы важен для оценки аварии, но не является
    # обязательным полем заявки. Поэтому спрашиваем, если он неизвестен.
    if impact.scope == "unknown":
        room = extracted.location.room
        if room:
            text = (
                f"Проблема наблюдается только в кабинете {room} "
                "или ещё где-то?"
            )
        else:
            text = "Проблема наблюдается на одном устройстве или на всех?"
        questions.append(
            ClarificationQuestion(field="impact_scope", question=text)
        )

    return questions


def build_intake(
    extracted: ExtractedFields,
    category_code: str,
    subcategory_code: str | None,
    impact: Impact,
    priority: Priority,
    overall_confidence: float,
    classification_status: str = "matched",
    extra_questions: list[ClarificationQuestion] | None = None,
) -> Intake:
    missing_paths = missing_field_paths(extracted, category_code, subcategory_code)

    questions = build_questions(extracted, missing_paths, impact, priority)

    # Добавляем вопросы модели, если они относятся к недостающим полям
    # или к масштабу проблемы. Остальные не показываем, чтобы не путать.
    allowed_fields = {path.split(".")[-1] for path in missing_paths}
    allowed_fields.add("impact_scope")
    if extra_questions:
        existing = {question.field for question in questions}
        for question in extra_questions:
            if (
                question.field in allowed_fields
                and question.field not in existing
                and question.question.strip()
            ):
                questions.append(question)
                existing.add(question.field)

    urgent = priority.suggested == "critical" or impact.scope in (
        "department",
        "building",
        "multiple_buildings",
    )

    ready = (
        not missing_paths
        and classification_status != "unclassified"
        and overall_confidence >= 0.6
    )

    if urgent:
        state = "urgent_escalation"
    elif ready:
        state = "ready_for_dispatcher"
    else:
        state = "collecting_info"

    return Intake(
        state=state,
        ready_for_dispatcher=ready or urgent,
        missing_fields=[path.split(".")[-1] for path in missing_paths],
        questions_to_client=questions,
    )
