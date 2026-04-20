"""Punto de entrada de FileMaster."""

from __future__ import annotations

import argparse
import os


def main() -> None:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument(
        "--observer",
        action="store_true",
        help="Ejecuta FileMaster en modo observador sin interfaz gráfica",
    )
    args = parser.parse_args()

    if os.getenv("FILEMASTER_DEV_RESET", "0") == "1":
        from reset_dev import reset
        reset()

    if args.observer:
        from core.background_observer import run_background_observer
        run_background_observer()
        return

    from gui.app import run_app
    run_app()


if __name__ == "__main__":
    main()
