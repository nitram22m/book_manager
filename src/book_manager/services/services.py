"""Logica de negocio de Book Manager."""
from book_manager.entities.entities import (
    Autor,
    Editorial,
    Genero,
    Moneda,
    TipoCotizacion,
)
from book_manager.repositories.repositories import (
    CsvRepositorioBase,
    CsvRepositorioCotizacion,
    CsvRepositorioLibro,
    CsvRepositorioPrecio,
    CsvRepositorioStock,
)


class ServicioLibreria:
    """Conecta la interfaz de consola con los repositorios CSV.

    Es el unico lugar donde se arma el grafo de repositorios, de modo que
    cada uno valide sus relaciones contra los repositorios correctos.
    """

    def __init__(self) -> None:
        """Crea y conecta los repositorios necesarios para el servicio."""
        self.repo_generos = CsvRepositorioBase(Genero, "generos.csv")
        self.repo_editoriales = CsvRepositorioBase(
            Editorial, "editoriales.csv"
        )
        self.repo_autores = CsvRepositorioBase(Autor, "autores.csv")
        self.repo_monedas = CsvRepositorioBase(Moneda, "monedas.csv")
        self.repo_tipo_cot = CsvRepositorioBase(
            TipoCotizacion, "tipo_cotizacion.csv"
        )
        self.repo_precios = CsvRepositorioPrecio(self.repo_monedas)
        self.repo_libros = CsvRepositorioLibro(
            self.repo_autores,
            self.repo_editoriales,
            self.repo_generos,
            self.repo_precios,
        )
        self.repo_stock = CsvRepositorioStock(self.repo_libros)
        self.repo_cotizaciones = CsvRepositorioCotizacion(self.repo_tipo_cot)

    def calcular_precio_ars(
        self, libro_id: int, tipo_dolar_id: int = 1
    ) -> float:
        """Calcula el precio final del libro en ARS.

        Si el precio esta en USD se multiplica por la cotizacion mas reciente
        del tipo de dolar indicado.
        """
        libro = self.repo_libros.leer_por_id(libro_id)
        if libro is None:
            raise ValueError("El libro no existe.")

        precio = libro.precio
        moneda = precio.moneda.nombre
        if moneda == "ARS":
            return precio.valor
        if moneda != "USD":
            raise ValueError(f"No hay conversion configurada para {moneda}.")

        if self.repo_tipo_cot.leer_por_id(tipo_dolar_id) is None:
            raise ValueError("El tipo de cotizacion no existe.")
        historico = self.repo_cotizaciones.leer_historico_por_tipo(
            tipo_dolar_id
        )
        if not historico:
            raise ValueError(
                "No hay cotizaciones cargadas para hacer la conversión."
            )

        ultima = max(historico, key=lambda c: c.fecha)
        return precio.valor * ultima.valor

    def consultar_stock(self, libro_id: int) -> int:
        """Devuelve las unidades disponibles, o cero si no hay registro."""
        stock = self.repo_stock.leer_por_libro(libro_id)
        return stock.cantidad if stock else 0

    def vender_libro(self, libro_id: int, cantidad_vendida: int) -> None:
        """Valida el libro y las existencias antes de descontar una venta."""
        if cantidad_vendida <= 0:
            raise ValueError("La cantidad a vender debe ser mayor que cero.")
        if self.repo_libros.leer_por_id(libro_id) is None:
            raise ValueError("El libro no existe.")
        stock = self.repo_stock.leer_por_libro(libro_id)
        if stock is None:
            raise ValueError("El libro no tiene stock registrado.")
        stock.descontar(cantidad_vendida)
        self.repo_stock.actualizar(stock)
