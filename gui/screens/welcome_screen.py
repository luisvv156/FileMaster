"""Pantalla de bienvenida — rediseño visual con Poppins y layout mejorado."""

from __future__ import annotations

import customtkinter as ctk

from gui.components.common import AppIcon, PillBadge, primary_button, secondary_button
from gui.components.status_badge import StatusBadge
from gui.theme import APP_FOLDER, COLORS, WELCOME_STEPS, WELCOME_TAGS


# ── Helpers de diseño ─────────────────────────────────────────────────────────

def _divider(parent: ctk.CTkFrame, color: str | None = None) -> ctk.CTkFrame:
    """Línea divisora horizontal sutil."""
    return ctk.CTkFrame(
        parent,
        height=1,
        fg_color=color or COLORS["border_soft"],
        corner_radius=0,
    )


def _accent_dot(parent: ctk.CTkFrame, color: str) -> ctk.CTkLabel:
    """Pequeño punto de acento de color."""
    return ctk.CTkLabel(
        parent,
        text="●",
        text_color=color,
        font=ctk.CTkFont(family="Poppins", size=7),
        width=10,
    )


# ── Pantalla principal ────────────────────────────────────────────────────────

class WelcomeScreen(ctk.CTkFrame):
    def __init__(self, master, fonts, controller, app):
        super().__init__(master, fg_color=COLORS["shell_bg"])
        self.fonts = fonts
        self.controller = controller
        self.app = app

        # Layout: 58 % hero · 42 % preview
        self.grid_columnconfigure(0, weight=58, uniform="hero")
        self.grid_columnconfigure(1, weight=42, uniform="hero")
        self.grid_rowconfigure(0, weight=1)

    # ── Ciclo de vida ──────────────────────────────────────────────────────────
    def refresh(self) -> None:
        for child in self.winfo_children():
            child.destroy()
        self._build_left()
        self._build_right()

    # ── Columna izquierda — hero ───────────────────────────────────────────────
    def _build_left(self) -> None:
        left = ctk.CTkFrame(self, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsew", padx=(32, 20), pady=30)

        # — Pill badge —
        PillBadge(
            left,
            self.fonts,
            text="✦  Aplicacion de escritorio · IA 100 % local",
            fg_color=COLORS["primary_glow"],
            text_color=COLORS["primary_light"],
            border_color=COLORS["border_accent"],
            padx=12,
        ).pack(anchor="w", pady=(4, 20))

        # — Titular en dos líneas —
        ctk.CTkLabel(
            left,
            text="Organiza tus archivos",
            text_color=COLORS["text"],
            font=self.fonts.hero,
            justify="left",
        ).pack(anchor="w")

        ctk.CTkLabel(
            left,
            text="con inteligencia artificial",
            text_color=COLORS["primary_soft"],
            font=self.fonts.hero,
            justify="left",
        ).pack(anchor="w")

        # — Subtítulo —
        ctk.CTkLabel(
            left,
            text=(
                "FileMaster monitorea tu carpeta en segundo plano,\n"
                "analiza cada documento y lo clasifica automaticamente.\n"
                "Sin esfuerzo. Sin desorden."
            ),
            text_color=COLORS["text_secondary"],
            font=self.fonts.subtitle,
            justify="left",
            wraplength=420,
        ).pack(anchor="w", pady=(14, 22))

        _divider(left).pack(fill="x", pady=(0, 20))

        # — Sección "Cómo funciona" —
        self._build_steps(left)

        _divider(left).pack(fill="x", pady=(20, 20))

        # — Botones de acción —
        self._build_actions(left)

        # — Tags / pills informativos —
        self._build_tags(left)

    def _build_steps(self, parent: ctk.CTkFrame) -> None:
        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.pack(anchor="w", pady=(0, 10))

        _accent_dot(header, COLORS["primary"]).pack(side="left", padx=(0, 6))
        ctk.CTkLabel(
            header,
            text="CÓMO FUNCIONA",
            text_color=COLORS["text_muted"],
            font=self.fonts.section,
        ).pack(side="left")

        # (acento_texto, fondo_burbuja, borde_burbuja) — todos sólidos, tkinter no soporta alfa
        STEP_ACCENTS = [
            (COLORS["primary"], "#0f1f42", "#1a3060"),
            (COLORS["success"], "#0a2b1e", "#144d32"),
            (COLORS["warning"], "#2a1e0e", "#4a3218"),
        ]

        for idx, (text, (accent, bubble_bg, bubble_border)) in enumerate(
            zip(WELCOME_STEPS, STEP_ACCENTS), start=1
        ):
            row = ctk.CTkFrame(
                parent,
                fg_color=COLORS["card_alt"],
                corner_radius=12,
                border_width=1,
                border_color=COLORS["border_soft"],
            )
            row.pack(fill="x", pady=(0, 8))

            # Burbuja numérica — fondos sólidos equivalentes al tono translúcido
            bubble_frame = ctk.CTkFrame(row, fg_color="transparent", width=44, height=44)
            bubble_frame.pack(side="left", padx=(14, 0), pady=14)
            bubble_frame.pack_propagate(False)

            bubble = ctk.CTkFrame(
                bubble_frame,
                width=28,
                height=28,
                fg_color=bubble_bg,
                corner_radius=999,
                border_width=1,
                border_color=bubble_border,
            )
            bubble.place(relx=0.5, rely=0.5, anchor="center")
            bubble.pack_propagate(False)

            ctk.CTkLabel(
                bubble,
                text=str(idx),
                text_color=accent,   # accent = color del texto (primer elemento de la tupla)
                font=self.fonts.badge,
            ).place(relx=0.5, rely=0.5, anchor="center")

            # Texto del paso
            ctk.CTkLabel(
                row,
                text=text,
                text_color=COLORS["text"] if idx < 3 else COLORS["primary_light"],
                font=self.fonts.body_bold if idx == 3 else self.fonts.body,
                justify="left",
                wraplength=340,
            ).pack(side="left", fill="x", expand=True, pady=14, padx=(10, 14))

    def _build_actions(self, parent: ctk.CTkFrame) -> None:
        actions = ctk.CTkFrame(parent, fg_color="transparent")
        actions.pack(anchor="w", pady=(0, 18))

        primary_button(
            actions,
            self.fonts,
            "Configurar mi carpeta  →",
            command=lambda: self.app.show_screen("config"),
            width=200,
        ).pack(side="left")

        if self.controller.has_configuration():
            secondary_button(
                actions,
                self.fonts,
                "Abrir panel",
                command=lambda: self.app.show_screen("main"),
                width=130,
            ).pack(side="left", padx=(10, 0))

    def _build_tags(self, parent: ctk.CTkFrame) -> None:
        tags = ctk.CTkFrame(parent, fg_color="transparent")
        tags.pack(anchor="w")

        for idx, tag in enumerate(WELCOME_TAGS):
            PillBadge(
                tags,
                self.fonts,
                text=tag,
                fg_color=COLORS["card_soft"],
                text_color=COLORS["text_secondary"],
                border_color=COLORS["border"],
                padx=10,
            ).grid(row=idx // 3, column=idx % 3, padx=(0, 8), pady=(0, 8), sticky="w")

    # ── Columna derecha — preview ──────────────────────────────────────────────
    def _build_right(self) -> None:
        snapshot   = self.controller.snapshot()
        status     = snapshot.get("status_message") or "Listo para comenzar con la configuracion inicial."
        watch_folder = snapshot.get("config", {}).get("watch_folder") or APP_FOLDER
        total      = snapshot.get("stats", {}).get("total_organized", 0)
        precision  = snapshot.get("stats", {}).get("average_confidence", 0)
        duplicates = snapshot.get("stats", {}).get("duplicates_detected", 0)
        recent     = snapshot.get("recent_files", [])[:3]

        right = ctk.CTkFrame(self, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew", padx=(0, 28), pady=30)
        right.grid_rowconfigure(0, weight=1)
        right.grid_columnconfigure(0, weight=1)

        # ── Tarjeta preview principal ──────────────────────────────────────────
        preview = ctk.CTkFrame(
            right,
            fg_color=COLORS["card_bg"],
            corner_radius=16,
            border_width=1,
            border_color=COLORS["border"],
        )
        preview.grid(row=0, column=0, sticky="nsew")

        # Barra de título (chrome)
        self._build_chrome(preview)

        # Cuerpo del panel
        body = ctk.CTkFrame(preview, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=16, pady=(12, 16))

        # Badge de estado
        StatusBadge(body, self.fonts).pack(fill="x")
        ctk.CTkLabel(
            body,
            text=status,
            text_color=COLORS["text_muted"],
            font=self.fonts.tiny,
            justify="left",
            wraplength=360,
        ).pack(anchor="w", pady=(4, 14))

        _divider(body).pack(fill="x", pady=(0, 14))

        # Config activa
        self._build_folder_card(body, watch_folder)

        # Stats
        self._build_stats_row(body, total, precision, duplicates)

        _divider(body).pack(fill="x", pady=(0, 12))

        # Últimos archivos
        self._build_recent(body, recent)

    def _build_chrome(self, parent: ctk.CTkFrame) -> None:
        """Barra superior estilo ventana nativa."""
        chrome = ctk.CTkFrame(
            parent,
            fg_color=COLORS["chrome_bg"],
            height=34,
            corner_radius=0,
        )
        chrome.pack(fill="x")
        chrome.pack_propagate(False)

        # Título centrado
        ctk.CTkLabel(
            chrome,
            text="FileMaster",
            text_color=COLORS["brand"],
            font=self.fonts.tiny,
        ).pack(side="left", padx=14)

        # Semáforo macOS-style
        dot_frame = ctk.CTkFrame(chrome, fg_color="transparent")
        dot_frame.pack(side="right", padx=12)
        for color in ("#ff5f57", "#febc2e", "#28c840"):
            ctk.CTkFrame(
                dot_frame,
                width=10,
                height=10,
                fg_color=color,
                corner_radius=999,
            ).pack(side="right", padx=3)

    def _build_folder_card(self, parent: ctk.CTkFrame, watch_folder: str) -> None:
        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.pack(anchor="w", pady=(0, 8))
        _accent_dot(header, COLORS["warning"]).pack(side="left", padx=(0, 6))
        ctk.CTkLabel(
            header,
            text="CONFIGURACIÓN ACTIVA",
            text_color=COLORS["text_muted"],
            font=self.fonts.section,
        ).pack(side="left")

        folder_card = ctk.CTkFrame(
            parent,
            fg_color=COLORS["card_alt"],
            corner_radius=10,
            border_width=1,
            border_color=COLORS["border_soft"],
        )
        folder_card.pack(fill="x", pady=(0, 12))

        row = ctk.CTkFrame(folder_card, fg_color="transparent")
        row.pack(fill="x", padx=12, pady=10)

        # Ícono carpeta
        box = ctk.CTkFrame(
            row,
            width=26,
            height=26,
            fg_color=COLORS["warning_bg"],
            corner_radius=7,
        )
        box.pack(side="left", padx=(0, 10))
        box.pack_propagate(False)
        AppIcon(box, "folder", size=12, color=COLORS["warning"], bg=COLORS["warning_bg"]).place(
            relx=0.5, rely=0.5, anchor="center"
        )

        text_wrap = ctk.CTkFrame(row, fg_color="transparent")
        text_wrap.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(
            text_wrap,
            text="Carpeta origen",
            text_color=COLORS["text_muted"],
            font=self.fonts.tiny,
        ).pack(anchor="w")
        ctk.CTkLabel(
            text_wrap,
            text=watch_folder,
            text_color=COLORS["text"],
            font=self.fonts.body_bold,
        ).pack(anchor="w")

    def _build_stats_row(
        self,
        parent: ctk.CTkFrame,
        total: int,
        precision: float,
        duplicates: int,
    ) -> None:
        stats = ctk.CTkFrame(parent, fg_color="transparent")
        stats.pack(fill="x", pady=(0, 12))

        entries = (
            ("Organizados", str(total),        COLORS["primary"]),
            ("Precisión",   f"{precision}%",   COLORS["success"]),
            ("Duplicados",  str(duplicates),   COLORS["warning"]),
        )

        for idx, (label, value, accent) in enumerate(entries):
            card = ctk.CTkFrame(
                stats,
                fg_color=COLORS["card_alt"],
                corner_radius=10,
                border_width=1,
                border_color=COLORS["border_soft"],
            )
            card.grid(row=0, column=idx, sticky="ew", padx=(0 if idx == 0 else 6, 0))
            stats.grid_columnconfigure(idx, weight=1)

            # Barra de color superior
            bar = ctk.CTkFrame(card, height=3, fg_color=accent, corner_radius=0)
            bar.pack(fill="x")

            ctk.CTkLabel(
                card,
                text=label,
                text_color=COLORS["text_muted"],
                font=self.fonts.tiny,
            ).pack(anchor="w", padx=10, pady=(8, 0))

            ctk.CTkLabel(
                card,
                text=value,
                text_color=accent,
                font=self.fonts.title,
            ).pack(anchor="w", padx=10, pady=(0, 10))

    def _build_recent(self, parent: ctk.CTkFrame, recent: list) -> None:
        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.pack(anchor="w", pady=(0, 8))
        _accent_dot(header, COLORS["success"]).pack(side="left", padx=(0, 6))
        ctk.CTkLabel(
            header,
            text="ÚLTIMOS ARCHIVOS ORGANIZADOS",
            text_color=COLORS["text_muted"],
            font=self.fonts.section,
        ).pack(side="left")

        list_card = ctk.CTkFrame(parent, fg_color="transparent")
        list_card.pack(fill="x")

        if recent:
            for item in recent:
                row = ctk.CTkFrame(
                    list_card,
                    fg_color=COLORS["card_alt"],
                    corner_radius=8,
                    border_width=1,
                    border_color=COLORS["border_soft"],
                )
                row.pack(fill="x", pady=(0, 6))

                ctk.CTkLabel(
                    row,
                    text=item["name"],
                    text_color=COLORS["text"],
                    font=self.fonts.small,
                ).pack(side="left", padx=12, pady=9)

                PillBadge(
                    row,
                    self.fonts,
                    text=item["category"],
                    fg_color=COLORS["primary_deep"],
                    text_color=COLORS["primary_light"],
                    border_color=COLORS["border_accent"],
                    padx=8,
                ).pack(side="right", padx=8, pady=6)
        else:
            empty = ctk.CTkFrame(
                list_card,
                fg_color=COLORS["card_alt"],
                corner_radius=8,
                border_width=1,
                border_color=COLORS["border_soft"],
            )
            empty.pack(fill="x")
            ctk.CTkLabel(
                empty,
                text="Tu actividad aparecerá aquí en cuanto FileMaster organice los primeros archivos.",
                text_color=COLORS["text_secondary"],
                font=self.fonts.small,
                justify="left",
                wraplength=340,
            ).pack(anchor="w", padx=14, pady=14)