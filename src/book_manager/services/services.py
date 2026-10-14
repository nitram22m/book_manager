"""Logica de negocio de Book Manager."""
from __future__ import annotations

from datetime import date
import math
import os
from pathlib import Path
from typing import Callable

import requests
from dotenv import load_dotenv

from book_manager.entities.entities import (
    CotizacionDolar,
    Libro,
    TipoCotizacion,
)
from book_manager.repositories.repositories import (
    SQLRepositorioBase,
    SQLRepositorioCotizacion,
    SQLRepositorioStock,
    crear_repositorio_autor,
    crear_repositorio_editorial,
    crear_repositorio_genero,
    crear_repositorio_libro,
    crear_repositorio_moneda,
    crear_repositorio_precio,
    crear_repositorio_tipo_cotizacion,
)

ROOT_DIR: Path = Path(__file__).resolve().parents[3]
load_dotenv(ROOT_DIR / ".env")


class ServicioLibreria:
    """Conecta la interfaz de consola con los repositorios SQL.

    Es el unico lugar donde se arma el grafo de repositorios, de modo que
    cada servicio use el repositorio de persistencia correspondiente.
    """

    def __init__(self) -> None:
        """Crea y conecta los repositorios necesarios para el servicio."""
        self.repo_generos = crear_repositorio_genero()
        self.repo_editoriales = crear_repositorio_editorial()
        self.repo_autores = crear_repositorio_autor()
        self.repo_monedas = crear_repositorio_moneda()
        self.repo_tipo_cot = crear_repositorio_tipo_cotizacion()
        self.repo_precios = crear_repositorio_precio()
        self.repo_libros = crear_repositorio_libro()
        self.repo_stock = SQLRepositorioStock()
        self.repo_cotizaciones = SQLRepositorioCotizacion()
        self.servicio_cotizaciones = ServicioCotizacionDolar(
            self.repo_tipo_cot,
            self.repo_cotizaciones,
        )

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

    def obtener_precios_bimonetarios(
        self,
        tipo_dolar_id: int,
    ) -> list[tuple[Libro, float | None, float | None]]:
        """Devuelve los precios ARS/USD o None si la moneda no se convierte."""
        if self.repo_tipo_cot.leer_por_id(tipo_dolar_id) is None:
            raise ValueError("El tipo de cotizacion no existe.")

        libros = self.repo_libros.leer_todos()
        necesita_cotizacion = any(
            libro.precio.moneda.nombre == "USD" for libro in libros
        )
        valor_cotizacion: float | None = None
        if necesita_cotizacion:
            historico = self.repo_cotizaciones.leer_historico_por_tipo(
                tipo_dolar_id
            )
            if not historico:
                raise ValueError(
                    "No hay cotizaciones cargadas para hacer la conversión."
                )
            ultima = max(historico, key=lambda registro: registro.fecha)
            valor_cotizacion = ultima.valor

        precios: list[tuple[Libro, float | None, float | None]] = []
        for libro in libros:
            precio = libro.precio
            moneda = precio.moneda.nombre
            if moneda == "ARS":
                precio_ars = precio.valor
                precio_usd = (
                    precio.valor / valor_cotizacion
                    if valor_cotizacion is not None
                    else None
                )
            elif moneda == "USD":
                precio_usd = precio.valor
                if valor_cotizacion is None:
                    raise ValueError(
                        "No hay cotización disponible para convertir USD."
                    )
                precio_ars = precio.valor * valor_cotizacion
            else:
                precio_ars = None
                precio_usd = None
            precios.append((libro, precio_ars, precio_usd))

        return precios

    def obtener_precios_para_exportacion(
        self,
        tipo_dolar_id: int | None = None,
    ) -> list[tuple[Libro, float | None]]:
        """Devuelve el precio original y su equivalente ARS cuando aplica."""
        libros = self.repo_libros.leer_todos()
        necesita_cotizacion = any(
            libro.precio.moneda.nombre == "USD" for libro in libros
        )
        valor_cotizacion: float | None = None

        if necesita_cotizacion:
            if tipo_dolar_id is None:
                raise ValueError(
                    "Debe seleccionar un tipo de cotización "
                    "para convertir USD."
                )
            if self.repo_tipo_cot.leer_por_id(tipo_dolar_id) is None:
                raise ValueError("El tipo de cotizacion no existe.")
            historico = self.repo_cotizaciones.leer_historico_por_tipo(
                tipo_dolar_id
            )
            if not historico:
                raise ValueError(
                    "No hay cotizaciones cargadas para hacer la conversión."
                )
            valor_cotizacion = max(
                historico,
                key=lambda registro: registro.fecha,
            ).valor

        precios: list[tuple[Libro, float | None]] = []
        for libro in libros:
            precio = libro.precio
            moneda = precio.moneda.nombre
            if moneda == "ARS":
                equivalente_ars: float | None = precio.valor
            elif moneda == "USD":
                if valor_cotizacion is None:
                    raise ValueError(
                        "No hay cotización disponible para convertir USD."
                    )
                equivalente_ars = precio.valor * valor_cotizacion
            else:
                equivalente_ars = None
            precios.append((libro, equivalente_ars))

        return precios

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


class ServicioCotizacionDolar:
    """Obtiene y registra cotizaciones desde DolarApi."""

    _CASAS_A_TIPOS: dict[str, str] = {
        "oficial": "oficial",
        "blue": "blue",
        "bolsa": "mep",
        "contadoconliqui": "ccl",
        "mayorista": "mayorista",
        "cripto": "cripto",
        "tarjeta": "tarjeta",
    }

    def __init__(
        self,
        repositorio_tipos: SQLRepositorioBase[TipoCotizacion],
        repositorio_cotizaciones: SQLRepositorioCotizacion,
        api_url: str | None = None,
        solicitar: Callable[..., requests.Response] = requests.get,
    ) -> None:
        """Configura los repositorios y el acceso HTTP a la API."""
        self.__repositorio_tipos = repositorio_tipos
        self.__repositorio_cotizaciones = repositorio_cotizaciones
        self.__api_url = api_url or os.getenv("API_URL")
        if not self.__api_url:
            raise RuntimeError(
                "No se configuró API_URL. Defínala en el archivo .env."
            )
        self.__solicitar = solicitar

    def obtener_cotizaciones(self) -> list[CotizacionDolar]:
        """Descarga el precio de venta y lo guarda para la fecha actual."""
        try:
            respuesta = self.__solicitar(self.__api_url, timeout=15)
            respuesta.raise_for_status()
        except requests.RequestException as error:
            raise RuntimeError(
                f"No se pudieron obtener cotizaciones desde {self.__api_url}."
            ) from error

        try:
            datos = respuesta.json()
        except ValueError as error:
            raise RuntimeError(
                "La API devolvió una respuesta JSON inválida."
            ) from error

        if not isinstance(datos, list):
            raise ValueError("La respuesta de la API debe ser una lista.")

        tipos = {
            tipo.nombre.casefold(): tipo
            for tipo in self.__repositorio_tipos.leer_todos()
        }
        fecha_actual = date.today()
        cotizaciones: list[CotizacionDolar] = []
        claves_procesadas: set[int] = set()

        for indice, elemento in enumerate(datos, start=1):
            if not isinstance(elemento, dict):
                raise ValueError(
                    f"El registro {indice} de la API no es un objeto."
                )

            casa = elemento.get("casa")
            if not isinstance(casa, str):
                raise ValueError(
                    f"El registro {indice} de la API no contiene una casa."
                )

            nombre_tipo = self._CASAS_A_TIPOS.get(casa.casefold())
            if nombre_tipo is None:
                continue

            tipo = tipos.get(nombre_tipo)
            if tipo is None:
                raise ValueError(
                    f"No está registrado el tipo de cotización "
                    f"'{nombre_tipo}'."
                )
            if tipo.id in claves_procesadas:
                raise ValueError(
                    f"La API devolvió más de una cotización para "
                    f"'{tipo.nombre}'."
                )

            venta = elemento.get("venta")
            if (
                isinstance(venta, bool)
                or not isinstance(venta, (int, float))
                or not math.isfinite(venta)
                or venta <= 0
            ):
                raise ValueError(
                    f"La cotización de venta del registro {indice} "
                    "no es un número positivo válido."
                )

            cotizaciones.append(
                CotizacionDolar(tipo, fecha_actual, float(venta))
            )
            claves_procesadas.add(tipo.id)

        if not cotizaciones:
            raise ValueError(
                "La API no devolvió cotizaciones compatibles con el sistema."
            )

        return self.__repositorio_cotizaciones.guardar_o_actualizar_lote(
            cotizaciones
        )
