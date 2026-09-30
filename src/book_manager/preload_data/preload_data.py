import datetime

from book_manager.entities.entities import (
    CotizacionDolar,
    Editorial,
    Genero,
    Libro,
    Moneda,
    Precio,
    Stock,
    TipoCotizacion,
)
from book_manager.repositories.repositories import (
    CsvRepositorioBase,
    CsvRepositorioCotizacion,
    CsvRepositorioStock,
)


def inicializar_datos() -> None:
    """
    Script para precargar al menos 10 registros por entidad.
    Solo inserta si detecta que los archivos estan vacios.
    """
    repo_generos = CsvRepositorioBase(Genero, 'generos.csv')
    repo_editoriales = CsvRepositorioBase(Editorial, 'editoriales.csv')
    repo_monedas = CsvRepositorioBase(Moneda, 'monedas.csv')
    repo_tipos_cot = CsvRepositorioBase(TipoCotizacion, 'tipo_cotizacion.csv')
    repo_precios = CsvRepositorioBase(Precio, 'precios.csv')
    repo_libros = CsvRepositorioBase(Libro, 'libros.csv')
    repo_stock = CsvRepositorioStock()
    repo_cotizaciones = CsvRepositorioCotizacion()

    print("Verificando y precargando datos iniciales...")

    if not repo_generos.leer_todos():
        nombres = ["Novela", "Ensayo", "Ciencia Ficcion", "Fantasia", "Terror",
                   "Misterio", "Biografia", "Historia", "Tecnologia", "Infantil"]
        for i, nombre in enumerate(nombres, start=1):
            repo_generos.crear(Genero(id=i, nombre=nombre))

    if not repo_editoriales.leer_todos():
        nombres = ["Planeta", "Sudamericana", "Salamandra", "Minotauro", "Siglo XXI",
                   "Alfaguara", "Anagrama", "Tusquets", "Norma", "OReilly"]
        for i, nombre in enumerate(nombres, start=1):
            repo_editoriales.crear(Editorial(id=i, nombre=nombre))

    if not repo_monedas.leer_todos():
        datos = [("ARS", "$"), ("USD", "U$S"), ("EUR", "€"), ("GBP", "£"), ("BRL", "R$"),
                 ("CLP", "$"), ("UYU", "$U"), ("MXN", "$"), ("PEN", "S/"), ("COP", "$")]
        for i, (nombre, sim) in enumerate(datos, start=1):
            repo_monedas.crear(Moneda(id=i, nombre=nombre, simbolo=sim))

    if not repo_tipos_cot.leer_todos():
        nombres = ["Oficial", "Blue", "MEP", "CCL", "Tarjeta",
                   "Mayorista", "Cripto", "Solidario", "Turista", "Minorista"]
        for i, nombre in enumerate(nombres, start=1):
            repo_tipos_cot.crear(TipoCotizacion(id=i, nombre=nombre))

    if not repo_precios.leer_todos():
        # 10 precios (1=ARS, 2=USD)
        valores = [(15000.0, 1), (20000.0, 1), (25.5, 2), (30.0, 2), (18000.0, 1),
                   (45.0, 2), (12000.0, 1), (22000.0, 1), (15.5, 2), (50.0, 2)]
        for i, (val, mon) in enumerate(valores, start=1):
            repo_precios.crear(Precio(id=i, valor=val, moneda_id=mon))

    if not repo_libros.leer_todos():
        # id, isbn, titulo, autor_id, editorial_id, genero_id, precio_id, stock_id
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
        for i, (isbn, tit, aut, ed, gen, pre, stk) in enumerate(datos_libros, start=1):
            repo_libros.crear(Libro(id=i, isbn=isbn, titulo=tit, autor_id=aut,
                                    editorial_id=ed, genero_id=gen, precio_id=pre, stock_id=stk))

    if not repo_stock.leer_todos():
        cantidades = [50, 20, 100, 15, 10, 30, 5, 45, 60, 25]
        for i, cant in enumerate(cantidades, start=1):
            repo_stock.crear(Stock(libro_id=i, cantidad=cant))

    # 10 dias de cotizacion por cada tipo de dolar (Oficial=1, Blue=2, MEP=3)
    cotizaciones_por_tipo = {
        1: [870.0, 875.0, 880.0, 885.0, 890.0, 895.0, 900.0, 905.0, 910.0, 915.0],
        2: [1000.0, 1010.0, 1025.0, 1020.0, 1050.0, 1045.0, 1060.0, 1080.0, 1100.0, 1120.0],
        3: [980.0, 985.0, 990.0, 995.0, 1000.0, 1005.0, 1010.0, 1015.0, 1020.0, 1025.0],
    }
    fecha_base = datetime.date(2024, 1, 1)
    for tipo_id, valores in cotizaciones_por_tipo.items():
        # Insertamos solo si ese tipo todavia no tiene historial cargado
        if not repo_cotizaciones.leer_historico_por_tipo(tipo_id):
            for i, val in enumerate(valores):
                fecha = fecha_base + datetime.timedelta(days=i)
                repo_cotizaciones.crear(CotizacionDolar(tipo_id=tipo_id, fecha=fecha, valor=val))

    print("Precarga de datos finalizada.")

if __name__ == "__main__":
    inicializar_datos()