"""Items de Scrapy utilizados para representar libros de Cúspide."""

import scrapy


class BookItem(scrapy.Item):
    """Datos normalizados de una publicación de libros."""

    titulo = scrapy.Field()
    precio = scrapy.Field()
    moneda = scrapy.Field()
    disponibilidad_stock = scrapy.Field()
    descripcion = scrapy.Field()
    url_imagen = scrapy.Field()
    formas_pago = scrapy.Field()
    fecha_actualizacion = scrapy.Field()
    url = scrapy.Field()
