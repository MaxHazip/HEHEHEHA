# T-one: локальный сервер распознавания речи

T-one — открытая русскоязычная ASR-модель от Т-Банка
(<https://github.com/T-Bank-AI/T-one>). Ollama её не обслуживает,
поэтому backend общается с T-one по HTTP.

Backend ожидает **OpenAI-совместимый** эндпоинт:

```
POST /audio/transcriptions
Content-Type: multipart/form-data

file=<аудио>
model=t-one
language=ru
response_format=verbose_json
```

Ответ:

```json
{
  "text": "распознанный текст",
  "language": "ru",
  "segments": [{"start": 0.0, "end": 2.4, "text": "фрагмент"}]
}
```

Поля `segments` и `language` необязательны.

## Вариант 1: готовый OpenAI-совместимый сервер

Если ваша сборка T-one уже отдаёт такой API, обёртка не нужна.
Достаточно указать адрес в `backend/.env`:

```env
SPEECH_PROVIDER=tone
TONE_BASE_URL=http://localhost:8002
TONE_ENDPOINT=/audio/transcriptions
TONE_MODEL=t-one
TONE_FILE_FIELD=file
TONE_LANGUAGE=ru
```

## Вариант 2: обёртка (шаблон)

1. Установите T-one по официальному README (PyTorch + веса).
2. Создайте `server.py` рядом с проектом T-one и подключите его функцию
   инференса. Ниже — каркас; замените `transcribe_with_t_one` на вызов
   из официального примера T-one.

```python
import os
import tempfile

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import JSONResponse

# Импорт из официального репозитория T-one (путь зависит от версии):
# from tone import AsrModel
# model = AsrModel(...)

app = FastAPI(title="T-one ASR")


def transcribe_with_t_one(path: str, language: str) -> dict:
    """Замените на вызов инференса T-one из официального README."""
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

3. Запуск:

```bash
uvicorn server:app --host 0.0.0.0 --port 8002
```

4. Проверка:

```bash
curl -s http://localhost:8002/audio/transcriptions \
  -F file=@sample.wav \
  -F model=t-one \
  -F language=ru \
  -F response_format=verbose_json
```

## Проверка со стороны backend

```bash
curl -s -X POST http://localhost:8000/api/voice/transcribe \
  -F file=@sample.wav \
  -F language=ru-RU
```

`GET /api/health` покажет `"speech": {"tone": true, "providers": ["tone"]}`.
