"""Aplicacion principal de FileMaster."""

from __future__ import annotations

import queue

import customtkinter as ctk

from core.controller import FileMasterController
from gui.components.common import WindowTitleBar, apply_window_icon, configure_windows_runtime
from gui.components.sidebar import Sidebar
from gui.screens.config_screen import ConfigScreen
from gui.screens.duplicates_screen import DuplicatesScreen
from gui.screens.groups_screen import GroupsScreen
from gui.screens.main_panel import MainPanelScreen
from gui.screens.manual_classify_screen import ManualClassifyScreen
from gui.screens.summary_screen import SummaryScreen
from gui.screens.welcome_screen import WelcomeScreen
from gui.theme import (
    COLORS,
    SCREEN_NAV_STATE,
    SHELL_PADDING,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
    build_fonts,
    setup_appearance,
)


class FileMasterApp:
    def __init__(self) -> None:
        setup_appearance()
        configure_windows_runtime()
        self.root = ctk.CTk()
        self.fonts = build_fonts()
        self._refresh_queue: queue.SimpleQueue[str] = queue.SimpleQueue()
        self.controller = FileMasterController(notify_callback=self._enqueue_refresh)
        self.current_screen = "welcome"

        self.root.title("FileMaster")
        apply_window_icon(self.root)
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.minsize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.root.resizable(False, False)
        self.root.configure(fg_color=COLORS["window_bg"])
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self.titlebar = WindowTitleBar(self.root, self.fonts)
        self.titlebar.grid(row=0, column=0, sticky="ew")

        self.body = ctk.CTkFrame(self.root, fg_color=COLORS["shell_bg"], corner_radius=0)
        self.body.grid(row=1, column=0, sticky="nsew")
        self.body.grid_rowconfigure(0, weight=1)
        self.body.grid_columnconfigure(0, weight=1)

        self.welcome_host = ctk.CTkFrame(self.body, fg_color=COLORS["shell_bg"], corner_radius=0)
        self.welcome_host.grid(row=0, column=0, sticky="nsew")
        self.welcome_host.grid_rowconfigure(0, weight=1)
        self.welcome_host.grid_columnconfigure(0, weight=1)

        self.shell_host = ctk.CTkFrame(self.body, fg_color=COLORS["shell_bg"], corner_radius=0)
        self.shell_host.grid(row=0, column=0, sticky="nsew")
        self.shell_host.grid_rowconfigure(0, weight=1)
        self.shell_host.grid_columnconfigure(1, weight=1)

        self.sidebar = Sidebar(self.shell_host, self.fonts, self.show_screen, active_key="main")
        self.sidebar.grid(row=0, column=0, sticky="ns")

        self.content = ctk.CTkFrame(self.shell_host, fg_color=COLORS["shell_bg"], corner_radius=0)
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

        self.screen_container = ctk.CTkFrame(self.content, fg_color=COLORS["shell_bg"], corner_radius=0)
        self.screen_container.grid(row=0, column=0, sticky="nsew", padx=SHELL_PADDING, pady=SHELL_PADDING)
        self.screen_container.grid_rowconfigure(0, weight=1)
        self.screen_container.grid_columnconfigure(0, weight=1)

        self.welcome_screen = WelcomeScreen(self.welcome_host, self.fonts, self.controller, self)
        self.welcome_screen.grid(row=0, column=0, sticky="nsew")

        self.screens = {
            "config": ConfigScreen(self.screen_container, self.fonts, self.controller, self),
            "groups": GroupsScreen(self.screen_container, self.fonts, self.controller, self),
            "main": MainPanelScreen(self.screen_container, self.fonts, self.controller, self),
            "summary": SummaryScreen(self.screen_container, self.fonts, self.controller, self),
            "manual": ManualClassifyScreen(self.screen_container, self.fonts, self.controller, self),
            "duplicates": DuplicatesScreen(self.screen_container, self.fonts, self.controller, self),
        }

        for screen in self.screens.values():
            screen.grid(row=0, column=0, sticky="nsew")

        initial_screen = "welcome"
        snapshot = self.controller.snapshot()
        if snapshot.get("pending_groups"):
            initial_screen = "groups"
        elif self.controller.has_configuration():
            initial_screen = "main"
        self.show_screen(initial_screen)
        self.root.after(250, self._process_refresh_queue)

    def _enqueue_refresh(self) -> None:
        self._refresh_queue.put("refresh")

    def _process_refresh_queue(self) -> None:
        should_refresh = False
        try:
            while True:
                self._refresh_queue.get_nowait()
                should_refresh = True
        except queue.Empty:
            pass

        if should_refresh:
            self.refresh_current_screen()

        try:
            self.root.after(250, self._process_refresh_queue)
        except RuntimeError:
            return

    def refresh_current_screen(self) -> None:
        if self.current_screen == "welcome":
            self.welcome_screen.refresh()
            return
        screen = self.screens.get(self.current_screen)
        if screen is not None:
            screen.refresh()

    def show_screen(self, key: str) -> None:
        self.current_screen = key
        if key == "welcome":
            self.welcome_host.tkraise()
            self.sidebar.set_active(None)
            self.welcome_screen.refresh()
            return

        self.shell_host.tkraise()
        screen = self.screens.get(key, self.screens["main"])
        screen.tkraise()
        self.sidebar.set_active(SCREEN_NAV_STATE.get(key))
        screen.refresh()

    def _on_close(self) -> None:
        self.controller.stop_agent()
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()
