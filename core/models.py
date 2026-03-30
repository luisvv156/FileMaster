"""Modelos de datos compartidos entre el backend, la IA y la GUI de FileMaster."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Resultado de extracción de texto
# ---------------------------------------------------------------------------

@dataclass
class ExtractionResult:
    """Resultado de la extracción de texto de un documento.

    Attributes:
        text: Texto extraído del documento.
        method: Método usado: "pymupdf", "docx", "pptx", "ocr", "plain".
        note: Mensaje informativo o de advertencia (vacío si fue exitoso).
    """
    text: str
    method: str
    note: str = ""

    @property
    def success(self) -> bool:
        """True si se extrajo texto útil."""
        return bool(self.text.strip())

    def __repr__(self) -> str:
        preview = self.text[:50].replace("\n", " ") if self.text else ""
        return (
            f"ExtractionResult(method={self.method!r}, "
            f"chars={len(self.text)}, preview={preview!r})"
        )


# ---------------------------------------------------------------------------
# Registro de documento procesado
# ---------------------------------------------------------------------------

@dataclass
class DocumentRecord:
    """Representa un documento analizado por el pipeline de FileMaster.

    Es la estructura central que fluye desde text_extractor → embeddings
    → clustering → keyword_extractor → renamer → organizer.
    """
    doc_id: str                          # UUID del documento
    path: str                            # Ruta absoluta actual
    name: str                            # Nombre de archivo con extensión
    extension: str                       # Extensión sin punto: "pdf", "docx"
    size_bytes: int                      # Tamaño en bytes
    modified_at: float                   # Timestamp Unix de última modificación
    text: str                            # Texto extraído (limpio)
    keywords: list[str]                  # Keywords extraídas por NLP
    embedding: list[float]               # Vector semántico (384 dims con MiniLM)
    hash_sha256: str                     # Hash del contenido para deduplicación
    extraction_method: str               # "pymupdf", "docx", "pptx", "ocr", "plain"
    extraction_note: str = ""            # Advertencia del extractor si la hubo
    assigned_category: str | None = None # Nombre del cluster/categoría asignada
    confidence: float = 0.0             # Confianza de clasificación (0.0-1.0)
    duplicate: bool = False             # True si es duplicado detectado
    processed_at: float = field(        # Timestamp de cuando FileMaster lo procesó
        default_factory=time.time
    )

    def __post_init__(self) -> None:
        # Normalizar extensión: siempre sin punto y en minúsculas
        self.extension = self.extension.lstrip(".").lower()
        # Clamping de confianza al rango válido
        self.confidence = max(0.0, min(1.0, self.confidence))

    @property
    def has_text(self) -> bool:
        """True si el documento tiene texto extraído no vacío."""
        return bool(self.text.strip())

    @property
    def has_embedding(self) -> bool:
        """True si el embedding fue calculado (no es vector de ceros)."""
        return bool(self.embedding) and any(v != 0.0 for v in self.embedding)

    @property
    def size_kb(self) -> float:
        """Tamaño del archivo en kilobytes."""
        return round(self.size_bytes / 1024, 2)

    def to_dict(self) -> dict[str, Any]:
        """Serializa el registro a dict para guardarlo en SQLite o JSON."""
        return {
            "doc_id": self.doc_id,
            "path": self.path,
            "name": self.name,
            "extension": self.extension,
            "size_bytes": self.size_bytes,
            "modified_at": self.modified_at,
            "processed_at": self.processed_at,
            "keywords": self.keywords,
            "hash_sha256": self.hash_sha256,
            "extraction_method": self.extraction_method,
            "extraction_note": self.extraction_note,
            "assigned_category": self.assigned_category,
            "confidence": self.confidence,
            "duplicate": self.duplicate,
            # Embedding y texto se omiten por tamaño — se guardan separado si se necesitan
        }

    def __repr__(self) -> str:
        return (
            f"DocumentRecord(name={self.name!r}, "
            f"category={self.assigned_category!r}, "
            f"confidence={self.confidence:.2f}, "
            f"duplicate={self.duplicate})"
        )


# ---------------------------------------------------------------------------
# Propuesta de grupo/cluster para la GUI
# ---------------------------------------------------------------------------

@dataclass
class GroupProposal:
    """Propuesta de agrupación generada por DBSCAN para mostrar en la GUI.

    La pantalla de grupos (groups_screen.py) usa esta estructura para
    mostrar al usuario los clusters detectados y pedir su aprobación.
    """
    group_id: str                    # ID único del cluster (ej: "cluster_0")
    suggested_name: str              # Nombre sugerido por keyword_extractor + renamer
    keywords: list[str]              # Keywords representativas del cluster
    file_ids: list[str]              # doc_ids de los documentos en el cluster
    file_names: list[str]            # Nombres de archivo (para la GUI, sin path)
    centroid: list[float] = field(   # Centroide del cluster (para clasificar nuevos docs)
        default_factory=list
    )
    confidence_avg: float = 0.0      # Confianza promedio de los documentos del cluster

    def __post_init__(self) -> None:
        self.confidence_avg = max(0.0, min(1.0, self.confidence_avg))

    @property
    def file_count(self) -> int:
        return len(self.file_ids)

    def __repr__(self) -> str:
        return (
            f"GroupProposal(name={self.suggested_name!r}, "
            f"files={self.file_count}, "
            f"keywords={self.keywords[:3]})"
        )


# ---------------------------------------------------------------------------
# Perfil de categoría persistente
# ---------------------------------------------------------------------------

@dataclass
class CategoryProfile:
    """Categoría aprendida y guardada en categories.json.

    Representa una categoría ya aprobada por el usuario que se usa
    para clasificar documentos nuevos mediante similitud de centroide.
    """
    name: str
    keywords: list[str] = field(default_factory=list)
    centroid: list[float] = field(default_factory=list)
    files: list[str] = field(default_factory=list)

    @property
    def is_trained(self) -> bool:
        """True si la categoría tiene centroide calculado."""
        return bool(self.centroid) and any(v != 0.0 for v in self.centroid)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "keywords": self.keywords,
            "centroid": self.centroid,
            "files": self.files,
        }


# ---------------------------------------------------------------------------
# Modelos para duplicados
# ---------------------------------------------------------------------------

@dataclass
class DuplicateItem:
    """Un archivo individual dentro de un grupo de duplicados."""
    item_id: str
    doc_id: str
    name: str
    current_path: str
    original_path: str
    state: str        # "original" | "duplicate" | "pending"
    detail: str       # Descripción: "Idéntico (hash)" o "Similar (92%)"
    meta: str         # Info adicional: tamaño, fecha, etc.
    selected: bool = False

    @property
    def is_exact_duplicate(self) -> bool:
        """True si el duplicado es idéntico por hash (no solo similar)."""
        return "hash" in self.detail.lower() or "idéntico" in self.detail.lower()


@dataclass
class DuplicateGroup:
    """Grupo de archivos duplicados o muy similares."""
    group_id: str
    title: str
    mode: str         # "exact" | "similar"
    items: list[DuplicateItem]

    @property
    def item_count(self) -> int:
        return len(self.items)

    @property
    def selected_items(self) -> list[DuplicateItem]:
        """Retorna solo los items marcados para acción."""
        return [item for item in self.items if item.selected]


# ---------------------------------------------------------------------------
# Resumen de ciclo de procesamiento
# ---------------------------------------------------------------------------

@dataclass
class CycleSummary:
    """Estadísticas de un ciclo completo de organización.

    Mostrado en summary_screen.py al finalizar el procesamiento.
    """
    detected: int = 0           # Total de documentos detectados
    organized: int = 0          # Documentos movidos exitosamente
    renamed: int = 0            # Documentos renombrados por la IA
    unclassified: int = 0       # Documentos que DBSCAN marcó como ruido (-1)
    duplicates: int = 0         # Duplicados detectados
    precision: float = 0.0      # Confianza promedio del ciclo (0.0-1.0)
    duration_seconds: float = 0.0
    folders: list[dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.precision = max(0.0, min(1.0, self.precision))

    @property
    def success_rate(self) -> float:
        """Porcentaje de documentos organizados sobre total detectados."""
        if self.detected == 0:
            return 0.0
        return round(self.organized / self.detected, 4)

    @property
    def duration_str(self) -> str:
        """Duración formateada como '2m 34s' o '45s'."""
        total = int(self.duration_seconds)
        minutes, seconds = divmod(total, 60)
        return f"{minutes}m {seconds}s" if minutes > 0 else f"{seconds}s"

    def to_dict(self) -> dict[str, Any]:
        return {
            "detected": self.detected,
            "organized": self.organized,
            "renamed": self.renamed,
            "unclassified": self.unclassified,
            "duplicates": self.duplicates,
            "precision": self.precision,
            "duration_seconds": self.duration_seconds,
            "success_rate": self.success_rate,
            "folders": self.folders,
        }