from fastapi import APIRouter, Request
from starlette.responses import FileResponse
from pathlib import Path

router = APIRouter(tags=["STREMIO: manifest"])


@router.get("/")
@router.get("/configure")
async def get_config(request: Request):
    caminho = Path("app/static/configure.html").resolve()
    return FileResponse(caminho)


@router.get("/manifest.json")
async def get_manifest(request: Request):
    return {
        "id": "io.yggdrasil",
        "version": request.app.version,
        "name": "Yggdrasil Server",
        "logo": str(request.base_url) + "static/logo.png",
        "resources": ["catalog", "stream", "meta"],
        "types": ["movie", "series"],
        "catalogs": [
            {
                "id": "ygg",
                "type": "movie",
                "extra": [{"name": "search", "isRequired": True}],
                "name": "Resultados achados pelo Server",
            },
        ],
        "idPrefixes": ["tt", "ygg", "kitsu"],
    }
