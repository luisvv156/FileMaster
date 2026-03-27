"""Logica de movimiento y renombrado de archivos."""

from __future__ import annotations

from pathlib import Path

from ai.renamer import SmartRenamer
from core.file_manager import FileManager


class Organizer:
    def __init__(self, file_manager: FileManager | None = None, renamer: SmartRenamer | None = None) -> None:
        self.file_manager = file_manager or FileManager()
        self.renamer = renamer or SmartRenamer()

    def organize(
        self,
        source: Path,
        root_folder: Path,
        category_name: str,
        *,
        auto_rename: bool = True,
        keywords: list[str] | None = None,
    ) -> Path:
        target_folder = self.file_manager.ensure_folder(root_folder / category_name)
        target_name = source.name
        if auto_rename:
            target_name = self.renamer.suggest_name(source, category_name, keywords or [])
        return self.file_manager.move_file(source, target_folder / target_name)

    def move_to_duplicates(self, source: Path, duplicates_folder: Path) -> Path:
        self.file_manager.ensure_folder(duplicates_folder)
        return self.file_manager.move_file(source, duplicates_folder / source.name)
