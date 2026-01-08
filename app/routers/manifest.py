from fastapi import APIRouter, Request

router = APIRouter(tags=["STREMIO: manifest"])


@router.get("/manifest.json")
async def get_manifest(request: Request):
    return {
        "id": "io.yggdrasil",
        "version": request.app.version,
        "name": "Yggdrasil Server",
        "resources": ["catalog", "stream", "meta"],
        "types": ["movie", "series"],
        "catalogs": [
            {
                "id": "ygg_src",
                "type": "movie",
                "extra": [{"name": "search", "isRequired": "true"}],
                "name": "Resultados achados pelo Server",
            }
        ],
        "idPrefixes": ["tt", "ygg_src", "kitsu"],
    }
