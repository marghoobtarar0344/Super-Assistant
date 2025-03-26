from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse
from .schemas import QueryRequest
from utils.stream import SSEService

router = APIRouter()

@router.post("/query")
async def query_endpoint(request: QueryRequest):
    sse_service = SSEService()
    return EventSourceResponse(
        sse_service.generate_response(request.query),
        ping=20
    )