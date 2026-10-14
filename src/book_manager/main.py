"""Punto de entrada de la aplicación Book Manager."""

import os
import sys

# Permite ejecutar el punto de entrada desde distintos directorios.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main(import_default_data: bool = True) -> None:
    """Inicializa los datos opcionales y lanza la interfaz de consola.

    Args:
        import_default_data: Indica si se deben precargar los datos de ejemplo.
    """
    if import_default_data:
        from book_manager.preload_data.preload_data import inicializar_datos

        inicializar_datos()

    from book_manager.ui.console import iniciar_app

    iniciar_app()


if __name__ == "__main__":
    main(import_default_data=True)