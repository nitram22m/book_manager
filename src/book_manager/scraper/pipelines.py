"""Pipelines de validación, normalización y persistencia de Scrapy."""

from datetime import datetime, timezone
import logging
from math import isfinite
import re

from scrapy import Item, Spider

from book_manager.repositories.scraped_repository import (
    SQLRepositorioLibroScrapeado,
)
from book_manager.scraper.items import BookItem

LOGGER = logging.getLogger(__name__)
PRECIO_RE = re.compile(
    r"(U\$S|£|\$)?\s*([\d.,]+)",
    re.IGNORECASE,
)


class LogPipeline:
    """Registra el ingreso y finalización del procesamiento de cada libro."""

    def process_item(self, item: Item, spider: Spider) -> Item:
        """Registra el título de entrada y confirma su paso por el pipeline."""
        LOGGER.info(
            "Ingreso de item: título=%s, estado=recibido, spider=%s",
            item.get("titulo", ""),
            spider.name,
        )
        return item


class FixDataPipeline:
    """Normaliza precio, moneda, disponibilidad y fecha de observación."""

    def process_item(self, item: BookItem, spider: Spider) -> BookItem:
        """Convierte los campos extraídos a los tipos de dominio esperados."""
        precio_crudo = item.get("precio")
        if not isinstance(precio_crudo, str):
            raise ValueError("El precio scrapeado debe ser una cadena.")
        coincidencias = list(PRECIO_RE.finditer(precio_crudo))
        if not coincidencias:
            raise ValueError(
                f"No se pudo interpretar el precio: {precio_crudo!r}."
            )

        coincidencia = coincidencias[-1]
        simbolo, valor_crudo = coincidencia.groups()
        item["precio"] = self._parsear_importe(valor_crudo)
        item["moneda"] = (
            self._codigo_moneda(simbolo)
            if simbolo is not None
            else "ARS"
        )
        item["disponibilidad_stock"] = self._parsear_stock(
            str(item.get("disponibilidad_stock", ""))
        )
        item["fecha_actualizacion"] = datetime.now(timezone.utc)
        LOGGER.debug("Datos normalizados por el spider %s", spider.name)
        return item

    @staticmethod
    def _parsear_importe(valor: str) -> float:
        """Interpreta importes argentinos y decimales con punto."""
        importe = valor.strip()
        if "," in importe and "." in importe:
            if importe.rfind(",") > importe.rfind("."):
                importe = importe.replace(".", "").replace(",", ".")
            else:
                importe = importe.replace(",", "")
        elif "," in importe:
            importe = importe.replace(".", "").replace(",", ".")
        elif re.fullmatch(r"\d{1,3}(?:\.\d{3})+", importe):
            importe = importe.replace(".", "")

        numero = float(importe)
        if not isfinite(numero) or numero <= 0:
            raise ValueError(
                "El precio scrapeado debe ser un número finito positivo."
            )
        return numero

    @staticmethod
    def _codigo_moneda(simbolo: str) -> str:
        """Convierte el símbolo monetario en un código de moneda."""
        simbolo_normalizado = simbolo.upper()
        monedas = {"U$S": "USD", "$": "ARS", "£": "GBP"}
        try:
            return monedas[simbolo_normalizado]
        except KeyError as error:
            raise ValueError(
                f"Símbolo monetario no soportado: {simbolo}."
            ) from error

    @staticmethod
    def _parsear_stock(disponibilidad: str) -> int:
        """Extrae existencias numéricas o reconoce publicaciones agotadas."""
        texto = " ".join(disponibilidad.casefold().split())
        if any(
            expresion in texto
            for expresion in ("sin stock", "agotado", "no disponible")
        ):
            return 0
        coincidencia = re.search(r"\d+", texto)
        return int(coincidencia.group()) if coincidencia else 0


class PersistencePipeline:
    """Actualiza las observaciones de libros en PostgreSQL/Supabase."""

    def __init__(self) -> None:
        """Crea el repositorio de publicaciones externas."""
        self.__repositorio = SQLRepositorioLibroScrapeado()

    def open_spider(self, spider: Spider) -> None:
        """Asegura que exista la tabla antes de persistir items."""
        self.__repositorio.asegurar_esquema()
        LOGGER.info("Persistencia preparada para %s", spider.name)

    def process_item(self, item: Item, spider: Spider) -> Item:
        """Guarda o actualiza el registro usando el repositorio SQLAlchemy."""
        if not isinstance(item, BookItem):
            raise TypeError("PersistencePipeline requiere un BookItem.")
        self.__repositorio.guardar_o_actualizar(item)
        LOGGER.info(
            "Libro persistido por %s: %s",
            spider.name,
            item.get("titulo", ""),
        )
        return item

    def close_spider(self, spider: Spider) -> None:
        """Registra el cierre ordenado del pipeline de persistencia."""
        LOGGER.info("Persistencia finalizada para %s", spider.name)
