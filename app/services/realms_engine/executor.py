from app.core.interfaces import YggScraper, StreamResult
from app.schemas.content import ParsedContent
import asyncio


class RealmsExecutor:
    async def get_meta(
        self, content: ParsedContent, correlation_id: str, listRealms: list[YggScraper]
    ):
        for realm in listRealms:
            if realm.id == content.id.realm_id:
                return await realm.get_meta(content, correlation_id)

    async def search_realms(
        self, query: str, correlation_id: str, listRealms: list[YggScraper]
    ):
        tasks = []
        all_results = []
        for realm in listRealms:
            if realm.searchable:
                tasks.append(asyncio.create_task(realm.search(query, correlation_id)))
        results = await asyncio.gather(*tasks)
        if results:
            for result in results:
                for item in result:
                    if item:
                        all_results.append(item)
        return all_results

    async def run_realms(
        self,
        content: ParsedContent,
        correlation_id: str,
        listRealms: list[YggScraper],
    ) -> list[StreamResult]:
        tasks = []
        all_streams = []
        for realm in listRealms:
            if (
                content.id.prefix in realm.idPrefixies
                or content.id.realm_id in realm.idPrefixies
            ):
                tasks.append(
                    asyncio.create_task(realm.get_streams(content, correlation_id))
                )
        results = await asyncio.gather(*tasks)
        if results:
            for result in results:
                for stream in result:
                    if stream:
                        all_streams.append(stream)

        return all_streams
