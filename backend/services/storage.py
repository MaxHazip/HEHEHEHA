"""Работа с загружаемыми файлами."""

import re
from pathlib import Path

from fastapi import Request, UploadFile
from fastapi.responses import Response

IMAGE_MIME_PREFIX = "image/"
AUDIO_MIME_PREFIX = "audio/"

_EXTENSION_MIME = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".gif": "image/gif",
    ".webm": "audio/webm",
    ".ogg": "audio/ogg",
    ".oga": "audio/ogg",
    ".wav": "audio/wav",
    ".mp3": "audio/mpeg",
    ".m4a": "audio/mp4",
    ".mp4": "audio/mp4",
    ".pdf": "application/pdf",
    ".txt": "text/plain",
    ".log": "text/plain",
}

_ALLOWED_KINDS = ("image", "audio", "document")


class UploadTooLargeError(ValueError):
    pass


async def read_upload(upload: UploadFile, max_bytes: int) -> bytes:
    data = await upload.read()
    if not data:
        raise ValueError("Файл пустой")
    if len(data) > max_bytes:
        raise UploadTooLargeError(
            f"Файл больше допустимых {max_bytes // (1024 * 1024)} МБ"
        )
    return data


def guess_mime(filename: str | None, provided: str | None) -> str:
    if provided and provided != "application/octet-stream":
        return provided
    suffix = Path(filename or "").suffix.lower()
    return _EXTENSION_MIME.get(suffix, "application/octet-stream")


def detect_kind(mime_type: str, filename: str | None = None) -> str:
    if mime_type.startswith(IMAGE_MIME_PREFIX):
        return "image"
    if mime_type.startswith(AUDIO_MIME_PREFIX):
        return "audio"
    suffix = Path(filename or "").suffix.lower()
    if suffix in (".png", ".jpg", ".jpeg", ".webp", ".gif"):
        return "image"
    if suffix in (".webm", ".ogg", ".oga", ".wav", ".mp3", ".m4a", ".mp4"):
        return "audio"
    return "document"


def safe_filename(filename: str | None, fallback: str = "file") -> str:
    name = Path(filename or fallback).name or fallback
    # Убираем управляющие символы и кавычки, ломающие заголовки.
    return re.sub(r'[\x00-\x1f"\\]', "_", name)[:255]


def content_disposition(filename: str) -> str:
    ascii_name = filename.encode("ascii", "ignore").decode("ascii") or "file"
    ascii_name = ascii_name.replace('"', "_")
    return f'inline; filename="{ascii_name}"'


def file_response(
    request: Request,
    data: bytes,
    mime_type: str,
    filename: str,
) -> Response:
    """Отдаёт файл с поддержкой Range (нужно для перемотки аудио)."""

    mime_type = mime_type.partition(";")[0].strip().lower()
    inline = mime_type in {"image/png", "image/jpeg", "image/gif", "image/webp"} or mime_type.startswith("audio/")
    disposition = content_disposition(filename)
    if not inline:
        disposition = disposition.replace("inline;", "attachment;", 1)
        mime_type = "application/octet-stream"
    headers = {
        "Accept-Ranges": "bytes",
        "Content-Disposition": disposition,
        "X-Content-Type-Options": "nosniff",
        "Cache-Control": "private, no-store",
    }

    range_header = request.headers.get("range")
    if range_header:
        match = re.fullmatch(r"bytes=([0-9]{0,19})-([0-9]{0,19})", range_header)
        if match:
            start_text, end_text = match.groups()
            total = len(data)
            if start_text:
                start = int(start_text)
                end = int(end_text) if end_text else total - 1
            else:
                # bytes=-500 -> последние 500 байт.
                length = int(end_text or 0)
                start = max(total - length, 0)
                end = total - 1

            end = min(end, total - 1)
            if start >= total or start > end:
                return Response(
                    status_code=416,
                    headers={"Content-Range": f"bytes */{total}"},
                )

            chunk = data[start : end + 1]
            headers["Content-Range"] = f"bytes {start}-{end}/{total}"
            return Response(
                content=chunk,
                status_code=206,
                media_type=mime_type,
                headers=headers,
            )

    return Response(content=data, media_type=mime_type, headers=headers)
