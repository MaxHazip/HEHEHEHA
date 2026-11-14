"""Справочники системы: категории, подкатегории, симптомы, действия.

Коды из этого файла — единственный разрешённый набор значений.
Backend и ИИ обязаны использовать только их (требование ТЗ, п. 7).
"""

from ai_module.core.schemas import (
    TaxonomyCategory,
    TaxonomySubcategory,
)

TAXONOMY_VERSION = "1.0"

# Категории и подкатегории обращений.
TAXONOMY: list[TaxonomyCategory] = [
    TaxonomyCategory(
        id=1,
        code="network",
        name="Сеть и интернет",
        description="Проблемы с подключением, Wi-Fi, VPN, DHCP и сетевой инфраструктурой.",
        required_fields=["location.building", "location.room"],
        subcategories=[
            TaxonomySubcategory(
                id=11,
                code="no_internet",
                name="Нет доступа в интернет",
                required_fields=["ip_address"],
            ),
            TaxonomySubcategory(
                id=12,
                code="connection_error",
                name="Ошибка подключения",
                required_fields=["ip_address"],
            ),
            TaxonomySubcategory(
                id=13,
                code="wifi",
                name="Проблемы с Wi-Fi",
            ),
            TaxonomySubcategory(
                id=14,
                code="slow_connection",
                name="Низкая скорость соединения",
            ),
            TaxonomySubcategory(
                id=15,
                code="vpn",
                name="Проблемы с VPN",
            ),
        ],
    ),
    TaxonomyCategory(
        id=2,
        code="hardware",
        name="Компьютеры и оборудование",
        description="Неисправности компьютеров, принтеров, мониторов и периферии.",
        required_fields=["location.building", "location.room", "device"],
        subcategories=[
            TaxonomySubcategory(
                id=21,
                code="computer",
                name="Компьютер / ноутбук",
            ),
            TaxonomySubcategory(
                id=22,
                code="printer",
                name="Принтер / МФУ",
            ),
            TaxonomySubcategory(
                id=23,
                code="monitor",
                name="Монитор",
            ),
            TaxonomySubcategory(
                id=24,
                code="peripheral",
                name="Периферия",
            ),
            TaxonomySubcategory(
                id=25,
                code="power",
                name="Питание оборудования",
            ),
        ],
    ),
    TaxonomyCategory(
        id=3,
        code="software",
        name="Программное обеспечение",
        description="Ошибки приложений, ОС, почты, лицензии и обновления.",
        required_fields=["location.room", "device"],
        subcategories=[
            TaxonomySubcategory(
                id=31,
                code="application_error",
                name="Ошибка приложения",
            ),
            TaxonomySubcategory(
                id=32,
                code="os_problem",
                name="Проблема операционной системы",
            ),
            TaxonomySubcategory(
                id=33,
                code="mail",
                name="Почта",
            ),
            TaxonomySubcategory(
                id=34,
                code="license",
                name="Лицензии",
            ),
            TaxonomySubcategory(
                id=35,
                code="update",
                name="Обновления",
            ),
        ],
    ),
    TaxonomyCategory(
        id=4,
        code="phone",
        name="Телефония",
        description="Проблемы с IP-телефонией, SIP-регистрацией и звуком при звонках.",
        required_fields=["location.room", "device"],
        subcategories=[
            TaxonomySubcategory(
                id=41,
                code="no_signal",
                name="Нет сигнала / гудка",
            ),
            TaxonomySubcategory(
                id=42,
                code="no_audio",
                name="Нет звука при звонке",
            ),
            TaxonomySubcategory(
                id=43,
                code="sip_registration",
                name="SIP-регистрация",
            ),
            TaxonomySubcategory(
                id=44,
                code="call_quality",
                name="Качество связи",
            ),
        ],
    ),
    TaxonomyCategory(
        id=5,
        code="access",
        name="Доступы и учётные записи",
        description="Пароли, блокировки, права доступа и учётные записи.",
        required_fields=["device"],
        subcategories=[
            TaxonomySubcategory(
                id=51,
                code="account",
                name="Учётная запись",
            ),
            TaxonomySubcategory(
                id=52,
                code="password",
                name="Пароль",
            ),
            TaxonomySubcategory(
                id=53,
                code="permissions",
                name="Права доступа",
            ),
        ],
    ),
    TaxonomyCategory(
        id=6,
        code="other",
        name="Прочее",
        description="Обращения, которые не удалось классифицировать.",
        required_fields=["location.room"],
        subcategories=[
            TaxonomySubcategory(
                id=61,
                code="unknown",
                name="Не определено",
            ),
        ],
    ),
]

# Разрешённые коды симптомов.
SYMPTOMS: dict[str, str] = {
    "no_internet": "Нет доступа в интернет",
    "connection_error": "Ошибка соединения",
    "slow_connection": "Низкая скорость соединения",
    "no_power": "Устройство не включается",
    "blue_screen": "Синий экран / BSOD",
    "slow_performance": "Устройство работает медленно",
    "no_audio": "Нет звука",
    "no_signal": "Нет сигнала",
    "error_message": "Сообщение об ошибке",
    "paper_jam": "Замятие бумаги",
    "no_print": "Принтер не печатает",
    "cannot_login": "Не удаётся войти",
    "account_locked": "Учётная запись заблокирована",
    "vpn_error": "Ошибка VPN",
    "reboot_loop": "Циклическая перезагрузка",
    "other": "Другое",
}

# Разрешённые действия, которые уже выполнил заявитель.
ATTEMPTED_ACTIONS: dict[str, str] = {
    "reboot": "Перезагрузка",
    "reconnect_cable": "Переподключение кабеля",
    "reinstall": "Переустановка",
    "restart_service": "Перезапуск службы",
    "check_power": "Проверка питания",
    "other": "Другое",
}

PRIORITIES = ("low", "medium", "high", "critical", "needs_review")
IMPACT_SCOPES = (
    "single_device",
    "single_user",
    "department",
    "building",
    "multiple_buildings",
    "unknown",
)

_CATEGORIES_BY_CODE = {category.code: category for category in TAXONOMY}


def get_taxonomy() -> list[TaxonomyCategory]:
    """Возвращает справочник для передачи в ИИ и backend."""

    return TAXONOMY


def category_by_code(code: str | None) -> TaxonomyCategory | None:
    if not code:
        return None
    return _CATEGORIES_BY_CODE.get(code)


def category_name(code: str | None) -> str:
    category = category_by_code(code)
    return category.name if category else "Не определено"


def subcategory_by_code(
    category_code: str | None, subcategory_code: str | None
) -> TaxonomySubcategory | None:
    category = category_by_code(category_code)
    if not category or not subcategory_code:
        return None
    for subcategory in category.subcategories:
        if subcategory.code == subcategory_code:
            return subcategory
    return None


def is_valid_category(code: str | None) -> bool:
    return code in _CATEGORIES_BY_CODE


def is_valid_subcategory(
    category_code: str | None, subcategory_code: str | None
) -> bool:
    return subcategory_by_code(category_code, subcategory_code) is not None


def required_fields(
    category_code: str | None, subcategory_code: str | None = None
) -> list[str]:
    """Поля, без которых заявку нельзя передать диспетчеру."""

    fields: list[str] = []
    category = category_by_code(category_code)
    if category:
        fields.extend(category.required_fields)
    subcategory = subcategory_by_code(category_code, subcategory_code)
    if subcategory:
        fields.extend(subcategory.required_fields)

    # Убираем дубли, сохраняя порядок.
    return list(dict.fromkeys(fields))


def symptom_codes() -> set[str]:
    return set(SYMPTOMS)


def action_codes() -> set[str]:
    return set(ATTEMPTED_ACTIONS)


def taxonomy_as_text() -> str:
    """Текстовое представление справочника для промпта."""

    lines: list[str] = []
    for category in TAXONOMY:
        fields = ", ".join(category.required_fields) or "нет"
        lines.append(
            f"- {category.code} ({category.name}); обязательные поля: {fields}"
        )
        for subcategory in category.subcategories:
            sub_fields = ", ".join(subcategory.required_fields)
            suffix = f"; обязательные поля: {sub_fields}" if sub_fields else ""
            lines.append(f"  - {subcategory.code} ({subcategory.name}){suffix}")
    return "\n".join(lines)
