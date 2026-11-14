"""Анализатор обращений.

Стратегия:
1. Всегда строится детерминированный результат на правилах (офлайн).
2. Если настроена Google Gemini, её JSON аккуратно накладывается сверху
   и проверяется по справочникам.
3. Итог всегда соответствует контракту ``TicketAIResult``.

Так демо не зависит от внешнего API, а при наличии ключа получает
качество языковой модели.
"""

import logging
import re

from ai_module.core.schemas import (
    AnalysisRequest,
    Classification,
    Confidence,
    ExtractedFields,
    Impact,
    Intake,
    Issue,
    Location,
    Priority,
    TicketAIResult,
    VisualObservation,
)
from ai_module.core.taxonomy import (
    ATTEMPTED_ACTIONS,
    category_by_code,
    subcategory_by_code,
)
from ai_module.core.validator import (
    apply_operator_overrides,
    clamp01,
    extract_extra_questions,
    merge_payload,
)
from ai_module.providers.text_provider import (
    RuleBasedTextProvider,
    TextProvider,
    build_text_provider,
)

logger = logging.getLogger(__name__)

# --- Словари для офлайн-анализа -------------------------------------------

CATEGORY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "network": (
        "интернет",
        "сетев",
        "сеть",
        "wi-fi",
        "wifi",
        "вайфай",
        "dhcp",
        "dns",
        "vpn",
        "впн",
        "роутер",
        "коммутатор",
        "пинг",
        "ping",
        "подключен",
    ),
    "hardware": (
        "компьютер",
        "ноутбук",
        "системный блок",
        "принтер",
        "мфу",
        "картридж",
        "монитор",
        "клавиатур",
        "мыш",
        "сканер",
        "не включается",
        "блок питания",
        "жестк",
        "ssd",
    ),
    "software": (
        "программа",
        "приложение",
        "windows",
        "виндовс",
        "1с",
        "excel",
        "word",
        "outlook",
        "почт",
        "обновлен",
        "лиценз",
        "синий экран",
        "bsod",
    ),
    "phone": (
        "sip",
        "сип",
        "телефони",
        "телефон",
        "гудок",
        "звонок",
        "не дозвониться",
        "станция",
        "микрофон",
        "динамик",
    ),
    "access": (
        "пароль",
        "доступ",
        "учетн",
        "учётн",
        "аккаунт",
        "логин",
        "заблокирован",
        "права доступа",
    ),
}

SUBCATEGORY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "network:no_internet": (
        "нет интернет",
        "интернета нет",
        "пропал интернет",
        "интернет пропал",
        "не работает интернет",
        "интернет не работает",
        "без интернета",
    ),
    "network:connection_error": (
        "не подключа",
        "ошибка подключ",
        "не получает ip",
        "ограничено",
        "не выходит в интернет",
        "соединени",
    ),
    "network:wifi": ("wifi", "wi-fi", "вайфай", "беспровод"),
    "network:slow_connection": (
        "медленн",
        "низк",
        "скорост",
        "тормозит интернет",
    ),
    "network:vpn": ("vpn", "впн"),
    "hardware:computer": (
        "компьютер",
        "пк",
        "ноутбук",
        "системный блок",
        "не включается",
    ),
    "hardware:printer": (
        "принтер",
        "мфу",
        "печата",
        "картридж",
        "бумаг",
        "сканер",
    ),
    "hardware:monitor": ("монитор", "экран", "изображени"),
    "hardware:peripheral": ("клавиатур", "мыш", "наушник", "колонк"),
    "hardware:power": ("питани", "розетк", "блок питания", "не включается"),
    "software:application_error": (
        "программа",
        "приложение",
        "1с",
        "excel",
        "word",
        "браузер",
        "ошибка",
    ),
    "software:os_problem": (
        "windows",
        "виндовс",
        "операционн",
        "синий экран",
        "не загружа",
    ),
    "software:mail": ("почт", "outlook", "письм", "email"),
    "software:license": ("лиценз", "активац", "ключ"),
    "software:update": ("обновлен", "апдейт", "update"),
    "phone:no_signal": (
        "нет гудка",
        "нет сигнала",
        "не звонит",
        "телефон не работает",
    ),
    "phone:no_audio": (
        "нет звука",
        "не слышно",
        "микрофон",
        "динамик",
    ),
    "phone:sip_registration": ("sip", "сип", "регистрац", "станция"),
    "phone:call_quality": (
        "качество связи",
        "прерывается",
        "хрипит",
        "эхо",
    ),
    "access:account": ("учетн", "учётн", "аккаунт", "логин"),
    "access:password": ("пароль", "сброс пароля", "не помню пароль"),
    "access:permissions": ("права", "доступ", "запрещен"),
}

SYMPTOM_PATTERNS: dict[str, tuple[str, ...]] = {
    "no_internet": (
        r"нет интернет",
        r"интернета нет",
        r"не работает интернет",
        r"интернет\w* не работает",
        r"пропал интернет",
        r"интернет\w* пропал",
        r"без интернета",
    ),
    "connection_error": (
        r"не подключа",
        r"ошибк\w* подключ",
        r"ограничено",
        r"не получает ip",
        r"соединени",
    ),
    "slow_connection": (
        r"медленн\w* интернет",
        r"низк\w* скорость",
        r"тормозит интернет",
        r"лагает",
    ),
    "no_power": (
        r"не включается",
        r"не включ",
        r"нет питания",
        r"не горит",
    ),
    "blue_screen": (r"синий экран", r"bsod", r"экран смерти"),
    "slow_performance": (
        r"тормоз",
        r"медленн",
        r"долго загруж",
        r"зависа",
        r"лагает",
    ),
    "no_audio": (r"нет звука", r"не слышно", r"микрофон", r"динамик"),
    "no_signal": (r"нет сигнала", r"нет гудка", r"не звонит"),
    "error_message": (r"ошибк", r"error", r"исключени"),
    "paper_jam": (r"замят", r"застрял\w* бумаг"),
    "no_print": (r"не печата", r"принтер не"),
    "cannot_login": (
        r"не могу войти",
        r"не входит",
        r"не удает\w* войти",
        r"не получает\w* войти",
    ),
    "account_locked": (
        r"заблокирован\w* (учет|учёт|аккаунт|пользоват)",
        r"блокировк\w* (учет|учёт|аккаунт)",
    ),
    "vpn_error": (r"vpn", r"впн"),
    "reboot_loop": (
        r"перезагружается сам",
        r"циклическ\w* перезагруз",
        r"перезагружается постоянно",
    ),
}

ACTION_PATTERNS: dict[str, tuple[str, ...]] = {
    "reboot": (
        r"перезагруз",
        r"перезапуст\w* (комп|пк|устройств|ноутбук)",
        r"выключ\w* и включ",
    ),
    "reconnect_cable": (
        r"переподключ",
        r"переткну",
        r"проверил кабель",
        r"вынул кабель",
    ),
    "reinstall": (r"переустанов",),
    "restart_service": (r"перезапуст\w* служб", r"перезапуст\w* сервис"),
    "check_power": (r"проверил питани", r"розетк", r"блок питания"),
}

RU_NUMBERS = {
    "перв": "1",
    "втор": "2",
    "трет": "3",
    "четверт": "4",
    "пят": "5",
    "шест": "6",
    "седьм": "7",
    "восьм": "8",
    "девят": "9",
    "десят": "10",
}

ROOM_RE = re.compile(
    r"(?:кабинет\w*|каб\.?|аудитори\w*|ауд\.?|офис\w*)\s*[№#]?\s*"
    r"([0-9]{1,4}[а-яa-z]?)",
    re.IGNORECASE,
)
ROOM_FALLBACK_RE = re.compile(
    r"\bв\s+([0-9]{2,3}[а-яa-z]?)\b", re.IGNORECASE
)
BUILDING_RE = re.compile(
    r"(?:корпус\w*\s*[№#]?\s*([0-9]{1,3}))|([0-9]{1,3})\s*(?:-?\s*"
    r"(?:й|ий|ой|ом|ем|м))?\s*корпус",
    re.IGNORECASE,
)
BUILDING_WORD_RE = re.compile(
    r"(перв|втор|трет|четверт|пят|шест|седьм|восьм|девят|десят)\w*\s+корпус",
    re.IGNORECASE,
)
FLOOR_RE = re.compile(
    r"(?:этаж\w*\s*[№#]?\s*([0-9]{1,2}))|([0-9]{1,2})\s*(?:-?\s*"
    r"(?:й|ий|ой|ом|ем|м))?\s*этаж",
    re.IGNORECASE,
)
FLOOR_WORD_RE = re.compile(
    r"(перв|втор|трет|четверт|пят|шест|седьм|восьм|девят|десят)\w*\s+этаж",
    re.IGNORECASE,
)
IP_RE = re.compile(r"\b((?:\d{1,3}\.){3}\d{1,3})\b")
SERIAL_RE = re.compile(
    r"(?:серийн\w*\s*номер|s/n|sn)\s*[:\s№]*([A-Za-z0-9-]{4,})",
    re.IGNORECASE,
)
HOSTNAME_RE = re.compile(
    r"(?:hostname|имя компьютера|имя пк)\s*[:\s]*([A-Za-z0-9._-]{3,})",
    re.IGNORECASE,
)
COUNT_RE = re.compile(
    r"(\d{1,3})\s*(?:компьютер\w*|пк|человек\w*|сотрудник\w*)",
    re.IGNORECASE,
)

DEVICE_KEYWORDS = (
    ("принтер", "printer"),
    ("мфу", "printer"),
    ("сканер", "scanner"),
    ("монитор", "monitor"),
    ("ноутбук", "laptop"),
    ("компьютер", "computer"),
    ("пк", "computer"),
    ("телефон", "ip_phone"),
    ("клавиатур", "keyboard"),
    ("мыш", "mouse"),
)


def _any(patterns: tuple[str, ...], text: str) -> bool:
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)


def _first_group(pattern: re.Pattern[str], text: str) -> str | None:
    match = pattern.search(text)
    if not match:
        return None
    for group in match.groups():
        if group:
            return group.strip()
    return None


def _count_matches(keywords: tuple[str, ...], text: str) -> int:
    return sum(1 for keyword in keywords if keyword in text)


def _extract_room(text: str) -> str | None:
    room = _first_group(ROOM_RE, text)
    if room:
        return room

    for match in ROOM_FALLBACK_RE.finditer(text):
        candidate = match.group(1)
        tail = text[match.end() : match.end() + 12].lower()
        if re.match(r"\s*(?:корпус|этаж)", tail):
            continue
        return candidate
    return None


def _extract_building(text: str) -> str | None:
    number = _first_group(BUILDING_RE, text)
    if number:
        return number

    match = BUILDING_WORD_RE.search(text)
    if match:
        return RU_NUMBERS.get(match.group(1).lower())
    return None


def _extract_floor(text: str) -> str | None:
    number = _first_group(FLOOR_RE, text)
    if number:
        return number

    match = FLOOR_WORD_RE.search(text)
    if match:
        return RU_NUMBERS.get(match.group(1).lower())
    return None


def _extract_device(text: str) -> str | None:
    for keyword, device in DEVICE_KEYWORDS:
        if keyword in text:
            return device
    return None


def _classify(text: str) -> tuple[str, str | None, int, list[str]]:
    scores = {
        code: _count_matches(keywords, text)
        for code, keywords in CATEGORY_KEYWORDS.items()
    }
    best_code = max(scores, key=lambda code: scores[code])
    best_score = scores[best_code]

    if best_score == 0:
        return "other", None, 0, []

    matched = [
        keyword
        for keyword in CATEGORY_KEYWORDS[best_code]
        if keyword in text
    ]

    category = category_by_code(best_code)
    subcategory_code: str | None = None
    best_sub_score = 0
    if category:
        for subcategory in category.subcategories:
            key = f"{best_code}:{subcategory.code}"
            score = _count_matches(SUBCATEGORY_KEYWORDS.get(key, ()), text)
            if score > best_sub_score:
                best_sub_score = score
                subcategory_code = subcategory.code

    return best_code, subcategory_code, best_score, matched


def _detect_impact(text: str) -> Impact:
    count_match = COUNT_RE.search(text)
    count = int(count_match.group(1)) if count_match else None

    if "нескольк" in text and "здан" in text:
        return Impact(scope="multiple_buildings", affected_users_count=count)
    if (
        "все здан" in text
        or "всё здан" in text
        or "весь корпус" in text
        or "всем здан" in text
    ):
        return Impact(scope="building", affected_users_count=count)
    if (
        "у всех" in text
        or "весь отдел" in text
        or "всем отдел" in text
        or "все сотрудник" in text
        or "у коллег" in text
    ):
        return Impact(scope="department", affected_users_count=count)
    if "один компьютер" in text or "одном компьютер" in text or "одно устройств" in text:
        return Impact(scope="single_device", affected_users_count=1)
    if "у меня" in text or "у себя" in text:
        return Impact(scope="single_user", affected_users_count=1)
    return Impact(scope="unknown", affected_users_count=count)


def _detect_priority(
    text: str,
    category_code: str,
    impact: Impact,
    symptoms: list[str],
) -> Priority:
    reasons: list[str] = []

    critical_markers = (
        "авари",
        "пожар",
        "затоп",
        "дым",
        "все здан",
        "весь корпус",
        "все сервер",
        "не работает весь",
    )
    high_markers = (
        "срочно",
        "очень нужно",
        "остановил",
        "критично",
        "у всех",
        "весь отдел",
        "сервер",
        "бухгалтер",
    )
    low_markers = (
        "не срочно",
        "некритично",
        "не критично",
        "когда будет время",
        "косметич",
    )

    if _any(critical_markers, text) or impact.scope in (
        "building",
        "multiple_buildings",
    ):
        reasons.append("Обнаружены признаки массовой аварии.")
        return Priority(suggested="critical", reasons=reasons)

    if _any(high_markers, text) or impact.scope == "department":
        reasons.append("Проблема затрагивает нескольких пользователей.")
        return Priority(suggested="high", reasons=reasons)

    if _any(low_markers, text):
        reasons.append("Признаков срочности нет.")
        return Priority(suggested="low", reasons=reasons)

    reasons.append("Стандартный приоритет: срочность не подтверждена.")
    return Priority(suggested="medium", reasons=reasons)


def _detect_symptoms(text: str) -> list[str]:
    symptoms = [
        code
        for code, patterns in SYMPTOM_PATTERNS.items()
        if _any(patterns, text)
    ]
    return symptoms


def _detect_actions(text: str) -> list[str]:
    return [
        code
        for code, patterns in ACTION_PATTERNS.items()
        if _any(patterns, text)
    ]


def _collect_text(request: AnalysisRequest) -> str:
    client_messages = [
        message.text for message in request.messages if message.role == "client"
    ]
    texts = client_messages or [message.text for message in request.messages]
    texts.extend(
        attachment.description
        for attachment in request.attachments
        if attachment.description
    )
    return "\n".join(text for text in texts if text).strip()


def analyze_rule_based(request: AnalysisRequest) -> TicketAIResult:
    """Детерминированный анализ без внешней модели."""

    text = _collect_text(request)
    lower = text.lower()

    category_code, subcategory_code, category_score, matched = _classify(lower)

    if category_code == "other":
        classification = Classification(
            category_id=category_by_code("other").id,  # type: ignore[union-attr]
            category_code="other",
            subcategory_id=None,
            subcategory_code="unknown",
            status="unclassified",
        )
    else:
        category = category_by_code(category_code)
        subcategory = subcategory_by_code(category_code, subcategory_code)
        classification = Classification(
            category_id=category.id if category else None,
            category_code=category_code,
            subcategory_id=subcategory.id if subcategory else None,
            subcategory_code=subcategory_code or "none",
            status="matched" if subcategory else "category_only",
        )

    room = _extract_room(text)
    building = _extract_building(text)
    floor = _extract_floor(text)
    device = _extract_device(lower)
    ip_address = _first_group(IP_RE, text)
    serial_number = _first_group(SERIAL_RE, text)
    hostname = _first_group(HOSTNAME_RE, text)

    extracted = ExtractedFields(
        location=Location(building=building, floor=floor, room=room),
        device=device,
        ip_address=ip_address,
        serial_number=serial_number,
        hostname=hostname,
    )

    symptoms = _detect_symptoms(lower)
    actions = _detect_actions(lower)
    impact = _detect_impact(lower)
    priority = _detect_priority(lower, category_code, impact, symptoms)

    description = re.sub(r"\s+", " ", text).strip()[:400] or None

    notes: list[str] = []
    if matched:
        notes.append(
            "Категория определена по ключевым словам: "
            + ", ".join(matched[:6])
            + "."
        )
    else:
        notes.append(
            "Не удалось уверенно классифицировать обращение по ключевым словам."
        )

    if actions:
        action_names = [
            ATTEMPTED_ACTIONS.get(code, code) for code in actions
        ]
        notes.append("Пользователь уже выполнил: " + ", ".join(action_names) + ".")

    if impact.scope != "unknown":
        notes.append(f"Масштаб проблемы: {impact.scope}.")

    found_fields = sum(
        1
        for value in (
            room,
            building,
            floor,
            device,
            ip_address,
            serial_number,
            hostname,
        )
        if value
    )
    extraction_confidence = min(0.95, 0.35 + 0.1 * found_fields)

    if classification.status == "unclassified":
        classification_confidence = 0.2
    elif classification.status == "category_only":
        classification_confidence = 0.5
    else:
        classification_confidence = min(
            0.9, 0.6 + 0.05 * max(category_score - 1, 0)
        )

    overall = clamp01(
        classification_confidence * 0.6 + extraction_confidence * 0.4
    )
    if classification.status == "unclassified":
        overall = min(overall, 0.35)

    confidence = Confidence(
        classification=classification_confidence,
        extraction=extraction_confidence,
        overall=overall,
    )

    visual_observations = [
        VisualObservation(
            attachment_id=attachment.attachment_id,
            description=attachment.description,
            confidence=0.6,
        )
        for attachment in request.attachments
        if attachment.type == "image"
        and attachment.description
        and attachment.description.strip()
    ]

    return TicketAIResult(
        schema_version="1.0",
        ticket_id=request.ticket_id,
        intake=Intake(
            state="collecting_info",
            ready_for_dispatcher=False,
        ),
        classification=classification,
        extracted_fields=extracted,
        issue=Issue(
            description=description,
            symptoms=symptoms,
            attempted_actions=actions,
            impact=impact,
        ),
        priority=priority,
        confidence=confidence,
        requires_clarification=True,
        needs_human_review=True,
        decision_notes=notes,
        visual_observations=visual_observations,
    )


class TicketAnalyzer:
    """Оркестратор: офлайн-база + LLM + проверка контракта."""

    def __init__(self, provider: TextProvider | None = None) -> None:
        self.provider = provider if provider is not None else build_text_provider()
        self.last_provider = getattr(self.provider, "name", "rule-based")
        self.last_model = getattr(self.provider, "model", None)

    async def analyze(self, request: AnalysisRequest) -> TicketAIResult:
        baseline = analyze_rule_based(request)

        if isinstance(self.provider, RuleBasedTextProvider):
            result = merge_payload(baseline, None)
            return apply_operator_overrides(
                result,
                request.operator_overrides.fields,
                extract_extra_questions(None),
            )

        payload: dict | None = None
        try:
            payload = await self.provider.analyze(request)
            self.last_provider = self.provider.name
            self.last_model = self.provider.model
        except Exception as exc:  # noqa: BLE001
            logger.warning("LLM analysis failed: %s", exc)
            baseline.decision_notes.append(
                "Языковая модель недоступна, использован офлайн-анализ."
            )
            self.last_provider = "rule-based"
            self.last_model = None

        extra_questions = extract_extra_questions(payload)
        result = merge_payload(baseline, payload, extra_questions)
        result = apply_operator_overrides(
            result,
            request.operator_overrides.fields,
            extra_questions,
        )
        return result


_analyzer: TicketAnalyzer | None = None


def get_analyzer() -> TicketAnalyzer:
    global _analyzer
    if _analyzer is None:
        _analyzer = TicketAnalyzer()
    return _analyzer
