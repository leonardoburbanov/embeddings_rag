"""Shared image encoding and embedding input helpers."""

import base64


def to_data_uri(image: bytes, mime_type: str) -> str:
    """Encode image bytes as a data URI the embedding APIs accept."""
    encoded = base64.b64encode(image).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def content_parts(
    text: str | None,
    image: bytes | None,
    mime_type: str | None,
) -> list[dict[str, object]]:
    """Build one multimodal content block. At least one part is required."""
    parts: list[dict[str, object]] = []
    if text and text.strip():
        parts.append({"type": "text", "text": text.strip()})
    if image:
        parts.append(
            {
                "type": "image_url",
                "image_url": {"url": to_data_uri(image, mime_type or "image/jpeg")},
            }
        )
    if not parts:
        raise ValueError("An embedding needs text, an image, or both.")
    return parts


def check_dimension(vector: list[float], expected: int, provider: str) -> None:
    """Fail loud when a provider returns a vector that will not fit the collection."""
    if len(vector) != expected:
        raise RuntimeError(f"{provider} returned {len(vector)} dimensions, expected {expected}.")
