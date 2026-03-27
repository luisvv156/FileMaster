"""Pantalla de grupos detectados por la IA."""

from __future__ import annotations

import customtkinter as ctk

from gui.components.common import AppIcon, PillBadge, primary_button, secondary_button
from gui.components.keyword_tag import KeywordTag
from gui.theme import COLORS


class GroupsScreen(ctk.CTkFrame):
    def __init__(self, master, fonts, controller, app):
        super().__init__(master, fg_color=COLORS["shell_bg"])
        self.fonts = fonts
        self.controller = controller
        self.app = app
        self.entry_vars: dict[str, ctk.StringVar] = {}

    def refresh(self) -> None:
        for child in self.winfo_children():
            child.destroy()
        self.entry_vars = {}

        snapshot = self.controller.snapshot()
        groups = snapshot.get("pending_groups", [])
        total_files = sum(len(group["file_names"]) for group in groups)

        self.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(header, text="Grupos detectados por la IA", text_color=COLORS["text"], font=self.fonts.title).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            header,
            text="Revisa y confirma los nombres antes de organizar - puedes editarlos si lo deseas",
            text_color=COLORS["text_secondary"],
            font=self.fonts.small,
        ).grid(row=1, column=0, sticky="w", pady=(2, 0))

        right = ctk.CTkFrame(header, fg_color="transparent")
        right.grid(row=0, column=1, rowspan=2, sticky="e")
        for idx, (label, value) in enumerate((("Documentos", str(total_files)), ("Grupos", str(len(groups))), ("Precision", "DBSCAN"))):
            block = ctk.CTkFrame(right, fg_color=COLORS["card_alt"], corner_radius=9, border_width=1, border_color=COLORS["border_soft"])
            block.grid(row=0, column=idx, padx=(0, 14 if idx < 2 else 0))
            ctk.CTkLabel(block, text=label, text_color=COLORS["text_muted"], font=self.fonts.tiny).pack(padx=12, pady=(8, 2))
            ctk.CTkLabel(block, text=value, text_color=COLORS["primary_light"], font=self.fonts.body_bold).pack(padx=12, pady=(0, 8))

        banner = ctk.CTkFrame(self, fg_color=COLORS["info_bg"], corner_radius=9, border_width=1, border_color=COLORS["border"])
        banner.grid(row=1, column=0, sticky="ew", pady=(14, 14))
        icon_wrap = ctk.CTkFrame(banner, width=28, height=28, fg_color=COLORS["card_alt"], corner_radius=7)
        icon_wrap.pack(side="left", padx=12, pady=12)
        icon_wrap.pack_propagate(False)
        AppIcon(icon_wrap, "bot", size=14, color=COLORS["primary_light"], bg=COLORS["card_alt"]).place(relx=0.5, rely=0.5, anchor="center")
        text = ctk.CTkFrame(banner, fg_color="transparent")
        text.pack(side="left", fill="x", expand=True, pady=10)
        ctk.CTkLabel(text, text=f"Analisis completado - se encontraron {len(groups)} grupos tematicos", text_color=COLORS["text"], font=self.fonts.body_bold).pack(anchor="w")
        ctk.CTkLabel(
            text,
            text="No se movera nada todavia. Puedes modificar los nombres sugeridos antes de confirmar.",
            text_color=COLORS["text_secondary"],
            font=self.fonts.tiny,
        ).pack(anchor="w")

        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.grid(row=2, column=0, sticky="nsew")
        columns = max(1, min(4, len(groups)))
        for idx in range(columns):
            grid.grid_columnconfigure(idx, weight=1, uniform="groups")

        if not groups:
            empty = ctk.CTkFrame(grid, fg_color=COLORS["card_alt"], corner_radius=10, border_width=1, border_color=COLORS["border"])
            empty.grid(row=0, column=0, sticky="ew")
            ctk.CTkLabel(empty, text="No hay grupos pendientes", text_color=COLORS["text"], font=self.fonts.title).pack(padx=18, pady=(18, 6))
            ctk.CTkLabel(
                empty,
                text="Vuelve a la configuracion y analiza una carpeta con documentos.",
                text_color=COLORS["text_secondary"],
                font=self.fonts.small,
            ).pack(padx=18, pady=(0, 18))
        else:
            for idx, group in enumerate(groups):
                row = idx // columns
                column = idx % columns
                card = ctk.CTkFrame(
                    grid,
                    height=340,
                    fg_color=COLORS["card_alt"],
                    corner_radius=12,
                    border_width=1,
                    border_color=COLORS["border"],
                )
                card.grid(row=row, column=column, sticky="nsew", padx=(0 if column == 0 else 10, 0), pady=(0, 10))
                card.pack_propagate(False)

                top = ctk.CTkFrame(card, fg_color="transparent")
                top.pack(fill="x", padx=12, pady=(12, 8))
                ctk.CTkLabel(top, text=group["group_id"].upper(), text_color=COLORS["text_muted"], font=self.fonts.section).pack(side="left")
                PillBadge(top, self.fonts, text=f"{len(group['file_names'])} archivos", fg_color=COLORS["primary_deep"], text_color=COLORS["primary_light"], border_color=COLORS["border"], padx=8).pack(side="right")

                ctk.CTkLabel(card, text="PALABRAS CLAVE DETECTADAS", text_color=COLORS["text_muted"], font=self.fonts.section).pack(anchor="w", padx=12)
                chips = ctk.CTkFrame(card, fg_color="transparent")
                chips.pack(fill="x", padx=12, pady=(8, 12))
                for tag_idx, keyword in enumerate(group["keywords"]):
                    KeywordTag(chips, self.fonts, keyword).grid(row=tag_idx // 2, column=tag_idx % 2, sticky="w", padx=(0, 6), pady=(0, 6))

                ctk.CTkLabel(card, text="MUESTRA DE ARCHIVOS", text_color=COLORS["text_muted"], font=self.fonts.section).pack(anchor="w", padx=12)
                names_box = ctk.CTkFrame(card, fg_color=COLORS["card_bg"], corner_radius=9, border_width=1, border_color=COLORS["border_soft"])
                names_box.pack(fill="x", padx=12, pady=(8, 10))
                for file_name in group["file_names"][:4]:
                    ctk.CTkLabel(names_box, text=file_name, text_color=COLORS["text_secondary"], font=self.fonts.tiny).pack(anchor="w", padx=10, pady=(8, 0))
                ctk.CTkLabel(names_box, text="", font=self.fonts.tiny).pack(anchor="w", padx=10, pady=(0, 8))

                spacer = ctk.CTkFrame(card, fg_color="transparent")
                spacer.pack(fill="both", expand=True)

                ctk.CTkLabel(card, text="NOMBRE DE CARPETA", text_color=COLORS["text_muted"], font=self.fonts.section).pack(anchor="w", padx=12, pady=(0, 6))
                variable = ctk.StringVar(value=group["suggested_name"])
                self.entry_vars[group["group_id"]] = variable
                entry = ctk.CTkEntry(
                    card,
                    textvariable=variable,
                    height=34,
                    corner_radius=7,
                    fg_color=COLORS["field_bg"],
                    border_color=COLORS["border"],
                    text_color=COLORS["text"],
                    font=self.fonts.body_bold,
                )
                entry.pack(fill="x", padx=12, pady=(0, 12))

        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=3, column=0, sticky="e", pady=(14, 0))
        secondary_button(footer, self.fonts, "<- Regresar", width=110, command=lambda: self.app.show_screen("config")).pack(side="left", padx=(0, 10))
        primary_button(footer, self.fonts, "Confirmar y organizar ->", width=210, command=self._confirm).pack(side="left")

    def _confirm(self) -> None:
        mapping = {group_id: variable.get().strip() for group_id, variable in self.entry_vars.items()}
        self.controller.confirm_groups(mapping)
        self.app.show_screen("summary")
