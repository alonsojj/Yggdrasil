from pydantic import BaseModel
from abc import abstractmethod, ABC
from typing import Literal,List

class StreamResult(BaseModel):
    title: str
    url: str


class SearchResult(BaseModel):
    type: Literal["movie", "series"]
    id: str
    name: str
    poster: str|None = None


class YggScraper(ABC):
    @abstractmethod
    async def search(query: str) -> List[SearchResult]:
        pass

    @abstractmethod
    async def get_streams(content: dict) -> List[StreamResult]:
        pass
