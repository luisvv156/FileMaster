"""Switch con titulo y subtitulo para la pantalla de configuracion."""

from __future__ import annotations

import customtkinter as ctk

from gui.theme import COLORS


class ToggleSwitch(ctk.CTkFrame):
    def __init__(self, master, fonts, title: str, subtitle: str, enabled: bool = False):
        super().__init__(
            master,
            fg_color=COLORS["card_bg"],
            corner_radius=10,
            border_width=1,
            border_color=COLORS["border_soft"],
        )
        self.fonts = fonts
        self.enabled = enabled
        self.grid_columnconfigure(0, weight=1)

        text_wrap = ctk.CTkFrame(self, fg_color="transparent")
        text_wrap.grid(row=0, column=0, sticky="w", padx=14, pady=12)
        ctk.CTkLabel(text_wrap, text=title, text_color=COLORS["text"], font=self.fonts.body_bold).pack(anchor="w")
        ctk.CTkLabel(
            text_wrap,
            text=subtitle,
            text_color=COLORS["text_muted"],
            font=self.fonts.tiny,
            wraplength=360,
            justify="left",
        ).pack(anchor="w", pady=(2, 0))

        self.track = ctk.CTkButton(
            self,
            text="",
            width=36,
            height=20,
            corner_radius=999,
            fg_color=COLORS["border"],
            hover_color=COLORS["border"],
            command=self.toggle,
        )
        self.track.grid(row=0, column=1, sticky="e", padx=14)

        self.thumb = ctk.CTkFrame(self.track, width=14, height=14, corner_radius=999, fg_color="#ffffff")
        self._render()

    def toggle(self) -> None:
        self.enabled = not self.enabled
        self._render()

    def get_value(self) -> bool:
        return self.enabled

    def set_value(self, value: bool) -> None:
        self.enabled = value
        self._render()

    def _render(self) -> None:
        active_color = COLORS["primary"] if self.enabled else COLORS["border"]
        self.track.configure(fg_color=active_color, hover_color=active_color)
        self.thumb.place(x=19 if self.enabled else 3, y=3)
