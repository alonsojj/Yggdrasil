from app.core.interfaces import Meta, StreamResult
from app.schemas.content import ParsedContent
from .manager import RealmsManager
from .executor import RealmsExecutor
from .installer import RealmsInstaller
from .storage import RealmsStorage
from urllib.parse import quote


class RealmsEngine:
    def __init__(self, realms_path: str):
        self.executor = RealmsExecutor()
        self.installer = RealmsInstaller()
        self.manager = RealmsManager(realms_path=realms_path)
        self.manager.load_all()

    # ==========================================
    # Stream-controller
    # ==========================================
    def _proxy_streams(self, server_url: str, content_id: str, stream_id: str) -> str:
        # TODO: add logic to external proxys
        return f"{server_url}/proxy/stream/{quote(content_id)}/{quote(stream_id)}"

    async def get_streams(
        self, content: ParsedContent, correlation_id: str, server_url: str
    ) -> list[StreamResult]:
        if RealmsStorage.cached_results.get(content.id.raw_id):
            streams = list(RealmsStorage.cached_results.get(content.id.raw_id).values())
        else:
            listRealms = self.manager.loaded_realms
            streams = await self.executor.run_realms(
                content, correlation_id, listRealms
            )
            RealmsStorage.cached_results[content.id.raw_id] = {}
        for stream in streams:
            RealmsStorage.cached_results[content.id.raw_id][stream.stream_id] = stream
            if stream.proxy:
                stream.url = self._proxy_streams(
                    server_url, content.id.raw_id, stream.stream_id
                )
        return streams

    async def get_meta(self, content: ParsedContent, correlation_id: str):
        listRealms = self.manager.loaded_realms
        results = await self.executor.get_meta(content, correlation_id, listRealms)
        return results

    async def search(self, query: str, correlation_id: str) -> list[Meta]:
        listRealms = self.manager.loaded_realms
        results = await self.executor.search_realms(query, correlation_id, listRealms)
        return results

    # ==========================================
    # Realms-controller
    # ==========================================
    async def update_realm(self):
        pass

    async def add_realm(self):
        pass

    async def del_realm(self):
        pass

    def read_realms(self):
        pass
