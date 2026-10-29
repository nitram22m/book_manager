"""Spider de catálogo público de Cúspide."""

from collections.abc import AsyncIterator, Iterator
import json
import re
from typing import Any
from urllib.parse import urlencode

import scrapy
from parsel import Selector
from scrapy.http import Request, Response

from book_manager.scraper.items import BookItem
from book_manager.scraper.loaders import BookItemLoader


class CuspideSpider(scrapy.Spider):
    """Busca publicaciones en Cúspide y extrae hasta diez libros."""

    name = "cuspide_spider"
    allowed_domains = ["cuspide.com", "www.cuspide.com"]
    start_urls = ["https://cuspide.com/"]

    def __init__(
        self,
        query: str = "",
        max_items: str = "10",
        name: str | None = None,
        queries: str = "",
        **kwargs: Any,
    ) -> None:
        """Configura la búsqueda y el límite de resultados por ejecución."""
        super().__init__(name=name, **kwargs)
        if queries:
            try:
                consultas = json.loads(queries)
            except json.JSONDecodeError as error:
                raise ValueError(
                    "queries debe ser una lista JSON de títulos."
                ) from error
            if (
                not isinstance(consultas, list)
                or any(
                    not isinstance(consulta, str) or not consulta.strip()
                    for consulta in consultas
                )
            ):
                raise ValueError(
                    "queries debe contener únicamente títulos no vacíos."
                )
            self.__consultas = [consulta.strip() for consulta in consultas]
        else:
            consulta = query.strip()
            self.__consultas = [consulta]
        try:
            limite = int(max_items)
        except ValueError as error:
            raise ValueError(
                "max_items debe ser un entero positivo."
            ) from error
        if limite < 1:
            raise ValueError("max_items debe ser un entero positivo.")
        self.__max_items = min(limite, 10)
        self.__items_procesados: dict[str, int] = {}
        self.__urls_procesadas: set[str] = set()

    def start_requests(self) -> Iterator[Request]:
        """Genera las peticiones iniciales al inicio o búsqueda de Cúspide."""
        for consulta in self.__consultas:
            url = self.start_urls[0]
            if consulta:
                query_string = urlencode(
                    {"s": consulta, "post_type": "product"}
                )
                url = f"{url}?{query_string}"
            yield scrapy.Request(
                url,
                callback=self.parse,
                meta={"search_query": consulta},
            )

    async def start(self) -> AsyncIterator[Request]:
        """Inicia el spider en Scrapy moderno usando start_requests()."""
        for request in self.start_requests():
            yield request

    def parse(self, response: Response) -> Iterator[Request]:
        """Extrae hasta diez resultados y solicita su página de detalle."""
        consulta = str(response.meta.get("search_query", ""))
        productos = response.css(
            ".products li.product, "
            "ul.products li.product, "
            ".product-small, "
            "li.product"
        )
        for producto in productos:
            cantidad = self.__items_procesados.get(consulta, 0)
            if cantidad >= self.__max_items:
                return

            titulo = self._primer_texto(
                producto,
                (
                    ".woocommerce-loop-product__title::text",
                    "h2.product-title a::text",
                    ".product-title a::text",
                    "h2 a::text",
                    "a[title]::attr(title)",
                    "img::attr(alt)",
                ),
            )
            precio = self._texto_unido(
                producto.css(
                    ".price .woocommerce-Price-amount::text, "
                    ".price::text, "
                    ".price bdi::text"
                ).getall()
            )
            if not titulo or not precio:
                self.logger.debug(
                    "Se omite un producto sin título o precio en %s",
                    response.url,
                )
                continue

            url = producto.css(
                "a.woocommerce-LoopProduct-link::attr(href), "
                "a.woocommerce-loop-product__link::attr(href), "
                "a::attr(href)"
            ).get()
            if not url:
                self.logger.debug(
                    "Se omite un producto sin URL en %s",
                    response.url,
                )
                continue
            url = response.urljoin(url)
            if url in self.__urls_procesadas:
                continue
            self.__urls_procesadas.add(url)
            disponibilidad = self._primer_texto(
                producto,
                (".stock::text", ".availability::text"),
            )
            imagen = self._primer_texto(
                producto,
                (
                    "img::attr(data-large_image)",
                    "img::attr(data-src)",
                    "img::attr(data-lazy-src)",
                    "img::attr(src)",
                ),
            )

            loader = BookItemLoader(item=BookItem(), selector=producto)
            loader.add_value("titulo", titulo)
            loader.add_value("precio", precio)
            loader.add_value("disponibilidad_stock", disponibilidad or "")
            loader.add_value("descripcion", "")
            loader.add_value(
                "url_imagen",
                response.urljoin(imagen) if imagen else "",
            )
            loader.add_value("formas_pago", [])
            loader.add_value("url", url)
            item = loader.load_item()
            item["url_imagen"] = (
                response.urljoin(imagen) if imagen else ""
            )
            item["formas_pago"] = []
            self.__items_procesados[consulta] = cantidad + 1
            yield scrapy.Request(
                url,
                callback=self.parse_detail,
                meta={
                    "book_item": item,
                    "search_query": consulta,
                },
            )

        if self.__items_procesados.get(consulta, 0) < self.__max_items:
            siguiente = response.css(
                "a.next.page-numbers::attr(href), "
                "a.next::attr(href)"
            ).get()
            if siguiente:
                yield scrapy.Request(
                    response.urljoin(siguiente),
                    callback=self.parse,
                    meta={"search_query": consulta},
                )

    def parse_detail(self, response: Response) -> Iterator[BookItem]:
        """Obtiene descripción, imagen y formas de pago del producto."""
        item = response.meta.get("book_item")
        if not isinstance(item, BookItem):
            raise TypeError(
                "La respuesta de detalle no contiene un BookItem válido."
            )

        productos = self._productos_jsonld(response)
        descripcion = self._primer_texto(
            response,
            (
                ".woocommerce-product-details__short-description ::text",
                "#tab-description ::text",
                ".woocommerce-Tabs-panel--description ::text",
                "[itemprop='description']::text",
                ".entry-summary .product-description ::text",
            ),
        )
        if not descripcion:
            descripcion = next(
                (
                    str(producto["description"]).strip()
                    for producto in productos
                    if isinstance(producto.get("description"), str)
                    and producto["description"].strip()
                ),
                "",
            )

        imagen = self._primer_texto(
            response,
            (
                ".woocommerce-product-gallery__image "
                "a::attr(href)",
                ".woocommerce-product-gallery__image img"
                "::attr(data-large_image)",
                ".woocommerce-product-gallery__image img::attr(src)",
                "img.wp-post-image::attr(src)",
                "[itemprop='image']::attr(src)",
            ),
        )
        if not imagen:
            imagen = self._imagen_jsonld(productos)

        pagos = self._extraer_formas_pago(response)
        loader = BookItemLoader(item=item, response=response)
        if descripcion:
            loader.replace_value("descripcion", descripcion)
        if imagen:
            loader.replace_value("url_imagen", response.urljoin(imagen))
        item_procesado = loader.load_item()
        item_procesado["url_imagen"] = (
            response.urljoin(imagen) if imagen else item.get("url_imagen", "")
        )
        item_procesado["formas_pago"] = pagos
        yield item_procesado

    @staticmethod
    def _productos_jsonld(response: Response) -> list[dict[str, Any]]:
        """Extrae los objetos Product de bloques JSON-LD estructurados."""
        productos: list[dict[str, Any]] = []
        for contenido in response.css(
            "script[type='application/ld+json']::text"
        ).getall():
            try:
                datos = json.loads(contenido)
            except json.JSONDecodeError:
                continue
            productos.extend(CuspideSpider._buscar_productos_jsonld(datos))
        return productos

    @staticmethod
    def _buscar_productos_jsonld(datos: Any) -> list[dict[str, Any]]:
        """Busca recursivamente nodos Product en grafos JSON-LD."""
        if isinstance(datos, list):
            return [
                producto
                for elemento in datos
                for producto in CuspideSpider._buscar_productos_jsonld(
                    elemento
                )
            ]
        if not isinstance(datos, dict):
            return []

        tipo = datos.get("@type")
        es_producto = (
            tipo == "Product"
            or isinstance(tipo, list)
            and "Product" in tipo
        )
        productos = [datos] if es_producto else []
        for valor in datos.values():
            if isinstance(valor, (dict, list)):
                productos.extend(
                    CuspideSpider._buscar_productos_jsonld(valor)
                )
        return productos

    @staticmethod
    def _imagen_jsonld(
        productos: list[dict[str, Any]],
    ) -> str:
        """Obtiene la primera URL de imagen disponible en JSON-LD."""
        for producto in productos:
            imagen = producto.get("image")
            if isinstance(imagen, str) and imagen.strip():
                return imagen.strip()
            if isinstance(imagen, list):
                for elemento in imagen:
                    if isinstance(elemento, str) and elemento.strip():
                        return elemento.strip()
                    if (
                        isinstance(elemento, dict)
                        and isinstance(elemento.get("url"), str)
                    ):
                        return elemento["url"].strip()
            if isinstance(imagen, dict) and isinstance(
                imagen.get("url"),
                str,
            ):
                return imagen["url"].strip()
        return ""

    @staticmethod
    def _extraer_formas_pago(response: Response) -> list[dict[str, Any]]:
        """Extrae textos de financiación y el importe publicado por opción."""
        selectores = response.css(
            "li, p, [class*='cuota'], [class*='pago'], "
            "[class*='payment'], [class*='installment'], "
            ".woocommerce-Tabs-panel--additional_information"
        )
        bloques: set[str] = set()
        for selector in selectores:
            texto = CuspideSpider._texto_unido(
                selector.xpath(".//text()").getall()
            )
            if texto:
                bloques.add(texto)

        formas: list[dict[str, Any]] = []
        vistos: set[str] = set()
        for bloque in sorted(bloques):
            normalizado = " ".join(bloque.split())
            clave = normalizado.casefold()
            if (
                clave in vistos
                or clave in {"medios de pago", "formas de pago"}
                or not any(
                    palabra in clave
                    for palabra in (
                        "cuota",
                        "tarjetas de ",
                        "visa",
                        "mastercard",
                        "american express",
                        "transferencia bancaria",
                        "cuenta bancaria",
                        "deposito bancario",
                        "depósito bancario",
                        "mercadopago",
                        "mercado pago",
                        "rapipago",
                        "pago facil",
                        "pago fácil",
                        "payu",
                        "mobbex",
                        "efectivo",
                    )
                )
            ):
                continue
            vistos.add(clave)
            coincidencia = re.search(
                r"(U\$S|£|\$)\s*([\d.,]+)"
                r"|\b(?:de|por)\s+([\d.]+(?:,\d{2})?)",
                normalizado,
                re.IGNORECASE,
            )
            precio: float | None = None
            moneda = "ARS"
            if coincidencia is not None:
                simbolo, importe_con_simbolo, importe_sin_simbolo = (
                    coincidencia.groups()
                )
                importe = importe_con_simbolo or importe_sin_simbolo
                if importe:
                    precio = CuspideSpider._parsear_precio_pago(importe)
                if simbolo:
                    moneda = {
                        "U$S": "USD",
                        "£": "GBP",
                        "$": "ARS",
                    }[simbolo.upper()]
            formas.append(
                {
                    "descripcion": normalizado,
                    "precio": precio,
                    "moneda": moneda,
                }
            )
        return formas

    @staticmethod
    def _parsear_precio_pago(importe: str) -> float:
        """Convierte una cuota monetaria a un número decimal."""
        valor = importe.strip()
        if "," in valor:
            valor = valor.replace(".", "").replace(",", ".")
        elif re.fullmatch(r"\d{1,3}(?:\.\d{3})+", valor):
            valor = valor.replace(".", "")
        return float(valor)

    @staticmethod
    def _primer_texto(
        selector: Selector | Response,
        selectores: tuple[str, ...],
    ) -> str:
        """Devuelve el primer valor no vacío de una lista de selectores."""
        for expresion in selectores:
            valores = selector.css(expresion).getall()
            valor = " ".join(" ".join(valores).split())
            if valor:
                return valor
        return ""

    @staticmethod
    def _texto_unido(valores: list[str]) -> str:
        """Combina los fragmentos de texto eliminando espacios redundantes."""
        return " ".join(" ".join(valores).split())


def __getattr__(nombre: str) -> Any:
    """Conserva el nombre histórico sin registrar un spider duplicado."""
    if nombre == "CuspideBookSpider":
        return CuspideSpider
    raise AttributeError(f"El módulo {__name__!r} no define {nombre!r}.")
