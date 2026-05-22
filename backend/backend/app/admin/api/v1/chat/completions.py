"""Chat completions API endpoints."""  # pragma: exclude file

from typing import Any

from fastapi import APIRouter
from starlette.responses import StreamingResponse

from backend.app.admin.schema.chat import ChatCompletionPayload
from backend.app.admin.service.chat_service import chat_service


router: APIRouter = APIRouter()


@router.post("/completions", summary="Chat completions (SSE)", response_model=None)  # pyright: ignore[reportGeneralTypeIssues]
async def chat_completions(payload: ChatCompletionPayload) -> StreamingResponse | dict[str, Any]:
    """Chat completions endpoint with SSE support."""
    payload_data = chat_service.normalize_payload(payload.to_payload())
    if payload_data["stream"]:  # pragma: no cover
        stream = await chat_service.create_stream(payload_data)
        headers = {
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
        return StreamingResponse(chat_service.iter_stream(stream), media_type="text/event-stream", headers=headers)

    return await chat_service.create_completion(payload_data)  # pragma: no cover
