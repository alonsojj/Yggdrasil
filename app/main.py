from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from .routers import manifest, resources, proxy
from app.services.realms_engine import RealmsEngine
from app.core.config import get_settings
from app.core.engines import httpxCrawl
from asgi_correlation_id import CorrelationIdMiddleware
import asyncio
import uvicorn

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    realms_path = settings.realms_path
    realms_engine = RealmsEngine(realms_path=realms_path)
    app.state.realms_engine = realms_engine
    asyncio.create_task(httpxCrawl.run([]))

    yield
    httpxCrawl.stop()
    print("Servidor finalizado")


app = FastAPI(title="Yggdrasil", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(CorrelationIdMiddleware)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(manifest.router)
app.include_router(resources.router)
app.include_router(proxy.router)

if __name__ == "__main__":
    if settings.enable_https:
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=settings.port,
            ssl_keyfile="certs/key.pem",
            ssl_certfile="certs/cert.pem",
            proxy_headers=True,
            forwarded_allow_ips="*",
        )
    else:
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=settings.port,
            proxy_headers=True,
            forwarded_allow_ips="*",
        )
