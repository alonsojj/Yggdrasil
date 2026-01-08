from crawlee.crawlers import HttpCrawlingContext
from crawlee import Request
from app.core.engines import httpx_router
from parsel import Selector
from addons.fembed.utils import decrypt_AEG
import asyncio
import json

MIRROR_LINK = "https://bysevepoin.com"
CRYPT_LINK = "https://g9r6.com"
fembed_storage = dict[str, asyncio.Future[dict[str, str]]]()  # setup the storage


def handler_error(correlation_id: str):
    fembed_storage[correlation_id].set_result({})


# routers:
@httpx_router.handler("FEMBED_EMBED")
async def fembed_handler(context: HttpCrawlingContext) -> None:
    response_bytes = await context.http_response.read()
    response = response_bytes.decode()
    selector = Selector(text=response)
    try:
        iframe = selector.xpath("//iframe")
        if iframe is None:
            raise ValueError("Iframe not founded")
        mirror_link = iframe.attrib["src"]
        if not mirror_link:
            raise ValueError("link in iframe not founded")
        parts = mirror_link.split("/")
        if (not parts) and (len(parts) < 4):
            raise ValueError("link in iframe is not valid")
        video_id = parts[4]
        header = {
            "Referer": mirror_link,
            "X-Embed-Origin": "fembed.sx",
            "Accept": "application/json",
        }
        next_request = Request.from_url(
            url=f"{MIRROR_LINK}/api/videos/{video_id}/embed/details",
            headers=header,
            unique_key=f"{context.request.unique_key}:mirror",
            label="FEMBED_MIRROR",
        )
        await context.add_requests([next_request])
        print("foi para o mirror fase")
    except Exception as e:
        print(e)
        handler_error(context.request.unique_key)


@httpx_router.handler("FEMBED_MIRROR")
async def mirror_handler(context: HttpCrawlingContext) -> None:
    print("mirror fase")
    response_bytes = await context.http_response.read()
    response = response_bytes.decode()
    selector = Selector(text=response)
    try:
        crypited_link = selector.jmespath("embed_frame_url").get()
        if not crypited_link:
            raise ValueError("unexpected response")
        parts = crypited_link.split("/")
        if (not parts) and (len(parts) < 4):
            raise ValueError("link in iframe is not valid")
        video_id = parts[4]
        header = {
            "Host": "g9r6.com",
            "Accept": "*/*",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Connection": "keep-alive",
            "Referer": crypited_link,
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "X-Embed-Origin": "fembed.sx",
            "X-Embed-Parent": context.request.headers.get("Referer"),
            "Accept-Encoding": "gzip, deflate, br, zstd",
        }
        print(header)
        next_request = Request.from_url(
            url=f"{CRYPT_LINK}/api/videos/{video_id}/embed/playback",
            headers=header,
            unique_key=f"{context.request.unique_key}:decrypt",
            label="FEMBED_CRYPT",
        )
        await context.add_requests([next_request])
        print("foi para o mirror crypt")
    except Exception as e:
        print(e)
        handler_error(context.request.unique_key.split(":")[0])


@httpx_router.handler("FEMBED_CRYPT")
async def crypt_handler(context: HttpCrawlingContext) -> None:
    response_bytes = await context.http_response.read()
    response = response_bytes.decode()
    data = json.loads(response)
    try:
        playback = data.get("playback", {})

        payload = playback.get("payload")
        iv = playback.get("iv")
        key_parts = playback.get("key_parts", [])
        legacy = playback.get("decrypt_keys", {}).get("legacy_fallback")
        if not all([payload, iv, key_parts, legacy]):
            raise ValueError("Unexpected reposnse")
        decrypted_str = decrypt_AEG(
            payload=payload, iv=iv, key_parts=key_parts, legacy=legacy
        )
        if not decrypted_str:
            raise RuntimeError("Failed to decrypt link")
        result_data = json.loads(decrypted_str)
        sources = result_data.get("sources", [])
        if not sources:
            raise RuntimeError("Sources not founded")

        final_url = sources[0].get("url")

        if not final_url:
            raise RuntimeError("Label url not founded")
        correlation_id = context.request.unique_key.split(":")[0]
        fembed_storage[correlation_id].set_result(
            {"url": final_url, "headers": final_url}
        )
    except Exception as e:
        print(e)
        handler_error(context.request.unique_key.split(":")[0])
