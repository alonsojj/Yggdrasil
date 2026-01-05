from pydantic import BaseModel, model_validator
from typing import Literal, Optional


class ParsedId(BaseModel):
    raw_id: str
    prefix: str
    id: str
    type: Literal["series", "movie"]
    season: Optional[int] = None
    episode: Optional[int] = None

    @model_validator(mode="after")
    def validate_fields(self):
        if self.type == "series":
            if self.season is None or self.episode is None:
                ValueError("Series have to be seasons and episode")
        else:
            if self.episode is not None or self.season is not None:
                ValueError("Movies must not have episode and season")
        return self


class ParsedContent(BaseModel):
    id: ParsedId
    name: str
    original_name: str | None = None
