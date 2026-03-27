"""Panel principal."""

from __future__ import annotations

import customtkinter as ctk

from config.settings import DEFAULT_DUPLICATES_FOLDER_NAME
from gui.components.common import AppIcon, primary_button, secondary_button
from gui.components.file_card import FileCard
from gui.components.stat_card import StatCard
from gui.components.status_badge import StatusBadge
from gui.theme import COLORS


class MainPanelScreen(ctk.CTkFrame):
    def __init__(self, master, fonts, controller, app):
        super().__init__(master, fg_color=COLORS["shell_bg"])
        self.fonts = fonts
        self.controller = controller
        self.app = app

    def refresh(self) -> None:
        for child in self.winfo_children():
            child.destroy()

        snapshot = self.controller.snapshot()
        config = snapshot.get("config", {})
        stats = snapshot.get("stats", {})
        recent_files = snapshot.get("recent_files", [])
        agent = snapshot.get("agent", {})
        pending_groups = snapshot.get("pending_groups", [])
        watch_folder = config.get("watch_folder", "Sin configurar")
        status_message = snapshot.get("status_message", "")

        self.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(header, text="Panel principal", text_color=COLORS["text"], font=self.fonts.title).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(header, text="Estado del agente y configuracion activa", text_color=COLORS["text_secondary"], font=self.fonts.small).grid(row=1, column=0, sticky="w", pady=(2, 0))
        StatusBadge(header, self.fonts, text="Agente activo - monitoreando" if agent.get("active") and not agent.get("paused") else "Agente en pausa").grid(row=0, column=1, rowspan=2, sticky="e")

        if status_message:
            ctk.CTkLabel(self, text=status_message, text_color=COLORS["text_muted"], font=self.fonts.tiny).grid(row=1, column=0, sticky="w", pady=(6, 0))

        row_index = 2
        if pending_groups:
            pending_banner = ctk.CTkFrame(
                self,
                fg_color=COLORS["info_bg"],
                corner_radius=9,
                border_width=1,
                border_color=COLORS["border"],
            )
            pending_banner.grid(row=row_index, column=0, sticky="ew", pady=(10, 12))
            icon_box = ctk.CTkFrame(pending_banner, width=28, height=28, fg_color=COLORS["card_alt"], corner_radius=7)
            icon_box.pack(side="left", padx=12, pady=12)
            icon_box.pack_propagate(False)
            AppIcon(icon_box, "bot", size=14, color=COLORS["primary_light"], bg=COLORS["card_alt"]).place(relx=0.5, rely=0.5, anchor="center")
            text = ctk.CTkFrame(pending_banner, fg_color="transparent")
            text.pack(side="left", fill="x", expand=True, pady=10)
            ctk.CTkLabel(
                text,
                text=f"Hay {len(pending_groups)} grupos pendientes de confirmacion",
                text_color=COLORS["text"],
                font=self.fonts.body_bold,
            ).pack(anchor="w")
            ctk.CTkLabel(
                text,
                text="Antes de organizar automaticamente, confirma los nombres sugeridos por la IA.",
                text_color=COLORS["text_secondary"],
                font=self.fonts.tiny,
            ).pack(anchor="w")
            primary_button(
                pending_banner,
                self.fonts,
                "Revisar grupos ->",
                width=150,
                command=lambda: self.app.show_screen("groups"),
            ).pack(side="right", padx=12)
            row_index += 1

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.grid(row=row_index, column=0, sticky="ew", pady=(0, 12))
        top.grid_columnconfigure(0, weight=60, uniform="top")
        top.grid_columnconfigure(1, weight=40, uniform="top")

        left = ctk.CTkFrame(top, fg_color=COLORS["card_alt"], corner_radius=12, border_width=1, border_color=COLORS["border"])
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        ctk.CTkLabel(left, text="CONFIGURACION ACTIVA", text_color=COLORS["text_muted"], font=self.fonts.section).pack(anchor="w", padx=16, pady=(14, 10))
        rows = [
            ("folder", "Carpeta monitoreada", watch_folder),
            ("spark", "Renombrado IA", "Activado" if config.get("auto_rename") else "Desactivado"),
            ("bot", "Modo de operacion", f"Observador {'en pausa' if agent.get('paused') else 'en segundo plano'} - desde {agent.get('started_at') or '--:--:--'}"),
            ("duplicate", "Carpeta de duplicados", f"{watch_folder}/{DEFAULT_DUPLICATES_FOLDER_NAME}" if watch_folder != "Sin configurar" else "Sin configurar"),
        ]
        for icon_name, label, value in rows:
            row = ctk.CTkFrame(left, fg_color=COLORS["card_bg"], corner_radius=9, border_width=1, border_color=COLORS["border_soft"])
            row.pack(fill="x", padx=12, pady=(0, 8))
            box = ctk.CTkFrame(row, width=22, height=22, fg_color=COLORS["field_bg"], corner_radius=6)
            box.pack(side="left", padx=12, pady=12)
            box.pack_propagate(False)
            icon_color = COLORS["warning"] if icon_name == "folder" else COLORS["success"] if icon_name in {"spark", "bot"} else COLORS["primary"]
            AppIcon(box, icon_name, size=12, color=icon_color, bg=COLORS["field_bg"]).place(relx=0.5, rely=0.5, anchor="center")
            text = ctk.CTkFrame(row, fg_color="transparent")
            text.pack(side="left", fill="x", expand=True, pady=10)
            ctk.CTkLabel(text, text=label, text_color=COLORS["text_muted"], font=self.fonts.tiny).pack(anchor="w")
            ctk.CTkLabel(text, text=value, text_color=COLORS["text"], font=self.fonts.small).pack(anchor="w")
            if icon_name == "folder":
                secondary_button(row, self.fonts, "Editar", width=76, command=lambda: self.app.show_screen("config")).pack(side="right", padx=12)

        right = ctk.CTkFrame(top, fg_color=COLORS["card_alt"], corner_radius=12, border_width=1, border_color=COLORS["border"])
        right.grid(row=0, column=1, sticky="nsew")
        ctk.CTkLabel(right, text="ESTADO DEL AGENTE", text_color=COLORS["text_muted"], font=self.fonts.section).pack(anchor="w", padx=16, pady=(14, 10))
        agent_box = ctk.CTkFrame(right, fg_color=COLORS["card_bg"], corner_radius=10, border_width=1, border_color=COLORS["border_soft"])
        agent_box.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        circle = ctk.CTkFrame(agent_box, width=56, height=56, fg_color=COLORS["success_bg"], corner_radius=999, border_width=1, border_color=COLORS["success"])
        circle.pack(pady=(18, 12))
        circle.pack_propagate(False)
        AppIcon(circle, "bot", size=18, color=COLORS["success"], bg=COLORS["success_bg"]).place(relx=0.5, rely=0.5, anchor="center")
        ctk.CTkLabel(
            agent_box,
            text="Monitoreando activamente" if agent.get("active") and not agent.get("paused") else "Agente en pausa",
            text_color=COLORS["success"] if agent.get("active") and not agent.get("paused") else COLORS["warning"],
            font=self.fonts.body_bold,
        ).pack()
        ctk.CTkLabel(
            agent_box,
            text=f"Ultima ejecucion: {agent.get('last_run') or 'sin ejecuciones'}",
            text_color=COLORS["text_muted"],
            font=self.fonts.tiny,
        ).pack(pady=(4, 14))
        actions = ctk.CTkFrame(agent_box, fg_color="transparent")
        actions.pack(fill="x", padx=12, pady=(0, 12))
        secondary_button(actions, self.fonts, "Reanudar agente" if agent.get("paused") else "Pausar agente", width=132, command=self.controller.toggle_agent).pack(side="left")
        primary_button(actions, self.fonts, "Organizar ahora ->", width=148, command=self._organize_now).pack(side="right")

        stats_row = ctk.CTkFrame(self, fg_color="transparent")
        stats_row.grid(row=row_index + 1, column=0, sticky="ew", pady=(0, 12))
        cards = [
            {"label": "Total organizados", "value": str(stats.get("total_organized", 0)), "icon": "file", "accent": "primary"},
            {"label": "Precision promedio", "value": f"{stats.get('average_confidence', 0)}%", "icon": "check", "accent": "success"},
            {"label": "Carpetas creadas", "value": str(stats.get("folders_created", 0)), "icon": "folder", "accent": "warning"},
            {"label": "Duplicados detectados", "value": str(stats.get("duplicates_detected", 0)), "icon": "warning", "accent": "warning"},
        ]
        for idx in range(len(cards)):
            stats_row.grid_columnconfigure(idx, weight=1, uniform="stats")
        for idx, item in enumerate(cards):
            StatCard(stats_row, self.fonts, item["label"], item["value"], item["icon"], item["accent"]).grid(row=0, column=idx, sticky="ew", padx=(0 if idx == 0 else 8, 0))

        panel = ctk.CTkFrame(self, fg_color=COLORS["card_alt"], corner_radius=12, border_width=1, border_color=COLORS["border"])
        panel.grid(row=row_index + 2, column=0, sticky="nsew")
        panel_header = ctk.CTkFrame(panel, fg_color="transparent")
        panel_header.pack(fill="x", padx=16, pady=(14, 8))
        ctk.CTkLabel(panel_header, text="ULTIMOS ARCHIVOS ORGANIZADOS", text_color=COLORS["text_muted"], font=self.fonts.section).pack(side="left")
        ctk.CTkLabel(panel_header, text=f"{len(recent_files)} recientes", text_color=COLORS["text_muted"], font=self.fonts.tiny).pack(side="right")
        list_wrap = ctk.CTkFrame(panel, fg_color="transparent")
        list_wrap.pack(fill="x", padx=12, pady=(0, 12))
        if recent_files:
            for idx, item in enumerate(recent_files):
                FileCard(list_wrap, self.fonts, item).pack(fill="x", pady=(0, 8))
        else:
            ctk.CTkLabel(list_wrap, text="Todavia no hay archivos organizados. Ejecuta un analisis o deja que el watcher detecte nuevos documentos.", text_color=COLORS["text_secondary"], font=self.fonts.small).pack(anchor="w", padx=14, pady=(0, 12))

    def _organize_now(self) -> None:
        self.controller.organize_now()
        if self.controller.snapshot().get("pending_groups"):
            self.app.show_screen("groups")
            return
        self.app.show_screen("summary")
