"""Persistencia SQLAlchemy de observaciones de libros de Cúspide."""

from datetime import datetime
import json
from math import isfinite

from sqlalchemy import Table, inspect, select

from book_manager.database.connection import get_db_session, get_engine
from book_manager.models.models import LibroScrapeado
from book_manager.scraper.items import BookItem
from book_manager.services.auditoria import auditar_operacion


class SQLRepositorioLibroScrapeado:
    """Guarda la última observación conocida de cada publicación externa."""

    @auditar_operacion
    def asegurar_esquema(self) -> None:
        """Crea o amplía la tabla de scraping para la estructura vigente."""
        engine = get_engine()
        tabla = LibroScrapeado.__table__
        if not isinstance(tabla, Table):
            raise TypeError("El modelo scrapeado no define una tabla SQL.")
        tabla.metadata.create_all(
            bind=engine,
            tables=[tabla],
            checkfirst=True,
        )
        columnas = {
            columna["name"]
            for columna in inspect(engine).get_columns(
                LibroScrapeado.__tablename__
            )
        }
        migraciones = {
            "url_imagen": (
                "VARCHAR(2048) NOT NULL DEFAULT ''"
            ),
            "formas_pago": "TEXT NOT NULL DEFAULT '[]'",
        }
        with engine.begin() as conexion:
            for nombre, tipo in migraciones.items():
                if nombre not in columnas:
                    conexion.exec_driver_sql(
                        f"ALTER TABLE libros_scrapeados "
                        f"ADD COLUMN {nombre} {tipo}"
                    )

    @auditar_operacion
    def guardar_o_actualizar(self, item: BookItem) -> None:
        """Inserta o actualiza la observación identificada por URL."""
        valores = self._validar_item(item)
        with get_db_session() as sesion:
            registro = sesion.scalar(
                select(LibroScrapeado).where(
                    LibroScrapeado.url == valores["url"]
                )
            )
            if registro is None:
                registro = LibroScrapeado(**valores)
                sesion.add(registro)
            else:
                for nombre, valor in valores.items():
                    setattr(registro, nombre, valor)
            sesion.flush()

    @auditar_operacion
    def leer_todos(self) -> list[dict[str, object]]:
        """Devuelve las observaciones más recientes ordenadas por fecha."""
        with get_db_session() as sesion:
            registros = sesion.scalars(
                select(LibroScrapeado).order_by(
                    LibroScrapeado.fecha_actualizacion.desc(),
                    LibroScrapeado.id.desc(),
                )
            ).all()
            return [
                {
                    "titulo": registro.titulo,
                    "precio": registro.precio,
                    "moneda": registro.moneda,
                    "disponibilidad_stock": registro.disponibilidad_stock,
                    "url": registro.url,
                    "fecha_actualizacion": (
                        registro.fecha_actualizacion.isoformat()
                    ),
                }
                for registro in registros
            ]

    @staticmethod
    def _validar_item(item: BookItem) -> dict[str, object]:
        """Valida y convierte los campos requeridos antes de persistirlos."""
        url = item.get("url")
        titulo = item.get("titulo")
        moneda = item.get("moneda")
        descripcion = item.get("descripcion", "")
        url_imagen = item.get("url_imagen", "")
        formas_pago = item.get("formas_pago", [])
        precio = item.get("precio")
        stock = item.get("disponibilidad_stock")
        fecha = item.get("fecha_actualizacion")

        if not isinstance(url, str) or not url.strip():
            raise ValueError("El libro scrapeado debe tener una URL válida.")
        if not isinstance(titulo, str) or not titulo.strip():
            raise ValueError("El libro scrapeado debe tener un título.")
        if not isinstance(moneda, str) or not moneda.strip():
            raise ValueError("El libro scrapeado debe tener una moneda.")
        if not isinstance(descripcion, str):
            raise ValueError("La descripción scrapeada debe ser texto.")
        if not isinstance(url_imagen, str):
            raise ValueError("La URL de imagen scrapeada debe ser texto.")
        if not SQLRepositorioLibroScrapeado._formas_pago_validas(
            formas_pago
        ):
            raise ValueError("Las formas de pago scrapeadas no son válidas.")
        if (
            isinstance(precio, bool)
            or not isinstance(precio, (int, float))
            or not isfinite(precio)
            or precio <= 0
        ):
            raise ValueError(
                "El precio scrapeado debe ser un número positivo."
            )
        if (
            isinstance(stock, bool)
            or not isinstance(stock, int)
            or stock < 0
        ):
            raise ValueError(
                "El stock scrapeado debe ser un entero no negativo."
            )
        if not isinstance(fecha, datetime):
            raise ValueError(
                "La fecha de actualización debe ser un objeto datetime."
            )

        return {
            "url": url.strip(),
            "titulo": titulo.strip(),
            "precio": float(precio),
            "moneda": moneda.strip(),
            "disponibilidad_stock": stock,
            "descripcion": descripcion.strip(),
            "url_imagen": url_imagen.strip(),
            "formas_pago": json.dumps(
                formas_pago,
                ensure_ascii=False,
            ),
            "fecha_actualizacion": fecha,
        }

    @staticmethod
    def _formas_pago_validas(formas_pago: object) -> bool:
        """Comprueba la estructura y los importes de las formas de pago."""
        if not isinstance(formas_pago, list):
            return False
        for forma in formas_pago:
            if not isinstance(forma, dict):
                return False
            descripcion = forma.get("descripcion")
            moneda = forma.get("moneda", "ARS")
            precio = forma.get("precio")
            if not isinstance(descripcion, str) or not isinstance(moneda, str):
                return False
            if precio is not None and (
                isinstance(precio, bool)
                or not isinstance(precio, (int, float))
                or not isfinite(precio)
                or precio <= 0
            ):
                return False
        return True
