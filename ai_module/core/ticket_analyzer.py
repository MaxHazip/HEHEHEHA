
from core.schemas import TicketAnalysis
from core.prompts import SYSTEM_PROMPT


def call_llm(user_text: str) -> dict:
    """
    ЗЗаглушка пока что.

    Здесь будет подключение языковой модели.
    Она должна возвращать обычный Python dict,
    соответствующий TicketAnalysis.

    Позже подключим OpenAI API, другой совместимый
    API или локальную модель через Ollama.
    """

    raise NotImplementedError(
        "Подключение LLM пока не настроено"
    )


def analyze_ticket(user_text: str) -> dict:
    """
    Главная функция анализа обращения.

    Вход: текст пользователя.
    Выход: структурированный JSON в виде dict.
    """

    if not user_text or not user_text.strip():
        raise ValueError("Текст обращения пустой")

    raw_result = call_llm(user_text)

    # Проверяем структуру ответа
    analysis = TicketAnalysis.model_validate(raw_result)

    return analysis.model_dump(mode="json")
