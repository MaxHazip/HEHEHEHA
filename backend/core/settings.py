import os
from functools import lru_cache
from typing import ClassVar

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    DATABASE_URL: str = "sqlite+aiosqlite:///./dispatcher.db"
    ALEMBIC_DATABASE_URL: str | None = None

    # JWT: в production обязательно задайте длинный случайный секрет через env.
    JWT_SECRET_KEY: str = "CHANGE_ME_USE_A_LONG_RANDOM_SECRET_IN_ENV"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    DEMO_USER_PASSWORD: str | None = None

    APP_NAME: str = "DispatchAI"
    APP_VERSION: str = "0.1.0"

    # Список origin'ов frontend'а через запятую.
    CORS_ORIGINS: str = (
        "http://localhost:5173,http://127.0.0.1:5173,"
        "https://localhost:5173,https://127.0.0.1:5173"
    )
    # Разрешает HTTPS-режим Vite и локальную сеть (192.168.x.x, 10.x.x.x).
    CORS_ORIGIN_REGEX: str | None = (
        r"https?://(localhost|127\.0\.0\.1|192\.168\.\d{1,3}\.\d{1,3}"
        r"|10\.\d{1,3}\.\d{1,3}\.\d{1,3}):\d+"
    )

    # Ограничения на размер загружаемых файлов.
    MAX_UPLOAD_MB: int = 30
    MAX_AUDIO_MB: int = 60

    # Демо-пользователи (диспетчер/инженер) при первом запуске.
    SEED_DEMO_DATA: bool = True

    # auto -> Gemini, если задан ключ, иначе офлайн-анализатор.
    AI_PROVIDER: str = "auto"
    AI_AUTO_ANALYZE: bool = True
    GOOGLE_API_KEY: str | None = None
    GEMINI_API_KEY: str | None = None
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GOOGLE_STT_LANGUAGE: str = "ru-RU"
    AI_TIMEOUT_SECONDS: float = 20.0

    # Локальная текстовая модель (Ollama / OpenAI-совместимый сервер).
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5:7b-instruct"
    OPENAI_BASE_URL: str | None = None
    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str | None = None

    # Распознавание речи: auto | local | http | google | none.
    SPEECH_PROVIDER: str = "auto"
    WHISPER_BASE_URL: str | None = None
    WHISPER_API_KEY: str | None = None
    WHISPER_HTTP_MODEL: str = "Systran/faster-whisper-small"
    WHISPER_MODEL: str = "small"
    WHISPER_DEVICE: str = "auto"
    WHISPER_COMPUTE_TYPE: str = "int8"
    WHISPER_LANGUAGE: str = "ru"

    # SIP-шлюз (Asterisk/FreeSWITCH/облачная АТС) присылает события сюда.
    SIP_WEBHOOK_TOKEN: str | None = None
    SIP_AUTO_ANALYZE: bool = True

    # ARI (Asterisk REST Interface): backend сам слушает события АТС.
    ARI_ENABLED: bool = False
    ARI_URL: str = "http://localhost:8088"
    ARI_WS_URL: str | None = None
    ARI_USERNAME: str = "dispatchai"
    ARI_PASSWORD: str | None = None
    ARI_APP: str = "dispatchai"
    ARI_RECORD: bool = True
    ARI_GREETING_MEDIA: str | None = None
    ARI_AUTO_ANALYZE: bool = True
    ARI_RECORDING_FORMAT: str = "wav"
    ARI_RECONNECT_SECONDS: float = 5.0
    ARI_VERIFY_SSL: bool = True

    _RUNTIME_ENV_KEYS: ClassVar[tuple[str, ...]] = (
        "AI_PROVIDER",
        "AI_TIMEOUT_SECONDS",
        "GOOGLE_API_KEY",
        "GEMINI_API_KEY",
        "GEMINI_MODEL",
        "GOOGLE_STT_LANGUAGE",
        "OLLAMA_BASE_URL",
        "OLLAMA_MODEL",
        "OPENAI_BASE_URL",
        "OPENAI_API_KEY",
        "OPENAI_MODEL",
        "SPEECH_PROVIDER",
        "WHISPER_BASE_URL",
        "WHISPER_API_KEY",
        "WHISPER_HTTP_MODEL",
        "WHISPER_MODEL",
        "WHISPER_DEVICE",
        "WHISPER_COMPUTE_TYPE",
        "WHISPER_LANGUAGE",
        "SIP_WEBHOOK_TOKEN",
        "SIP_AUTO_ANALYZE",
    )

    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins(self) -> list[str]:
        return [item.strip() for item in self.CORS_ORIGINS.split(",") if item.strip()]

    @property
    def google_api_key(self) -> str | None:
        return self.GOOGLE_API_KEY or self.GEMINI_API_KEY

    @property
    def max_upload_bytes(self) -> int:
        return self.MAX_UPLOAD_MB * 1024 * 1024

    @property
    def max_audio_bytes(self) -> int:
        return self.MAX_AUDIO_MB * 1024 * 1024

    def export_runtime_env(self) -> None:
        """Пробрасывает настройки из .env в os.environ.

        ИИ-модуль не зависит от pydantic-settings и читает окружение
        напрямую, поэтому .env должен стать настоящими env-переменными.
        """

        for key in self._RUNTIME_ENV_KEYS:
            value = getattr(self, key, None)
            if value is None or value == "":
                continue
            os.environ.setdefault(key, str(value))


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
settings.export_runtime_env()
