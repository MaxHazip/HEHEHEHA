"""Сервис описания изображений."""

from ai_module.providers.vision_provider import describe_image


async def describe_attachment(data: bytes, mime_type: str) -> str | None:
    return await describe_image(data, mime_type)
