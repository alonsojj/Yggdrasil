from pathlib import Path
from app.core.interfaces import YggScraper, StreamResult
from app.schemas.content import ParsedContent
import asyncio
import importlib.util
import inspect


class AddonEngine:
    def __init__(self, addon_path: str | None = "addons"):
        self.addons_path = Path(addon_path or "addons")
        self.loaded_addons = []

    async def load_all(self):
        for folder in self.addons_path.iterdir():
            if folder.is_dir():
                addon_file = Path(f"{folder}/main.py")
                if addon_file.exists():
                    spec = importlib.util.spec_from_file_location(
                        folder.name, addon_file
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
                            print(obj)
                            self.loaded_addons.append(obj())

    async def load(self, addon_directory: str):
        pass

    async def get_streams(
        self, content: ParsedContent, correlation_id: str
    ) -> list[StreamResult]:
        tasks = []
        all_streams = []
        for addon in self.loaded_addons:
            tasks.append(
                asyncio.create_task(addon.get_streams(content, correlation_id))
            )
        results = await asyncio.gather(*tasks)
        if results:
            for result in results:
                for stream in result:
                    all_streams.append(stream)
        print(all_streams)
        return all_streams
