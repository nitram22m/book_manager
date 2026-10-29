"""Cargadores y procesadores de datos para los libros scrapeados."""

import re
from itemloaders import ItemLoader
from itemloaders.processors import MapCompose, TakeFirst

from book_manager.scraper.items import BookItem


def limpiar_espacios(valor: str) -> str:
    """Elimina saltos y compacta espacios en un fragmento extraído."""
    return re.sub(r"\s+", " ", str(valor)).strip()


def transformar_titulo(valor: str) -> str:
    """Normaliza el título conservando una presentación legible."""
    return limpiar_espacios(valor).title()


class BookItemLoader(ItemLoader):
    """Aplica limpieza consistente al cargar campos de un BookItem."""

    default_item_class = BookItem
    default_output_processor = TakeFirst()

    titulo_in = MapCompose(limpiar_espacios, transformar_titulo)
    precio_in = MapCompose(limpiar_espacios)
    moneda_in = MapCompose(limpiar_espacios)
    disponibilidad_stock_in = MapCompose(limpiar_espacios)
    descripcion_in = MapCompose(limpiar_espacios)
    url_imagen_in = MapCompose(limpiar_espacios)
    url_in = MapCompose(limpiar_espacios)
