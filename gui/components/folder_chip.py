"""Chip de carpeta con contador."""

from __future__ import annotations

import customtkinter as ctk

from gui.theme import COLORS


class FolderChip(ctk.CTkFrame):
    def __init__(self, master, fonts, name: str, count: int):
        super().__init__(master, fg_color=COLORS["card_alt"], corner_radius=16, border_width=1, border_color=COLORS["border_soft"])
        label = ctk.CTkLabel(self, text=name, font=fonts.small, text_color=COLORS["text"])
        label.pack(side="left", padx=(12, 8), pady=8)
        badge = ctk.CTkLabel(
            self,
            text=str(count),
            font=fonts.badge,
            text_color=COLORS["primary"],
            fg_color=COLORS["window_bg"],
            corner_radius=10,
            padx=8,
            pady=2,
        )
        badge.pack(side="left", padx=(0, 10), pady=8)
