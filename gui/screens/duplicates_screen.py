"""Pantalla de papelera de duplicados."""

from __future__ import annotations

import customtkinter as ctk

from gui.components.common import AppIcon, PillBadge, ask_app_dialog, secondary_button
from gui.theme import COLORS


class DuplicatesScreen(ctk.CTkFrame):
    def __init__(self, master, fonts, controller, app):
        super().__init__(master, fg_color=COLORS["shell_bg"])
        self.fonts = fonts
        self.controller = controller
        self.app = app
        self.selection_vars: dict[str, ctk.BooleanVar] = {}

    def refresh(self) -> None:
        for child in self.winfo_children():
            child.destroy()
        self.selection_vars = {}

        snapshot = self.controller.snapshot()
        groups = snapshot.get("duplicate_groups", [])
        duplicates_count = sum(
            1 for group in groups for item in group.get("items", []) if item.get("state") == "Duplicado"
        )

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(header, text="Papelera de duplicados", text_color=COLORS["text"], font=self.fonts.title).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            header,
            text="Revisa los archivos duplicados detectados y decide cuales eliminar - la IA no elimina nada sin tu confirmacion",
            text_color=COLORS["text_secondary"],
            font=self.fonts.small,
        ).grid(row=1, column=0, sticky="w", pady=(2, 0))
        PillBadge(header, self.fonts, text=f"{len(groups)} grupos - {duplicates_count} duplicados", fg_color=COLORS["warning_bg"], text_color=COLORS["warning"], border_color=COLORS["warning"], padx=8).grid(row=0, column=1, rowspan=2, sticky="e")

        banner = ctk.CTkFrame(self, fg_color=COLORS["warning_bg"], corner_radius=12, border_width=1, border_color=COLORS["warning"])
        banner.grid(row=1, column=0, sticky="ew", pady=(14, 12))
        icon_box = ctk.CTkFrame(banner, width=28, height=28, fg_color=COLORS["card_alt"], corner_radius=7)
        icon_box.pack(side="left", padx=12, pady=12)
        icon_box.pack_propagate(False)
        AppIcon(icon_box, "warning", size=14, color=COLORS["warning"], bg=COLORS["card_alt"]).place(relx=0.5, rely=0.5, anchor="center")
        text = ctk.CTkFrame(banner, fg_color="transparent")
        text.pack(side="left", fill="x", expand=True, pady=10)
        ctk.CTkLabel(text, text="Se detectaron archivos duplicados en tu carpeta", text_color=COLORS["text"], font=self.fonts.body_bold).pack(anchor="w")
        ctk.CTkLabel(
            text,
            text="Puedes restaurarlos al directorio principal o eliminarlos manualmente. Ningun archivo se borra automaticamente.",
            text_color=COLORS["text_secondary"],
            font=self.fonts.tiny,
        ).pack(anchor="w")

        ctk.CTkLabel(self, text="GRUPOS DE ARCHIVOS DUPLICADOS", text_color=COLORS["text_muted"], font=self.fonts.section).grid(row=2, column=0, sticky="nw")
        scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            corner_radius=0,
            scrollbar_button_color=COLORS["border"],
            scrollbar_button_hover_color=COLORS["hover_bg"],
        )
        scroll.grid(row=3, column=0, sticky="nsew", pady=(18, 0))

        if not groups:
            ctk.CTkLabel(scroll, text="No hay duplicados pendientes.", text_color=COLORS["text_secondary"], font=self.fonts.small).pack(anchor="w", padx=10, pady=10)
        else:
            for group in groups:
                card = ctk.CTkFrame(scroll, fg_color=COLORS["card_alt"], corner_radius=12, border_width=1, border_color=COLORS["border"])
                card.pack(fill="x", pady=(0, 12))

                top = ctk.CTkFrame(card, fg_color=COLORS["card_bg"], corner_radius=10, border_width=1, border_color=COLORS["border_soft"])
                top.pack(fill="x", padx=12, pady=12)
                ctk.CTkLabel(top, text=group["title"], text_color=COLORS["text"], font=self.fonts.body_bold).pack(side="left", padx=12, pady=10)
                mode = group["mode"]
                is_similar = "Levenshtein" in mode
                PillBadge(
                    top,
                    self.fonts,
                    text=mode,
                    fg_color=COLORS["warning_bg"] if is_similar else COLORS["success_bg"],
                    text_color=COLORS["warning"] if is_similar else COLORS["success"],
                    border_color=COLORS["warning"] if is_similar else COLORS["success"],
                    padx=8,
                ).pack(side="left")
                ctk.CTkLabel(
                    top,
                    text=f"{len(group['items'])} archivos",
                    text_color=COLORS["text_muted"],
                    font=self.fonts.tiny,
                ).pack(side="right", padx=12)

                for item in group["items"]:
                    row = ctk.CTkFrame(card, fg_color=COLORS["card_bg"], corner_radius=9, border_width=1, border_color=COLORS["border_soft"])
                    row.pack(fill="x", padx=12, pady=(0, 8))
                    selected = bool(item.get("selected", False))
                    variable = ctk.BooleanVar(value=selected)
                    self.selection_vars[item["current_path"]] = variable
                    checkbox = ctk.CTkCheckBox(
                        row,
                        text="",
                        variable=variable,
                        onvalue=True,
                        offvalue=False,
                        checkbox_width=16,
                        checkbox_height=16,
                        border_width=1,
                        corner_radius=4,
                        fg_color=COLORS["danger"] if item["state"] == "Duplicado" else COLORS["success"],
                        hover_color=COLORS["danger"] if item["state"] == "Duplicado" else COLORS["success"],
                    )
                    checkbox.pack(side="left", padx=(10, 12), pady=12)
                    if item["state"] == "Original":
                        checkbox.configure(state="disabled")
                    text = ctk.CTkFrame(row, fg_color="transparent")
                    text.pack(side="left", fill="x", expand=True, pady=10)
                    ctk.CTkLabel(text, text=item["name"], text_color=COLORS["text"], font=self.fonts.small).pack(anchor="w")
                    ctk.CTkLabel(text, text=item["meta"], text_color=COLORS["text_muted"], font=self.fonts.tiny).pack(anchor="w")
                    PillBadge(
                        row,
                        self.fonts,
                        text=item["state"],
                        fg_color=COLORS["success_bg"] if item["state"] == "Original" else COLORS["danger_bg"],
                        text_color=COLORS["success"] if item["state"] == "Original" else COLORS["danger"],
                        border_color=COLORS["success"] if item["state"] == "Original" else COLORS["danger"],
                        padx=8,
                    ).pack(side="right", padx=(10, 12))
                    if item["detail"]:
                        PillBadge(
                            row,
                            self.fonts,
                            text=item["detail"],
                            fg_color=COLORS["card_bg"],
                            text_color=COLORS["text_muted"],
                            border_color=COLORS["border"],
                            padx=8,
                        ).pack(side="right")

        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=4, column=0, sticky="ew", pady=(12, 0))
        footer.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(footer, text=f"{len(self._selected_paths())} archivos seleccionados", text_color=COLORS["text_muted"], font=self.fonts.tiny).grid(row=0, column=0, sticky="w")
        right = ctk.CTkFrame(footer, fg_color="transparent")
        right.grid(row=0, column=1, sticky="e")
        secondary_button(right, self.fonts, "Restaurar seleccion", width=150, command=self._restore_selected).pack(side="left", padx=(0, 10))
        delete_button = ctk.CTkButton(
            right,
            text="Eliminar seleccionados",
            width=160,
            height=32,
            corner_radius=7,
            fg_color=COLORS["danger_bg"],
            hover_color=COLORS["danger"],
            border_width=1,
            border_color=COLORS["danger"],
            text_color=COLORS["danger"],
            font=self.fonts.body_bold,
            command=self._delete_selected,
        )
        delete_button.pack(side="left")

    def _selected_paths(self) -> list[str]:
        return [path for path, variable in self.selection_vars.items() if variable.get()]

    def _restore_selected(self) -> None:
        paths = self._selected_paths()
        if not paths:
            return
        self.controller.restore_duplicates(paths)
        self.refresh()

    def _delete_selected(self) -> None:
        paths = self._selected_paths()
        if not paths:
            return
        if not ask_app_dialog(
            self,
            self.fonts,
            "Eliminar duplicados",
            "¿Seguro que deseas eliminar los duplicados seleccionados?",
            variant="danger",
        ):
            return
        self.controller.delete_duplicates(paths)
        self.refresh()
