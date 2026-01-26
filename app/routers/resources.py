from email.utils import unquote
from fastapi import APIRouter, Depends, Request
from typing import Annotated
from app.core.interfaces import Meta
from app.dependencies import parse_content
from app.schemas.content import ParsedContent
from app.utils.network import get_server_url

router = APIRouter(tags=["STREMIO: Resources"])


@router.get("/{resource}/{type}/{raw_id}.json")
async def handle_resources(
    resource: str,
    content: Annotated[ParsedContent, Depends(parse_content)],
    request: Request,
):
    correlation_id = request.headers.get("X-Request-ID")
    server_url = get_server_url(request)
    if resource == "stream":
        result = await request.app.state.realms_engine.get_streams(
            content, correlation_id, server_url
        )
        return {"streams": result}
    elif resource == "meta":
        result = await request.app.state.realms_engine.get_meta(content, correlation_id)
        return {"meta": result}


@router.get("/{resource}/{type}/{raw_id}/{extraArgs}.json")
async def handle_search(
    resource: str,
    raw_id: str,
    extraArgs: str,
    request: Request,
):
    if resource == "catalog":
        if "search=" not in extraArgs:
            return "coming soon..."
        parts = extraArgs.split("&")
        query = unquote(parts[0].split("search=")[1])
        correlation_id = request.headers.get("X-Request-ID")
        print(query)
        result: list[Meta] = await request.app.state.realms_engine.search(
            query,
            correlation_id,
        )
        print(query)
        return {"cacheMaxAge": 86400, "metas": result, "rank": 33.125, "query": query}

    else:
        return "coming soon..."
