"""Fila de archivo reciente."""

from __future__ import annotations

import customtkinter as ctk

from gui.components.common import AppIcon, PillBadge
from gui.theme import COLORS, color_for_category


class FileCard(ctk.CTkFrame):
    def __init__(self, master, fonts, file_data: dict[str, str]):
        super().__init__(
            master,
            fg_color=COLORS["card_bg"],
            corner_radius=10,
            border_width=1,
            border_color=COLORS["border_soft"],
        )
        self.grid_columnconfigure(1, weight=1)

        icon_box = ctk.CTkFrame(self, width=24, height=24, fg_color=COLORS["field_bg"], corner_radius=7)
        icon_box.grid(row=0, column=0, rowspan=2, sticky="nw", padx=(14, 12), pady=12)
        icon_box.pack_propagate(False)
        AppIcon(icon_box, "file", size=12, color=COLORS["text_secondary"], bg=COLORS["field_bg"]).place(
            relx=0.5, rely=0.5, anchor="center"
        )

        ctk.CTkLabel(self, text=file_data["name"], text_color=COLORS["text"], font=fonts.body_bold).grid(
            row=0, column=1, sticky="w", pady=(12, 2)
        )
        ctk.CTkLabel(self, text=file_data["original"], text_color=COLORS["text_muted"], font=fonts.tiny).grid(
            row=1, column=1, sticky="w", pady=(0, 12)
        )

        style = color_for_category(file_data["category"])
        meta = ctk.CTkFrame(self, fg_color="transparent")
        meta.grid(row=0, column=2, rowspan=2, sticky="e", padx=(12, 12))
        badge = PillBadge(
            meta,
            fonts,
            text=file_data["category"],
            fg_color=style["bg"],
            text_color=style["text"],
            border_color=style["border"],
            padx=8,
        )
        badge.pack(anchor="e", pady=(10, 4))
        ctk.CTkLabel(meta, text=file_data["time"], text_color=COLORS["text_muted"], font=fonts.tiny).pack(anchor="e")
