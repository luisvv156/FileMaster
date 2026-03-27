"""Tarjeta compacta de estadistica."""

from __future__ import annotations

import customtkinter as ctk

from gui.components.common import AppIcon
from gui.theme import COLORS


class StatCard(ctk.CTkFrame):
    def __init__(self, master, fonts, label: str, value: str, icon: str, accent: str):
        super().__init__(
            master,
            fg_color=COLORS["card_alt"],
            corner_radius=12,
            border_width=1,
            border_color=COLORS["border_soft"],
        )
        accent_color = COLORS[accent]

        highlight = ctk.CTkFrame(self, height=3, fg_color=accent_color, corner_radius=999)
        highlight.pack(fill="x", padx=14, pady=(14, 0))

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=14, pady=(12, 4))
        ctk.CTkLabel(self, text=label, text_color=COLORS["text_muted"], font=fonts.tiny).pack(anchor="w", padx=14)

        value_row = ctk.CTkFrame(self, fg_color="transparent")
        value_row.pack(fill="x", padx=14, pady=(6, 14))

        ctk.CTkLabel(
            value_row,
            text=value,
            text_color=accent_color if accent in {"success", "danger", "warning"} else COLORS["primary"],
            font=fonts.stat,
        ).pack(side="left")

        icon_box = ctk.CTkFrame(top, width=24, height=24, fg_color=COLORS["field_bg"], corner_radius=7)
        icon_box.pack(side="right")
        icon_box.pack_propagate(False)
        AppIcon(icon_box, icon, size=12, color=accent_color, bg=COLORS["field_bg"]).place(relx=0.5, rely=0.5, anchor="center")
