# IP-телефония: WebRTC + SIP-шлюз

## Почему WebRTC первым

У системы уже есть браузерный клиент. WebRTC даёт рабочий сценарий
«позвонить из браузера» без PBX, SIP-транка и покупки номеров:

- микрофон — `getUserMedia`;
- запись — `MediaRecorder`;
- live-субтитры — Google Web Speech API;
- fallback-расшифровка — Whisper/Google STT на backend;
- запись и текст — в БД.

SIP нужен для реальных номеров, входящих из PSTN и интеграции с АТС.
Backend уже принимает SIP-события, поэтому подключение Asterisk,
FreeSWITCH или облачной АТС не меняет модель заявки.

## Что реализовано

### Браузерный звонок

`frontend/src/features/calls/`

- `useCallRecorder` — `getUserMedia` + `MediaRecorder` + Web Speech API.
- `CallWidget` — создаёт сессию звонка **в начале** разговора, шлёт
  live-расшифровку по WebSocket, при завершении загружает запись,
  сохраняет текст и запускает анализ.
- Если браузер не распознал речь, вызывается серверная транскрибация.

### WebRTC-сигналинг

`WS /api/calls/{id}/signal?role=client|dispatcher&peer_id=...`

`backend/services/signalling.py` — in-memory relay:

- `offer` / `answer` / `ice`;
- `transcript` — live-субтитры;
- `status` — изменение статуса;
- `snapshot` — состояние звонка при подключении диспетчера.

Финальные фрагменты транскрипта сохраняются в БД прямо из WebSocket,
поэтому диспетчер видит текст в реальном времени.

### Панель диспетчера

`/calls` — список звонков, плеер, расшифровка, таймкоды и live-субтитры
активных звонков. Данные обновляются автоматически.

### SIP-шлюз

Backend не поднимает собственный SIP-стек. АТС присылает события:

| Метод | Путь | Назначение |
|---|---|---|
| `POST` | `/api/telephony/sip/calls` | звонок начался |
| `POST` | `/api/telephony/sip/calls/{external_id}/ended` | звонок завершён (можно передать `recording_url`) |
| `POST` | `/api/telephony/sip/recording` | загрузить файл записи |
| `GET` | `/api/telephony/sip/calls/{external_id}` | состояние звонка |

Все запросы защищены заголовком:

```
X-Telephony-Token: <SIP_WEBHOOK_TOKEN>
```

Если токен не задан, эндпоинты отвечают `503`; неверный токен — `401`.

Пример старта и загрузки записи:

```bash
TOKEN=change-me
EXT=1712345678.42

curl -X POST http://localhost:8000/api/telephony/sip/calls \
  -H "X-Telephony-Token: $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"external_id":"1712345678.42","from_number":"+79990000000","direction":"inbound"}'

curl -X POST http://localhost:8000/api/telephony/sip/recording \
  -H "X-Telephony-Token: $TOKEN" \
  -F external_id=$EXT \
  -F from_number=+79990000000 \
  -F file=@/var/spool/asterisk/monitor/$EXT.wav
```

`POST .../ended` с `recording_url` сам скачает запись:

```json
{
  "status": "completed",
  "duration_seconds": 95,
  "recording_url": "http://pbx.local/records/1712345678.42.wav",
  "recording_mime": "audio/wav"
}
```

После загрузки backend:

1. сохраняет файл в `calls.recording_data`;
2. расшифровывает запись (если текста ещё нет);
3. запускает ИИ-анализ и создаёт заявку `source=phone`;
4. рассылает статус и транскрипт диспетчеру.

## Asterisk

Готовый пример dialplan: `deploy/asterisk/dialplan-snippet.conf`.
Кратко:

1. `MixMonitor` пишет разговор в WAV.
2. На `h`-extension вызывается `curl` к `/api/telephony/sip/recording`.
3. `external_id` — `${UNIQUEID}`.
4. Backend и Asterisk должны видеть друг друга по сети; в Docker —
   общая сеть compose, адрес `http://web:8000`.

Для облачной АТС используйте её webhook-механизм и те же эндпоинты.

## Хранение

- `calls.recording_data` — аудиофайл целиком в БД;
- `calls.transcript_text`, `recording_mime`, `recording_size`;
- `call_transcript_segments` — таймкоды;
- `calls.external_id` — ID звонка в АТС;
- `GET /api/calls/{id}/recording` поддерживает `Range` (перемотка).

## Ограничения

- Backend не заменяет PBX: нужен Asterisk/FreeSWITCH/облачная АТС.
- In-memory сигналинг не масштабируется горизонтально; для продакшена —
  Redis pub/sub и TURN/SFU.
- Запись в БД удобна для демо; для больших объёмов — S3/MinIO.
- Загрузка записи по `recording_url` — доверенный webhook, защищённый
  токеном. Не открывайте эндпоинты без токена в интернет.
