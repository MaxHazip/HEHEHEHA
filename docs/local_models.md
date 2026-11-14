# Локальные нейросети: текст и речь

Система умеет работать полностью локально: без Google-ключа и без
внешних API. Ниже — как подключить модели.

## 1. Текстовая модель (анализ заявок)

### Вариант A: Ollama

```bash
# на своей машине
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen2.5:7b-instruct

# проверка
ollama run qwen2.5:7b-instruct "Ответь одним словом: ok"
```

`backend/.env`:

```env
AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b-instruct
AI_TIMEOUT_SECONDS=60
```

Перезапустить backend. Анализ пойдёт через Ollama; при недоступности
модели backend автоматически откатится на офлайн-правила.

Подойдут и другие модели: `qwen2.5:3b-instruct` (быстрее, слабее),
`llama3.1:8b-instruct`, `gemma2:9b`.

### Вариант B: Docker Compose

```bash
docker compose --profile ollama up -d
docker compose exec ollama ollama pull qwen2.5:7b-instruct
```

В `web` уже проброшен `OLLAMA_BASE_URL=http://ollama:11434`.
Запуск backend с локальной моделью:

```bash
AI_PROVIDER=ollama docker compose up -d web
```

### Вариант C: OpenAI-совместимый сервер

Подходит LM Studio, llama.cpp server, vLLM, LocalAI.

```env
AI_PROVIDER=openai
OPENAI_BASE_URL=http://localhost:1234/v1
OPENAI_MODEL=qwen2.5-7b-instruct
OPENAI_API_KEY=
```

`OPENAI_BASE_URL` должен включать `/v1`.

## 2. Распознавание речи

### Почему не работает Web Speech API

`SpeechRecognition`/`webkitSpeechRecognition` в Chrome и Edge — это
Google-сервис, но у него жёсткие условия:

1. **Только Chrome/Edge** (Firefox и Safari его не поддерживают).
2. **Secure context**: `http://localhost` или `https://`. На
   `http://192.168.x.x` браузер блокирует и микрофон, и распознавание.
3. **Нужен доступ к серверам Google**. Если сеть блокирует
   `speech.googleapis.com`, распознавания не будет.
4. Микрофон должен быть разрешён в настройках браузера.

Виджет звонка теперь показывает конкретную причину, а если браузер не
дал текст — backend расшифровывает сохранённую запись сам.

### Вариант A (рекомендуется): локальный Whisper-сервер

Работает с Python 3.14, не тянет тяжёлые зависимости в backend.

```bash
# из корня проекта
docker compose --profile whisper up -d
```

Сервис поднимается на `http://localhost:8001` с OpenAI-совместимым API.

`backend/.env`:

```env
SPEECH_PROVIDER=http
WHISPER_BASE_URL=http://localhost:8001/v1
WHISPER_HTTP_MODEL=Systran/faster-whisper-small
WHISPER_LANGUAGE=ru
```

Если backend тоже в Docker, используйте
`WHISPER_BASE_URL=http://whisper:8000/v1`.

Проверка:

```bash
curl -s http://localhost:8001/v1/audio/transcriptions \
  -F file=@sample.wav \
  -F model=Systran/faster-whisper-small \
  -F language=ru
```

### Вариант B: faster-whisper прямо в backend

```bash
pip install faster-whisper
```

```env
SPEECH_PROVIDER=local
WHISPER_MODEL=small
WHISPER_DEVICE=auto
WHISPER_COMPUTE_TYPE=int8
WHISPER_LANGUAGE=ru
```

- `WHISPER_MODEL`: `tiny`, `base`, `small`, `medium`, `large-v3`;
- `WHISPER_DEVICE`: `cpu`, `cuda` или `auto`;
- `WHISPER_COMPUTE_TYPE`: `int8` для CPU, `float16` для GPU.

Модель скачивается с HuggingFace при первом вызове (нужен интернет).
Для Python 3.14 колёса `ctranslate2` могут отсутствовать — тогда
используйте HTTP-вариант (A).

### Вариант C: Google Cloud Speech-to-Text

```env
SPEECH_PROVIDER=google
GOOGLE_API_KEY=...
GOOGLE_STT_LANGUAGE=ru-RU
```

Нужен включённый Speech-to-Text API. Синхронный метод ограничен ~1
минутой аудио.

### Как это работает в звонке

1. Браузер пишет `webm/opus` и пытается распознать речь сам.
2. При завершении звонка запись загружается в БД.
3. Если браузерного текста нет, frontend вызывает
   `POST /api/calls/{id}/transcribe`.
4. Backend пробует провайдеров по порядку (`auto`):
   HTTP Whisper → локальный faster-whisper → Google STT.
5. Текст и таймкоды сохраняются в `calls` и `call_transcript_segments`.
6. Запускается ИИ-анализ и создаётся/обновляется заявка.

Проверить, что видит backend:

```bash
curl -s http://localhost:8000/api/health
```

В ответе будет блок `speech`:

```json
{
  "mode": "auto",
  "local_faster_whisper": false,
  "http_whisper": true,
  "google_stt": false,
  "providers": ["http"]
}
```

## 3. Vision (скриншоты)

Для описания изображений используется Gemini (`GOOGLE_API_KEY`).
Локальную vision-модель можно добавить тем же способом, что и текстовую:
через Ollama (например, `llava`) — это следующий шаг, сейчас endpoint
`POST /api/attachments/{id}/describe` использует Gemini.

## 4. Полезные команды

```bash
# backend
uvicorn backend.main:app --reload --port 8000

# frontend с микрофоном на localhost
cd frontend && npm run dev

# frontend по HTTPS для доступа с другого устройства
cd frontend && npm run dev:https
```

Для HTTPS-режима браузер покажет предупреждение о самоподписанном
сертификате — примите его. Origin `https://<IP>:5173` разрешён
регуляркой CORS по умолчанию.
