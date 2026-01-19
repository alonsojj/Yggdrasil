from app.core.interfaces import YggScraper, StreamResult
from app.schemas.content import ParsedContent
import asyncio


class RealmsExecutor:
    async def run_realms(
        self,
        content: ParsedContent,
        correlation_id: str,
        listRealms: list[YggScraper],
    ) -> list[StreamResult]:
        tasks = []
        all_streams = []
        for realm in listRealms:
            if content.id.prefix in realm.idPrefixies:
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
