# Подключение Asterisk к DispatchAI

Backend принимает записи звонков и метаданные через SIP-webhook.
Сам Asterisk в репозиторий не входит: используется уже установленная АТС
или облачная телефония.

## 1. Настройте backend

В `backend/.env` (или в окружении Docker):

```env
SIP_WEBHOOK_TOKEN=длинный-случайный-токен
SIP_AUTO_ANALYZE=true
SPEECH_PROVIDER=auto
WHISPER_BASE_URL=http://whisper:8000/v1   # если поднят профиль whisper
```

Перезапустите backend. Проверка:

```bash
curl -s http://localhost:8000/api/health
```

В ответе должно быть:

```json
"telephony": { "sip_webhook_enabled": true }
```

## 2. Подключите dialplan

Скопируйте `dialplan-snippet.conf` в `/etc/asterisk/` и добавьте в
`extensions.conf`:

```ini
#include "dialplan-snippet.conf"
```

Либо вставьте содержимое вручную. Обязательно замените:

- `BACKEND_URL` — адрес backend, доступный из Asterisk
  (в Docker Compose это `http://web:8000`);
- `TELEPHONY_TOKEN` — тот же токен, что `SIP_WEBHOOK_TOKEN`.

Перезагрузите:

```bash
asterisk -rx "dialplan reload"
```

## 3. Проверьте запись

Dialplan использует `MixMonitor` и сохраняет WAV в
`/var/spool/asterisk/monitor/`. После звонка на `h`-extension выполняется:

```bash
curl -X POST "$BACKEND_URL/api/telephony/sip/recording" \
  -H "X-Telephony-Token: $TELEPHONY_TOKEN" \
  -F "external_id=$UNIQUEID" \
  -F "from_number=$CALLERID(num)" \
  -F "file=@$REC"
```

Backend:

1. создаёт звонок `transport=sip`, `external_id=<UNIQUEID>`;
2. сохраняет запись в `calls.recording_data`;
3. расшифровывает её локальным Whisper/Google STT;
4. запускает ИИ-анализ и создаёт заявку `source=phone`;
5. отправляет live-события диспетчеру.

## 4. События начала и завершения (опционально)

Если АТС умеет вызывать webhook, можно отправлять:

```bash
curl -X POST "$BACKEND_URL/api/telephony/sip/calls" \
  -H "X-Telephony-Token: $TELEPHONY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"external_id":"1712345678.42","from_number":"+79990000000","direction":"inbound"}'

curl -X POST "$BACKEND_URL/api/telephony/sip/calls/1712345678.42/ended" \
  -H "X-Telephony-Token: $TELEPHONY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status":"completed","duration_seconds":95,"recording_url":"http://pbx.local/records/1712345678.42.wav","recording_mime":"audio/wav"}'
```

`recording_url` должен быть доступен backend по http(s).

## 5. Безопасность

- Не публикуйте `/api/telephony/*` в интернет без токена и HTTPS.
- Токен передаётся в `X-Telephony-Token`; при утечке смените его.
- `recording_url` скачивается backend'ом — разрешайте только доверенные
  хосты АТС.
- Для больших объёмов записей используйте S3/MinIO вместо BLOB в БД.
