from pathlib import Path
from urllib.parse import quote
from app.core.interfaces import YggScraper, StreamResult
from app.schemas.content import ParsedContent
import asyncio
import importlib.util
import inspect


class RealmsEngine:
    def __init__(self, realms_path: str | None = "realms"):
        self.realms_path = Path(realms_path or "realms")
        self.loaded_realms: list[YggScraper] = []
        self.cached_results: dict[str, dict[str, StreamResult]] = {}

    async def load_all(self):
        for folder in self.realms_path.iterdir():
            if folder.is_dir():
                realm_file = Path(f"{folder}/main.py")
                if realm_file.exists():
                    spec = importlib.util.spec_from_file_location(
                        folder.name, realm_file
                    )
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    for member in inspect.getmembers(module):
                        nome, obj = member
                        if (
                            inspect.isclass(obj)
                            and issubclass(obj, YggScraper)
                            and (
                                obj is not YggScraper
                            )  # ignore the import of base class
                        ):
                            self.loaded_realms.append(obj())

    async def load(self, realm_directory: str):
        pass

    def _set_proxy(
        self, content: ParsedContent, stream: StreamResult, server_url: str
    ) -> StreamResult:
        stream.url = f"{server_url}/proxy/stream/{quote(content.id.raw_id)}/{quote(stream.stream_id)}"
        self.cached_results[content.id.raw_id][stream.stream_id] = stream
        return stream

    async def get_streams(
        self, content: ParsedContent, correlation_id: str, server_url: str
    ) -> list[StreamResult]:
        tasks = []
        all_streams = []
        if self.cached_results.get(content.id.raw_id):
            results = [list(self.cached_results[content.id.raw_id].values())]
        else:
            self.cached_results[content.id.raw_id] = {}
            for realm in self.loaded_realms:
                if content.id.prefix in realm.idPrefixies:
                    tasks.append(
                        asyncio.create_task(realm.get_streams(content, correlation_id))
                    )
            results = await asyncio.gather(*tasks)
        if results:
            for result in results:
                for stream in result:
                    if stream:
                        if stream.proxy:
                            stream = self._set_proxy(
                                stream=stream, content=content, server_url=server_url
                            )
                        all_streams.append(stream)

        return all_streams
