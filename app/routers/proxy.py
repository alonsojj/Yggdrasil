import httpx
import hmac
from urllib.parse import unquote, urljoin
from fastapi import APIRouter, Request, HTTPException, Header, Response
from fastapi.responses import StreamingResponse
from cachetools import TTLCache
from app.core.security import decode_url_path, sign_path
from app.utils.hls_utils import (
    select_best_playlist,
    stream_generator,
    rewrite_hls_playlist,
)

router = APIRouter(prefix="/proxy", tags=["Proxy"])

# CONFIG:
hls_map = TTLCache(maxsize=2000, ttl=14400)
limits = httpx.Limits(max_keepalive_connections=20, max_connections=100)
timeout = httpx.Timeout(90.0, connect=20.0, read=30.0)
client = httpx.AsyncClient(
    timeout=timeout, follow_redirects=True, http2=False, limits=limits
)


# HELPER:
async def get_upstream(
    url: str, request_headers: Header, headers: dict
) -> tuple[Response, dict[str, str]]:
    req_h = {k.lower(): v for k, v in request_headers.items()}
    # pass important incoming headers
    if "range" in req_h:
        headers["range"] = req_h["range"]
    if "accept" in req_h:
        headers["accept"] = req_h["accept"]

    try:
        req = client.build_request("GET", url, headers=headers)
        response = await client.send(req, stream=True)

        # update headers to not cause conflit
        response_headers = {k.lower(): v for k, v in response.headers.items()}
        response_headers.update({"access-control-allow-origin": "*"})
        for h in ["content-encoding", "content-length", "transfer-encoding"]:
            response_headers.pop(h, None)

        return response, response_headers
    except Exception as e:
        raise HTTPException(status_code=502, detail="Upstream connection failed")


# ENDPOINT
@router.get("/stream/{content_id}/{stream_id}")
async def proxy_stream_endpoint(content_id: str, stream_id: str, request: Request):
    unquote_id = unquote(content_id)
    cached_result = request.app.state.addon_engine.cached_results.get(unquote_id)

    if not cached_result or not (stream := cached_result.get(stream_id)):
        raise HTTPException(status_code=404, detail="Streaming not found")

    headers = dict(stream.headers.copy())

    response, response_headers = await get_upstream(
        url=stream.scraped_url, request_headers=request.headers, headers=headers
    )
    content_type = response_headers.get("content-type", "").lower()

    is_hls = (
        any(x in content_type for x in ["mpegurl", "text"])
        or "m3u8" in stream.scraped_url
    )

    if is_hls:
        raw_content = await response.aread()
        decoded_content = raw_content.decode("utf-8", errors="ignore")

        # get the best variant playlist, useful for some devices who doesnt support mulviarant playlist
        best_url = select_best_playlist(decoded_content, stream.scraped_url)

        # TODO: change this to addon engine and offer every link like slipted stream
        #   add suport to multiples audios on multivariants playlists
        if best_url:
            await response.aclose()
            try:
                req = client.build_request(request.method, best_url, headers=headers)
                response = await client.send(req, stream=True)
                stream.scraped_url = best_url
                raw_content = await response.aread()
                decoded_content = raw_content.decode("utf-8", errors="ignore")
            except Exception as e:
                print(f"Erro ao buscar best_url: {e}")
                raise HTTPException(status_code=502, detail="Best playlist failed")
        modified = rewrite_hls_playlist(
            decoded_content,
            stream.headers,
            stream.scraped_url,
            hls_map,
        )
        response_headers["content-type"] = "application/vnd.apple.mpegurl"

        return Response(
            content=modified,
            headers=response_headers,
            status_code=200,
        )
    return StreamingResponse(
        stream_generator(response, request),
        headers=response_headers,
        media_type=content_type,
        status_code=response.status_code,
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

    if not hmac.compare_digest(signature, sign_path(raw_path)):
        raise HTTPException(status_code=403, detail="Invalid signature")

    target_url = urljoin(context["base_url"], raw_path)
    headers = context["headers"].copy()

    response, response_headers = await get_upstream(
        url=target_url, request_headers=request.headers, headers=headers
    )

    content_type = response.headers.get("content-type", "").lower()

    return StreamingResponse(
        stream_generator(response, request),
        media_type=content_type,
        headers=response_headers,
        status_code=response.status_code,
    )
