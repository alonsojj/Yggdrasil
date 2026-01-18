from fastapi import HTTPException
from app.schemas.content import ParsedContent, ParsedId
import httpx
from app.core.config import get_settings

client = httpx.AsyncClient()

tmdb_key = get_settings().tmdb_key


async def get_info(content: ParsedId):
    prefixfunc = PREFIX_HANDLER[content.prefix]
    return await prefixfunc(content)


async def get_imdb_info(content: ParsedId) -> ParsedContent:
    BASE_URL = "https://api.themoviedb.org/3/find"
    headers = {"Authorization": f"Bearer {tmdb_key}", "accept": "application/json"}
    external_id = content.prefix + content.id
    final_url = (
        f"{BASE_URL}/{external_id}?external_source=imdb_id&language=pt-BR&region=BR"
    )
    response = await client.get(final_url, headers=headers)

    json_data = response.json()
    key = "tv_results" if content.type == "series" else "movie_results"
    results = json_data.get(key, [])
    if not results:
        raise HTTPException(status_code=404, detail="Metadata for the movie not found")

    data = results[0]
    name = data.get("name") or data.get("title")
    if not name:
        raise HTTPException(status_code=404, detail="Name for the movie not found")

    content_info = ParsedContent(id=content, name=name)
    return content_info


async def get_kitsu_info(content: ParsedId) -> ParsedContent:
    BASE_URL = "https://kitsu.io/api/edge"
    final_url = f"{BASE_URL}/anime/{content.id}"
    response = await client.get(final_url)
    data = response.json()["data"]["attributes"]
    content_info = ParsedContent(id=content, name=data["canonicalTitle"])
    return content_info


PREFIX_HANDLER = {"tt": get_imdb_info, "kitsu": get_kitsu_info}
