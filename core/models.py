"""Modelos compartidos del backend."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ExtractionResult:
    text: str
    method: str
    note: str = ""


@dataclass
class DocumentRecord:
    doc_id: str
    path: str
    name: str
    extension: str
    size_bytes: int
    modified_at: float
    text: str
    keywords: list[str]
    embedding: list[float]
    hash_sha256: str
    extraction_method: str
    extraction_note: str = ""
    assigned_category: str | None = None
    confidence: float = 0.0
    duplicate: bool = False


@dataclass
class GroupProposal:
    group_id: str
    suggested_name: str
    keywords: list[str]
    file_ids: list[str]
    file_names: list[str]


@dataclass
class CategoryProfile:
    name: str
    keywords: list[str] = field(default_factory=list)
    centroid: list[float] = field(default_factory=list)
    files: list[str] = field(default_factory=list)


@dataclass
class DuplicateItem:
    item_id: str
    doc_id: str
    name: str
    current_path: str
    original_path: str
    state: str
    detail: str
    meta: str
    selected: bool = False


@dataclass
class DuplicateGroup:
    group_id: str
    title: str
    mode: str
    items: list[DuplicateItem]


@dataclass
class CycleSummary:
    detected: int = 0
    organized: int = 0
    renamed: int = 0
    unclassified: int = 0
    duplicates: int = 0
    precision: float = 0.0
    duration_seconds: float = 0.0
    folders: list[dict[str, object]] = field(default_factory=list)
