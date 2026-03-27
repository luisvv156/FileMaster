"""Sidebar principal de la aplicacion."""

from __future__ import annotations

import customtkinter as ctk

from gui.components.common import AppIcon
from gui.theme import BOTTOM_SIDEBAR_ITEMS, COLORS, SIDEBAR_ITEMS, SIDEBAR_WIDTH


class Sidebar(ctk.CTkFrame):
    def __init__(self, master, fonts, on_navigate, active_key: str = "main"):
        super().__init__(
            master,
            width=SIDEBAR_WIDTH,
            fg_color=COLORS["sidebar_bg"],
            corner_radius=0,
            border_width=1,
            border_color=COLORS["border_soft"],
        )
        self.fonts = fonts
        self.on_navigate = on_navigate
        self.active_key = active_key
        self.rows: dict[str, ctk.CTkFrame] = {}
        self.labels: dict[str, ctk.CTkLabel] = {}
        self.icons: dict[str, AppIcon] = {}
        self.accents: dict[str, ctk.CTkFrame] = {}

        self.grid_propagate(False)
        self.grid_rowconfigure(2, weight=1)
        self._build_brand()
        self._build_section(SIDEBAR_ITEMS, 1)
        self._build_footer_divider()
        self._build_section(BOTTOM_SIDEBAR_ITEMS, 3)

    def _build_brand(self) -> None:
        brand = ctk.CTkFrame(
            self,
            fg_color=COLORS["card_bg"],
            corner_radius=12,
            border_width=1,
            border_color=COLORS["border_soft"],
        )
        brand.grid(row=0, column=0, sticky="ew", padx=12, pady=(14, 18))

        row = ctk.CTkFrame(brand, fg_color="transparent")
        row.pack(fill="x", padx=10, pady=(10, 4))

        icon_box = ctk.CTkFrame(row, width=20, height=20, corner_radius=6, fg_color=COLORS["logo_bg"])
        icon_box.pack(side="left", padx=(0, 8))
        icon_box.pack_propagate(False)
        AppIcon(icon_box, "folder", size=12, color=COLORS["primary"], bg=COLORS["logo_bg"]).place(
            relx=0.5, rely=0.5, anchor="center"
        )

        text = ctk.CTkFrame(row, fg_color="transparent")
        text.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(text, text="FileMaster", text_color=COLORS["brand"], font=self.fonts.body_bold).pack(anchor="w")
        ctk.CTkLabel(text, text="Organizador inteligente", text_color=COLORS["text_muted"], font=self.fonts.tiny).pack(anchor="w")

        ctk.CTkLabel(
            brand,
            text="Monitoreo local y clasificacion automatica",
            text_color=COLORS["text_secondary"],
            font=self.fonts.tiny,
            wraplength=112,
            justify="left",
        ).pack(anchor="w", padx=10, pady=(0, 10))

    def _build_section(self, items: list[tuple[str, str, str]], row: int) -> None:
        wrapper = ctk.CTkFrame(self, fg_color="transparent")
        wrapper.grid(row=row, column=0, sticky="nsew", padx=10)
        for label, key, icon_name in items:
            item = ctk.CTkFrame(wrapper, fg_color="transparent", corner_radius=10, height=38)
            item.pack(fill="x", pady=(0, 6))
            item.pack_propagate(False)

            accent = ctk.CTkFrame(item, width=3, fg_color="transparent", corner_radius=3)
            accent.pack(side="left", fill="y", pady=5)

            inner = ctk.CTkFrame(item, fg_color="transparent")
            inner.pack(side="left", fill="both", expand=True, padx=(7, 0))

            icon_wrap = ctk.CTkFrame(inner, width=22, height=22, fg_color="transparent", corner_radius=7)
            icon_wrap.pack(side="left", padx=(6, 8), pady=8)
            icon_wrap.pack_propagate(False)
            icon = AppIcon(icon_wrap, icon_name, size=12, color=COLORS["text_muted"], bg=COLORS["sidebar_bg"])
            icon.place(relx=0.5, rely=0.5, anchor="center")

            text = ctk.CTkLabel(inner, text=label, text_color=COLORS["text_muted"], font=self.fonts.nav)
            text.pack(side="left")

            self._bind_click(item, key)
            self._bind_click(inner, key)
            self._bind_click(text, key)
            self._bind_click(icon_wrap, key)
            self._bind_click(icon, key)

            self.rows[key] = item
            self.labels[key] = text
            self.icons[key] = icon
            self.accents[key] = accent

        self.set_active(self.active_key)

    def _build_footer_divider(self) -> None:
        spacer = ctk.CTkFrame(self, fg_color="transparent")
        spacer.grid(row=2, column=0, sticky="nsew", padx=12)
        spacer.grid_rowconfigure(0, weight=1)
        divider = ctk.CTkFrame(spacer, fg_color=COLORS["border_soft"], height=1, corner_radius=0)
        divider.grid(row=1, column=0, sticky="ew", pady=(0, 10))

    def _bind_click(self, widget, key: str) -> None:
        widget.bind("<Button-1>", lambda _event, screen=key: self.on_navigate(screen))

    def set_active(self, key: str | None) -> None:
        self.active_key = key or ""
        for item_key, row in self.rows.items():
            active = item_key == key
            row.configure(fg_color=COLORS["primary_deep"] if active else "transparent")
            self.accents[item_key].configure(fg_color=COLORS["primary"] if active else "transparent")
            self.labels[item_key].configure(text_color=COLORS["primary_light"] if active else COLORS["text_muted"])
            self.icons[item_key].destroy()
            icon_parent = row.winfo_children()[1].winfo_children()[0]
            icon_parent.configure(fg_color=COLORS["card_alt"] if active else "transparent")
            bg = COLORS["card_alt"] if active else COLORS["sidebar_bg"]
            icon = AppIcon(
                icon_parent,
                self.icons[item_key].kind,
                size=12,
                color=COLORS["primary_light"] if active else COLORS["text_muted"],
                bg=bg,
            )
            icon.place(relx=0.5, rely=0.5, anchor="center")
            self.icons[item_key] = icon
            self._bind_click(icon, item_key)
