from book_manager.entities.entities import (
    Editorial,
    Genero,
    Libro,
    Moneda,
    Precio,
    TipoCotizacion,
)
from book_manager.repositories.repositories import (
    CsvRepositorioBase,
    CsvRepositorioCotizacion,
    CsvRepositorioStock,
)


class ServicioLibreria:
    """
    Clase principal para manejar la logica de negocio.
    Conecta la interfaz de consola con los repositorios CSV.
    """
    def __init__(self) -> None:
        # Instanciamos los repositorios para tenerlos a mano
        self.repo_generos = CsvRepositorioBase(Genero, 'generos.csv')
        self.repo_editoriales = CsvRepositorioBase(Editorial, 'editoriales.csv')
        self.repo_libros = CsvRepositorioBase(Libro, 'libros.csv')
        self.repo_precios = CsvRepositorioBase(Precio, 'precios.csv')
        self.repo_monedas = CsvRepositorioBase(Moneda, 'monedas.csv')
        self.repo_tipo_cot = CsvRepositorioBase(TipoCotizacion, 'tipo_cotizacion.csv')
        self.repo_stock = CsvRepositorioStock()
        self.repo_cotizaciones = CsvRepositorioCotizacion()

    def calcular_precio_ars(self, libro_id: int, tipo_dolar_id: int = 1) -> float:
        """
        Calcula el valor final del libro en ARS.
        Si esta en USD, lo multiplica por la cotizacion mas reciente.
        """
        libro = self.repo_libros.leer_por_id(libro_id)
        if not libro:
            raise ValueError("El libro no existe.")

        precio = self.repo_precios.leer_por_id(libro.precio_id)
        if not precio:
            raise ValueError("El libro no tiene un precio asignado.")

        moneda = self.repo_monedas.leer_por_id(precio.moneda_id)
        if not moneda:
            raise ValueError("Moneda no encontrada.")

        # Si la moneda ya es pesos argentinos, devolvemos el valor tal cual
        if moneda.nombre == "ARS":
            return precio.valor

        if moneda.nombre != "USD":
            raise ValueError(f"No hay conversion configurada para {moneda.nombre}.")

        # Buscamos la cotizacion mas reciente del tipo de dolar seleccionado
        historico = self.repo_cotizaciones.leer_historico_por_tipo(tipo_dolar_id)
        if not historico:
            raise ValueError("No hay cotizaciones cargadas para hacer la conversion.")

        # Ordenamos las fechas de mayor a menor para sacar la mas nueva
        historico.sort(key=lambda x: x.fecha, reverse=True)
        ultima_cot = historico[0]

        return precio.valor * ultima_cot.valor

    def consultar_stock(self, libro_id: int) -> int:
        """Devuelve la cantidad disponible de un libro."""
        stock = self.repo_stock.leer_por_libro(libro_id)
        if stock:
            return stock.cantidad
        return 0

    def vender_libro(self, libro_id: int, cantidad_vendida: int) -> None:
        """
        Valida que haya stock y lo descuenta simulando una venta.
        """
        if cantidad_vendida <= 0:
            raise ValueError("La cantidad a vender debe ser mayor que cero.")

        stock_actual = self.consultar_stock(libro_id)

        if stock_actual < cantidad_vendida:
            raise ValueError(f"Stock insuficiente. Solo hay {stock_actual} unidades.")

        # Leemos el objeto stock y lo actualizamos
        stock = self.repo_stock.leer_por_libro(libro_id)
        stock.cantidad -= cantidad_vendida
        self.repo_stock.actualizar(stock)