from app.core.interfaces import YggScraper
from pathlib import Path
import importlib.util
import inspect
import uuid


class RealmsManager:
    loaded_realms: list[YggScraper] = []

    def __init__(self, realms_path: str):
        self.realms_path = Path(realms_path or "realms")

    def load_realm(self, realm_folder: Path) -> YggScraper | None:
        if realm_folder.is_dir():
            realm_file = Path(f"{realm_folder}/main.py")
            if realm_file.exists():
                spec = importlib.util.spec_from_file_location(
                    realm_folder.name, realm_file
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                for member in inspect.getmembers(module):
                    nome, obj = member
                    if (
                        inspect.isclass(obj)
                        and issubclass(obj, YggScraper)
                        and (obj is not YggScraper)  # ignore the import of base class
                    ):
                        instance = obj(str(uuid.uuid4()))
                        instance.source_path = str(realm_folder)
                        self.loaded_realms.append(instance)
        return None

    def load_all(self):
        self.loaded_realms = []
        for realm_folder in self.realms_path.iterdir():
            realm = self.load_realm(realm_folder)
            if realm:
                self.loaded_realms.append(realm)

    def remove(self, realm_id: str):
        self.loaded_realms = [
            realm for realm in self.loaded_realms if realm.id != realm_id
        ]
