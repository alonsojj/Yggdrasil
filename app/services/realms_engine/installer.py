import asyncio
import os
from pathlib import Path
import shutil
import stat


class RealmsInstaller:
    def delete_realm(self, folder_path: Path):
        folder_path = str(folder_path)

        if not os.path.exists(folder_path):
            return True

        def remove_readonly(func, path, excinfo):
            os.chmod(path, stat.S_IWRITE)
            func(path)

        try:
            shutil.rmtree(folder_path, onerror=remove_readonly)
            return True
        except Exception:
            return False

    async def update_from_git(self, folder_path: Path):
        command = "git"
        args = ["-C", folder_path, "pull"]

        process = await asyncio.create_subprocess_exec(
            command,
            *args,
        )
        await process.communicate()
        if process.returncode == 0:
            return True
        else:
            return False

    async def install_from_git(self, url: str, folder_name: Path) -> bool:
        command = "git"
        args = ["clone", url, folder_name]

        process = await asyncio.create_subprocess_exec(
            command,
            *args,
        )
        await process.communicate()
        if process.returncode == 0:
            return True
        else:
            return False
