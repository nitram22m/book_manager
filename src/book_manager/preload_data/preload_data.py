"""Carga de registros de ejemplo para iniciar Book Manager."""

import datetime

from book_manager.entities.entities import (
    Autor,
    CotizacionDolar,
    Editorial,
    Genero,
    Libro,
    Moneda,
    Precio,
    Stock,
    TipoCotizacion,
)
from book_manager.services.services import ServicioLibreria


def inicializar_datos() -> None:
    """Carga datos de ejemplo en entidades con archivos vacíos."""
    servicio = ServicioLibreria()
    repo_generos = servicio.repo_generos
    repo_editoriales = servicio.repo_editoriales
    repo_autores = servicio.repo_autores
    repo_monedas = servicio.repo_monedas
    repo_tipos_cot = servicio.repo_tipo_cot
    repo_precios = servicio.repo_precios
    repo_libros = servicio.repo_libros
    repo_stock = servicio.repo_stock
    repo_cotizaciones = servicio.repo_cotizaciones

    print("Verificando y precargando datos iniciales...")

    if not repo_generos.leer_todos():
        nombres = [
            "Novela", "Ensayo", "Ciencia Ficcion", "Fantasia", "Terror",
            "Misterio", "Biografia", "Historia", "Tecnologia", "Infantil",
        ]
        for i, nombre in enumerate(nombres, start=1):
            repo_generos.crear(Genero(id=i, nombre=nombre))

    if not repo_editoriales.leer_todos():
        nombres = [
            "Planeta", "Sudamericana", "Salamandra", "Minotauro", "Siglo XXI",
            "Alfaguara", "Anagrama", "Tusquets", "Norma", "OReilly",
        ]
        for i, nombre in enumerate(nombres, start=1):
            repo_editoriales.crear(Editorial(id=i, nombre=nombre))

    if not repo_autores.leer_todos():
        nombres = [
            "George Orwell", "Jorge Luis Borges", "J. K. Rowling",
            "Ray Bradbury", "Robert C. Martin", "Bram Stoker",
            "Walter Isaacson", "J. R. R. Tolkien", "Gabriel Garcia Marquez",
            "Frank Herbert",
        ]
        for i, nombre in enumerate(nombres, start=1):
            repo_autores.crear(Autor(id=i, nombre=nombre))

    if not repo_monedas.leer_todos():
        datos = [
            ("ARS", "$"), ("USD", "U$S"), ("EUR", "€"), ("GBP", "£"),
            ("BRL", "R$"), ("CLP", "$"), ("UYU", "$U"), ("MXN", "$"),
            ("PEN", "S/"), ("COP", "$"),
        ]
        for i, (nombre, sim) in enumerate(datos, start=1):
            repo_monedas.crear(Moneda(id=i, nombre=nombre, simbolo=sim))

    if not repo_tipos_cot.leer_todos():
        nombres = [
            "Oficial", "Blue", "MEP", "CCL", "Tarjeta", "Mayorista",
            "Cripto", "Solidario", "Turista", "Minorista",
        ]
        for i, nombre in enumerate(nombres, start=1):
            repo_tipos_cot.crear(TipoCotizacion(id=i, nombre=nombre))

    if not repo_precios.leer_todos():
        # Cada tupla contiene el importe y el identificador de moneda.
        valores = [
            (15000.0, 1), (20000.0, 1), (25.5, 2), (30.0, 2), (18000.0, 1),
            (45.0, 2), (12000.0, 1), (22000.0, 1), (15.5, 2), (50.0, 2),
        ]
        for i, (val, mon) in enumerate(valores, start=1):
            moneda = repo_monedas.leer_por_id(mon)
            if moneda is not None:
                repo_precios.crear(Precio(id=i, valor=val, moneda=moneda))

    if not repo_libros.leer_todos():
        # isbn, titulo, autor, editorial, genero y precio.
        datos_libros = [
            ("978-1", "1984", 1, 1, 3, 1, 1),
            ("978-2", "El Aleph", 2, 2, 1, 2, 2),
            ("978-3", "Harry Potter y la Piedra Filosofal", 3, 3, 4, 3, 3),
            ("978-4", "Fahrenheit 451", 4, 4, 3, 4, 4),
            ("978-5", "Clean Code", 5, 10, 9, 5, 5),
            ("978-6", "Dracula", 6, 8, 5, 6, 6),
            ("978-7", "Steve Jobs", 7, 1, 7, 7, 7),
            ("978-8", "El Hobbit", 8, 4, 4, 8, 8),
            ("978-9", "Cien anos de soledad", 9, 2, 1, 9, 9),
            ("978-10", "Dune", 10, 5, 3, 10, 10)
        ]
        for i, (isbn, tit, aut, ed, gen, pre, _) in enumerate(
            datos_libros, start=1
        ):
            autor = repo_autores.leer_por_id(aut)
            editorial = repo_editoriales.leer_por_id(ed)
            genero = repo_generos.leer_por_id(gen)
            precio = repo_precios.leer_por_id(pre)
            if all((autor, editorial, genero, precio)):
                repo_libros.crear(
                    Libro(i, isbn, tit, autor, editorial, genero, precio)
                )

    if not repo_stock.leer_todos():
        cantidades = [50, 20, 100, 15, 10, 30, 5, 45, 60, 25]
        for i, cant in enumerate(cantidades, start=1):
            libro = repo_libros.leer_por_id(i)
            if libro is not None:
                repo_stock.crear(Stock(libro=libro, cantidad=cant))

    # Carga diez días de cotización para los tipos Oficial, Blue y MEP.
    cotizaciones_por_tipo = {
        1: [
            870.0, 875.0, 880.0, 885.0, 890.0, 895.0, 900.0, 905.0,
            910.0, 915.0,
        ],
        2: [
            1000.0, 1010.0, 1025.0, 1020.0, 1050.0, 1045.0, 1060.0,
            1080.0, 1100.0, 1120.0,
        ],
        3: [
            980.0, 985.0, 990.0, 995.0, 1000.0, 1005.0, 1010.0, 1015.0,
            1020.0, 1025.0,
        ],
    }
    fecha_base = datetime.date(2024, 1, 1)
    for tipo_id, valores in cotizaciones_por_tipo.items():
        # Evita duplicar el historial de un tipo ya cargado.
        if not repo_cotizaciones.leer_historico_por_tipo(tipo_id):
            tipo = repo_tipos_cot.leer_por_id(tipo_id)
            if tipo is None:
                continue
            for i, val in enumerate(valores):
                fecha = fecha_base + datetime.timedelta(days=i)
                repo_cotizaciones.crear(
                    CotizacionDolar(tipo=tipo, fecha=fecha, valor=val)
                )

    print("Precarga de datos finalizada.")


if __name__ == "__main__":
    inicializar_datos()
