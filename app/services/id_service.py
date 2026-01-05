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

    if content.type == "series":
        data = response.json()["tv_results"][0]
    else:
        data = response.json()["movie_results"][0]
    content_info = ParsedContent(id=content, name=data["name"])
    return content_info


PREFIX_HANDLER = {"tt": get_imdb_info}
