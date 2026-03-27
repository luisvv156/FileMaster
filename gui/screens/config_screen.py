"""Pantalla de configuracion inicial."""

from __future__ import annotations

from pathlib import Path

import customtkinter as ctk

from gui.components.common import (
    AppIcon,
    PillBadge,
    default_folder_shortcuts,
    primary_button,
    secondary_button,
    show_app_dialog,
    show_folder_browser,
)
from gui.components.toggle_switch import ToggleSwitch
from gui.theme import COLORS


class ConfigScreen(ctk.CTkFrame):
    def __init__(self, master, fonts, controller, app):
        super().__init__(master, fg_color=COLORS["shell_bg"])
        self.fonts = fonts
        self.controller = controller
        self.app = app
        self.folder_var = ctk.StringVar()
        self.auto_toggle: ToggleSwitch | None = None
        self.duplicate_toggle: ToggleSwitch | None = None

    def refresh(self) -> None:
        for child in self.winfo_children():
            child.destroy()

        snapshot = self.controller.snapshot()
        config = snapshot.get("config", {})
        status_message = snapshot.get("status_message", "")
        self.folder_var.set(config.get("watch_folder", ""))

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)
        ctk.CTkLabel(self, text="Configuracion inicial", text_color=COLORS["text"], font=self.fonts.title).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            self,
            text="Indica la carpeta que deseas organizar y ajusta las opciones segun tus preferencias",
            text_color=COLORS["text_secondary"],
            font=self.fonts.small,
        ).grid(row=1, column=0, sticky="w", pady=(2, 14))
        ctk.CTkFrame(self, height=1, fg_color=COLORS["border_soft"]).grid(row=2, column=0, sticky="ew", pady=(0, 12))

        outer = ctk.CTkFrame(self, fg_color="transparent")
        outer.grid(row=3, column=0, sticky="nsew")
        outer.grid_columnconfigure(0, weight=62, uniform="config")
        outer.grid_columnconfigure(1, weight=38, uniform="config")
        outer.grid_rowconfigure(1, weight=1)

        if status_message:
            status = ctk.CTkFrame(
                outer,
                fg_color=COLORS["info_bg"],
                corner_radius=9,
                border_width=1,
                border_color=COLORS["border"],
            )
            status.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12))
            icon_box = ctk.CTkFrame(status, width=28, height=28, fg_color=COLORS["card_alt"], corner_radius=7)
            icon_box.pack(side="left", padx=12, pady=10)
            icon_box.pack_propagate(False)
            AppIcon(icon_box, "spark", size=13, color=COLORS["primary_light"], bg=COLORS["card_alt"]).place(
                relx=0.5, rely=0.5, anchor="center"
            )
            ctk.CTkLabel(status, text=status_message, text_color=COLORS["text"], font=self.fonts.small).pack(
                side="left", pady=10
            )

        left = ctk.CTkFrame(outer, fg_color="transparent")
        left.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        right = ctk.CTkFrame(outer, fg_color="transparent")
        right.grid(row=1, column=1, sticky="nsew")

        folder = ctk.CTkFrame(left, fg_color=COLORS["card_alt"], corner_radius=12, border_width=1, border_color=COLORS["border"])
        folder.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(folder, text="CARPETA A MONITOREAR", text_color=COLORS["text_muted"], font=self.fonts.section).pack(anchor="w", padx=16, pady=(14, 8))
        ctk.CTkLabel(folder, text="Selecciona la carpeta", text_color=COLORS["text"], font=self.fonts.body_bold).pack(anchor="w", padx=16)

        field_row = ctk.CTkFrame(folder, fg_color="transparent")
        field_row.pack(fill="x", padx=16, pady=(10, 8))
        field_row.grid_columnconfigure(0, weight=1)
        entry = ctk.CTkEntry(
            field_row,
            textvariable=self.folder_var,
            height=34,
            corner_radius=7,
            fg_color=COLORS["field_bg"],
            border_color=COLORS["border"],
            text_color=COLORS["text"],
            font=self.fonts.body,
        )
        entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        secondary_button(field_row, self.fonts, "Abrir selector", width=138, command=self._browse_folder).grid(row=0, column=1)
        ctk.CTkLabel(
            folder,
            text="El agente monitoreara esta carpeta y organizara su contenido automaticamente. El selector se abrira dentro de FileMaster.",
            text_color=COLORS["text_muted"],
            font=self.fonts.tiny,
        ).pack(anchor="w", padx=16, pady=(0, 12))

        shortcuts = ctk.CTkFrame(folder, fg_color="transparent")
        shortcuts.pack(fill="x", padx=16, pady=(0, 10))
        ctk.CTkLabel(shortcuts, text="ACCESOS RAPIDOS", text_color=COLORS["text_muted"], font=self.fonts.section).pack(
            anchor="w", pady=(0, 8)
        )
        shortcut_grid = ctk.CTkFrame(shortcuts, fg_color="transparent")
        shortcut_grid.pack(fill="x")
        for idx, (label, path) in enumerate(default_folder_shortcuts()[:6]):
            button = ctk.CTkButton(
                shortcut_grid,
                text=label,
                height=30,
                corner_radius=8,
                fg_color=COLORS["card_bg"],
                hover_color=COLORS["hover_bg"],
                border_width=1,
                border_color=COLORS["border_soft"],
                text_color=COLORS["text_secondary"],
                font=self.fonts.small,
                command=lambda target=str(path): self.folder_var.set(target),
            )
            button.grid(row=idx // 3, column=idx % 3, sticky="ew", padx=(0, 8), pady=(0, 8))
            shortcut_grid.grid_columnconfigure(idx % 3, weight=1)

        current = ctk.CTkFrame(folder, fg_color=COLORS["card_bg"], corner_radius=10, border_width=1, border_color=COLORS["border_soft"])
        current.pack(fill="x", padx=16, pady=(0, 14))
        top_row = ctk.CTkFrame(current, fg_color="transparent")
        top_row.pack(fill="x", padx=12, pady=(12, 8))
        ctk.CTkLabel(top_row, text="CARPETA ACTUAL", text_color=COLORS["text_muted"], font=self.fonts.section).pack(side="left")
        PillBadge(
            top_row,
            self.fonts,
            text="Lista para monitoreo" if self.folder_var.get().strip() else "Sin seleccionar",
            fg_color=COLORS["success_bg"] if self.folder_var.get().strip() else COLORS["card_alt"],
            text_color=COLORS["success"] if self.folder_var.get().strip() else COLORS["text_secondary"],
            border_color=COLORS["success"] if self.folder_var.get().strip() else COLORS["border"],
            padx=8,
        ).pack(side="right")
        ctk.CTkLabel(
            current,
            text=self.folder_var.get().strip() or "Todavia no has elegido ninguna carpeta.",
            text_color=COLORS["text"],
            font=self.fonts.small,
            justify="left",
            wraplength=470,
        ).pack(anchor="w", padx=12, pady=(0, 12))

        options = ctk.CTkFrame(left, fg_color=COLORS["card_alt"], corner_radius=12, border_width=1, border_color=COLORS["border"])
        options.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(options, text="OPCIONES DE ORGANIZACION", text_color=COLORS["text_muted"], font=self.fonts.section).pack(anchor="w", padx=16, pady=(14, 10))

        self.auto_toggle = ToggleSwitch(
            options,
            self.fonts,
            "Renombrado automatico de archivos",
            "La IA sugerira nombres descriptivos para cada archivo organizado",
            enabled=bool(config.get("auto_rename", True)),
        )
        self.auto_toggle.pack(fill="x", padx=12, pady=(0, 10))

        preview = ctk.CTkFrame(options, fg_color=COLORS["card_bg"], corner_radius=10, border_width=1, border_color=COLORS["border_soft"])
        preview.pack(fill="x", padx=12, pady=(0, 10))
        ctk.CTkLabel(preview, text="VISTA PREVIA DEL RENOMBRADO", text_color=COLORS["text_muted"], font=self.fonts.section).pack(anchor="w", padx=12, pady=(12, 8))
        for original, renamed in (
            ("SKDJH-KEFHE.pdf", "ia_reporte_2026-03-26.pdf"),
            ("trabajo_final_v3.docx", "base_de_datos_indices_2026-03-26.docx"),
        ):
            row = ctk.CTkFrame(preview, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=(0, 6))
            ctk.CTkLabel(row, text=original, text_color=COLORS["danger"], font=self.fonts.tiny).pack(side="left")
            ctk.CTkLabel(row, text=renamed, text_color=COLORS["success"], font=self.fonts.tiny).pack(side="right")

        self.duplicate_toggle = ToggleSwitch(
            options,
            self.fonts,
            "Carpeta de duplicados",
            "Los archivos duplicados se moveran a una carpeta especial para revision manual",
            enabled=bool(config.get("detect_duplicates", True)),
        )
        self.duplicate_toggle.pack(fill="x", padx=12, pady=(0, 12))

        actions = ctk.CTkFrame(left, fg_color="transparent")
        actions.pack(fill="x", pady=(0, 0))
        secondary_button(actions, self.fonts, "Cancelar", width=120, command=lambda: self.app.show_screen("welcome")).pack(side="left")
        primary_button(actions, self.fonts, "Analizar carpeta y continuar ->", width=260, command=self._save_and_analyze).pack(side="right")

        guide = ctk.CTkFrame(right, fg_color=COLORS["card_alt"], corner_radius=12, border_width=1, border_color=COLORS["border"])
        guide.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(guide, text="ASI FUNCIONARA FILEMASTER", text_color=COLORS["text_muted"], font=self.fonts.section).pack(
            anchor="w", padx=16, pady=(14, 10)
        )
        tips = [
            ("1", "Analiza", "Lee el contenido de tus documentos para detectar grupos tematicos."),
            ("2", "Propone", "Sugiere carpetas y nombres antes de mover tus archivos."),
            ("3", "Monitorea", "Se queda observando la carpeta y organiza nuevos archivos automaticamente."),
        ]
        for step, title, text in tips:
            row = ctk.CTkFrame(guide, fg_color=COLORS["card_bg"], corner_radius=10, border_width=1, border_color=COLORS["border_soft"])
            row.pack(fill="x", padx=12, pady=(0, 8))
            bubble = ctk.CTkLabel(
                row,
                text=step,
                width=20,
                height=20,
                fg_color=COLORS["primary"],
                text_color=COLORS["text"],
                corner_radius=999,
                font=self.fonts.badge,
            )
            bubble.pack(side="left", padx=12, pady=14)
            text_wrap = ctk.CTkFrame(row, fg_color="transparent")
            text_wrap.pack(side="left", fill="x", expand=True, pady=10)
            ctk.CTkLabel(text_wrap, text=title, text_color=COLORS["text"], font=self.fonts.body_bold).pack(anchor="w")
            ctk.CTkLabel(
                text_wrap,
                text=text,
                text_color=COLORS["text_secondary"],
                font=self.fonts.tiny,
                justify="left",
                wraplength=220,
            ).pack(anchor="w")

        formats = ctk.CTkFrame(right, fg_color=COLORS["card_alt"], corner_radius=12, border_width=1, border_color=COLORS["border"])
        formats.pack(fill="both", expand=True)
        ctk.CTkLabel(formats, text="SOPORTE Y RESULTADO", text_color=COLORS["text_muted"], font=self.fonts.section).pack(
            anchor="w", padx=16, pady=(14, 10)
        )
        badges = ctk.CTkFrame(formats, fg_color="transparent")
        badges.pack(fill="x", padx=12, pady=(0, 12))
        for idx, tag in enumerate(("TXT", "DOCX", "PPTX", "PDF", "OCR", "Duplicados")):
            PillBadge(
                badges,
                self.fonts,
                text=tag,
                fg_color=COLORS["card_bg"],
                text_color=COLORS["text_secondary"],
                border_color=COLORS["border_soft"],
                padx=8,
            ).grid(row=idx // 3, column=idx % 3, padx=(0, 8), pady=(0, 8), sticky="w")

        preview_result = ctk.CTkFrame(formats, fg_color=COLORS["card_bg"], corner_radius=10, border_width=1, border_color=COLORS["border_soft"])
        preview_result.pack(fill="x", padx=12, pady=(0, 12))
        ctk.CTkLabel(preview_result, text="DESPUES DEL ANALISIS", text_color=COLORS["text_muted"], font=self.fonts.section).pack(
            anchor="w", padx=12, pady=(12, 8)
        )
        results = [
            ("folder", "Carpetas tematicas generadas"),
            ("spark", "Renombres descriptivos sugeridos"),
            ("duplicate", "Duplicados enviados a revision"),
        ]
        for icon_name, text in results:
            row = ctk.CTkFrame(preview_result, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=(0, 8))
            icon_box = ctk.CTkFrame(row, width=18, height=18, fg_color=COLORS["field_bg"], corner_radius=5)
            icon_box.pack(side="left", padx=(0, 8))
            icon_box.pack_propagate(False)
            AppIcon(icon_box, icon_name, size=11, color=COLORS["primary_light"], bg=COLORS["field_bg"]).place(
                relx=0.5, rely=0.5, anchor="center"
            )
            ctk.CTkLabel(row, text=text, text_color=COLORS["text_secondary"], font=self.fonts.small).pack(side="left")

    def _browse_folder(self) -> None:
        selected = show_folder_browser(self, self.fonts, self.folder_var.get().strip())
        if selected:
            self.folder_var.set(selected)

    def _save_and_analyze(self) -> None:
        folder = self.folder_var.get().strip()
        if not folder:
            show_app_dialog(self, self.fonts, "Carpeta requerida", "Selecciona una carpeta antes de continuar.", variant="danger")
            return

        try:
            Path(folder).mkdir(parents=True, exist_ok=True)
        except OSError as error:
            show_app_dialog(
                self,
                self.fonts,
                "No fue posible preparar la carpeta",
                str(error),
                variant="danger",
            )
            return

        self.controller.update_config(
            folder,
            self.auto_toggle.get_value() if self.auto_toggle else True,
            self.duplicate_toggle.get_value() if self.duplicate_toggle else True,
        )
        proposals = self.controller.analyze_initial()
        if proposals:
            self.app.show_screen("groups")
            return

        self.controller.start_agent()
        show_app_dialog(
            self,
            self.fonts,
            "Monitoreo iniciado",
            "No se encontraron archivos iniciales para agrupar. El agente comenzara a monitorear la carpeta desde ahora.",
            variant="success",
        )
        self.app.show_screen("main")
