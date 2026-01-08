from app.core.interfaces import YggScraper, StreamResult
from addons.fembed.routers import fembed_storage
from app.core.engines import httpxCrawl
from app.schemas.content import ParsedContent
from crawlee import Request
import asyncio


class Fembed(YggScraper):
    BASE_URL = "https://fembed.sx"
    REQUEST_HEADERS = {
        "Referer": BASE_URL,
        "Content-Type": "application/x-www-form-urlencoded",
    }
    STREAMING_HEADERS = {
        "Referer": "https://g9r6.com/",
        "Origin": "https://g9r6.com",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
    }

    async def get_streams(self, content: ParsedContent, correlation_id: str):
        content_url = f"{self.BASE_URL}/api.php?action=getAds&s={content.id.prefix + content.id.id}-dub&c="
        if content.id.type == "series":
            content_url = (
                f"{content_url}{content.id.season}-{content.id.episode}&key=0&lang=DUB"
            )
        else:
            content_url = f"{content_url}&key=0&lang=DUB"

        request = Request.from_url(
            url=content_url,
            headers=self.REQUEST_HEADERS,
            unique_key=correlation_id,
            label="FEMBED_EMBED",
        )
        fembed_storage[correlation_id] = asyncio.Future[dict[str, str]]()
        await httpxCrawl.add_requests([request])
        result = await fembed_storage[correlation_id]
        if result:
            del fembed_storage[correlation_id]
            return [
                StreamResult(
                    title=f"Fembed/Goflix - {content.name}",
                    url=result["url"],
                    headers=self.STREAMING_HEADERS,
                )
            ]
        else:
            return []

    async def search(query):
        pass
