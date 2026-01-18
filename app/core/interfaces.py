from pydantic import BaseModel
from abc import abstractmethod, ABC
from typing import Literal, List


class StreamResult(BaseModel):
    stream_id: str
    name: str | None = None
    title: str
    scraped_url: str
    url: str | None = None
    headers: dict[str, str] | None = {}
    proxy: bool = True
    proxy_url: str | None = None
    expires_at: int | None = None
    behaviorHints: dict = {"notWebReady": False, "proxyHeaders": {}}


class SearchResult(BaseModel):
    type: Literal["movie", "series"]
    id: str
    name: str
    poster: str | None = None


class YggScraper(ABC):
    idPrefixies: list[str]

    @abstractmethod
    async def search(query: str) -> List[SearchResult]:
        pass

    @abstractmethod
    async def get_streams(content: dict, correlation_id: str) -> List[StreamResult]:
        pass
