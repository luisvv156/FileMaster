"""Pantalla de bienvenida."""

from __future__ import annotations

import customtkinter as ctk

from gui.components.common import AppIcon, PillBadge, primary_button, secondary_button
from gui.components.status_badge import StatusBadge
from gui.theme import APP_FOLDER, COLORS, WELCOME_STEPS, WELCOME_TAGS


class WelcomeScreen(ctk.CTkFrame):
    def __init__(self, master, fonts, controller, app):
        super().__init__(master, fg_color=COLORS["shell_bg"])
        self.fonts = fonts
        self.controller = controller
        self.app = app
        self.grid_columnconfigure(0, weight=58, uniform="hero")
        self.grid_columnconfigure(1, weight=42, uniform="hero")

    def refresh(self) -> None:
        for child in self.winfo_children():
            child.destroy()
        self._build_left()
        self._build_right()

    def _build_left(self) -> None:
        left = ctk.CTkFrame(self, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsew", padx=(26, 22), pady=24)

        PillBadge(
            left,
            self.fonts,
            text="Aplicacion de escritorio con IA local",
            fg_color=COLORS["card_alt"],
            text_color=COLORS["text_secondary"],
            border_color=COLORS["border_soft"],
            padx=10,
        ).pack(anchor="w", pady=(8, 18))

        ctk.CTkLabel(left, text="Organiza tus archivos", text_color=COLORS["text"], font=self.fonts.hero).pack(anchor="w", pady=(0, 0))
        ctk.CTkLabel(left, text="con inteligencia artificial", text_color=COLORS["primary_light"], font=self.fonts.hero).pack(anchor="w")

        ctk.CTkLabel(
            left,
            text=(
                "FileMaster monitorea tu carpeta en segundo plano, analiza\n"
                "el contenido de cada documento nuevo y lo clasifica\n"
                "automaticamente. Sin esfuerzo, sin desorden."
            ),
            text_color=COLORS["text_secondary"],
            font=self.fonts.subtitle,
            justify="left",
            wraplength=410,
        ).pack(anchor="w", pady=(18, 24))

        ctk.CTkLabel(left, text="COMO FUNCIONA", text_color=COLORS["text_muted"], font=self.fonts.section).pack(anchor="w", pady=(0, 10))
        for idx, text in enumerate(WELCOME_STEPS, start=1):
            row = ctk.CTkFrame(left, fg_color=COLORS["card_alt"], corner_radius=10, border_width=1, border_color=COLORS["border_soft"])
            row.pack(fill="x", pady=(0, 10))
            bubble = ctk.CTkLabel(
                row,
                text=str(idx),
                width=24,
                height=24,
                fg_color=COLORS["primary_soft"],
                text_color=COLORS["text"],
                corner_radius=999,
                font=self.fonts.badge,
            )
            bubble.pack(side="left", padx=(12, 10), pady=12)
            ctk.CTkLabel(
                row,
                text=text,
                text_color=COLORS["text"],
                font=self.fonts.body_bold if idx == 3 else self.fonts.body,
                justify="left",
                wraplength=350,
            ).pack(side="left", fill="x", expand=True, pady=12, padx=(0, 12))

        actions = ctk.CTkFrame(left, fg_color="transparent")
        actions.pack(anchor="w", pady=(18, 16))
        primary_button(actions, self.fonts, "Configurar mi carpeta ->", command=lambda: self.app.show_screen("config"), width=190).pack(side="left")
        if self.controller.has_configuration():
            secondary_button(actions, self.fonts, "Abrir panel", command=lambda: self.app.show_screen("main"), width=128).pack(
                side="left", padx=(10, 0)
            )

        tags = ctk.CTkFrame(left, fg_color="transparent")
        tags.pack(anchor="w")
        for idx, tag in enumerate(WELCOME_TAGS):
            PillBadge(
                tags,
                self.fonts,
                text=tag,
                fg_color=COLORS["card_alt"],
                text_color=COLORS["text_secondary"],
                border_color=COLORS["border_soft"],
                padx=8,
            ).grid(row=idx // 3, column=idx % 3, padx=(0, 8), pady=(0, 8), sticky="w")

    def _build_right(self) -> None:
        snapshot = self.controller.snapshot()
        status = snapshot.get("status_message") or "Listo para comenzar con la configuracion inicial."
        watch_folder = snapshot.get("config", {}).get("watch_folder") or APP_FOLDER
        total = snapshot.get("stats", {}).get("total_organized", 0)
        precision = snapshot.get("stats", {}).get("average_confidence", 0)
        duplicates = snapshot.get("stats", {}).get("duplicates_detected", 0)
        recent = snapshot.get("recent_files", [])[:3]

        right = ctk.CTkFrame(self, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew", padx=(0, 24), pady=24)

        preview = ctk.CTkFrame(
            right,
            width=418,
            height=334,
            fg_color=COLORS["card_bg"],
            corner_radius=14,
            border_width=1,
            border_color=COLORS["border"],
        )
        preview.pack(anchor="center", expand=True)
        preview.pack_propagate(False)

        top = ctk.CTkFrame(preview, fg_color=COLORS["chrome_bg"], height=20, corner_radius=0)
        top.pack(fill="x")
        top.pack_propagate(False)
        ctk.CTkLabel(top, text="FileMaster", text_color=COLORS["brand"], font=self.fonts.tiny).pack(side="left", padx=10)
        for symbol in ("-", "o", "x"):
            ctk.CTkLabel(top, text=symbol, text_color=COLORS["text_muted"], font=self.fonts.tiny).pack(side="right", padx=4)

        body = ctk.CTkFrame(preview, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=12, pady=12)

        StatusBadge(body, self.fonts).pack(fill="x")
        ctk.CTkLabel(body, text=status, text_color=COLORS["text_muted"], font=self.fonts.tiny, justify="left", wraplength=360).pack(anchor="w", pady=(6, 12))

        ctk.CTkLabel(body, text="CONFIGURACION ACTIVA", text_color=COLORS["text_muted"], font=self.fonts.section).pack(anchor="w", pady=(0, 8))
        folder_card = ctk.CTkFrame(body, fg_color=COLORS["card_alt"], corner_radius=10, border_width=1, border_color=COLORS["border_soft"])
        folder_card.pack(fill="x", pady=(0, 10))
        row = ctk.CTkFrame(folder_card, fg_color="transparent")
        row.pack(fill="x", padx=12, pady=12)
        box = ctk.CTkFrame(row, width=22, height=22, fg_color=COLORS["warning_bg"], corner_radius=6)
        box.pack(side="left", padx=(0, 10))
        box.pack_propagate(False)
        AppIcon(box, "folder", size=11, color=COLORS["warning"], bg=COLORS["warning_bg"]).place(relx=0.5, rely=0.5, anchor="center")
        text_wrap = ctk.CTkFrame(row, fg_color="transparent")
        text_wrap.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(text_wrap, text="Carpeta origen", text_color=COLORS["text_muted"], font=self.fonts.tiny).pack(anchor="w")
        ctk.CTkLabel(text_wrap, text=watch_folder, text_color=COLORS["text"], font=self.fonts.body_bold).pack(anchor="w")

        stats = ctk.CTkFrame(body, fg_color="transparent")
        stats.pack(fill="x", pady=(0, 10))
        for idx, (label, value, accent) in enumerate(
            (
                ("Organizados", str(total), COLORS["primary"]),
                ("Precision", f"{precision}%", COLORS["success"]),
                ("Duplicados", str(duplicates), COLORS["warning"]),
            )
        ):
            card = ctk.CTkFrame(stats, fg_color=COLORS["card_alt"], corner_radius=10, border_width=1, border_color=COLORS["border_soft"])
            card.grid(row=0, column=idx, sticky="ew", padx=(0 if idx == 0 else 6, 0))
            stats.grid_columnconfigure(idx, weight=1)
            ctk.CTkLabel(card, text=label, text_color=COLORS["text_muted"], font=self.fonts.tiny).pack(anchor="w", padx=10, pady=(10, 2))
            ctk.CTkLabel(card, text=value, text_color=accent, font=self.fonts.title).pack(anchor="w", padx=10, pady=(0, 10))

        ctk.CTkLabel(body, text="ULTIMOS ARCHIVOS ORGANIZADOS", text_color=COLORS["text_muted"], font=self.fonts.section).pack(
            anchor="w", pady=(0, 6)
        )
        list_card = ctk.CTkFrame(body, fg_color="transparent")
        list_card.pack(fill="x")
        for item in recent:
            row = ctk.CTkFrame(list_card, fg_color=COLORS["card_alt"], corner_radius=8, border_width=1, border_color=COLORS["border_soft"])
            row.pack(fill="x", pady=(0, 6))
            ctk.CTkLabel(row, text=item["name"], text_color=COLORS["text"], font=self.fonts.small).pack(side="left", padx=10, pady=9)
            PillBadge(
                row,
                self.fonts,
                text=item["category"],
                fg_color=COLORS["primary_deep"],
                text_color=COLORS["primary_light"],
                border_color=COLORS["border"],
                padx=8,
            ).pack(side="right", padx=8, pady=6)

        if not recent:
            empty = ctk.CTkFrame(list_card, fg_color=COLORS["card_alt"], corner_radius=8, border_width=1, border_color=COLORS["border_soft"])
            empty.pack(fill="x")
            ctk.CTkLabel(
                empty,
                text="Tu actividad aparecera aqui en cuanto FileMaster organice los primeros archivos.",
                text_color=COLORS["text_secondary"],
                font=self.fonts.small,
                justify="left",
                wraplength=340,
            ).pack(anchor="w", padx=12, pady=12)
