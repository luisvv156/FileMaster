"""Tema, layout y datos demo para la interfaz de FileMaster."""

from __future__ import annotations

from dataclasses import dataclass

import customtkinter as ctk


WINDOW_WIDTH = 1100
WINDOW_HEIGHT = 680
TITLEBAR_HEIGHT = 32
SIDEBAR_WIDTH = 148
SHELL_PADDING = 0

# ── Paleta principal ──────────────────────────────────────────────────────────
# Dark mode refinado: fondos más profundos, azules más vibrantes, bordes sutiles
COLORS = {
    # Fondos
    "window_bg":      "#080b12",
    "chrome_bg":      "#0d1018",
    "shell_bg":       "#0f1219",
    "sidebar_bg":     "#0b0e16",
    "card_bg":        "#131720",
    "card_alt":       "#181c27",
    "card_soft":      "#1e2335",
    "field_bg":       "#1c2030",
    "hover_bg":       "#1a1f2e",

    # Bordes
    "border":         "#1f2640",
    "border_soft":    "#191e2e",
    "border_accent":  "#2a3558",

    # Primario — azul eléctrico vibrante
    "primary":        "#4d7fff",
    "primary_soft":   "#6e97ff",
    "primary_light":  "#93b4ff",
    "primary_deep":   "#0f1f42",
    "primary_glow":   "#131d35",   # azul muy oscuro sólido (simula glow sin alfa)

    # Estado
    "success":        "#10d97e",
    "success_bg":     "#0a2b1e",
    "warning":        "#f5a623",
    "warning_bg":     "#2a1e0e",
    "danger":         "#ff4f4f",
    "danger_bg":      "#2a0f0f",
    "info":           "#38bdf8",
    "info_bg":        "#0c2233",

    # Texto
    "text":           "#eef2ff",
    "text_secondary": "#7b88a8",
    "text_muted":     "#3d4a68",

    # Marca
    "brand":          "#93b4ff",
    "logo_bg":        "#f4c04a",

    # Gradiente hero (izquierda de la welcome screen)
    "hero_grad_a":    "#0f1219",
    "hero_grad_b":    "#111523",
}

CATEGORY_STYLES = {
    "Inteligencia Artificial": {"bg": "#0f1f42", "text": "#4d7fff", "border": "#1a3060"},
    "Redes de Computadoras":   {"bg": "#0a2b1e", "text": "#10d97e", "border": "#144d32"},
    "Base de Datos":           {"bg": "#2a1e0e", "text": "#f5a623", "border": "#4a3218"},
    "Sistemas Operativos":     {"bg": "#1e0f2e", "text": "#c084fc", "border": "#3a1f52"},
}

SIDEBAR_ITEMS = [
    ("Inicio",        "main",       "home"),
    ("Configuracion", "config",     "folder"),
    ("Historial",     "summary",    "clock"),
    ("Duplicados",    "duplicates", "duplicate"),
]

BOTTOM_SIDEBAR_ITEMS = [("Ajustes", "manual", "gear")]

SCREEN_NAV_STATE = {
    "welcome":    None,
    "config":     "config",
    "groups":     "config",
    "main":       "main",
    "summary":    "summary",
    "manual":     "manual",
    "duplicates": "duplicates",
}

APP_FOLDER = "C:/Users/Genesis/Downloads"

WELCOME_STEPS = [
    "Indica la carpeta que deseas organizar",
    "La IA analiza el contenido de tus documentos y crea las carpetas automaticamente",
    "El agente monitorea en segundo plano y organiza cada archivo nuevo al instante",
]

WELCOME_TAGS = [
    "IA con DBSCAN",
    "Observador en tiempo real",
    "Renombrado opcional",
    "Papelera de duplicados",
    "100% local",
]

WELCOME_PREVIEW_FILES = [
    {"name": "IA_Reporte_2026-03-26.pdf",  "category": "Inteligencia Artificial"},
    {"name": "Redes_Practica3.docx",        "category": "Redes de Computadoras"},
    {"name": "BD_Investigacion.pdf",        "category": "Base de Datos"},
]

CONFIG_TOGGLES = [
    {
        "title":    "Renombrado automatico de archivos",
        "subtitle": "La IA sugerira nombres descriptivos para cada archivo organizado",
        "enabled":  True,
    },
    {
        "title":    "Carpeta de duplicados",
        "subtitle": "Los archivos duplicados se moveran a una carpeta especial para revision manual",
        "enabled":  True,
    },
]

CONFIG_PREVIEW_RENAME = [
    ("SKDJH-KEFHE.pdf",          "IA_Reporte_2026-03-26.pdf"),
    ("trabajo_final_v3.docx",    "BD_Investigacion_2026-03-20.docx"),
]

GROUPS_SUMMARY = [
    ("Documentos", "35"),
    ("Grupos",     "4"),
    ("Precision",  "94%"),
]

GROUP_CARDS = [
    {
        "title":    "GRUPO 1",
        "count":    "12 archivos",
        "keywords": ["algoritmo", "red neuronal", "clasificacion", "aprendizaje", "modelo"],
        "folder":   "Inteligencia Artificial",
    },
    {
        "title":    "GRUPO 2",
        "count":    "8 archivos",
        "keywords": ["protocolo", "router", "TCP/IP", "switch", "firewall"],
        "folder":   "Redes de Computadoras",
    },
    {
        "title":    "GRUPO 3",
        "count":    "6 archivos",
        "keywords": ["SQL", "joins", "normalizacion", "consulta", "indices"],
        "folder":   "Base de Datos",
    },
    {
        "title":    "GRUPO 4",
        "count":    "5 archivos",
        "keywords": ["procesos", "kernel", "memoria", "scheduler", "hilo"],
        "folder":   "Sistemas Operativos",
    },
]

MAIN_CONFIG_ROWS = [
    ("folder",    "Carpeta monitoreada", APP_FOLDER),
    ("spark",     "Activado",            "Renombres descriptivos por IA"),
    ("bot",       "Modo de operacion",   "Observador en segundo plano - desde 09:14 AM"),
    ("duplicate", "Carpeta de duplicados", "Activada - Downloads/_Duplicados/"),
]

MAIN_STATS = [
    {"label": "Total organizados",   "value": "284",  "icon": "file",    "accent": "primary"},
    {"label": "Precision promedio",  "value": "97%",  "icon": "check",   "accent": "success"},
    {"label": "Carpetas creadas",    "value": "8",    "icon": "folder",  "accent": "warning"},
    {"label": "Duplicados detectados", "value": "6",  "icon": "warning", "accent": "warning"},
]

RECENT_FILES = [
    {
        "name":     "IA_Reporte_2026-03-26.pdf",
        "original": "Origen: SKDJH-KEFHE.pdf",
        "category": "Inteligencia Artificial",
        "time":     "Hace 12 min",
    },
    {
        "name":     "Redes_Practica3_2026-03-26.docx",
        "original": "Origen: SKDJH-KEFHE.docx",
        "category": "Redes de Computadoras",
        "time":     "Hace 38 min",
    },
]

SUMMARY_BANNER = {
    "title":     "Organizacion completada - el agente continua activo",
    "subtitle":  "Los archivos detectados fueron clasificados. FileMaster sigue monitoreando tu carpeta en segundo plano.",
    "speed":     "4.2s",
    "precision": "94%",
}

SUMMARY_STATS = [
    {"label": "Detectados",    "value": "35", "icon": "file",      "accent": "primary"},
    {"label": "Organizados",   "value": "28", "icon": "check",     "accent": "success"},
    {"label": "Renombrados",   "value": "28", "icon": "spark",     "accent": "primary"},
    {"label": "Sin clasificar","value": "4",  "icon": "warning",   "accent": "warning"},
    {"label": "Duplicados",    "value": "3",  "icon": "duplicate", "accent": "danger"},
]

SUMMARY_FOLDERS = [
    ("Inteligencia Artificial", "Downloads/IA/",    "12 archivos"),
    ("Redes de Computadoras",   "Downloads/Redes/", "8 archivos"),
    ("Base de Datos",           "Downloads/BD/",    "5 archivos"),
    ("Sistemas Operativos",     "Downloads/SO/",    "3 archivos"),
]

SUMMARY_UNIDENTIFIED = [
    "imagen_escaneada.pdf",
    "documento_vacio.docx",
    "notas_sin_texto.txt",
    "captura_pantalla.pdf",
]

MANUAL_PENDING = "4 de 4"
MANUAL_FILES = [
    ("imagen_escaneada.pdf",   "1.2 MB - PDF"),
    ("documento_vacio.docx",   "92 KB - DOCX"),
    ("notas_sin_texto.txt",    "2 KB - TXT"),
    ("captura_pantalla.pdf",   "1.4 MB - PDF"),
]

MANUAL_TARGETS = [
    ("Inteligencia Artificial", "Downloads/Inteligencia Artificial/"),
    ("Redes de Computadoras",   "Downloads/Redes de Computadoras/"),
    ("Base de Datos",           "Downloads/Base de Datos/"),
    ("Sistemas Operativos",     "Downloads/Sistemas Operativos/"),
]

DUPLICATE_TOP_BANNER = {
    "title":      "Se detectaron archivos duplicados en tu carpeta",
    "subtitle":   "La IA identifico copias mediante hashing MD5/SHA-256. El archivo marcado como 'Original' es el mas reciente o completo. Tu decides que eliminar.",
    "duplicates": "3",
    "groups":     "7",
}

DUPLICATE_GROUPS = [
    {
        "title": "Grupo 1 - 3 archivos",
        "mode":  "Contenido identico (MD5)",
        "files": [
            {
                "name":   "IA_Reporte_2026-03-26.pdf",
                "meta":   "2.8 MB · Modificado: 23 mar 2026 · Downloads/Inteligencia Artificial/",
                "state":  "Original",
                "detail": "",
            },
            {
                "name":   "reporte_final_entrega.pdf",
                "meta":   "2.8 MB · Modificado: 21 mar 2026 · Downloads/",
                "state":  "Duplicado",
                "detail": "Mismo hash MD5",
            },
            {
                "name":   "reporte_final_v2_copia.pdf",
                "meta":   "2.8 MB · Modificado: 23 mar 2026 · Downloads/",
                "state":  "Duplicado",
                "detail": "Mismo hash MD5",
            },
        ],
    },
    {
        "title": "Grupo 2 - 2 archivos",
        "mode":  "Contenido muy similar (Levenshtein)",
        "files": [
            {
                "name":   "Redes_Practica3_2026-03-26.docx",
                "meta":   "1.8 MB · Modificado: 23 mar 2026 · Downloads/Redes de Computadoras/",
                "state":  "Original",
                "detail": "",
            },
            {
                "name":   "SKDJH-KEFHE.docx",
                "meta":   "1.8 MB · Modificado: 21 mar 2026 · Downloads/",
                "state":  "Duplicado",
                "detail": "Similar 97%",
            },
        ],
    },
]


# ── Tipografía: Poppins ───────────────────────────────────────────────────────
@dataclass(frozen=True)
class FontSet:
    hero:       ctk.CTkFont
    title:      ctk.CTkFont
    subtitle:   ctk.CTkFont
    section:    ctk.CTkFont
    body:       ctk.CTkFont
    body_bold:  ctk.CTkFont
    small:      ctk.CTkFont
    tiny:       ctk.CTkFont
    badge:      ctk.CTkFont
    stat:       ctk.CTkFont
    nav:        ctk.CTkFont
    titlebar:   ctk.CTkFont


def setup_appearance() -> None:
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")


def build_fonts() -> FontSet:
    # Poppins como fuente principal — asegúrate de tener Poppins instalada en Windows
    # o cárgala desde assets/ con tkinter font si es necesario.
    family = "Poppins"
    return FontSet(
        hero      = ctk.CTkFont(family=family, size=36, weight="bold"),
        title     = ctk.CTkFont(family=family, size=18, weight="bold"),
        subtitle  = ctk.CTkFont(family=family, size=12, weight="normal"),
        section   = ctk.CTkFont(family=family, size=9,  weight="bold"),
        body      = ctk.CTkFont(family=family, size=13, weight="normal"),
        body_bold = ctk.CTkFont(family=family, size=13, weight="bold"),
        small     = ctk.CTkFont(family=family, size=11, weight="normal"),
        tiny      = ctk.CTkFont(family=family, size=9,  weight="normal"),
        badge     = ctk.CTkFont(family=family, size=10, weight="bold"),
        stat      = ctk.CTkFont(family=family, size=22, weight="bold"),
        nav       = ctk.CTkFont(family=family, size=11, weight="normal"),
        titlebar  = ctk.CTkFont(family=family, size=10, weight="normal"),
    )


def color_for_category(category: str) -> dict[str, str]:
    return CATEGORY_STYLES.get(
        category,
        {"bg": COLORS["card_alt"], "text": COLORS["text_secondary"], "border": COLORS["border"]},
    )