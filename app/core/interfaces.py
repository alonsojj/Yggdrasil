from datetime import datetime
from pydantic import BaseModel, Field
from abc import abstractmethod, ABC
from typing import Optional, List


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


class Video(BaseModel):
    id: str
    name: str
    released: str = Field(default_factory=lambda: datetime.now().isoformat() + "Z")
    season: int
    episode: int
    description: Optional[str] = None
    thumbnail: Optional[str] = None


class Meta(BaseModel):
    id: str
    name: str
    type: str
    poster: Optional[str] = None
    background: Optional[str] = None
    logo: Optional[str] = None
    description: Optional[str] = None
    releaseInfo: Optional[str] = None
    videos: Optional[List[Video]] = None


class YggScraper(ABC):
    name: str
    idPrefixies: list[str]
    searchable: bool = False

    def __init__(self, id: str):
        self.id = id
        self.idPrefixies.append(id)

    @abstractmethod
    async def search(query: str, correlation_id: str) -> List[Meta]:
        pass

    @abstractmethod
    async def get_meta(raw_id: str, correlation_id: str) -> Meta:
        pass

    @abstractmethod
    async def get_streams(content: dict, correlation_id: str) -> List[StreamResult]:
        pass
