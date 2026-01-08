import httpx
import hmac
from urllib.parse import urljoin
from fastapi import APIRouter, Request, Response, HTTPException
from fastapi.responses import StreamingResponse
from cachetools import TTLCache
from app.core.security import decode_url_path, sign_path
from app.utils.hls_utils import stream_generator, rewrite_hls_playlist

router = APIRouter(prefix="/proxy", tags=["Proxy"])

# CONFIG:
# hls cache
hls_map = TTLCache(maxsize=2000, ttl=14400)
# httpx client
limits = httpx.Limits(max_keepalive_connections=20, max_connections=100)
timeout = httpx.Timeout(30.0, connect=10.0)
client = httpx.AsyncClient(
    timeout=timeout, follow_redirects=True, http2=True, limits=limits
)


@router.get("/stream/{content_id}/{stream_id}")
async def proxy_stream_endpoint(content_id: str, stream_id: str, request: Request):
    cached_result = request.app.state.addon_engine.cached_results.get(content_id)
    if not cached_result or not (stream := cached_result.get(stream_id)):
        raise HTTPException(status_code=404, detail="Streaming not found")

    headers = stream.headers.copy()
    if "range" in request.headers:
        headers["range"] = request.headers.get("range")

    try:
        req = client.build_request("GET", stream.scraped_url, headers=headers)
        response = await client.send(req, stream=True)
    except Exception:
        raise HTTPException(status_code=502, detail="Upstream connection failed")

    content_type = response.headers.get("content-type", "").lower().split(";")[0]
    # checks if it's a Hls type to rewrite the playlist
    if (
        any(x in content_type for x in ["mpegurl", "text"])
        or "m3u8" in stream.scraped_url
    ):
        content = await response.aread()
        modified = rewrite_hls_playlist(
            content.decode("utf-8", errors="ignore"),
            stream.headers,
            stream.scraped_url,
            hls_map,
        )
        return Response(content=modified, media_type="application/vnd.apple.mpegurl")

    return StreamingResponse(
        stream_generator(response, request),
        headers={"Access-Control-Allow-Origin": "*"},
        media_type=content_type,
    )


@router.get("/hls/{hls_id}/{signature}/{encoded_path}")
async def hls_proxy_handler(
    hls_id: str, signature: str, encoded_path: str, request: Request
):
    context = hls_map.get(hls_id)
    if not context:
        raise HTTPException(status_code=410, detail="Session expired")

    try:
        raw_path = decode_url_path(encoded_path)
    except:
        raise HTTPException(status_code=400, detail="Invalid encoding")

    # check if the signature is valid
    if not hmac.compare_digest(signature, sign_path(raw_path)):
        raise HTTPException(status_code=403, detail="Invalid signature")
    target_url = urljoin(context["base_url"], raw_path)

    try:
        req = client.build_request("GET", target_url, headers=context["headers"])
        response = await client.send(req, stream=True)

        content_type = response.headers.get("content-type", "").lower()
        # if it's a subplaylist rewrite the links
        if any(x in content_type for x in ["mpegurl", "text"]) or ".m3u8" in raw_path:
            content = await response.aread()
            modified = rewrite_hls_playlist(
                content.decode("utf-8", errors="ignore"),
                context["headers"],
                target_url,
                hls_map,
            )
            return Response(
                content=modified, media_type="application/vnd.apple.mpegurl"
            )

        return StreamingResponse(
            stream_generator(response, request),
            media_type=content_type,
            headers={"Access-Control-Allow-Origin": "*"},
        )
    except Exception:
        raise HTTPException(status_code=502, detail="Upstream error")
