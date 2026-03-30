"""Lógica de movimiento, renombrado y organización de archivos."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

from ai.renamer import SmartRenamer
from core.file_manager import FileManager

logger = logging.getLogger(__name__)


class Organizer:
    """Orquesta el movimiento y renombrado de archivos hacia su categoría destino.

    Responsabilidades:
    - Crear la carpeta destino si no existe.
    - Generar un nombre sugerido por la IA (o conservar el original).
    - Resolver colisiones de nombres sin sobreescribir archivos.
    - Mover duplicados a su carpeta especial.
    - Loguear cada operación para trazabilidad.
    """

    def __init__(
        self,
        file_manager: FileManager | None = None,
        renamer: SmartRenamer | None = None,
    ) -> None:
        self.file_manager = file_manager or FileManager()
        self.renamer = renamer or SmartRenamer()

    # ------------------------------------------------------------------
    # API principal
    # ------------------------------------------------------------------

    def organize(
        self,
        source: Path,
        root_folder: Path,
        category_name: str,
        *,
        auto_rename: bool = True,
        keywords: list[str] | None = None,
    ) -> Path | None:
        """Mueve `source` a `root_folder / category_name /` con nombre sugerido.

        Args:
            source: Ruta del archivo original.
            root_folder: Carpeta raíz donde se crean las subcarpetas de categoría.
            category_name: Nombre de la categoría/cluster (nombre de subcarpeta).
            auto_rename: Si True, usa SmartRenamer para sugerir un nombre nuevo.
            keywords: Keywords extraídas del documento (para el renombrador).

        Returns:
            La ruta final donde quedó el archivo, o None si falló.
        """
        if not source.exists():
            logger.warning("organize: origen no encontrado: %s", source)
            return None

        try:
            target_folder = self.file_manager.ensure_folder(
                root_folder / category_name
            )

            # Decidir el nombre destino
            if auto_rename:
                raw_name = self.renamer.suggest_name(
                    source, category_name, keywords or []
                )
            else:
                raw_name = source.name

            # Resolver colisión: nunca sobreescribir
            target_path = self._resolve_collision(target_folder / raw_name)

            final_path = self.file_manager.move_file(source, target_path)
            logger.info(
                "Organizado: '%s' → '%s'",
                source.name,
                final_path.relative_to(root_folder),
            )
            return final_path

        except (OSError, PermissionError) as exc:
            logger.error(
                "Error al organizar '%s' en '%s': %s",
                source.name,
                category_name,
                exc,
            )
            return None

    def move_to_duplicates(self, source: Path, duplicates_folder: Path) -> Path | None:
        """Mueve un archivo identificado como duplicado a su carpeta especial.

        Args:
            source: Ruta del archivo duplicado.
            duplicates_folder: Carpeta destino para duplicados.

        Returns:
            Ruta final del archivo, o None si falló.
        """
        if not source.exists():
            logger.warning("move_to_duplicates: origen no encontrado: %s", source)
            return None

        try:
            self.file_manager.ensure_folder(duplicates_folder)
            target_path = self._resolve_collision(duplicates_folder / source.name)
            final_path = self.file_manager.move_file(source, target_path)
            logger.info("Duplicado movido: '%s' → duplicados/", source.name)
            return final_path

        except (OSError, PermissionError) as exc:
            logger.error(
                "Error al mover duplicado '%s': %s", source.name, exc
            )
            return None

    def move_to_trash(self, source: Path, trash_folder: Path) -> Path | None:
        """Mueve un archivo a la papelera interna de FileMaster (no al SO).

        Diferente a `move_to_duplicates` — aquí el usuario pidió explícitamente
        descartar el archivo desde la GUI.

        Args:
            source: Ruta del archivo a descartar.
            trash_folder: Carpeta de papelera configurada por el usuario.

        Returns:
            Ruta en papelera, o None si falló.
        """
        if not source.exists():
            logger.warning("move_to_trash: origen no encontrado: %s", source)
            return None

        try:
            self.file_manager.ensure_folder(trash_folder)
            target_path = self._resolve_collision(trash_folder / source.name)
            final_path = self.file_manager.move_file(source, target_path)
            logger.info("Enviado a papelera: '%s'", source.name)
            return final_path

        except (OSError, PermissionError) as exc:
            logger.error(
                "Error al enviar a papelera '%s': %s", source.name, exc
            )
            return None

    def restore_file(self, source: Path, original_folder: Path) -> Path | None:
        """Restaura un archivo desde papelera/duplicados a su ubicación original.

        Usado desde la pantalla de historial en la GUI cuando el usuario
        deshace una operación.

        Args:
            source: Ruta actual del archivo (en papelera o duplicados).
            original_folder: Carpeta a donde se debe restaurar.

        Returns:
            Nueva ruta del archivo restaurado, o None si falló.
        """
        if not source.exists():
            logger.warning("restore_file: origen no encontrado: %s", source)
            return None

        try:
            self.file_manager.ensure_folder(original_folder)
            target_path = self._resolve_collision(original_folder / source.name)
            final_path = self.file_manager.move_file(source, target_path)
            logger.info("Restaurado: '%s' → '%s'", source.name, original_folder)
            return final_path

        except (OSError, PermissionError) as exc:
            logger.error("Error al restaurar '%s': %s", source.name, exc)
            return None

    # ------------------------------------------------------------------
    # Helpers internos
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_collision(target: Path) -> Path:
        """Genera un nombre único si el destino ya existe.

        Añade un sufijo numérico incremental:
            tarea_redes.pdf → tarea_redes (1).pdf → tarea_redes (2).pdf

        Args:
            target: Ruta destino original.

        Returns:
            Ruta con nombre garantizadamente no existente.
        """
        if not target.exists():
            return target

        stem = target.stem
        suffix = target.suffix
        parent = target.parent
        counter = 1

        while True:
            candidate = parent / f"{stem} ({counter}){suffix}"
            if not candidate.exists():
                return candidate
            counter += 1