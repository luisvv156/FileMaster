"""Operaciones seguras sobre el sistema de archivos para FileMaster."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)


class FileManager:
    """Abstracción sobre operaciones de filesystem con manejo de errores y logging.

    Todas las operaciones de movimiento, copia y eliminación del proyecto
    pasan por esta clase para garantizar consistencia y trazabilidad.
    """

    # ------------------------------------------------------------------
    # Carpetas
    # ------------------------------------------------------------------

    def ensure_folder(self, folder: Path) -> Path:
        """Crea la carpeta y todos sus padres si no existen.

        Args:
            folder: Ruta de la carpeta a garantizar.

        Returns:
            La misma ruta de carpeta (para encadenamiento).
        """
        folder.mkdir(parents=True, exist_ok=True)
        return folder

    # ------------------------------------------------------------------
    # Resolución de colisiones
    # ------------------------------------------------------------------

    def unique_path(self, destination: Path) -> Path:
        """Genera una ruta de destino que no colisione con un archivo existente.

        Añade sufijo numérico con formato `nombre (N).ext`:
            tarea_redes.pdf → tarea_redes (1).pdf → tarea_redes (2).pdf

        Args:
            destination: Ruta deseada para el archivo destino.

        Returns:
            Ruta garantizadamente libre (puede ser la original si no hay colisión).
        """
        if not destination.exists():
            return destination

        stem = destination.stem
        suffix = destination.suffix
        parent = destination.parent
        counter = 1

        while True:
            candidate = parent / f"{stem} ({counter}){suffix}"
            if not candidate.exists():
                return candidate
            counter += 1

    # ------------------------------------------------------------------
    # Operaciones principales
    # ------------------------------------------------------------------

    def move_file(self, source: Path, destination: Path) -> Path | None:
        """Mueve un archivo de origen a destino, creando carpetas si es necesario.

        Resuelve automáticamente colisiones de nombre.

        Args:
            source: Ruta del archivo a mover. Debe existir.
            destination: Ruta destino deseada.

        Returns:
            La ruta final donde quedó el archivo, o None si falló.
        """
        if not source.exists():
            logger.warning("move_file: origen no existe: %s", source)
            return None

        try:
            self.ensure_folder(destination.parent)
            final = self.unique_path(destination)
            shutil.move(source, final)
            logger.debug("Movido: '%s' → '%s'", source.name, final)
            return final
        except (OSError, PermissionError, shutil.Error) as exc:
            logger.error("Error al mover '%s': %s", source.name, exc)
            return None

    def copy_file(self, source: Path, destination: Path) -> Path | None:
        """Copia un archivo sin eliminar el original.

        Usado por el detector de duplicados para conservar ambas copias
        antes de mover una a la carpeta de duplicados.

        Args:
            source: Ruta del archivo fuente.
            destination: Ruta destino deseada.

        Returns:
            Ruta de la copia creada, o None si falló.
        """
        if not source.exists():
            logger.warning("copy_file: origen no existe: %s", source)
            return None

        try:
            self.ensure_folder(destination.parent)
            final = self.unique_path(destination)
            shutil.copy2(source, final)   # copy2 preserva metadatos (fecha, etc.)
            logger.debug("Copiado: '%s' → '%s'", source.name, final)
            return final
        except (OSError, PermissionError, shutil.Error) as exc:
            logger.error("Error al copiar '%s': %s", source.name, exc)
            return None

    def delete_file(self, file_path: Path) -> bool:
        """Elimina un archivo permanentemente del sistema.

        Nota: Para "papelera" usa `organizer.move_to_trash()` en lugar de este método.
        Este método es para eliminación definitiva (ej. limpiar archivos temporales).

        Args:
            file_path: Ruta del archivo a eliminar.

        Returns:
            True si se eliminó correctamente, False si no existía o falló.
        """
        if not file_path.exists():
            logger.debug("delete_file: archivo no encontrado (ya eliminado): %s", file_path.name)
            return False

        try:
            file_path.unlink()
            logger.info("Eliminado permanentemente: '%s'", file_path.name)
            return True
        except (OSError, PermissionError) as exc:
            logger.error("Error al eliminar '%s': %s", file_path.name, exc)
            return False

    def rename_file(self, source: Path, new_name: str) -> Path | None:
        """Renombra un archivo dentro de su misma carpeta.

        Args:
            source: Archivo a renombrar.
            new_name: Nuevo nombre con extensión (ej. 'redes_tcp.pdf').

        Returns:
            Nueva ruta, o None si falló.
        """
        if not source.exists():
            logger.warning("rename_file: origen no existe: %s", source)
            return None

        target = self.unique_path(source.parent / new_name)
        try:
            result = source.rename(target)
            logger.debug("Renombrado: '%s' → '%s'", source.name, result.name)
            return result
        except (OSError, PermissionError) as exc:
            logger.error("Error al renombrar '%s': %s", source.name, exc)
            return None

    # ------------------------------------------------------------------
    # Consultas de información
    # ------------------------------------------------------------------

    def file_info(self, file_path: Path) -> dict | None:
        """Retorna metadatos básicos de un archivo para poblar FileRecord.

        Args:
            file_path: Ruta del archivo.

        Returns:
            Dict con: name, extension, size_bytes, size_kb, exists.
            None si el archivo no existe.
        """
        if not file_path.exists():
            return None

        stat = file_path.stat()
        return {
            "name":       file_path.name,
            "stem":       file_path.stem,
            "extension":  file_path.suffix.lower().lstrip("."),
            "size_bytes": stat.st_size,
            "size_kb":    round(stat.st_size / 1024, 2),
            "parent":     str(file_path.parent),
        }

    def list_files(
        self,
        folder: Path,
        extensions: set[str] | None = None,
        *,
        recursive: bool = False,
    ) -> list[Path]:
        """Lista archivos en una carpeta, opcionalmente filtrando por extensión.

        Args:
            folder: Carpeta a explorar.
            extensions: Set de extensiones a incluir, ej. {'.pdf', '.docx'}.
                        None incluye todos los archivos.
            recursive: Si True, explora subcarpetas también.

        Returns:
            Lista de rutas de archivos encontrados.
        """
        if not folder.is_dir():
            logger.warning("list_files: carpeta no encontrada: %s", folder)
            return []

        pattern = "**/*" if recursive else "*"
        files = [
            p for p in folder.glob(pattern)
            if p.is_file() and (
                extensions is None or p.suffix.lower() in extensions
            )
        ]
        return sorted(files)