from urllib.parse import quote
from app.core.interfaces import Meta, Video, YggScraper, StreamResult
from realms.anitube.routers import anitube_storage, anitube_cached_meta
from app.core.engines import httpxCrawl
from app.schemas.content import ParsedContent
from crawlee import Request
import asyncio

ANITUBE_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36 Edg/144.0.0.0"


class Anitube(YggScraper):
    name = "Anitube"
    idPrefixies = ["anitube"]
    searchable = True
    BASE_URL = "https://www.anitube.news"
    REQUEST_HEADERS = {
        "Referer": BASE_URL,
        "User-Agent": ANITUBE_USER_AGENT,
    }
    STREAMING_HEADERS = {
        "referer": "https://api.anivideo.net/",
        "user-agent": ANITUBE_USER_AGENT,
    }

    async def get_streams(self, content: ParsedContent, correlation_id: str):
        content_url = f"{self.BASE_URL}/video/{content.id.id}"
        if content.id.type == "series":
            unique_key = f"{correlation_id}:{content.id.episode}"
            label = "ANITUBE_PLAYLIST"
        else:
            unique_key = correlation_id
            label = "ANITUBE_VIDEO"

        request = Request.from_url(
            url=content_url,
            headers=self.REQUEST_HEADERS,
            unique_key=unique_key,
            label=label,
        )
        anitube_storage[correlation_id] = asyncio.Future[dict[str, str]]()
        await httpxCrawl.add_requests([request])
        result = await anitube_storage[correlation_id]
        if result:
            del anitube_storage[correlation_id]
            return [
                StreamResult(
                    stream_id=f"anitube:{content.id.id}",
                    name="Anitube",
                    title=f"Anitube - {result['name']}",
                    scraped_url=result["url"],
                    headers=self.STREAMING_HEADERS,
                )
            ]
        else:
            return []

    async def search(self, query: str, correlation_id: str):
        content_url = f"{self.BASE_URL}/?s={quote(query)}"
        print("indo...")
        request = Request.from_url(
            url=content_url,
            headers=self.REQUEST_HEADERS,
            unique_key=correlation_id,
            label="ANITUBE_SEARCH",
        )
        anitube_storage[correlation_id] = asyncio.Future[list[dict[str, str]]]()
        await httpxCrawl.add_requests([request])
        results = await anitube_storage[correlation_id]
        meta = []
        if results:
            del anitube_storage[correlation_id]
            for result in results:
                meta.append(
                    Meta(
                        type=result["type"],
                        id=f"ygg:{self.id}:{result['id']}",
                        name=result["name"],
                        poster=result["poster"],
                    )
                )
        return meta

    async def get_meta(self, content: ParsedContent, correlation_id):
        meta = None
        episodes = []
        if content.id.type == "series":
            content_url = f"{self.BASE_URL}/video/{content.id.id}"
            label = "ANITUBE_PLAYLIST_META"
            request = Request.from_url(
                url=content_url,
                headers=self.REQUEST_HEADERS,
                unique_key=correlation_id,
                label=label,
            )
            anitube_storage[correlation_id] = asyncio.Future[list[dict[str, str]]]()
            await httpxCrawl.add_requests([request])
            results = await anitube_storage[correlation_id]
            if results:
                del anitube_storage[correlation_id]
                for result in results:
                    episodes.append(
                        Video(
                            id=f"{content.id.raw_id}:{result['id']}",
                            name=result["name"],
                            season=result["season"],
                            episode=result["episode"],
                        )
                    )
        result = anitube_cached_meta[content.id.id]
        meta = Meta(
            type=result["type"],
            id=f"ygg:{self.id}:{result['id']}",
            name=result["name"],
            poster=result["poster"],
            background=result["poster"],
        )
        if episodes:
            meta.videos = episodes
        print(meta)
        return meta
