# Instruction — запуск DispatchAI

Пошаговая инструкция: от установки Python/Node до запуска backend,
frontend, локальных ИИ-моделей и телефонии.

> Все команды выполняются **из корня репозитория `HEHEHEHA`**, если не
> указано иное. В примерах используется Linux/macOS; для Windows
> активация venv: `.venv\Scripts\activate`.

---

## 1. Что понадобится

| Компонент | Версия | Зачем |
|---|---|---|
| Python | 3.13+ | backend и ai_module |
| Node.js + npm | 20+ | frontend |
| Ollama | 0.9+ | Qwen3 и Qwen3-VL |
| Docker + Compose | опционально | Postgres, Ollama, Whisper |
| Asterisk | 20+ с `res_ari` | телефония (опционально) |
| T-one | по официальному репозиторию | распознавание речи |
| ffmpeg | опционально | нормализация аудио для STT |

Проверка:

```bash
python3 --version
node --version
npm --version
ollama --version
docker --version
```

---

## 2. Backend: виртуальное окружение и зависимости

### 2.1. Создание venv и установка

```bash
cd /путь/к/HEHEHEHA

python3 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip
pip install -r backend/requirements.txt
```

Windows:

```powershell
cd C:\путь\к\HEHEHEHA
py -3 -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r backend\requirements.txt
```

Единый файл зависимостей — `backend/requirements.txt`. Он объединяет
backend, ai_module и тесты.

### 2.2. Альтернатива: Poetry

Если предпочитаете Poetry (файлы `pyproject.toml` и `poetry.lock` уже есть):

```bash
pip install poetry
poetry install --no-root
```

Дальше команды те же, но активируйте окружение Poetry:

```bash
poetry shell
```

---

## 3. Конфигурация `.env`

```bash
cp backend/.env.example backend/.env
```

Откройте `backend/.env` и проверьте ключевые значения:

```env
# База: SQLite для локального запуска (Alembic создаст схему)
DATABASE_URL=sqlite+aiosqlite:///./dispatcher.db

# AI: auto = Ollama, при недоступности — офлайн-правила
AI_PROVIDER=auto
AI_AUTO_ANALYZE=true
AI_TIMEOUT_SECONDS=300

OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen3:4b-instruct
OLLAMA_THINK=false
OLLAMA_NUM_CTX=4096
OLLAMA_NUM_PREDICT=768
OLLAMA_KEEP_ALIVE=2m

VISION_PROVIDER=auto
OLLAMA_VISION_MODEL=qwen3-vl:2b
OLLAMA_VISION_NUM_CTX=4096
OLLAMA_VISION_NUM_PREDICT=256
VISION_TIMEOUT_SECONDS=240

SPEECH_PROVIDER=auto
TONE_BASE_URL=http://localhost:8002
TONE_MODEL=t-one
TONE_ENDPOINT=/audio/transcriptions
TONE_FILE_FIELD=file
TONE_LANGUAGE=ru
TONE_TIMEOUT_SECONDS=300

TTS_PROVIDER=silero
TTS_ENABLED=true
SILERO_TTS_URL=http://localhost:8003
SILERO_TTS_ENDPOINT=/tts
SILERO_SPEAKER=aidar
SILERO_SAMPLE_RATE=24000
```

`backend/.env` не коммитится (он в `.gitignore`).

---

## 4. База данных и Alembic

Схема создаётся **только через Alembic**. Приложение при старте само
выполняет `alembic upgrade head`.

### 4.1. SQLite (по умолчанию)

```bash
alembic upgrade head
alembic current
```

Если осталась БД со старой схемой:

```bash
rm -f dispatcher.db
alembic upgrade head
```

### 4.2. PostgreSQL через Docker

```bash
docker compose up -d db
```

В `backend/.env`:

```env
DATABASE_URL=postgresql+asyncpg://dispatcher_user:ef6a998e815ad6513ffe2f4a749208f3e269f24b43384d03f9acb2f5cb343169@localhost:5432/dispatcher_db
```

Затем:

```bash
alembic upgrade head
```

Полезные команды:

```bash
alembic history
alembic current
alembic downgrade -1
alembic check
```

---

## 5. Ollama: Qwen3 и Qwen3-VL

### 5.1. Установка

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama --version
```

Если сервис не запущен:

```bash
ollama serve
```

### 5.2. Ограничения памяти (важно для 16 ГБ / CPU)

Настройте демон Ollama так, чтобы он держал **одну** модель:

```bash
sudo systemctl edit ollama
```

```ini
[Service]
Environment="OLLAMA_MAX_LOADED_MODELS=1"
Environment="OLLAMA_NUM_PARALLEL=1"
Environment="OLLAMA_KEEP_ALIVE=2m"
```

```bash
sudo systemctl daemon-reload
sudo systemctl restart ollama
```

Если Ollama запускается вручную:

```bash
OLLAMA_MAX_LOADED_MODELS=1 OLLAMA_NUM_PARALLEL=1 OLLAMA_KEEP_ALIVE=2m ollama serve
```

### 5.3. Модели

```bash
ollama pull qwen3:4b-instruct
ollama pull qwen3-vl:2b
ollama list
```

Проверка:

```bash
ollama run qwen3:4b-instruct "Ответь одним словом: ok"
ollama ps
```

Для качества можно поставить `qwen3:8b` и/или `qwen3-vl:4b`, но на CPU
это заметно медленнее и требует больше памяти. Не держите 8B-текст и
8B-vision одновременно на 16 ГБ.

---

## 6. T-one: локальное распознавание речи

T-one — русскоязычная ASR-модель от Т-Банка. Она **не входит в Ollama**.
Backend обращается к ней по HTTP как к OpenAI-совместимому
`/audio/transcriptions`.

### 6.1. Контракт сервера

`POST /audio/transcriptions`, `multipart/form-data`:

| Поле | Значение |
|---|---|
| `file` (или `TONE_FILE_FIELD`) | аудиофайл |
| `model` | `t-one` |
| `language` | `ru` |
| `response_format` | `verbose_json` |

Ответ:

```json
{
  "text": "распознанный текст",
  "language": "ru",
  "segments": [
    {"start": 0.0, "end": 2.4, "text": "фрагмент"}
  ]
}
```

### 6.2. Запуск официального T-one

```bash
mkdir -p ~/tone-server
cd ~/tone-server

python3 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip
pip install fastapi "uvicorn[standard]" torch

# Затем установите T-one по официальному README:
# https://github.com/T-Bank-AI/T-one
```

### 6.3. Минимальная HTTP-обёртка

Создайте `server.py` и подключите функцию инференса T-one из
официального примера в `transcribe_with_t_one`:

```python
import os
import tempfile

import torch
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import JSONResponse

torch.set_num_threads(int(os.getenv("TORCH_NUM_THREADS", "2")))

app = FastAPI(title="T-one ASR")


def transcribe_with_t_one(path: str, language: str) -> dict:
    # Замените на вызов из официального репозитория T-one.
    raise NotImplementedError


@app.post("/audio/transcriptions")
async def transcriptions(
    file: UploadFile = File(...),
    model: str = Form("t-one"),
    language: str = Form("ru"),
    response_format: str = Form("verbose_json"),
):
    suffix = os.path.splitext(file.filename or "audio.wav")[1] or ".wav"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as handle:
        handle.write(await file.read())
        path = handle.name
    try:
        result = transcribe_with_t_one(path, language)
    finally:
        os.unlink(path)
    return JSONResponse(result)
```

Запуск:

```bash
TORCH_NUM_THREADS=2 uvicorn server:app --host 0.0.0.0 --port 8002
TONE_DECODER=greedy OMP_NUM_THREADS=2 uvicorn server:app --host 0.0.0.0 --port 8002
```

Проверка:

```bash
curl -s http://localhost:8002/audio/transcriptions \
  -F file=@sample.wav \
  -F model=t-one \
  -F language=ru \
  -F response_format=verbose_json
```

Если ваш сервер T-one уже отдаёт OpenAI-совместимый API, обёртка не
нужна — просто укажите его адрес в `TONE_BASE_URL`.

---

## 7. Silero TTS: синтез речи

Silero TTS — отдельный сервер на PyTorch. Он не входит в Ollama.

### 7.1. Установка (отдельное окружение)

```bash
cd deploy/silero

python3 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip
pip install fastapi "uvicorn[standard]" torch soundfile numpy
```

Для GPU установите PyTorch с CUDA по инструкции <https://pytorch.org>.
Первый запуск скачает модель с `torch.hub`.

### 7.2. Запуск

```bash
TORCH_NUM_THREADS=2 uvicorn tts_server:app --host 0.0.0.0 --port 8003
```

Проверка:

```bash
curl -s -X POST http://localhost:8003/tts \
  -H 'Content-Type: application/json' \
  -d '{"text":"Здравствуйте! Чем могу помочь?","speaker":"aidar"}' \
  --output speech.wav

file speech.wav
```

---

## 7.1. Qdrant и база знаний

Qdrant используется для семантического поиска статей. Если Qdrant или
модель эмбеддингов недоступны, backend автоматически ищет по ключевым
словам в БД — приложение продолжает работать.

1. Запустите Qdrant:

```bash
docker compose up -d qdrant
```

2. Установите `qdrant-client` (он уже в requirements):

```bash
pip install -r backend/requirements.txt
```

3. Скачайте модель эмбеддингов в Ollama:

```bash
ollama pull nomic-embed-text
```

4. В `backend/.env`:

```env
QDRANT_ENABLED=true
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=knowledge_articles
QDRANT_TOP_K=5
EMBEDDING_MODEL=nomic-embed-text
```

5. Перезапустите backend. Индексация выполняется при старте; вручную:

```bash
curl -X POST http://localhost:8000/api/knowledge/reindex
```

6. Проверка:

```bash
curl -s http://localhost:8000/api/knowledge/status
curl -s "http://localhost:8000/api/knowledge/search?q=не%20работает%20интернет"
```

Статьи берутся из `json/knowledge_articles.json` и таблицы
`knowledge_articles`. В Docker у сервиса `web` уже задан
`QDRANT_URL=http://qdrant:6333`.

---

## 8. Запуск backend

Вернитесь в корень репозитория и активируйте venv backend:

```bash
cd /путь/к/HEHEHEHA
source .venv/bin/activate

uvicorn backend.main:app --reload --port 8000
```

Проверка:

```bash
curl -s http://localhost:8000/api/health | python -m json.tool
```

Swagger: <http://localhost:8000/docs>.

---

## 9. Запуск frontend

```bash
cd frontend
npm install
npm run dev
```

Откройте <http://localhost:5173>.

Микрофон работает только в secure context. Для доступа с другого
устройства:

```bash
npm run dev:https
```

Сборка и линт:

```bash
npm run build
npm run lint
```

Опционально: браузерные live-субтитры (Google Web Speech):

```bash
VITE_BROWSER_SPEECH=true npm run dev
```

По умолчанию они выключены — расшифровка идёт локальным T-one после
звонка.

---

## 10. Docker Compose

```bash
docker compose up --build
```

Локальные модели — профилями:

```bash
docker compose --profile ollama up -d
docker compose exec ollama ollama pull qwen3:4b-instruct
docker compose exec ollama ollama pull qwen3-vl:2b
```

Whisper (резервный STT):

```bash
docker compose --profile whisper up -d
```

Если T-one/Silero запущены на хосте, backend в контейнере обращается к
ним через `host.docker.internal` (уже настроено в `extra_hosts`):

```env
TONE_BASE_URL=http://host.docker.internal:8002
SILERO_TTS_URL=http://host.docker.internal:8003
ARI_URL=http://host.docker.internal:8088
```

---

## 11. Asterisk: ARI и SIP-webhook

Конфиги лежат в `deploy/asterisk/`. Сам Asterisk в репозиторий не входит.

### 11.1. ARI (рекомендуется)

Скопируйте конфиги:

```bash
sudo cp deploy/asterisk/ari.conf /etc/asterisk/
sudo cp deploy/asterisk/http.conf /etc/asterisk/
sudo cp deploy/asterisk/dialplan-ari.conf /etc/asterisk/
```

В `/etc/asterisk/extensions.conf`:

```ini
#include "dialplan-ari.conf"
```

Задайте пароль в `/etc/asterisk/ari.conf`:

```ini
[dispatchai]
type = user
read_only = no
password = change-me
password_format = plain
```

И тот же пароль в `backend/.env`:

```env
ARI_ENABLED=true
ARI_URL=http://127.0.0.1:8088
ARI_USERNAME=dispatchai
ARI_PASSWORD=change-me
ARI_APP=dispatchai
ARI_RECORD=true
ARI_AUTO_ANALYZE=true
```

Перезагрузите Asterisk:

```bash
asterisk -rx "module reload res_http_websocket.so"
asterisk -rx "module reload res_ari.so"
asterisk -rx "dialplan reload"
```

Проверка ARI:

```bash
curl -u dispatchai:change-me http://localhost:8088/ari/asterisk/info
```

Перезапустите backend и проверьте health:

```bash
curl -s http://localhost:8000/api/health | python -m json.tool
```

Ожидаемо:

```json
"ari": {
  "enabled": true,
  "running": true,
  "connected": true,
  "app": "dispatchai"
}
```

Если `enabled: false` — выставьте `ARI_ENABLED=true` и **полностью**
перезапустите backend (настройки кешируются). Если `connected: false` —
смотрите `last_error`: `ConnectionRefusedError` (адрес/порт),
`InvalidStatus`/`401` (пароль), `TimeoutError` (сеть).

### 11.2. SIP-webhook (если ARI недоступен)

Используйте `deploy/asterisk/dialplan-snippet.conf`: `MixMonitor` пишет
файл, а `curl` на `h`-extension отправляет его в backend.

В dialplan замените:

```ini
[globals]
BACKEND_URL=http://web:8000
TELEPHONY_TOKEN=change-me
```

В `backend/.env`:

```env
SIP_WEBHOOK_TOKEN=change-me
SIP_AUTO_ANALYZE=true
```

Проверка:

```bash
curl -X POST http://localhost:8000/api/telephony/sip/calls \
  -H "X-Telephony-Token: change-me" \
  -H "Content-Type: application/json" \
  -d '{"external_id":"test-1","from_number":"+79990000000","direction":"inbound"}'

curl -X POST http://localhost:8000/api/telephony/sip/recording \
  -H "X-Telephony-Token: change-me" \
  -F external_id=test-1 \
  -F from_number=+79990000000 \
  -F file=@sample.wav
```

Не включайте ARI и webhook одновременно для одного звонка.

---

## 12. Проверка, что всё работает

### 12.1. Health

```bash
curl -s http://localhost:8000/api/health | python -m json.tool
```

Смотрите блоки `ai_model`, `speech`, `vision`, `tts`, `telephony`.

### 12.2. Текст → JSON

```bash
curl -s -X POST http://localhost:8000/api/ai/analyze-text \
  -H 'Content-Type: application/json' \
  -d '{"text":"В 305 кабинете не работает интернет, перезагрузка не помогла"}'
```

### 12.3. Фото → описание

```bash
curl -s -X POST http://localhost:8000/api/tickets \
  -H 'Content-Type: application/json' \
  -d '{"description":"Не работает принтер","source":"chat"}'

curl -s -X POST http://localhost:8000/api/tickets/1/attachments \
  -F file=@screen.png

curl -s -X POST http://localhost:8000/api/attachments/1/describe
```

### 12.4. Голос

```bash
# T-one: аудио -> текст
curl -s -X POST http://localhost:8000/api/voice/transcribe -F file=@sample.wav

# Silero: текст -> речь
curl -s -X POST http://localhost:8000/api/voice/tts \
  -H 'Content-Type: application/json' \
  -d '{"text":"Проверка синтеза речи"}' --output reply.wav

# Полный цикл T-one -> Qwen3 -> Silero
curl -s -X POST http://localhost:8000/api/voice/chat \
  -F file=@sample.wav -F language=ru-RU | python -m json.tool
```

### 12.5. Тесты

```bash
python -m pytest backend/tests ai_module/tests -q
```

### 12.6. Статистика, база знаний и чат

```bash
# Реальная статистика для дашбордов
curl -s http://localhost:8000/api/stats | python -m json.tool

# Семантический поиск (Qdrant или keyword-fallback)
curl -s "http://localhost:8000/api/knowledge/search?q=dns" | python -m json.tool

# Сообщение пользователя и реальный ответ LLM
curl -s -X POST http://localhost:8000/api/tickets/1/chat \
  -H 'Content-Type: application/json' \
  -d '{"text":"Не работает интернет в 305 кабинете"}'

# Потоковый ответ (SSE, текст приходит по мере генерации)
curl -N -X POST http://localhost:8000/api/tickets/1/chat/stream \
  -H 'Content-Type: application/json' \
  -d '{"text":"Не работает интернет в 305 кабинете"}'

# Автоназначение инженера по категории
curl -X POST http://localhost:8000/api/tickets/1/auto-assign

# Голосовой ответ ИИ на сохранённый звонок (T-one -> Qwen3 -> Silero)
curl -X POST http://localhost:8000/api/calls/1/voice-reply | python -m json.tool
```

WebSocket для потокового T-one:

```
WS /api/voice/stream
```

Формат: PCM16LE mono **8 kHz**, бинарные чанки по 300 мс
(2400 сэмплов = 4800 байт), в конце текстовое `finalize`. Backend
проксирует их в T-one `/ws/transcriptions` и возвращает partial/final JSON.

Страница `/knowledge` в интерфейсе показывает статьи, результаты поиска и
состояние Qdrant. Админ-панель `/analytics` использует реальный
`/api/stats`.

---

## 13. Частые проблемы

| Симптом | Решение |
|---|---|
| `SILERO_SAMPLE_RATE` invalid | Значение должно быть целым: `24000`, не `24s000`. |
| Запрос обрывается ровно через 30 с | Это таймаут Axios во фронтенде, а не backend. Сейчас в `frontend/src/lib/api.ts` общий таймаут 300 с, для ИИ-запросов — 600 с. Пересоберите frontend; за reverse-proxy (nginx) задайте `proxy_read_timeout 600s`. |
| Backend не стартует | Проверьте `backend/.env` и `python -c "from backend.core.settings import settings"`. |
| `alembic: table already exists` | Удалите старую `dispatcher.db` или пересоздайте volume Postgres. |
| ИИ пишет «офлайн-анализ» | Ollama не отвечает: `ollama list`, `curl localhost:11434/api/tags`. |
| `model "qwen3:4b-instruct" not found` | `ollama pull qwen3:4b-instruct`. |
| Очень медленный анализ | CPU: используйте `qwen3:4b-instruct`/`1.7b`, `OLLAMA_MAX_LOADED_MODELS=1`, не держите 8B. |
| Таймаут LLM | `AI_TIMEOUT_SECONDS=300`; первый запуск грузит модель. |
| Vision 503 | `OLLAMA_VISION_MODEL=qwen3-vl:2b`, модель скачана, `VISION_PROVIDER=ollama`. |
| T-one 503 | Сервер не запущен или неверный `TONE_BASE_URL`/`TONE_ENDPOINT`. |
| TTS 503 | `SILERO_TTS_URL` пуст, `TTS_ENABLED=false` или сервер не отвечает. |
| ARI `enabled:false` | `ARI_ENABLED=true` и полный перезапуск backend. |
| ARI `connected:false` | Смотрите `last_error`; проверьте URL, порт 8088, пароль. |
| Микрофон не работает | Нужен `localhost` или HTTPS (`npm run dev:https`). |
| Долгая загрузка модели | Нормально для CPU; далее работает `OLLAMA_KEEP_ALIVE`. |

---

## 14. Полезные команды

```bash
# Модели Ollama
ollama list
ollama ps
ollama stop qwen3:8b

# Миграции
alembic upgrade head
alembic current
alembic downgrade -1

# Backend
uvicorn backend.main:app --reload --port 8000

# Тесты
python -m pytest backend/tests ai_module/tests -q

# Frontend
cd frontend && npm run dev
cd frontend && npm run build
```
