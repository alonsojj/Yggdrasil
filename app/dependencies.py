from app.schemas.content import ParsedId, ParsedContent
from fastapi import HTTPException, status
from app.services.id_service import get_info


async def parse_content(type: str, raw_id: str) -> ParsedContent | None:
    episode = None
    season = None
    try:
        if "tt" in raw_id:
            prefix = "tt"
            parts = raw_id.split("tt")
            if type == "series":
                sub_parts = parts[1].split(":")
                if len(sub_parts) == 3:
                    id = sub_parts[0]
                    season = sub_parts[1]
                    episode = sub_parts[2]
                else:
                    raise ValueError("Series must have a season and episode")
            else:
                id = parts[1]
        else:
            parts = raw_id.split(":")
            prefix = parts[0]
            id = parts[1]
            if type == "series":
                if len(parts) < 4:
                    raise ValueError("Series must have a season and episode")
                season = parts[2]
                episode = parts[3]

        content = await get_info(
            ParsedId(
                raw_id=raw_id,
                id=id,
                prefix=prefix,
                type=type,
                season=season,
                episode=episode,
            )
        )
        return content
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid Id format for {type}:{raw_id}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Something is wrong",
        )
