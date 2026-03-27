"""Pantalla de clasificacion manual."""

from __future__ import annotations

import customtkinter as ctk

from gui.components.common import AppIcon, PillBadge, primary_button, secondary_button
from gui.theme import COLORS


class ManualClassifyScreen(ctk.CTkFrame):
    def __init__(self, master, fonts, controller, app):
        super().__init__(master, fg_color=COLORS["shell_bg"])
        self.fonts = fonts
        self.controller = controller
        self.app = app
        self.selected_path = ""
        self.selected_category = ctk.StringVar(value="")
        self.new_folder_var = ctk.StringVar(value="")

    def refresh(self) -> None:
        for child in self.winfo_children():
            child.destroy()

        snapshot = self.controller.snapshot()
        unclassified = snapshot.get("unclassified", [])
        categories = self.controller.manual_categories()
        if not self.selected_category.get() and categories:
            self.selected_category.set(categories[0])
        if unclassified and not self.selected_path:
            self.selected_path = unclassified[0]["path"]
        if self.selected_path and all(item["path"] != self.selected_path for item in unclassified):
            self.selected_path = unclassified[0]["path"] if unclassified else ""

        self.grid_columnconfigure(0, weight=34, uniform="manual")
        self.grid_columnconfigure(1, weight=66, uniform="manual")

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, columnspan=2, sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(header, text="Clasificacion manual", text_color=COLORS["text"], font=self.fonts.title).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            header,
            text="Indica donde debe ir cada archivo que la IA no pudo clasificar automaticamente",
            text_color=COLORS["text_secondary"],
            font=self.fonts.small,
        ).grid(row=1, column=0, sticky="w", pady=(2, 0))
        PillBadge(header, self.fonts, text=f"Archivos pendientes - {len(unclassified)}", fg_color=COLORS["card_alt"], text_color=COLORS["text_secondary"], border_color=COLORS["border"], padx=8).grid(row=0, column=1, rowspan=2, sticky="e")

        left = ctk.CTkFrame(self, fg_color=COLORS["card_alt"], corner_radius=12, border_width=1, border_color=COLORS["border"])
        left.grid(row=1, column=0, sticky="nsew", padx=(0, 10), pady=(14, 0))
        ctk.CTkLabel(left, text="ARCHIVOS SIN CLASIFICAR", text_color=COLORS["text_muted"], font=self.fonts.section).pack(anchor="w", padx=16, pady=(14, 10))

        if not unclassified:
            ctk.CTkLabel(left, text="No hay archivos pendientes.", text_color=COLORS["text_secondary"], font=self.fonts.small).pack(anchor="w", padx=14, pady=(0, 12))
        else:
            for item in unclassified:
                selected = item["path"] == self.selected_path
                row = ctk.CTkButton(
                    left,
                    text="",
                    fg_color=COLORS["primary_deep"] if selected else COLORS["card_bg"],
                    hover_color=COLORS["hover_bg"],
                    height=62,
                    corner_radius=9,
                    border_width=1,
                    border_color=COLORS["primary"] if selected else COLORS["border_soft"],
                    command=lambda path=item["path"]: self._select_file(path),
                )
                row.pack(fill="x", padx=12, pady=(0, 8))
                row.grid_columnconfigure(1, weight=1)
                icon_box = ctk.CTkFrame(row, width=20, height=20, fg_color=COLORS["field_bg"], corner_radius=6)
                icon_box.grid(row=0, column=0, rowspan=2, padx=12, pady=10)
                icon_box.pack_propagate(False)
                AppIcon(icon_box, "file", size=11, color=COLORS["text"], bg=COLORS["field_bg"]).place(relx=0.5, rely=0.5, anchor="center")
                ctk.CTkLabel(row, text=item["name"], text_color=COLORS["text"], font=self.fonts.small).grid(row=0, column=1, sticky="w", pady=(10, 0))
                ctk.CTkLabel(row, text=item.get("meta", item["reason"]), text_color=COLORS["text_muted"], font=self.fonts.tiny).grid(row=1, column=1, sticky="w", pady=(0, 9))

        right = ctk.CTkFrame(self, fg_color=COLORS["card_alt"], corner_radius=12, border_width=1, border_color=COLORS["border"])
        right.grid(row=1, column=1, sticky="nsew", pady=(14, 0))

        selected_file = next((item for item in unclassified if item["path"] == self.selected_path), None)
        if selected_file is None:
            ctk.CTkLabel(right, text="No hay archivos para clasificar.", text_color=COLORS["text"], font=self.fonts.title).pack(anchor="w", padx=14, pady=(14, 0))
            return

        ctk.CTkLabel(right, text="ARCHIVO SELECCIONADO", text_color=COLORS["text_muted"], font=self.fonts.section).pack(anchor="w", padx=16, pady=(14, 10))

        file_card = ctk.CTkFrame(right, fg_color=COLORS["card_bg"], corner_radius=10, border_width=1, border_color=COLORS["border_soft"])
        file_card.pack(fill="x", padx=16)
        icon_box = ctk.CTkFrame(file_card, width=24, height=24, fg_color=COLORS["field_bg"], corner_radius=7)
        icon_box.pack(side="left", padx=12, pady=12)
        icon_box.pack_propagate(False)
        AppIcon(icon_box, "file", size=12, color=COLORS["text"], bg=COLORS["field_bg"]).place(relx=0.5, rely=0.5, anchor="center")
        info = ctk.CTkFrame(file_card, fg_color="transparent")
        info.pack(side="left", fill="x", expand=True, pady=10)
        ctk.CTkLabel(info, text=selected_file["name"], text_color=COLORS["text"], font=self.fonts.body_bold).pack(anchor="w")
        ctk.CTkLabel(info, text=selected_file["path"], text_color=COLORS["text_muted"], font=self.fonts.tiny).pack(anchor="w")

        reason = ctk.CTkFrame(right, fg_color="#2d2318", corner_radius=8, border_width=1, border_color="#7c4a2a")
        reason.pack(fill="x", padx=16, pady=(12, 12))
        ctk.CTkLabel(reason, text="POR QUE NO PUDO CLASIFICARSE?", text_color=COLORS["warning"], font=self.fonts.section).pack(anchor="w", padx=12, pady=(10, 6))
        ctk.CTkLabel(
            reason,
            text=selected_file["reason"],
            text_color=COLORS["text_secondary"],
            font=self.fonts.tiny,
            wraplength=500,
            justify="left",
        ).pack(anchor="w", padx=12, pady=(0, 10))

        ctk.CTkLabel(right, text="SELECCIONA LA CARPETA DESTINO", text_color=COLORS["text_muted"], font=self.fonts.section).pack(anchor="w", padx=16, pady=(0, 10))
        for name in categories:
            selected = name == self.selected_category.get()
            row = ctk.CTkButton(
                right,
                text="",
                fg_color=COLORS["primary_deep"] if selected else COLORS["card_bg"],
                hover_color=COLORS["hover_bg"],
                height=56,
                corner_radius=9,
                border_width=1,
                border_color=COLORS["primary"] if selected else COLORS["border_soft"],
                command=lambda category=name: self._select_category(category),
            )
            row.pack(fill="x", padx=16, pady=(0, 8))
            row.grid_columnconfigure(1, weight=1)
            icon_box = ctk.CTkFrame(row, width=20, height=20, fg_color=COLORS["warning_bg"], corner_radius=6)
            icon_box.grid(row=0, column=0, rowspan=2, padx=12, pady=10)
            icon_box.pack_propagate(False)
            AppIcon(icon_box, "folder", size=11, color=COLORS["warning"], bg=COLORS["warning_bg"]).place(relx=0.5, rely=0.5, anchor="center")
            ctk.CTkLabel(row, text=name, text_color=COLORS["text"], font=self.fonts.small).grid(row=0, column=1, sticky="w", pady=(10, 0))
            ctk.CTkLabel(row, text=f"{snapshot.get('config', {}).get('watch_folder', '')}/{name}", text_color=COLORS["text_muted"], font=self.fonts.tiny).grid(row=1, column=1, sticky="w", pady=(0, 10))
            if selected:
                ctk.CTkLabel(row, text="v", text_color=COLORS["primary_light"], font=self.fonts.body_bold).grid(row=0, column=2, rowspan=2, padx=14)

        create = ctk.CTkFrame(right, fg_color=COLORS["card_bg"], corner_radius=9, border_width=1, border_color=COLORS["border_soft"])
        create.pack(fill="x", padx=16, pady=(4, 14))
        entry = ctk.CTkEntry(
            create,
            textvariable=self.new_folder_var,
            height=34,
            corner_radius=0,
            fg_color="transparent",
            border_width=0,
            text_color=COLORS["text"],
            placeholder_text="+ Crear nueva carpeta...",
            placeholder_text_color=COLORS["text_muted"],
            font=self.fonts.small,
        )
        entry.pack(side="left", fill="x", expand=True, padx=10)
        ctk.CTkLabel(create, text="Crear", text_color=COLORS["primary_light"], font=self.fonts.small).pack(side="right", padx=12)

        footer = ctk.CTkFrame(right, fg_color="transparent")
        footer.pack(fill="x", padx=16, pady=(0, 12))
        secondary_button(footer, self.fonts, "Omitir archivo", width=110, command=lambda: self.app.show_screen("summary")).pack(side="left")
        primary_button(footer, self.fonts, "Mover a carpeta seleccionada ->", width=260, command=self._move_selected).pack(side="right")

    def _select_file(self, path: str) -> None:
        self.selected_path = path
        self.refresh()

    def _select_category(self, category: str) -> None:
        self.selected_category.set(category)
        self.refresh()

    def _move_selected(self) -> None:
        self.controller.manual_classify(self.selected_path, self.selected_category.get(), self.new_folder_var.get())
        self.new_folder_var.set("")
        self.app.show_screen("summary")
