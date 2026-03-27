"""Tag para palabras clave."""

from __future__ import annotations

import customtkinter as ctk

from gui.theme import COLORS


class KeywordTag(ctk.CTkLabel):
    def __init__(self, master, fonts, text: str):
        super().__init__(
            master,
            text=text,
            fg_color=COLORS["field_bg"],
            text_color=COLORS["text_secondary"],
            corner_radius=4,
            border_width=1,
            border_color=COLORS["border_soft"],
            padx=9,
            pady=4,
            font=fonts.tiny,
        )
