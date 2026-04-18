"""Punto de entrada de FileMaster."""
import os  # ← agregar esta línea
from gui.app import run_app


def main() -> None:
    # ✅ En desarrollo, resetear estado al arrancar
    if os.getenv("FILEMASTER_DEV_RESET", "0") == "1":
        from reset_dev import reset
        reset()
    
    from gui.app import run_app
    run_app()


if __name__ == "__main__":
    main()
