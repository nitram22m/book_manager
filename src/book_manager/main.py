import os
import sys

# Aseguramos que Python encuentre nuestros modulos sin importar desde donde ejecutemos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main(import_default_data: bool = True) -> None:
    """
    Punto de entrada principal del sistema Book Manager.

    Args:
        import_default_data (bool): Bandera para forzar o evitar la precarga de datos.
    """
    if import_default_data:
        from book_manager.preload_data.preload_data import inicializar_datos

        inicializar_datos()

    # Arrancamos el menu interactivo por consola
    from book_manager.ui.console import iniciar_app

    iniciar_app()

if __name__ == "__main__":
    # Al ejecutar el script directamente desde la terminal, precargamos datos por defecto
    main(import_default_data=True)