"""Tema, layout y datos demo para la interfaz de FileMaster."""

from __future__ import annotations

from dataclasses import dataclass

import customtkinter as ctk


WINDOW_WIDTH = 1024
WINDOW_HEIGHT = 640
TITLEBAR_HEIGHT = 30
SIDEBAR_WIDTH = 138
SHELL_PADDING = 20

COLORS = {
    "window_bg": "#0e0f14",
    "chrome_bg": "#141623",
    "shell_bg": "#171926",
    "sidebar_bg": "#131522",
    "card_bg": "#1a1c24",
    "card_alt": "#1f2130",
    "card_soft": "#26283b",
    "field_bg": "#252736",
    "hover_bg": "#23263a",
    "border": "#2e3147",
    "border_soft": "#24273a",
    "primary": "#4f83ff",
    "primary_soft": "#7cb3ff",
    "primary_light": "#8bc4ff",
    "primary_deep": "#1a2f4e",
    "success": "#22c55e",
    "success_bg": "#16361f",
    "warning": "#f59e0b",
    "warning_bg": "#2d2318",
    "danger": "#ef4444",
    "danger_bg": "#2d1f1f",
    "info": "#3b82f6",
    "info_bg": "#1c2849",
    "text": "#f1f5f9",
    "text_secondary": "#8892b0",
    "text_muted": "#4a5568",
    "brand": "#b8c8ff",
    "logo_bg": "#f4c04a",
}

CATEGORY_STYLES = {
    "Inteligencia Artificial": {"bg": "#1a2f4e", "text": "#4f83ff", "border": "#2a4f7e"},
    "Redes de Computadoras": {"bg": "#1e3a2e", "text": "#22c55e", "border": "#2a5a3e"},
    "Base de Datos": {"bg": "#2d2318", "text": "#f59e0b", "border": "#4a3520"},
    "Sistemas Operativos": {"bg": "#2d1f2f", "text": "#c084fc", "border": "#4a2f5a"},
}

SIDEBAR_ITEMS = [
    ("Inicio", "main", "home"),
    ("Configuracion", "config", "folder"),
    ("Historial", "summary", "clock"),
    ("Duplicados", "duplicates", "duplicate"),
]

BOTTOM_SIDEBAR_ITEMS = [("Ajustes", "manual", "gear")]

SCREEN_NAV_STATE = {
    "welcome": None,
    "config": "config",
    "groups": "config",
    "main": "main",
    "summary": "summary",
    "manual": "manual",
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
    {"name": "IA_Reporte_2026-03-26.pdf", "category": "Inteligencia Artificial"},
    {"name": "Redes_Practica3.docx", "category": "Redes de Computadoras"},
    {"name": "BD_Investigacion.pdf", "category": "Base de Datos"},
]

CONFIG_TOGGLES = [
    {
        "title": "Renombrado automatico de archivos",
        "subtitle": "La IA sugerira nombres descriptivos para cada archivo organizado",
        "enabled": True,
    },
    {
        "title": "Carpeta de duplicados",
        "subtitle": "Los archivos duplicados se moveran a una carpeta especial para revision manual",
        "enabled": True,
    },
]

CONFIG_PREVIEW_RENAME = [
    ("SKDJH-KEFHE.pdf", "IA_Reporte_2026-03-26.pdf"),
    ("trabajo_final_v3.docx", "BD_Investigacion_2026-03-20.docx"),
]

GROUPS_SUMMARY = [
    ("Documentos", "35"),
    ("Grupos", "4"),
    ("Precision", "94%"),
]

GROUP_CARDS = [
    {
        "title": "GRUPO 1",
        "count": "12 archivos",
        "keywords": ["algoritmo", "red neuronal", "clasificacion", "aprendizaje", "modelo"],
        "folder": "Inteligencia Artificial",
    },
    {
        "title": "GRUPO 2",
        "count": "8 archivos",
        "keywords": ["protocolo", "router", "TCP/IP", "switch", "firewall"],
        "folder": "Redes de Computadoras",
    },
    {
        "title": "GRUPO 3",
        "count": "6 archivos",
        "keywords": ["SQL", "joins", "normalizacion", "consulta", "indices"],
        "folder": "Base de Datos",
    },
    {
        "title": "GRUPO 4",
        "count": "5 archivos",
        "keywords": ["procesos", "kernel", "memoria", "scheduler", "hilo"],
        "folder": "Sistemas Operativos",
    },
]

MAIN_CONFIG_ROWS = [
    ("folder", "Carpeta monitoreada", APP_FOLDER),
    ("spark", "Activado", "Renombres descriptivos por IA"),
    ("bot", "Modo de operacion", "Observador en segundo plano - desde 09:14 AM"),
    ("duplicate", "Carpeta de duplicados", "Activada - Downloads/_Duplicados/"),
]

MAIN_STATS = [
    {"label": "Total organizados", "value": "284", "icon": "file", "accent": "primary"},
    {"label": "Precision promedio", "value": "97%", "icon": "check", "accent": "success"},
    {"label": "Carpetas creadas", "value": "8", "icon": "folder", "accent": "warning"},
    {"label": "Duplicados detectados", "value": "6", "icon": "warning", "accent": "warning"},
]

RECENT_FILES = [
    {
        "name": "IA_Reporte_2026-03-26.pdf",
        "original": "Origen: SKDJH-KEFHE.pdf",
        "category": "Inteligencia Artificial",
        "time": "Hace 12 min",
    },
    {
        "name": "Redes_Practica3_2026-03-26.docx",
        "original": "Origen: SKDJH-KEFHE.docx",
        "category": "Redes de Computadoras",
        "time": "Hace 38 min",
    },
]

SUMMARY_BANNER = {
    "title": "Organizacion completada - el agente continua activo",
    "subtitle": "Los archivos detectados fueron clasificados. FileMaster sigue monitoreando tu carpeta en segundo plano.",
    "speed": "4.2s",
    "precision": "94%",
}

SUMMARY_STATS = [
    {"label": "Detectados", "value": "35", "icon": "file", "accent": "primary"},
    {"label": "Organizados", "value": "28", "icon": "check", "accent": "success"},
    {"label": "Renombrados", "value": "28", "icon": "spark", "accent": "primary"},
    {"label": "Sin clasificar", "value": "4", "icon": "warning", "accent": "warning"},
    {"label": "Duplicados", "value": "3", "icon": "duplicate", "accent": "danger"},
]

SUMMARY_FOLDERS = [
    ("Inteligencia Artificial", "Downloads/IA/", "12 archivos"),
    ("Redes de Computadoras", "Downloads/Redes/", "8 archivos"),
    ("Base de Datos", "Downloads/BD/", "5 archivos"),
    ("Sistemas Operativos", "Downloads/SO/", "3 archivos"),
]

SUMMARY_UNIDENTIFIED = [
    "imagen_escaneada.pdf",
    "documento_vacio.docx",
    "notas_sin_texto.txt",
    "captura_pantalla.pdf",
]

MANUAL_PENDING = "4 de 4"
MANUAL_FILES = [
    ("imagen_escaneada.pdf", "1.2 MB - PDF"),
    ("documento_vacio.docx", "92 KB - DOCX"),
    ("notas_sin_texto.txt", "2 KB - TXT"),
    ("captura_pantalla.pdf", "1.4 MB - PDF"),
]

MANUAL_TARGETS = [
    ("Inteligencia Artificial", "Downloads/Inteligencia Artificial/"),
    ("Redes de Computadoras", "Downloads/Redes de Computadoras/"),
    ("Base de Datos", "Downloads/Base de Datos/"),
    ("Sistemas Operativos", "Downloads/Sistemas Operativos/"),
]

DUPLICATE_TOP_BANNER = {
    "title": "Se detectaron archivos duplicados en tu carpeta",
    "subtitle": "La IA identifico copias mediante hashing MD5/SHA-256. El archivo marcado como 'Original' es el mas reciente o completo. Tu decides que eliminar.",
    "duplicates": "3",
    "groups": "7",
}

DUPLICATE_GROUPS = [
    {
        "title": "Grupo 1 - 3 archivos",
        "mode": "Contenido identico (MD5)",
        "files": [
            {
                "name": "IA_Reporte_2026-03-26.pdf",
                "meta": "2.8 MB · Modificado: 23 mar 2026 · Downloads/Inteligencia Artificial/",
                "state": "Original",
                "detail": "",
            },
            {
                "name": "reporte_final_entrega.pdf",
                "meta": "2.8 MB · Modificado: 21 mar 2026 · Downloads/",
                "state": "Duplicado",
                "detail": "Mismo hash MD5",
            },
            {
                "name": "reporte_final_v2_copia.pdf",
                "meta": "2.8 MB · Modificado: 23 mar 2026 · Downloads/",
                "state": "Duplicado",
                "detail": "Mismo hash MD5",
            },
        ],
    },
    {
        "title": "Grupo 2 - 2 archivos",
        "mode": "Contenido muy similar (Levenshtein)",
        "files": [
            {
                "name": "Redes_Practica3_2026-03-26.docx",
                "meta": "1.8 MB · Modificado: 23 mar 2026 · Downloads/Redes de Computadoras/",
                "state": "Original",
                "detail": "",
            },
            {
                "name": "SKDJH-KEFHE.docx",
                "meta": "1.8 MB · Modificado: 21 mar 2026 · Downloads/",
                "state": "Duplicado",
                "detail": "Similar 97%",
            },
        ],
    },
]


@dataclass(frozen=True)
class FontSet:
    hero: ctk.CTkFont
    title: ctk.CTkFont
    subtitle: ctk.CTkFont
    section: ctk.CTkFont
    body: ctk.CTkFont
    body_bold: ctk.CTkFont
    small: ctk.CTkFont
    tiny: ctk.CTkFont
    badge: ctk.CTkFont
    stat: ctk.CTkFont
    nav: ctk.CTkFont
    titlebar: ctk.CTkFont


def setup_appearance() -> None:
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")


def build_fonts() -> FontSet:
    family = "Inter"
    return FontSet(
        hero=ctk.CTkFont(family=family, size=40, weight="bold"),
        title=ctk.CTkFont(family=family, size=20, weight="bold"),
        subtitle=ctk.CTkFont(family=family, size=13, weight="normal"),
        section=ctk.CTkFont(family=family, size=10, weight="bold"),
        body=ctk.CTkFont(family=family, size=14, weight="normal"),
        body_bold=ctk.CTkFont(family=family, size=14, weight="bold"),
        small=ctk.CTkFont(family=family, size=12, weight="normal"),
        tiny=ctk.CTkFont(family=family, size=10, weight="normal"),
        badge=ctk.CTkFont(family=family, size=11, weight="bold"),
        stat=ctk.CTkFont(family=family, size=24, weight="bold"),
        nav=ctk.CTkFont(family=family, size=12, weight="normal"),
        titlebar=ctk.CTkFont(family=family, size=11, weight="normal"),
    )


def color_for_category(category: str) -> dict[str, str]:
    return CATEGORY_STYLES.get(
        category,
        {"bg": COLORS["card_alt"], "text": COLORS["text_secondary"], "border": COLORS["border"]},
    )
