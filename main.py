"""Punto de entrada de FileMaster."""

from config.logging_config import setup_logging
from gui.app import FileMasterApp


def main() -> None:
    """Inicia la aplicacion."""
    setup_logging()
    app = FileMasterApp()
    app.run()


if __name__ == "__main__":
    main()
