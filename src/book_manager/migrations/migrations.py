"""Migración de los datos CSV del TP1 a PostgreSQL."""

import csv
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Callable

from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Session

from book_manager.database.connection import get_db_session, get_engine
from book_manager.models.models import (
    Autor,
    Base,
    CotizacionDolar,
    Editorial,
    Genero,
    Libro,
    Moneda,
    Precio,
    Stock,
    TipoCotizacion,
)

RegistroCsv = dict[str, str]
DatosModelo = dict[str, Any]
Conversor = Callable[[RegistroCsv], DatosModelo]


@dataclass(frozen=True)
class _DefinicionMigracion:
    """Describe el CSV, modelo ORM y clave primaria de una entidad."""

    archivo: str
    modelo: type[Base]
    columnas: tuple[str, ...]
    clave_primaria: tuple[str, ...]
    convertir: Conversor


def _convertir_nombrada(fila: RegistroCsv) -> DatosModelo:
    return {"id": int(fila["id"]), "nombre": fila["nombre"]}


def _convertir_moneda(fila: RegistroCsv) -> DatosModelo:
    return {
        "id": int(fila["id"]),
        "nombre": fila["nombre"],
        "simbolo": fila["simbolo"],
    }


def _convertir_precio(fila: RegistroCsv) -> DatosModelo:
    return {
        "id": int(fila["id"]),
        "valor": float(fila["valor"]),
        "moneda_id": int(fila["moneda_id"]),
    }


def _convertir_libro(fila: RegistroCsv) -> DatosModelo:
    return {
        "id": int(fila["id"]),
        "isbn": fila["isbn"],
        "titulo": fila["titulo"],
        "autor_id": int(fila["autor_id"]),
        "editorial_id": int(fila["editorial_id"]),
        "genero_id": int(fila["genero_id"]),
        "precio_id": int(fila["precio_id"]),
    }


def _convertir_stock(fila: RegistroCsv) -> DatosModelo:
    return {
        "libro_id": int(fila["libro_id"]),
        "cantidad": int(fila["cantidad"]),
    }


def _convertir_cotizacion(fila: RegistroCsv) -> DatosModelo:
    return {
        "tipo_id": int(fila["tipo_id"]),
        "fecha": date.fromisoformat(fila["fecha"]),
        "valor": float(fila["valor"]),
    }


_MIGRACIONES = (
    _DefinicionMigracion(
        "autores.csv",
        Autor,
        ("id", "nombre"),
        ("id",),
        _convertir_nombrada,
    ),
    _DefinicionMigracion(
        "editoriales.csv",
        Editorial,
        ("id", "nombre"),
        ("id",),
        _convertir_nombrada,
    ),
    _DefinicionMigracion(
        "generos.csv",
        Genero,
        ("id", "nombre"),
        ("id",),
        _convertir_nombrada,
    ),
    _DefinicionMigracion(
        "monedas.csv",
        Moneda,
        ("id", "nombre", "simbolo"),
        ("id",),
        _convertir_moneda,
    ),
    _DefinicionMigracion(
        "tipo_cotizacion.csv",
        TipoCotizacion,
        ("id", "nombre"),
        ("id",),
        _convertir_nombrada,
    ),
    _DefinicionMigracion(
        "precios.csv",
        Precio,
        ("id", "valor", "moneda_id"),
        ("id",),
        _convertir_precio,
    ),
    _DefinicionMigracion(
        "libros.csv",
        Libro,
        (
            "id",
            "isbn",
            "titulo",
            "autor_id",
            "editorial_id",
            "genero_id",
            "precio_id",
        ),
        ("id",),
        _convertir_libro,
    ),
    _DefinicionMigracion(
        "stock.csv",
        Stock,
        ("libro_id", "cantidad"),
        ("libro_id",),
        _convertir_stock,
    ),
    _DefinicionMigracion(
        "cotizaciones.csv",
        CotizacionDolar,
        ("tipo_id", "fecha", "valor"),
        ("tipo_id", "fecha"),
        _convertir_cotizacion,
    ),
)


def _leer_csv(
    carpeta_csvs: Path,
    definicion: _DefinicionMigracion,
) -> list[DatosModelo]:
    """Lee un archivo CSV, valida sus columnas y convierte sus registros."""
    ruta = carpeta_csvs / definicion.archivo
    if not ruta.is_file():
        raise FileNotFoundError(f"No se encontró el archivo CSV: {ruta}")

    with ruta.open(newline="", encoding="utf-8-sig") as archivo:
        lector = csv.DictReader(archivo)
        if tuple(lector.fieldnames or ()) != definicion.columnas:
            raise ValueError(
                f"Encabezado inválido en {ruta}; "
                f"se esperaba: {', '.join(definicion.columnas)}."
            )

        registros: list[DatosModelo] = []
        for numero_fila, fila in enumerate(lector, start=2):
            if None in fila or any(valor is None for valor in fila.values()):
                raise ValueError(
                    f"La fila {numero_fila} de {ruta} tiene "
                    "una cantidad de columnas incorrecta."
                )
            try:
                registros.append(definicion.convertir(fila))
            except (KeyError, TypeError, ValueError) as error:
                raise ValueError(
                    f"Registro inválido en {ruta}, fila {numero_fila}: "
                    f"{error}"
                ) from error

    return registros


def _generar_sentencias(
    definicion: _DefinicionMigracion,
    registros: list[DatosModelo],
) -> str:
    """Genera INSERT idempotentes compatibles con PostgreSQL."""
    sentencias: list[str] = []
    claves_ya_generadas: set[tuple[Any, ...]] = set()

    for registro in registros:
        clave = tuple(
            registro[columna] for columna in definicion.clave_primaria
        )
        if clave in claves_ya_generadas:
            continue
        claves_ya_generadas.add(clave)

        columnas_clave = [
            getattr(definicion.modelo, columna)
            for columna in definicion.clave_primaria
        ]
        sentencia = (
            postgresql.insert(definicion.modelo)
            .values(**registro)
            .on_conflict_do_nothing(index_elements=columnas_clave)
        )
        sentencia_sql = sentencia.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": True},
        )
        sentencias.append(f"{sentencia_sql};")

    return "\n".join(sentencias) + ("\n" if sentencias else "")


def _insertar_registros(
    sesion: Session,
    definicion: _DefinicionMigracion,
    registros: list[DatosModelo],
) -> None:
    """Inserta solo claves que aún no existen y evita duplicados del CSV."""
    claves_vistas: set[tuple[Any, ...]] = set()
    for registro in registros:
        clave = tuple(
            registro[columna] for columna in definicion.clave_primaria
        )
        if clave in claves_vistas:
            continue
        claves_vistas.add(clave)

        clave_sesion: Any = clave[0] if len(clave) == 1 else clave
        if sesion.get(definicion.modelo, clave_sesion) is None:
            sesion.add(definicion.modelo(**registro))

    sesion.flush()


def migrar_datos(carpeta_csvs: str, carpeta_sqls: str) -> None:
    """Migra los CSV del TP1 y genera archivos SQL idempotentes.

    Args:
        carpeta_csvs: Directorio que contiene los archivos CSV de origen.
        carpeta_sqls: Directorio donde se guardarán las sentencias SQL.
    """
    ruta_csvs = Path(carpeta_csvs)
    ruta_sqls = Path(carpeta_sqls)
    datos = [
        (definicion, _leer_csv(ruta_csvs, definicion))
        for definicion in _MIGRACIONES
    ]

    ruta_sqls.mkdir(parents=True, exist_ok=True)
    for definicion, registros in datos:
        contenido_sql = _generar_sentencias(definicion, registros)
        (ruta_sqls / f"{definicion.modelo.__tablename__}.sql").write_text(
            contenido_sql,
            encoding="utf-8",
        )

    Base.metadata.create_all(bind=get_engine())
    with get_db_session() as sesion:
        for definicion, registros in datos:
            _insertar_registros(sesion, definicion, registros)

    print(
        f"Migración completada: {sum(len(registros) for _, registros in datos)} "
        f"registros CSV revisados; archivos SQL generados en {ruta_sqls}."
    )
