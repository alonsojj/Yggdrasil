from fastapi import APIRouter, Depends, Request
from typing import Annotated
from app.dependencies import parse_content
from app.schemas.content import ParsedContent

router = APIRouter(
    prefix="/stream",
    tags=["STREMIO: Streams"],
    dependencies=[Depends(parse_content)],
)


@router.get("/{type}/{raw_id}.json")
async def handle_streams(
    content: Annotated[ParsedContent, Depends(parse_content)], request: Request
):
    result = await request.app.state.addon_engine.get_streams(content)
    return result
