"""Operaciones seguras sobre archivos."""

from __future__ import annotations

import shutil
from pathlib import Path


class FileManager:
    def ensure_folder(self, folder: Path) -> Path:
        folder.mkdir(parents=True, exist_ok=True)
        return folder

    def unique_path(self, destination: Path) -> Path:
        if not destination.exists():
            return destination

        counter = 1
        while True:
            candidate = destination.with_name(f"{destination.stem}_{counter}{destination.suffix}")
            if not candidate.exists():
                return candidate
            counter += 1

    def move_file(self, source: Path, destination: Path) -> Path:
        self.ensure_folder(destination.parent)
        final_destination = self.unique_path(destination)
        shutil.move(str(source), str(final_destination))
        return final_destination

    def delete_file(self, file_path: Path) -> None:
        if file_path.exists():
            file_path.unlink()
