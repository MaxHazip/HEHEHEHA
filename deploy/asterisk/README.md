# Подключение Asterisk к DispatchAI

Есть два режима:

1. **ARI (рекомендуется)** — backend сам подключается к Asterisk по
   WebSocket, отвечает на звонок, включает запись, забирает её и создаёт
   заявку. Dialplan — только `Stasis(dispatchai)`.
2. **Webhook + dialplan curl** — Asterisk сам отправляет запись в backend.
   Подходит, если ARI включить нельзя. См. конец документа.

Сам Asterisk в репозиторий не входит: используется установленная АТС,
Docker-контейнер или облачная телефония.

## Режим ARI

### 1. Скопируйте конфиги

```bash
sudo cp ari.conf http.conf /etc/asterisk/
sudo cp dialplan-ari.conf /etc/asterisk/
```

В `/etc/asterisk/extensions.conf`:

```ini
#include "dialplan-ari.conf"
```

### 2. Задайте пароль

`/etc/asterisk/ari.conf`:

```ini
[dispatchai]
type = user
read_only = no
password = change-me
password_format = plain
```

`backend/.env`:

```env
ARI_ENABLED=true
ARI_URL=http://asterisk:8088
ARI_USERNAME=dispatchai
ARI_PASSWORD=change-me
ARI_APP=dispatchai
ARI_RECORD=true
ARI_AUTO_ANALYZE=true
```

- `ARI_URL` — адрес Asterisk из backend. Если backend в Docker Compose,
  а Asterisk на хосте, используйте `http://host.docker.internal:8088`.
- `ARI_APP` должен совпадать с именем в `Stasis(...)` и в `ari.conf`.

### 3. Перезагрузите Asterisk

```bash
asterisk -rx "module reload res_http_websocket.so"
asterisk -rx "module reload res_ari.so"
asterisk -rx "dialplan reload"
```

Проверка ARI:

```bash
curl -u dispatchai:change-me http://localhost:8088/ari/asterisk/info
```

### 4. Перезапустите backend

```bash
uvicorn backend.main:app --reload --port 8000
```

Проверка:

```bash
curl -s http://localhost:8000/api/health
```

Блок:

```json
"ari": {
  "enabled": true,
  "running": true,
  "connected": true,
  "app": "dispatchai"
}
```

### 5. Как проходит звонок

1. Входящий звонок попадает в `[from-trunk]` и уходит в `Stasis(dispatchai)`.
2. ARI присылает `StasisStart`.
3. Backend создаёт `Call(transport=sip, provider=asterisk-ari)`,
   отвечает на канал и запускает запись.
4. При завершении приходит `RecordingFinished`.
5. Backend скачивает WAV через
   `GET /ari/recordings/stored/{name}/file`.
6. Запись сохраняется в `calls.recording_data`, расшифровывается
   Whisper/Google STT и анализируется ИИ.
7. Создаётся заявка `source=phone`; диспетчер видит звонок в `/calls`.

Live-субтитры доступны для браузерных WebRTC-звонков. Для SIP/ARI
расшифровка появляется после завершения звонка (запись → STT).

### Опции

```env
ARI_GREETING_MEDIA=sound:hello-world   # приветствие после ответа
ARI_RECORD=false                       # только события, без записи
ARI_AUTO_ANALYZE=false                 # не создавать заявку автоматически
```

### Диагностика

- **401/403 от ARI** — пароль в `ari.conf` и `ARI_PASSWORD` не совпадают.
- **`connected: false`** — проверьте `ARI_URL`, порт 8088 и firewall.
- **Нет `StasisStart`** — dialplan не уходит в `Stasis(dispatchai)` или
  имя приложения не совпадает с `ARI_APP`.
- **Нет записи** — `ARI_RECORD=false` или ARI-пользователь с
  `read_only=yes`.
- **Запись не скачалась** — в логах backend будет `ARI: не удалось
  скачать запись ...`; проверьте, что файл stored recording существует.

## Режим webhook (альтернатива)

Если ARI недоступен, используйте `dialplan-snippet.conf`: `MixMonitor`
пишет файл, а `curl` на `h`-extension отправляет его в
`/api/telephony/sip/recording`. Подробности — в этом же каталоге и
`docs/telephony.md`.

Не включайте одновременно ARI и webhook для одного звонка: получите две
записи и два звонка в БД.
