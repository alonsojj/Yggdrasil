from app.core.interfaces import YggScraper
from pathlib import Path
import importlib.util
import inspect


class RealmsManager:
    loaded_realms: list[YggScraper] = []

    def __init__(self, realms_path: str):
        self.realms_path = Path(realms_path or "realms")

    def load_all(self):
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
