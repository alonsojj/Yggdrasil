from pydantic import BaseModel, model_validator
from typing import Literal, Optional


class ParsedId(BaseModel):
    raw_id: str
    prefix: str
    id: str
    type: Literal["series", "movie"]
    realm_id: Optional[str] = None
    season: Optional[int] = None
    episode: Optional[int] = None


class ParsedContent(BaseModel):
    id: ParsedId
    name: str
    original_name: str | None = None
