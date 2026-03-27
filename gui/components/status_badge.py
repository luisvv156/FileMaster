"""Badge verde de agente activo."""

from __future__ import annotations

from tkinter import Canvas

import customtkinter as ctk

from gui.theme import COLORS


class StatusBadge(ctk.CTkFrame):
    def __init__(self, master, fonts, text: str = "Agente activo - monitoreando"):
        super().__init__(
            master,
            fg_color=COLORS["success_bg"],
            border_width=1,
            border_color=COLORS["success"],
            corner_radius=999,
        )
        self._pulse = 0

        self.dot_canvas = Canvas(self, width=10, height=10, bg=COLORS["success_bg"], highlightthickness=0, bd=0)
        self.dot_canvas.pack(side="left", padx=(12, 6), pady=6)
        self.dot = self.dot_canvas.create_oval(2, 2, 8, 8, fill=COLORS["success"], outline="")

        label = ctk.CTkLabel(self, text=text, text_color=COLORS["success"], font=fonts.badge)
        label.pack(side="left", padx=(0, 14), pady=6)
        self.after(120, self._animate)

    def _animate(self) -> None:
        self._pulse = (self._pulse + 1) % 16
        radius = 2.4 + abs(8 - self._pulse) * 0.08
        center = 5
        self.dot_canvas.coords(self.dot, center - radius, center - radius, center + radius, center + radius)
        self.after(120, self._animate)
