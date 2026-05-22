"""Chat Service."""  # pragma: exclude file

from typing import Any, cast
from collections.abc import AsyncGenerator

from openai import AsyncOpenAI

from backend.core.conf import settings
from backend.common.exception.errors import GatewayError, RequestError


class ChatService:
    """Chat service for OpenAI API interactions."""

    @staticmethod
    def _get_openai_client() -> AsyncOpenAI:
        base_url = settings.OPENAI_BASE_URL or None
        return AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=base_url,
            timeout=settings.OPENAI_TIMEOUT_SECONDS,
        )

    @staticmethod
    def _apply_defaults(payload: dict[str, Any]) -> dict[str, Any]:
        payload = dict(payload)
        if not payload.get("model"):
            if settings.OPENAI_DEFAULT_MODEL:
                payload["model"] = settings.OPENAI_DEFAULT_MODEL
            else:
                raise RequestError(msg="OpenAI model is required")
        payload["stream"] = payload.get("stream", True)
        return payload

    @staticmethod
    async def iter_stream(stream: Any) -> AsyncGenerator[str]:  # noqa: ANN401
        """Iterate through stream and yield formatted chunks."""
        async for chunk in stream:
            yield f"data: {chunk.model_dump_json()}\n\n"
        yield "data: [DONE]\n\n"

    async def create_stream(self, payload: dict[str, Any]) -> Any:  # noqa: ANN401
        """Create a stream response."""
        client = self._get_openai_client()
        try:
            stream = cast("Any", await client.chat.completions.create(**payload))
        except Exception as exc:
            raise GatewayError(msg="OpenAI request failed") from exc
        else:
            return stream

    async def create_completion(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Create a completion response."""
        client = self._get_openai_client()
        try:
            completion = cast("Any", await client.chat.completions.create(**payload))
        except Exception as exc:
            raise GatewayError(msg="OpenAI request failed") from exc
        return cast("dict[str, Any]", completion.model_dump())

    def normalize_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Normalize payload with defaults."""
        return self._apply_defaults(payload)


chat_service = ChatService()
