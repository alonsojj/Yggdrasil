import uuid
import re
import httpx
from typing import AsyncGenerator
from app.core.security import sign_path, encode_url_path
from fastapi import Request
from urllib.parse import urljoin

CHUNK_SIZE = 128 * 1024  # 128Kb


def select_best_playlist(content: str, base_url: str) -> str | None:
    lines = content.splitlines()
    best_bandwidth = -1
    best_url = None
    # TODO: replace this to regex
    for i, line in enumerate(lines):
        if line.startswith("#EXT-X-STREAM-INF"):
            match = re.search(r"BANDWIDTH=(\d+)", line)
            if match:
                bandwidth = int(match.group(1))
                if bandwidth > best_bandwidth:
                    for j in range(i + 1, len(lines)):
                        next_line = lines[j].strip()
                        if next_line and not next_line.startswith("#"):
                            best_bandwidth = bandwidth
                            best_url = urljoin(base_url, next_line)
                            break
    return best_url


def rewrite_hls_playlist(
    content: str, original_headers: dict, base_url: str, hls_map: dict
) -> str:
    hls_id = str(uuid.uuid4())
    # save the context of the request to this hls playlist
    hls_map[hls_id] = {
        "base_url": base_url,
        "headers": original_headers,
    }

    lines = content.splitlines()
    processed_lines = []
    uri_regex = re.compile(r'(URI=["\'])(.*?)(["\'])')

    def make_proxy_url(target_path):
        encoded = encode_url_path(target_path)
        signature = sign_path(target_path)
        return f"/proxy/hls/{hls_id}/{signature}/{encoded}"

    for line in lines:
        clean = line.strip()
        if not clean:
            processed_lines.append(line)
            continue
        if clean.startswith("#"):
            if "URI=" in clean:

                def replace_uri(match):
                    q_start, uri, q_end = match.groups()
                    return f"{q_start}{make_proxy_url(uri)}{q_end}"

                processed_lines.append(uri_regex.sub(replace_uri, line))
            else:
                processed_lines.append(line)
            continue

        processed_lines.append(make_proxy_url(clean))
    return "\n".join(processed_lines)


async def stream_generator(
    response: httpx.Response, request: Request
) -> AsyncGenerator[bytes, None]:
    try:
        async for chunk in response.aiter_bytes(chunk_size=CHUNK_SIZE):
            if await request.is_disconnected():
                break
            yield chunk
    finally:
        await response.aclose()
