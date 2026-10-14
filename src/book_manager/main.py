"""Punto de entrada de la aplicación Book Manager."""

import os
import sys
from pathlib import Path

# Permite ejecutar el punto de entrada desde distintos directorios.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main(import_default_data: bool = True) -> None:
    """Migra los datos CSV a la base de datos y lanza la interfaz.

    Args:
        import_default_data: Indica si se deben migrar los CSV iniciales.
    """
    if import_default_data:
        from book_manager.migrations.migrations import migrar_datos

        directorio_migraciones = Path(__file__).resolve().parent / "migrations"
        migrar_datos(
            str(directorio_migraciones / "csv"),
            str(directorio_migraciones / "sql"),
        )

    from book_manager.ui.console import iniciar_app

    iniciar_app()


if __name__ == "__main__":
    main(import_default_data=True)
