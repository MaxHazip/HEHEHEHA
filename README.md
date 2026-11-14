# DispatchAI — диспетчерская система с ИИ

Единая система приёма обращений: чат, фото, звонки из браузера, SIP-АТС
и структурированный ИИ-анализ, который backend превращает в заявку.

## Что работает

- **Заявки**: создание, список, карточка, статусы, приоритеты, назначение
  инженера, сообщения.
- **Изображения**: загружаются в БД (`ticket_attachments.data`), отдаются
  через `GET /api/attachments/{id}/content`; Gemini может их описывать.
- **Браузерные звонки**: WebRTC-захват микрофона, запись `MediaRecorder`,
  live-субтитры Google Web Speech, сохранение аудио и текста в БД,
  прослушивание с перемоткой (`Range`).
- **Серверная расшифровка**: локальный Whisper (HTTP-сервер или пакет
  `faster-whisper`) и Google Cloud Speech-to-Text как fallback.
- **SIP-шлюз**: webhook-эндпоинты для Asterisk/FreeSWITCH/облачной АТС,
  загрузка записи, авто-расшифровка и создание заявки.
- **ARI**: backend сам слушает события Asterisk, отвечает на звонок,
  запускает запись через ARI REST, скачивает её и создаёт заявку — без
  `curl` в dialplan.
- **Панель диспетчера `/calls`**: список звонков, плеер, расшифровка,
  таймкоды и live-субтитры активных звонков.
- **ИИ-анализ**: контракт `TicketAIResult` — категория, локация, симптомы,
  действия, impact, приоритет, `missing_fields`, вопросы, уверенность,
  `needs_human_review`.
- **Локальные нейросети**: Ollama / OpenAI-совместимый сервер для текста,
  Whisper для речи. Без ключей всё работает на офлайн-правилах.

Подробнее:

- [`docs/local_models.md`](docs/local_models.md) — Ollama, Whisper, HTTPS
  и почему может не работать распознавание голоса.
- [`docs/telephony.md`](docs/telephony.md) — WebRTC/SIP, схема хранения,
  панель диспетчера.
- [`deploy/asterisk/`](deploy/asterisk/) — готовый dialplan.

## Быстрый старт

### Backend

```bash
cd HEHEHEHA
python -m venv .venv
source .venv/bin/activate
pip install poetry
poetry install --no-root

cp backend/.env.example backend/.env
uvicorn backend.main:app --reload --port 8000
```

- Swagger: <http://localhost:8000/docs>
- Health + диагностика речи: <http://localhost:8000/api/health>
- По умолчанию SQLite `dispatcher.db`; схема создаётся при старте.
- Для Postgres задайте `DATABASE_URL=postgresql+asyncpg://...`.

Для тестов: `pip install pytest`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

В dev фронтенд ходит на относительный `/api`; Vite проксирует его на
`http://localhost:8000` (меняется через `VITE_API_TARGET`). CORS и
mixed content не мешают.

Если открываете приложение не с `localhost`, а с другого устройства:

```bash
npm run dev:https
```

Откройте `https://<IP>:5173` и примите самоподписанный сертификат.
Без HTTPS браузер блокирует микрофон на `http://IP`.

В production задайте `VITE_API_URL=https://api.example.com` при сборке
или раздавайте frontend и backend с одного origin через reverse proxy.

### Docker

```bash
docker compose up --build
```

Локальные модели — отдельными профилями:

```bash
# текстовая модель
docker compose --profile ollama up -d
docker compose exec ollama ollama pull qwen2.5:7b-instruct
AI_PROVIDER=ollama docker compose up -d web

# Whisper
docker compose --profile whisper up -d
WHISPER_BASE_URL=http://whisper:8000/v1 docker compose up -d web
```

## Если не работает распознавание голоса

Проверьте по порядку:

1. **Браузер** — нужен Chrome или Edge. Firefox/Safari Web Speech API не
   поддерживают (серверный Whisper при этом продолжит работать).
2. **Secure context** — откройте `http://localhost:5173` или запустите
   `npm run dev:https`. На `http://192.168.x.x` микрофон запрещён
   политикой браузера.
3. **Разрешение на микрофон** — проверьте иконку замка в адресной строке.
4. **Доступ к Google** — если сеть блокирует `speech.googleapis.com`,
   live-субтитры не появятся. Это не ошибка записи: backend расшифрует
   сохранённый файл.
5. **Серверная расшифровка** — `GET /api/health`, блок `speech`:
   ```json
   {
     "mode": "auto",
     "local_faster_whisper": false,
     "http_whisper": true,
     "google_stt": false,
     "providers": ["http"]
   }
   ```
   Если `providers` пустой:
   - поднимите Whisper: `docker compose --profile whisper up -d` и задайте
     `WHISPER_BASE_URL=http://localhost:8001/v1`, либо
   - `pip install faster-whisper` и `SPEECH_PROVIDER=local`, либо
   - задайте `GOOGLE_API_KEY` и `SPEECH_PROVIDER=google`.

Подробная инструкция: [`docs/local_models.md`](docs/local_models.md).

## Локальная нейросеть для текста

```env
AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b-instruct
AI_TIMEOUT_SECONDS=60
```

Без Ollama:

```env
AI_PROVIDER=openai
OPENAI_BASE_URL=http://localhost:1234/v1
OPENAI_MODEL=qwen2.5-7b-instruct
```

Если модель недоступна, backend автоматически использует
детерминированный анализатор на правилах.

## Переменные окружения

| Переменная | По умолчанию | Назначение |
|---|---|---|
| `DATABASE_URL` | `sqlite+aiosqlite:///./dispatcher.db` | DSN базы |
| `CORS_ORIGINS` | localhost/127.0.0.1:5173 | Origins frontend'а |
| `AI_PROVIDER` | `auto` | `auto` / `gemini` / `ollama` / `openai` / `rule` |
| `AI_AUTO_ANALYZE` | `true` | Анализировать новую заявку сразу |
| `GOOGLE_API_KEY` | — | Gemini + Google STT |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Текстовая/vision-модель |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Локальная Ollama |
| `OLLAMA_MODEL` | `qwen2.5:7b-instruct` | Модель Ollama |
| `OPENAI_BASE_URL` | — | Локальный OpenAI-совместимый API |
| `OPENAI_MODEL` | — | Модель локального сервера |
| `SPEECH_PROVIDER` | `auto` | `auto` / `local` / `http` / `google` / `none` |
| `WHISPER_BASE_URL` | — | HTTP Whisper, включает `/v1` |
| `WHISPER_HTTP_MODEL` | `Systran/faster-whisper-small` | Модель HTTP Whisper |
| `WHISPER_MODEL` | `small` | Модель faster-whisper |
| `WHISPER_DEVICE` | `auto` | `cpu` / `cuda` / `auto` |
| `WHISPER_COMPUTE_TYPE` | `int8` | `int8` / `float16` |
| `WHISPER_LANGUAGE` | `ru` | Язык распознавания |
| `SIP_WEBHOOK_TOKEN` | — | Токен SIP-webhook'ов |
| `SIP_AUTO_ANALYZE` | `true` | Анализировать записи из АТС |
| `ARI_ENABLED` | `false` | Включить ARI-клиент |
| `ARI_URL` | `http://localhost:8088` | ARI REST Asterisk |
| `ARI_USERNAME` | `dispatchai` | Пользователь ARI |
| `ARI_PASSWORD` | — | Пароль ARI |
| `ARI_APP` | `dispatchai` | Имя Stasis-приложения |
| `ARI_RECORD` | `true` | Записывать ARI-звонки |
| `ARI_GREETING_MEDIA` | — | Приветствие, напр. `sound:hello-world` |
| `ARI_AUTO_ANALYZE` | `true` | Анализировать ARI-записи |
| `MAX_UPLOAD_MB` | `30` | Лимит вложений |
| `MAX_AUDIO_MB` | `60` | Лимит записи звонка |

## API

| Метод | Путь | Назначение |
|---|---|---|
| `POST` | `/api/tickets` | Создать заявку (и сразу проанализировать) |
| `GET` | `/api/tickets` | Список заявок с фильтрами |
| `GET` | `/api/tickets/{id}` | Сообщения, вложения, звонки |
| `PATCH` | `/api/tickets/{id}` | Статус, приоритет, исполнитель |
| `POST` | `/api/tickets/{id}/messages` | Сообщение (+вложения) |
| `POST` | `/api/tickets/{id}/attachments` | Загрузить фото в БД |
| `POST` | `/api/tickets/{id}/analyze` | ИИ-анализ заявки |
| `GET` | `/api/attachments/{id}/content` | Отдать файл |
| `POST` | `/api/attachments/{id}/describe` | Описать фото (Gemini) |
| `GET` | `/api/calls` | Список звонков |
| `POST` | `/api/calls` | Создать сессию звонка |
| `POST` | `/api/calls/{id}/recording` | Загрузить запись в БД |
| `GET` | `/api/calls/{id}/recording` | Прослушать (Range) |
| `PUT` | `/api/calls/{id}/transcript` | Сохранить расшифровку |
| `POST` | `/api/calls/{id}/transcribe` | Whisper/Google STT |
| `POST` | `/api/calls/{id}/analyze` | Анализ звонка → заявка |
| `WS` | `/api/calls/{id}/signal` | WebRTC + live-субтитры |
| `POST` | `/api/telephony/sip/calls` | SIP: звонок начался |
| `POST` | `/api/telephony/sip/calls/{id}/ended` | SIP: звонок завершён |
| `POST` | `/api/telephony/sip/recording` | SIP: загрузить запись |
| `GET` | `/api/telephony/sip/calls/{id}` | SIP: состояние звонка |
| `WS` | `ws://asterisk:8088/ari/events` | ARI: события Asterisk (исходящее подключение backend) |
| `GET` | `/api/ai/taxonomy` | Справочники кодов |
| `POST` | `/api/ai/analyze-text` | Анализ текста без заявки |
| `GET` | `/api/health` | Состояние, речь, SIP |

SIP-эндпоинты требуют `X-Telephony-Token`.

## Тесты

```bash
pip install pytest
python -m pytest ai_module/tests backend/tests -q
```

Покрыто: контракт ИИ, отсутствие галлюцинаций, массовая авария,
overrides диспетчера, полный цикл заявка → фото → звонок → расшифровка →
анализ, Range-аудио, SIP-webhook, ARI-поток (StasisStart →
RecordingFinished → StasisEnd), live-субтитры через WebSocket,
выбор локальных провайдеров.

Frontend:

```bash
cd frontend
npm run build
npm run lint
```

## Структура

```
backend/
  api/routes/      # tickets, attachments, calls, telephony, ai, users
  core/            # settings, database, мини-миграции
  models/          # tickets, messages, attachments, calls
  schemas/
  services/        # ai_service, call_service, transcription, ari_service, signalling
  tests/
ai_module/
  core/            # taxonomy, schemas, analyzer, clarification, validator
  providers/       # Gemini, Ollama, OpenAI-совместимый, Whisper, Google STT
  tests/
frontend/
  src/features/calls/       # WebRTC, live-субтитры, сохранение звонка
  src/pages/DispatcherCallsPage.tsx
  src/pages/ClientChatPage.tsx
deploy/asterisk/    # пример dialplan
docs/
  local_models.md
  telephony.md
```

## Ограничения MVP

- Нет авторизации: роли выбираются на frontend, API открыт.
- Файлы и аудио лежат в БД: удобно для демо, для продакшена — S3/MinIO.
- SIP-стек/PBX не входит в репозиторий — нужен Asterisk/FreeSWITCH или
  облачная АТС; backend принимает события и записи. ARI-режим требует
  включённого `res_ari` и настроенного `ari.conf`.
- In-memory сигналинг не переживает перезапуск и не масштабируется;
  для продакшена — Redis pub/sub и TURN/SFU.
- Web Speech API зависит от Chrome/Edge и доступа к Google; для
  остальных случаев есть серверный Whisper.
