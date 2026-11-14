# Если настройки читаются через pydantic-settings или os.environ:
import os

from qdrant_client import QdrantClient

from backend.core.settings import (
    settings,  # Подставьте ваш модуль настроек, если он отличается
)

QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))

# Инициализируем единый клиент Qdrant для всего приложения
qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
