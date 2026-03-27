"""Pantalla de resumen de organizacion."""

from __future__ import annotations

import customtkinter as ctk

from gui.components.common import AppIcon, PillBadge, primary_button, secondary_button
from gui.components.stat_card import StatCard
from gui.components.status_badge import StatusBadge
from gui.theme import COLORS


class SummaryScreen(ctk.CTkFrame):
    def __init__(self, master, fonts, controller, app):
        super().__init__(master, fg_color=COLORS["shell_bg"])
        self.fonts = fonts
        self.controller = controller
        self.app = app

    def refresh(self) -> None:
        for child in self.winfo_children():
            child.destroy()

        snapshot = self.controller.snapshot()
        summary = snapshot.get("last_summary", {})
        unclassified = snapshot.get("unclassified", [])
        folders = summary.get("folders", [])
        status_message = snapshot.get("status_message", "")

        self.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(header, text="Resumen de organizacion", text_color=COLORS["text"], font=self.fonts.title).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            header,
            text=f"{snapshot.get('config', {}).get('watch_folder', 'Sin configurar')} - {snapshot.get('agent', {}).get('last_run', '--:--:--')}",
            text_color=COLORS["text_secondary"],
            font=self.fonts.small,
        ).grid(row=1, column=0, sticky="w", pady=(2, 0))
        StatusBadge(header, self.fonts).grid(row=0, column=1, rowspan=2, sticky="e")

        banner = ctk.CTkFrame(self, fg_color=COLORS["success_bg"], corner_radius=12, border_width=1, border_color=COLORS["success"])
        banner.grid(row=1, column=0, sticky="ew", pady=(14, 12))
        box = ctk.CTkFrame(banner, width=28, height=28, fg_color=COLORS["card_alt"], corner_radius=7)
        box.pack(side="left", padx=12, pady=12)
        box.pack_propagate(False)
        AppIcon(box, "check", size=14, color=COLORS["success"], bg=COLORS["card_alt"]).place(relx=0.5, rely=0.5, anchor="center")
        text = ctk.CTkFrame(banner, fg_color="transparent")
        text.pack(side="left", fill="x", expand=True, pady=10)
        ctk.CTkLabel(text, text="Organizacion completada - el agente continua activo", text_color=COLORS["text"], font=self.fonts.body_bold).pack(anchor="w")
        ctk.CTkLabel(text, text=status_message or "Los archivos detectados fueron clasificados y el agente sigue monitoreando.", text_color=COLORS["text_secondary"], font=self.fonts.tiny).pack(anchor="w")
        right = ctk.CTkFrame(banner, fg_color="transparent")
        right.pack(side="right", padx=14)
        ctk.CTkLabel(right, text=f"{summary.get('duration_seconds', 0)}s", text_color=COLORS["success"], font=self.fonts.title).pack(anchor="e")
        ctk.CTkLabel(right, text=f"{summary.get('precision', 0)}%", text_color=COLORS["primary_light"], font=self.fonts.title).pack(anchor="e")

        stats_row = ctk.CTkFrame(self, fg_color="transparent")
        stats_row.grid(row=2, column=0, sticky="ew", pady=(0, 12))
        cards = [
            {"label": "Detectados", "value": str(summary.get("detected", 0)), "icon": "file", "accent": "primary"},
            {"label": "Organizados", "value": str(summary.get("organized", 0)), "icon": "check", "accent": "success"},
            {"label": "Renombrados", "value": str(summary.get("renamed", 0)), "icon": "spark", "accent": "primary"},
            {"label": "Sin clasificar", "value": str(summary.get("unclassified", 0)), "icon": "warning", "accent": "warning"},
            {"label": "Duplicados", "value": str(summary.get("duplicates", 0)), "icon": "duplicate", "accent": "danger"},
        ]
        for idx in range(len(cards)):
            stats_row.grid_columnconfigure(idx, weight=1, uniform="sum")
        for idx, item in enumerate(cards):
            StatCard(stats_row, self.fonts, item["label"], item["value"], item["icon"], item["accent"]).grid(row=0, column=idx, sticky="ew", padx=(0 if idx == 0 else 8, 0))

        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.grid(row=3, column=0, sticky="nsew")
        bottom.grid_columnconfigure(0, weight=52, uniform="bottom")
        bottom.grid_columnconfigure(1, weight=48, uniform="bottom")

        left = ctk.CTkFrame(bottom, fg_color=COLORS["card_alt"], corner_radius=12, border_width=1, border_color=COLORS["border"])
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        header_left = ctk.CTkFrame(left, fg_color="transparent")
        header_left.pack(fill="x", padx=16, pady=(14, 10))
        ctk.CTkLabel(header_left, text="CARPETAS CREADAS POR LA IA", text_color=COLORS["text_muted"], font=self.fonts.section).pack(side="left")
        ctk.CTkLabel(header_left, text=f"{len(folders)} resultados", text_color=COLORS["text_muted"], font=self.fonts.tiny).pack(side="right")
        if folders:
            for item in folders:
                row = ctk.CTkFrame(left, fg_color=COLORS["card_bg"], corner_radius=9, border_width=1, border_color=COLORS["border_soft"])
                row.pack(fill="x", padx=12, pady=(0, 8))
                icon_box = ctk.CTkFrame(row, width=20, height=20, fg_color=COLORS["warning_bg"], corner_radius=6)
                icon_box.pack(side="left", padx=12, pady=12)
                icon_box.pack_propagate(False)
                AppIcon(icon_box, "folder", size=11, color=COLORS["warning"], bg=COLORS["warning_bg"]).place(relx=0.5, rely=0.5, anchor="center")
                text = ctk.CTkFrame(row, fg_color="transparent")
                text.pack(side="left", fill="x", expand=True, pady=10)
                ctk.CTkLabel(text, text=item["name"], text_color=COLORS["text"], font=self.fonts.body_bold).pack(anchor="w")
                ctk.CTkLabel(text, text=item["path"], text_color=COLORS["text_muted"], font=self.fonts.tiny).pack(anchor="w")
                PillBadge(row, self.fonts, text=f"{item['count']} archivos", fg_color=COLORS["primary_deep"], text_color=COLORS["primary_light"], border_color=COLORS["border"], padx=8).pack(side="right", padx=12)
        else:
            ctk.CTkLabel(left, text="Todavia no hay carpetas utilizadas en el ultimo ciclo.", text_color=COLORS["text_secondary"], font=self.fonts.small).pack(anchor="w", padx=14, pady=(0, 12))

        right = ctk.CTkFrame(bottom, fg_color=COLORS["card_alt"], corner_radius=12, border_width=1, border_color=COLORS["border"])
        right.grid(row=0, column=1, sticky="nsew")
        header_right = ctk.CTkFrame(right, fg_color="transparent")
        header_right.pack(fill="x", padx=16, pady=(14, 10))
        ctk.CTkLabel(header_right, text="ARCHIVOS NO IDENTIFICADOS", text_color=COLORS["text_muted"], font=self.fonts.section).pack(side="left")
        ctk.CTkLabel(header_right, text=f"{len(unclassified)} pendientes", text_color=COLORS["text_muted"], font=self.fonts.tiny).pack(side="right")

        if unclassified:
            banner = ctk.CTkFrame(right, fg_color=COLORS["warning_bg"], corner_radius=8, border_width=1, border_color=COLORS["warning"])
            banner.pack(fill="x", padx=10, pady=(0, 10))
            icon_box = ctk.CTkFrame(banner, width=18, height=18, fg_color=COLORS["card_alt"], corner_radius=5)
            icon_box.pack(side="left", padx=10, pady=10)
            icon_box.pack_propagate(False)
            AppIcon(icon_box, "warning", size=11, color=COLORS["warning"], bg=COLORS["card_alt"]).place(relx=0.5, rely=0.5, anchor="center")
            text = ctk.CTkFrame(banner, fg_color="transparent")
            text.pack(side="left", fill="x", expand=True, pady=8)
            ctk.CTkLabel(text, text=f"{len(unclassified)} archivos requieren clasificacion manual", text_color=COLORS["text"], font=self.fonts.body_bold).pack(anchor="w")
            ctk.CTkLabel(text, text="La IA no encontro suficiente contenido para clasificarlos", text_color=COLORS["text_secondary"], font=self.fonts.tiny).pack(anchor="w")
            for item in unclassified:
                row = ctk.CTkFrame(right, fg_color=COLORS["card_bg"], corner_radius=9, border_width=1, border_color=COLORS["border_soft"])
                row.pack(fill="x", padx=12, pady=(0, 8))
                icon_box = ctk.CTkFrame(row, width=18, height=18, fg_color=COLORS["field_bg"], corner_radius=5)
                icon_box.pack(side="left", padx=12, pady=10)
                icon_box.pack_propagate(False)
                AppIcon(icon_box, "file", size=11, color=COLORS["text_secondary"], bg=COLORS["field_bg"]).place(relx=0.5, rely=0.5, anchor="center")
                ctk.CTkLabel(row, text=item["name"], text_color=COLORS["text_secondary"], font=self.fonts.small).pack(side="left", pady=10)
        else:
            ctk.CTkLabel(right, text="No hay archivos pendientes de clasificacion manual.", text_color=COLORS["text_secondary"], font=self.fonts.small).pack(anchor="w", padx=14, pady=(0, 12))

        footer = ctk.CTkFrame(right, fg_color="transparent")
        footer.pack(fill="x", padx=12, pady=(16, 12))
        primary_button(footer, self.fonts, "Clasificar manualmente ->", width=210, command=lambda: self.app.show_screen("manual")).pack(side="left")
        secondary_button(footer, self.fonts, "Ver duplicados", width=120, command=lambda: self.app.show_screen("duplicates")).pack(side="right")
