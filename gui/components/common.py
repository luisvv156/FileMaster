"""Componentes base para construir la interfaz de FileMaster."""

from __future__ import annotations

import ctypes
import os
import sys
from pathlib import Path
from tkinter import Canvas, PhotoImage, TclError

import customtkinter as ctk

from config.settings import LOGO_PATH
from gui.theme import COLORS, TITLEBAR_HEIGHT


class AppIcon(Canvas):
    def __init__(self, master, kind: str, size: int = 14, color: str = "#ffffff", bg: str | None = None):
        super().__init__(
            master,
            width=size,
            height=size,
            highlightthickness=0,
            bd=0,
            bg=bg or COLORS["card_bg"],
        )
        self.kind = kind
        self.size = size
        self.color = color
        self._draw()

    def _draw(self) -> None:
        s = self.size
        c = self.color
        if self.kind == "folder":
            self.create_rectangle(2, 5, s - 2, s - 3, outline=c, width=1.4)
            self.create_rectangle(3, 3, s * 0.46, 6, outline=c, width=1.4)
        elif self.kind == "file":
            self.create_rectangle(3, 2, s - 3, s - 2, outline=c, width=1.4)
            self.create_line(s - 6, 2, s - 6, 6, fill=c, width=1.2)
            self.create_line(s - 6, 6, s - 2, 6, fill=c, width=1.2)
        elif self.kind == "home":
            self.create_polygon(s / 2, 2, s - 2, s / 2 + 1, 2, s / 2 + 1, outline=c, fill="", width=1.4)
            self.create_rectangle(4, s / 2 + 1, s - 4, s - 2, outline=c, width=1.4)
        elif self.kind == "clock":
            self.create_oval(2, 2, s - 2, s - 2, outline=c, width=1.4)
            self.create_line(s / 2, s / 2, s / 2, 4, fill=c, width=1.2)
            self.create_line(s / 2, s / 2, s - 5, s / 2 + 2, fill=c, width=1.2)
        elif self.kind == "duplicate":
            self.create_rectangle(5, 4, s - 2, s - 5, outline=c, width=1.3)
            self.create_rectangle(2, 7, s - 5, s - 2, outline=c, width=1.3)
        elif self.kind == "gear":
            self.create_oval(4, 4, s - 4, s - 4, outline=c, width=1.3)
            self.create_line(s / 2, 1, s / 2, 4, fill=c, width=1.2)
            self.create_line(s / 2, s - 4, s / 2, s - 1, fill=c, width=1.2)
            self.create_line(1, s / 2, 4, s / 2, fill=c, width=1.2)
            self.create_line(s - 4, s / 2, s - 1, s / 2, fill=c, width=1.2)
        elif self.kind == "check":
            self.create_line(3, s / 2, s / 2 - 1, s - 4, s - 3, 3, fill=c, width=2.0, smooth=True)
        elif self.kind == "warning":
            self.create_polygon(s / 2, 2, s - 2, s - 2, 2, s - 2, outline=c, fill="", width=1.3)
            self.create_line(s / 2, 5, s / 2, s - 6, fill=c, width=1.2)
            self.create_oval(s / 2 - 1, s - 5, s / 2 + 1, s - 3, outline=c, fill=c)
        elif self.kind == "spark":
            self.create_line(s / 2, 1, s / 2, s - 1, fill=c, width=1.3)
            self.create_line(1, s / 2, s - 1, s / 2, fill=c, width=1.3)
            self.create_line(3, 3, s - 3, s - 3, fill=c, width=1.1)
            self.create_line(3, s - 3, s - 3, 3, fill=c, width=1.1)
        elif self.kind == "bot":
            self.create_rectangle(3, 4, s - 3, s - 3, outline=c, width=1.3)
            self.create_line(s / 2, 1, s / 2, 4, fill=c, width=1.1)
            self.create_oval(5, 7, 7, 9, outline=c, fill=c)
            self.create_oval(s - 7, 7, s - 5, 9, outline=c, fill=c)
        else:
            self.create_oval(3, 3, s - 3, s - 3, outline=c, width=1.4)


class PillBadge(ctk.CTkFrame):
    def __init__(
        self,
        master,
        fonts,
        text: str,
        fg_color: str,
        text_color: str,
        border_color: str | None = None,
        dot_color: str | None = None,
        padx: int = 10,
    ):
        super().__init__(
            master,
            fg_color=fg_color,
            corner_radius=999,
            border_width=1 if border_color else 0,
            border_color=border_color or fg_color,
        )
        if dot_color:
            dot = Canvas(self, width=8, height=8, bg=fg_color, highlightthickness=0, bd=0)
            dot.create_oval(1, 1, 7, 7, fill=dot_color, outline="")
            dot.pack(side="left", padx=(padx, 6), pady=5)
        label = ctk.CTkLabel(self, text=text, font=fonts.badge, text_color=text_color)
        label.pack(side="left", padx=(0 if dot_color else padx, padx), pady=5)


def configure_windows_runtime() -> None:
    if sys.platform != "win32":
        return

    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("FileMaster.Desktop")
    except Exception:
        pass


def apply_window_icon(window) -> None:
    if not LOGO_PATH.exists():
        return
    try:
        image = PhotoImage(file=str(LOGO_PATH))
        window.iconphoto(True, image)
        setattr(window, "_filemaster_icon", image)
    except (TclError, OSError):
        return


def default_folder_shortcuts() -> list[tuple[str, Path]]:
    home = Path.home()
    mapping = [
        ("Inicio", home),
        ("Descargas", home / "Downloads"),
        ("Documentos", home / "Documents"),
        ("Escritorio", home / "Desktop"),
    ]

    if sys.platform == "win32":
        mapping = [
            ("Usuario", Path(os.environ.get("USERPROFILE", str(home)))),
            ("Descargas", Path(os.environ.get("USERPROFILE", str(home))) / "Downloads"),
            ("Documentos", Path(os.environ.get("USERPROFILE", str(home))) / "Documents"),
            ("Escritorio", Path(os.environ.get("USERPROFILE", str(home))) / "Desktop"),
        ]

    visible = [(label, path) for label, path in mapping if path.exists()]
    if sys.platform == "win32":
        for letter in "CDEFGHIJKLMNOPQRSTUVWXYZ":
            drive = Path(f"{letter}:/")
            if drive.exists():
                visible.append((f"Disco {letter}:", drive))
    return visible


def primary_button(master, fonts, text: str, command=None, width: int = 190) -> ctk.CTkButton:
    return ctk.CTkButton(
        master,
        text=text,
        width=width,
        height=36,
        corner_radius=10,
        fg_color=COLORS["primary"],
        hover_color=COLORS["primary_soft"],
        text_color=COLORS["text"],
        font=fonts.body_bold,
        command=command,
    )


def secondary_button(master, fonts, text: str, command=None, width: int = 120) -> ctk.CTkButton:
    return ctk.CTkButton(
        master,
        text=text,
        width=width,
        height=36,
        corner_radius=10,
        fg_color=COLORS["card_alt"],
        hover_color=COLORS["hover_bg"],
        border_width=1,
        border_color=COLORS["border"],
        text_color=COLORS["text_secondary"],
        font=fonts.body,
        command=command,
    )


class WindowTitleBar(ctk.CTkFrame):
    def __init__(self, master, fonts):
        super().__init__(
            master,
            fg_color=COLORS["chrome_bg"],
            height=TITLEBAR_HEIGHT,
            corner_radius=0,
            border_width=1,
            border_color=COLORS["border_soft"],
        )
        self.grid_propagate(False)
        self.grid_columnconfigure(0, weight=1)

        left = ctk.CTkFrame(self, fg_color="transparent")
        left.grid(row=0, column=0, sticky="w", padx=12)

        mark = ctk.CTkFrame(left, width=14, height=14, corner_radius=4, fg_color=COLORS["logo_bg"])
        mark.pack(side="left", padx=(0, 8))
        mark.pack_propagate(False)
        AppIcon(mark, "folder", size=10, color=COLORS["primary"], bg=COLORS["logo_bg"]).place(relx=0.5, rely=0.5, anchor="center")

        title = ctk.CTkLabel(left, text="FileMaster", text_color=COLORS["brand"], font=fonts.titlebar)
        title.pack(side="left")

        right = ctk.CTkFrame(self, fg_color="transparent")
        right.grid(row=0, column=1, sticky="e", padx=10)
        controls = (
            ("-", COLORS["text_muted"]),
            ("o", COLORS["text_muted"]),
            ("x", COLORS["danger"]),
        )
        for symbol, color in controls:
            pill = ctk.CTkFrame(right, width=20, height=18, corner_radius=7, fg_color=COLORS["card_alt"])
            pill.pack(side="left", padx=3, pady=5)
            pill.pack_propagate(False)
            ctk.CTkLabel(pill, text=symbol, text_color=color, font=fonts.tiny).place(relx=0.5, rely=0.5, anchor="center")


class AppDialog(ctk.CTkToplevel):
    def __init__(
        self,
        master,
        fonts,
        title: str,
        message: str,
        *,
        variant: str = "info",
        confirm_text: str = "Aceptar",
        cancel_text: str | None = None,
    ) -> None:
        super().__init__(master.winfo_toplevel())
        self.fonts = fonts
        self.result = False
        self.title(title)
        self.geometry("420x220")
        self.resizable(False, False)
        self.transient(master.winfo_toplevel())
        self.grab_set()
        self.configure(fg_color=COLORS["window_bg"])
        self.protocol("WM_DELETE_WINDOW", self._cancel)
        apply_window_icon(self)

        accent_map = {
            "info": ("spark", COLORS["primary"], COLORS["info_bg"]),
            "success": ("check", COLORS["success"], COLORS["success_bg"]),
            "warning": ("warning", COLORS["warning"], COLORS["warning_bg"]),
            "danger": ("warning", COLORS["danger"], COLORS["danger_bg"]),
        }
        icon_name, accent_color, accent_bg = accent_map.get(variant, accent_map["info"])

        shell = ctk.CTkFrame(
            self,
            fg_color=COLORS["card_bg"],
            border_width=1,
            border_color=COLORS["border"],
            corner_radius=12,
        )
        shell.pack(fill="both", expand=True, padx=14, pady=14)

        header = ctk.CTkFrame(
            shell,
            fg_color=COLORS["chrome_bg"],
            height=28,
            corner_radius=0,
            border_width=0,
        )
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(header, text="FileMaster", text_color=COLORS["brand"], font=fonts.titlebar).pack(side="left", padx=10)
        for symbol in ("-", "o", "x"):
            ctk.CTkLabel(header, text=symbol, text_color=COLORS["text_muted"], font=fonts.titlebar).pack(
                side="right", padx=4
            )

        body = ctk.CTkFrame(shell, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=18, pady=18)

        icon_box = ctk.CTkFrame(body, width=34, height=34, fg_color=accent_bg, corner_radius=9)
        icon_box.pack(anchor="w")
        icon_box.pack_propagate(False)
        AppIcon(icon_box, icon_name, size=16, color=accent_color, bg=accent_bg).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(body, text=title, text_color=COLORS["text"], font=fonts.title).pack(anchor="w", pady=(14, 6))
        ctk.CTkLabel(
            body,
            text=message,
            text_color=COLORS["text_secondary"],
            font=fonts.body,
            justify="left",
            wraplength=350,
        ).pack(anchor="w")

        footer = ctk.CTkFrame(body, fg_color="transparent")
        footer.pack(side="bottom", fill="x", pady=(18, 0))
        if cancel_text:
            secondary_button(footer, fonts, cancel_text, command=self._cancel, width=110).pack(side="left")
        primary_button(footer, fonts, confirm_text, command=self._confirm, width=140).pack(side="right")

        self.update_idletasks()
        self._center(master.winfo_toplevel())

    def _center(self, root) -> None:
        root.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = root.winfo_rootx() + (root.winfo_width() - width) // 2
        y = root.winfo_rooty() + (root.winfo_height() - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _confirm(self) -> None:
        self.result = True
        self.destroy()

    def _cancel(self) -> None:
        self.result = False
        self.destroy()


def show_app_dialog(master, fonts, title: str, message: str, *, variant: str = "info") -> None:
    dialog = AppDialog(master, fonts, title, message, variant=variant)
    dialog.wait_window()


def ask_app_dialog(master, fonts, title: str, message: str, *, variant: str = "warning") -> bool:
    dialog = AppDialog(
        master,
        fonts,
        title,
        message,
        variant=variant,
        confirm_text="Confirmar",
        cancel_text="Cancelar",
    )
    dialog.wait_window()
    return dialog.result


class FolderBrowserDialog(ctk.CTkFrame):
    def __init__(self, master, fonts, initial_path: str = "") -> None:
        root = master.winfo_toplevel()
        super().__init__(root, fg_color=COLORS["window_bg"], corner_radius=0)
        self.fonts = fonts
        self.result: str | None = None
        self.current_path = self._resolve_initial_path(initial_path)
        self.path_var = ctk.StringVar(value=str(self.current_path))
        self.selection_var = ctk.StringVar(value=str(self.current_path))
        self.browser_status_var = ctk.StringVar(value="")
        self._list_host: ctk.CTkScrollableFrame | None = None

        self.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.lift()

        shell = ctk.CTkFrame(
            self,
            fg_color=COLORS["shell_bg"],
            border_width=1,
            border_color=COLORS["border"],
            corner_radius=12,
        )
        shell.pack(fill="both", expand=True, padx=26, pady=22)

        header = ctk.CTkFrame(shell, fg_color=COLORS["chrome_bg"], height=30, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(header, text="FileMaster", text_color=COLORS["brand"], font=fonts.titlebar).pack(side="left", padx=10)
        ctk.CTkButton(
            header,
            text="Cerrar",
            width=82,
            height=24,
            corner_radius=8,
            fg_color=COLORS["card_alt"],
            hover_color=COLORS["hover_bg"],
            border_width=1,
            border_color=COLORS["border"],
            text_color=COLORS["text_secondary"],
            font=fonts.small,
            command=self._cancel,
        ).pack(side="right", padx=8, pady=3)

        content = ctk.CTkFrame(shell, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=18, pady=18)
        title_block = ctk.CTkFrame(content, fg_color="transparent")
        title_block.pack(fill="x")
        ctk.CTkLabel(title_block, text="Selecciona la carpeta a monitorear", text_color=COLORS["text"], font=fonts.title).pack(
            anchor="w"
        )
        ctk.CTkLabel(
            title_block,
            text="Navega entre carpetas locales y confirma la ubicacion que FileMaster analizara en segundo plano.",
            text_color=COLORS["text_secondary"],
            font=fonts.small,
        ).pack(anchor="w", pady=(4, 0))

        main = ctk.CTkFrame(content, fg_color="transparent")
        main.pack(fill="both", expand=True, pady=(14, 0))
        main.grid_columnconfigure(0, weight=28, uniform="folder")
        main.grid_columnconfigure(1, weight=72, uniform="folder")
        main.grid_rowconfigure(0, weight=1)

        shortcuts = ctk.CTkFrame(
            main,
            fg_color=COLORS["card_alt"],
            corner_radius=10,
            border_width=1,
            border_color=COLORS["border"],
        )
        shortcuts.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        shortcuts.grid_rowconfigure(1, weight=1)
        shortcuts.grid_columnconfigure(0, weight=1)

        shortcuts_header = ctk.CTkFrame(shortcuts, fg_color="transparent")
        shortcuts_header.pack(fill="x", padx=14, pady=(14, 10))
        ctk.CTkLabel(shortcuts_header, text="ACCESOS RAPIDOS", text_color=COLORS["text_muted"], font=fonts.section).pack(
            side="left"
        )
        PillBadge(
            shortcuts_header,
            self.fonts,
            text=f"{len(self._favorite_paths())} ubicaciones",
            fg_color=COLORS["card_bg"],
            text_color=COLORS["text_secondary"],
            border_color=COLORS["border_soft"],
            padx=8,
        ).pack(side="right")

        shortcuts_list = ctk.CTkScrollableFrame(
            shortcuts,
            fg_color="transparent",
            corner_radius=0,
            scrollbar_button_color=COLORS["border"],
            scrollbar_button_hover_color=COLORS["hover_bg"],
        )
        shortcuts_list.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        for label, path in self._favorite_paths():
            button = ctk.CTkButton(
                shortcuts_list,
                text=label,
                anchor="w",
                height=34,
                corner_radius=8,
                fg_color=COLORS["card_bg"],
                hover_color=COLORS["hover_bg"],
                border_width=1,
                border_color=COLORS["border_soft"],
                text_color=COLORS["text"],
                font=fonts.body,
                command=lambda target=path: self._open_directory(target),
            )
            button.pack(fill="x", pady=(0, 8))

        summary = ctk.CTkFrame(shortcuts, fg_color=COLORS["card_bg"], corner_radius=8)
        summary.pack(fill="x", padx=10, pady=(0, 12))
        ctk.CTkLabel(summary, text="CARPETA ACTUAL", text_color=COLORS["text_muted"], font=fonts.section).pack(
            anchor="w", padx=12, pady=(12, 6)
        )
        self.selection_label = ctk.CTkLabel(
            summary,
            textvariable=self.selection_var,
            text_color=COLORS["text"],
            font=fonts.small,
            justify="left",
            wraplength=220,
        )
        self.selection_label.pack(anchor="w", padx=12, pady=(0, 12))

        browser = ctk.CTkFrame(
            main,
            fg_color=COLORS["card_alt"],
            corner_radius=10,
            border_width=1,
            border_color=COLORS["border"],
        )
        browser.grid(row=0, column=1, sticky="nsew")
        browser.grid_columnconfigure(0, weight=1)
        browser.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(browser, text="NAVEGADOR DE CARPETAS", text_color=COLORS["text_muted"], font=fonts.section).pack(
            anchor="w", padx=16, pady=(14, 10)
        )

        path_row = ctk.CTkFrame(browser, fg_color="transparent")
        path_row.pack(fill="x", padx=16)
        path_row.grid_columnconfigure(0, weight=1)
        path_entry = ctk.CTkEntry(
            path_row,
            textvariable=self.path_var,
            height=34,
            corner_radius=8,
            fg_color=COLORS["field_bg"],
            border_color=COLORS["border"],
            text_color=COLORS["text"],
            font=fonts.body,
        )
        path_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        path_entry.bind("<Return>", lambda _event: self._go_to_typed_path())
        secondary_button(path_row, fonts, "Ir", command=self._go_to_typed_path, width=74).grid(row=0, column=1, padx=(0, 8))
        secondary_button(path_row, fonts, "Subir", command=self._go_parent, width=82).grid(row=0, column=2, padx=(0, 8))
        secondary_button(path_row, fonts, "Home", command=lambda: self._open_directory(Path.home()), width=82).grid(row=0, column=3)

        ctk.CTkLabel(
            browser,
            textvariable=self.browser_status_var,
            text_color=COLORS["text_secondary"],
            font=fonts.tiny,
            justify="left",
        ).pack(anchor="w", padx=16, pady=(8, 0))

        self._list_host = ctk.CTkScrollableFrame(
            browser,
            fg_color=COLORS["card_bg"],
            corner_radius=8,
            scrollbar_button_color=COLORS["border"],
            scrollbar_button_hover_color=COLORS["hover_bg"],
        )
        self._list_host.pack(fill="both", expand=True, padx=16, pady=(12, 14))

        footer = ctk.CTkFrame(content, fg_color="transparent")
        footer.pack(fill="x", pady=(16, 0))
        footer_left = ctk.CTkFrame(footer, fg_color="transparent")
        footer_left.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(
            footer_left,
            text="La carpeta seleccionada sera analizada por la IA y usada para el monitoreo automatico.",
            text_color=COLORS["text_muted"],
            font=fonts.tiny,
            wraplength=360,
            justify="left",
        ).pack(side="left", pady=8)
        secondary_button(footer_left, fonts, "Cancelar", command=self._cancel, width=120).pack(side="left", padx=(16, 0))
        primary_button(footer, fonts, "Usar esta carpeta ->", command=self._confirm, width=180).pack(side="right")

        self._render_directory_listing()
        self.focus_set()
        self.bind("<Escape>", lambda _event: self._cancel())
        try:
            self.grab_set()
        except Exception:
            pass

    def _resolve_initial_path(self, initial_path: str) -> Path:
        candidate = Path(initial_path).expanduser() if initial_path else Path.home()
        if candidate.exists():
            if candidate.is_file():
                return candidate.parent
            return candidate
        return Path.home()

    def _favorite_paths(self) -> list[tuple[str, Path]]:
        return default_folder_shortcuts()

    def _clear_listing(self) -> None:
        if self._list_host is None:
            return
        for child in self._list_host.winfo_children():
            child.destroy()

    def _render_directory_listing(self) -> None:
        self._clear_listing()
        self.selection_var.set(str(self.current_path))
        self.path_var.set(str(self.current_path))

        if self._list_host is None:
            return

        try:
            directories = sorted(
                [child for child in self.current_path.iterdir() if child.is_dir()],
                key=lambda item: item.name.lower(),
            )
        except OSError:
            self.browser_status_var.set("No fue posible leer esta carpeta. Verifica permisos o intenta con otra ubicacion.")
            ctk.CTkLabel(
                self._list_host,
                text="No fue posible leer esta carpeta.",
                text_color=COLORS["danger"],
                font=self.fonts.small,
            ).pack(anchor="w", padx=12, pady=12)
            return

        total_directories = len(directories)
        if total_directories:
            self.browser_status_var.set(
                f"Ruta actual: {self.current_path}    ·    {total_directories} subcarpetas disponibles"
            )
        else:
            self.browser_status_var.set(
                f"Ruta actual: {self.current_path}    ·    No hay subcarpetas visibles, pero puedes usarla tal como esta"
            )

        if self.current_path.parent != self.current_path:
            self._directory_row(self.current_path.parent, label="..", subtitle="Subir al directorio anterior")

        if not directories:
            ctk.CTkLabel(
                self._list_host,
                text="Esta carpeta no tiene subcarpetas visibles. Puedes usarla tal como esta.",
                text_color=COLORS["text_secondary"],
                font=self.fonts.small,
                justify="left",
                wraplength=420,
            ).pack(anchor="w", padx=12, pady=12)
            return

        for directory in directories:
            self._directory_row(directory)

    def _directory_row(self, directory: Path, *, label: str | None = None, subtitle: str | None = None) -> None:
        if self._list_host is None:
            return

        row = ctk.CTkFrame(
            self._list_host,
            fg_color=COLORS["card_alt"],
            corner_radius=8,
            border_width=1,
            border_color=COLORS["border_soft"],
        )
        row.pack(fill="x", pady=(0, 8))
        row.grid_columnconfigure(1, weight=1)

        icon_box = ctk.CTkFrame(row, width=20, height=20, fg_color=COLORS["warning_bg"], corner_radius=5)
        icon_box.grid(row=0, column=0, rowspan=2, padx=10, pady=10)
        icon_box.pack_propagate(False)
        AppIcon(icon_box, "folder", size=12, color=COLORS["warning"], bg=COLORS["warning_bg"]).place(
            relx=0.5, rely=0.5, anchor="center"
        )

        display_name = label or directory.name or str(directory)
        ctk.CTkLabel(row, text=display_name, text_color=COLORS["text"], font=self.fonts.body_bold).grid(
            row=0, column=1, sticky="w", pady=(9, 0)
        )
        ctk.CTkLabel(
            row,
            text=subtitle or str(directory),
            text_color=COLORS["text_muted"],
            font=self.fonts.tiny,
        ).grid(row=1, column=1, sticky="w", pady=(0, 9))

        def open_target(_event=None, target=directory) -> None:
            self._open_directory(target)

        secondary_button(
            row,
            self.fonts,
            "Abrir",
            width=82,
            command=lambda target=directory: self._open_directory(target),
        ).grid(
            row=0,
            column=2,
            rowspan=2,
            padx=12,
        )
        row.bind("<Button-1>", open_target)
        for child in row.winfo_children():
            if not isinstance(child, ctk.CTkButton):
                child.bind("<Button-1>", open_target)

    def _open_directory(self, directory: Path) -> None:
        if not directory.exists() or not directory.is_dir():
            return
        self.current_path = directory
        self._render_directory_listing()

    def _go_parent(self) -> None:
        if self.current_path.parent != self.current_path:
            self._open_directory(self.current_path.parent)

    def _go_to_typed_path(self) -> None:
        typed_path = Path(self.path_var.get().strip()).expanduser()
        if typed_path.exists() and typed_path.is_dir():
            self._open_directory(typed_path)

    def _confirm(self) -> None:
        self.result = str(self.current_path)
        try:
            self.grab_release()
        except Exception:
            pass
        self.destroy()

    def _cancel(self) -> None:
        self.result = None
        try:
            self.grab_release()
        except Exception:
            pass
        self.destroy()


def show_folder_browser(master, fonts, initial_path: str = "") -> str | None:
    dialog = FolderBrowserDialog(master, fonts, initial_path)
    dialog.wait_window()
    return dialog.result
