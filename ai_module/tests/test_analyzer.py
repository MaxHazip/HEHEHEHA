"""Тесты качества офлайн-анализатора и контракта."""

import asyncio
import os

import pytest

os.environ["AI_PROVIDER"] = "rule"
os.environ.pop("GOOGLE_API_KEY", None)
os.environ.pop("GEMINI_API_KEY", None)

from ai_module.core.analyzer import get_analyzer  # noqa: E402
from ai_module.core.schemas import (  # noqa: E402
    AnalysisRequest,
    Message,
    OperatorOverrides,
)
from ai_module.core.taxonomy import (  # noqa: E402
    TAXONOMY_VERSION,
    get_taxonomy,
    is_valid_category,
    is_valid_subcategory,
)


def _analyze(text: str, overrides: dict | None = None):
    request = AnalysisRequest(
        ticket_id="test",
        source="chat",
        messages=[Message(role="client", text=text)],
        taxonomy_version=TAXONOMY_VERSION,
        taxonomy=get_taxonomy(),
        operator_overrides=OperatorOverrides(fields=overrides or {}),
    )
    return asyncio.run(get_analyzer().analyze(request))


def test_contract_and_required_question() -> None:
    result = _analyze(
        "У меня в 305 кабинете не работает компьютер. "
        "Интернет пропал, перезагрузка не помогла."
    )

    assert result.classification.category_code == "network"
    assert result.classification.status in ("matched", "category_only")
    assert is_valid_category(result.classification.category_code)
    if result.classification.status == "matched":
        assert is_valid_subcategory(
            result.classification.category_code,
            result.classification.subcategory_code,
        )

    assert result.extracted_fields.location.room == "305"
    assert result.extracted_fields.device == "computer"
    assert "no_internet" in result.issue.symptoms
    assert "reboot" in result.issue.attempted_actions

    # В ТЗ ожидаются building и ip_address.
    assert "building" in result.intake.missing_fields
    question = " ".join(
        item.question for item in result.intake.questions_to_client
    )
    assert "кабинет" in question.lower() or "здани" in question.lower()
    assert result.intake.state == "collecting_info"
    assert 0 <= result.confidence.overall <= 1


def test_no_hallucinated_building() -> None:
    result = _analyze("Не работает интернет в кабинете 101.")
    assert result.extracted_fields.location.building is None
    assert result.extracted_fields.ip_address is None


def test_mass_outage_is_escalated() -> None:
    result = _analyze(
        "Интернет не работает у всех в здании, похоже на аварию."
    )
    assert result.priority.suggested == "critical"
    assert result.issue.impact.scope in (
        "department",
        "building",
        "multiple_buildings",
    )
    assert result.intake.state == "urgent_escalation"
    assert result.needs_human_review is True


def test_operator_overrides_are_respected() -> None:
    result = _analyze(
        "Не работает интернет в 305 кабинете.",
        overrides={"building": "2", "room": "305"},
    )
    assert result.extracted_fields.location.building == "2"
    assert "building" not in result.intake.missing_fields


def test_unclassified_is_marked() -> None:
    result = _analyze("Здравствуйте, хочу узнать график работы.")
    assert result.classification.category_code == "other"
    assert result.classification.status == "unclassified"
    assert result.needs_human_review is True
    assert result.confidence.overall <= 0.4


def test_empty_text_is_handled_safely() -> None:
    result = _analyze("   ")
    assert result.classification.status == "unclassified"
    assert result.needs_human_review is True


def test_ollama_provider_selection(monkeypatch) -> None:
    from ai_module.providers.text_provider import build_text_provider

    monkeypatch.setenv("AI_PROVIDER", "ollama")
    monkeypatch.setenv("OLLAMA_MODEL", "qwen2.5:7b-instruct")
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    provider = build_text_provider()
    assert provider.name == "ollama"
    assert provider.model == "qwen2.5:7b-instruct"


def test_speech_provider_none_raises(monkeypatch) -> None:
    from ai_module.providers.speech_provider import (
        SpeechProviderError,
        transcribe_audio,
    )

    monkeypatch.setenv("SPEECH_PROVIDER", "none")
    with pytest.raises(SpeechProviderError):
        asyncio.run(transcribe_audio(b"audio", "audio/webm"))
