from fastapi import APIRouter, Depends, Request
from typing import Annotated
from app.dependencies import parse_content
from app.schemas.content import ParsedContent
from app.utils.network import get_server_url

router = APIRouter(
    prefix="/stream",
    tags=["STREMIO: Streams"],
    dependencies=[Depends(parse_content)],
)


@router.get("/{type}/{raw_id}.json")
async def handle_streams(
    content: Annotated[ParsedContent, Depends(parse_content)], request: Request
):
    correlation_id = request.headers.get("X-Request-ID")
    server_url = get_server_url(request)
    result = await request.app.state.addon_engine.get_streams(
        content, correlation_id, server_url
    )
    return {"streams": result}
