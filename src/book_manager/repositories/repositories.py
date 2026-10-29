"""Repositorios CRUD para las entidades persistidas en PostgreSQL."""

import abc
from datetime import date
from typing import Any, Callable, Generic, TypeVar

from sqlalchemy import Table, select
from sqlalchemy.exc import IntegrityError

from book_manager.database.connection import get_db_session, get_engine
from book_manager.entities.entities import (
    Autor as EntidadAutor,
    CotizacionDolar as EntidadCotizacion,
    Editorial as EntidadEditorial,
    EntidadBase,
    Genero as EntidadGenero,
    Libro as EntidadLibro,
    Moneda as EntidadMoneda,
    Precio as EntidadPrecio,
    Stock as EntidadStock,
    TipoCotizacion as EntidadTipoCotizacion,
)
from book_manager.services.auditoria import auditar_operacion
from book_manager.models.models import (
    Autor,
    Auditoria,
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

T = TypeVar("T")
TEntidad = TypeVar("TEntidad", bound=EntidadBase)
ConvertirEntidad = Callable[[Any], T]
ConvertirValores = Callable[[T], dict[str, Any]]


class IRepositorio(abc.ABC, Generic[TEntidad]):
    """Contrato CRUD para entidades identificadas por un id entero."""

    @abc.abstractmethod
    def crear(self, entidad: TEntidad) -> TEntidad:
        """Persiste una entidad nueva."""

    @abc.abstractmethod
    def leer_por_id(self, id: int) -> TEntidad | None:
        """Devuelve la entidad con ese id o None."""

    @abc.abstractmethod
    def leer_todos(self) -> list[TEntidad]:
        """Devuelve todas las entidades."""

    @abc.abstractmethod
    def actualizar(self, entidad: TEntidad) -> TEntidad:
        """Reemplaza la entidad existente con el mismo id."""

    @abc.abstractmethod
    def eliminar(self, id: int) -> bool:
        """Elimina la entidad; devuelve False si no existía."""


class IRepositorioStock(abc.ABC):
    """Contrato CRUD para Stock, identificado por libro_id."""

    @abc.abstractmethod
    def crear(self, stock: EntidadStock) -> EntidadStock:
        """Persiste un stock nuevo."""

    @abc.abstractmethod
    def leer_por_libro(self, libro_id: int) -> EntidadStock | None:
        """Devuelve el stock del libro o None."""

    @abc.abstractmethod
    def actualizar(self, stock: EntidadStock) -> EntidadStock:
        """Reemplaza el stock existente del mismo libro."""

    @abc.abstractmethod
    def eliminar(self, libro_id: int) -> bool:
        """Elimina el stock del libro; devuelve False si no existía."""


class IRepositorioCotizacionDolar(abc.ABC):
    """Contrato CRUD para cotizaciones con clave tipo_id y fecha."""

    @abc.abstractmethod
    def crear(
        self, cotizacion: EntidadCotizacion
    ) -> EntidadCotizacion:
        """Persiste una cotización nueva."""

    @abc.abstractmethod
    def leer_por_tipo_y_fecha(
        self, tipo_id: int, fecha: date
    ) -> EntidadCotizacion | None:
        """Devuelve la cotización de ese tipo y fecha o None."""

    @abc.abstractmethod
    def leer_historico_por_tipo(
        self, tipo_id: int
    ) -> list[EntidadCotizacion]:
        """Devuelve todas las cotizaciones de un tipo."""

    @abc.abstractmethod
    def actualizar(
        self, cotizacion: EntidadCotizacion
    ) -> EntidadCotizacion:
        """Reemplaza la cotización existente del mismo tipo y fecha."""

    @abc.abstractmethod
    def eliminar(self, tipo_id: int, fecha: date) -> bool:
        """Elimina la cotización; devuelve False si no existía."""


class SQLRepositorioBase(Generic[T]):
    """Implementa operaciones CRUD para una entidad SQLAlchemy."""

    def __init__(
        self,
        modelo: type[Base],
        clave_primaria: tuple[str, ...],
        convertir_entidad: ConvertirEntidad[T],
        convertir_valores: ConvertirValores[T],
        nombre_entidad: str,
    ) -> None:
        """Configura el modelo ORM y las conversiones del dominio."""
        self._modelo = modelo
        self._clave_primaria = clave_primaria
        self._convertir_entidad = convertir_entidad
        self._convertir_valores = convertir_valores
        self._nombre_entidad = nombre_entidad

    @auditar_operacion
    def crear(self, entidad: T) -> T:
        """Inserta la entidad y rechaza claves ya registradas."""
        valores = self._convertir_valores(entidad)
        clave = self._obtener_clave(valores)
        try:
            with get_db_session() as sesion:
                if sesion.get(self._modelo, clave) is not None:
                    raise ValueError(
                        f"Ya existe un registro de {self._nombre_entidad} "
                        f"con clave {clave}."
                    )
                sesion.add(self._modelo(**valores))
                sesion.flush()
        except IntegrityError as error:
            raise ValueError(
                f"No se pudo crear {self._nombre_entidad}; "
                "verifique sus claves y relaciones."
            ) from error
        return entidad

    @auditar_operacion
    def leer_por_id(self, id: int) -> T | None:
        """Devuelve la entidad por su identificador simple."""
        if len(self._clave_primaria) != 1:
            raise ValueError(
                f"{self._nombre_entidad} requiere una clave compuesta."
            )
        resultado = self.leer_por_clave(id)
        return resultado

    @auditar_operacion
    def leer_por_clave(self, *clave: int | date) -> T | None:
        """Busca una entidad por los valores de su clave primaria."""
        clave_primaria = self._normalizar_clave(clave)
        with get_db_session() as sesion:
            registro = sesion.get(self._modelo, clave_primaria)
            return (
                self._convertir_entidad(registro)
                if registro is not None
                else None
            )

    @auditar_operacion
    def leer_todos(self) -> list[T]:
        """Devuelve las entidades ordenadas por su clave primaria."""
        columnas = [
            getattr(self._modelo, nombre)
            for nombre in self._clave_primaria
        ]
        with get_db_session() as sesion:
            registros = sesion.scalars(
                select(self._modelo).order_by(*columnas)
            ).all()
            return [
                self._convertir_entidad(registro)
                for registro in registros
            ]

    @auditar_operacion
    def actualizar(self, entidad: T) -> T:
        """Actualiza una entidad existente conservando su clave primaria."""
        valores = self._convertir_valores(entidad)
        clave = self._obtener_clave(valores)
        try:
            with get_db_session() as sesion:
                registro = sesion.get(self._modelo, clave)
                if registro is None:
                    raise ValueError(
                        f"No se encontró {self._nombre_entidad} "
                        f"con clave {clave}."
                    )
                for nombre, valor in valores.items():
                    if nombre not in self._clave_primaria:
                        setattr(registro, nombre, valor)
                sesion.flush()
        except IntegrityError as error:
            raise ValueError(
                f"No se pudo actualizar {self._nombre_entidad}; "
                "verifique sus claves y relaciones."
            ) from error
        return entidad

    @auditar_operacion
    def eliminar(self, id: int) -> bool:
        """Elimina un registro identificado por un único id entero."""
        if len(self._clave_primaria) != 1:
            raise ValueError(
                f"{self._nombre_entidad} requiere una clave compuesta."
            )
        return self._eliminar_por_clave(id)

    def _eliminar_por_clave(self, *clave: int | date) -> bool:
        """Elimina la entidad o rechaza borrar registros relacionados."""
        clave_primaria = self._normalizar_clave(clave)
        try:
            with get_db_session() as sesion:
                registro = sesion.get(self._modelo, clave_primaria)
                if registro is None:
                    return False
                sesion.delete(registro)
                sesion.flush()
        except IntegrityError as error:
            raise ValueError(
                f"No se puede eliminar {self._nombre_entidad}: "
                "hay registros relacionados."
            ) from error
        return True

    def _obtener_clave(
        self, valores: dict[str, Any]
    ) -> int | date | tuple[int | date, ...]:
        """Extrae del diccionario de valores la clave del registro."""
        clave = tuple(valores[nombre] for nombre in self._clave_primaria)
        return clave[0] if len(clave) == 1 else clave

    def _normalizar_clave(
        self, clave: tuple[int | date, ...]
    ) -> int | date | tuple[int | date, ...]:
        """Valida y adapta la clave al formato esperado por Session.get."""
        if len(clave) != len(self._clave_primaria):
            raise ValueError(
                f"{self._nombre_entidad} requiere "
                f"{len(self._clave_primaria)} valores de clave."
            )
        return clave[0] if len(clave) == 1 else clave


class SQLRepositorioEntidad(
    SQLRepositorioBase[TEntidad],
    IRepositorio[TEntidad],
    Generic[TEntidad],
):
    """Repositorio SQL que implementa el contrato CRUD de una entidad."""


def _entidad_autor(registro: Autor) -> EntidadAutor:
    """Convierte una fila ORM de autor en entidad de dominio."""
    return EntidadAutor(registro.id, registro.nombre)


def _valores_autor(entidad: EntidadAutor) -> dict[str, Any]:
    """Obtiene las columnas persistibles de un autor."""
    return {"id": entidad.id, "nombre": entidad.nombre}


def _entidad_editorial(registro: Editorial) -> EntidadEditorial:
    """Convierte una fila ORM de editorial en entidad de dominio."""
    return EntidadEditorial(registro.id, registro.nombre)


def _valores_editorial(entidad: EntidadEditorial) -> dict[str, Any]:
    """Obtiene las columnas persistibles de una editorial."""
    return {"id": entidad.id, "nombre": entidad.nombre}


def _entidad_genero(registro: Genero) -> EntidadGenero:
    """Convierte una fila ORM de género en entidad de dominio."""
    return EntidadGenero(registro.id, registro.nombre)


def _valores_genero(entidad: EntidadGenero) -> dict[str, Any]:
    """Obtiene las columnas persistibles de un género."""
    return {"id": entidad.id, "nombre": entidad.nombre}


def _entidad_moneda(registro: Moneda) -> EntidadMoneda:
    """Convierte una fila ORM de moneda en entidad de dominio."""
    return EntidadMoneda(registro.id, registro.nombre, registro.simbolo)


def _valores_moneda(entidad: EntidadMoneda) -> dict[str, Any]:
    """Obtiene las columnas persistibles de una moneda."""
    return {
        "id": entidad.id,
        "nombre": entidad.nombre,
        "simbolo": entidad.simbolo,
    }


def _entidad_tipo_cotizacion(
    registro: TipoCotizacion,
) -> EntidadTipoCotizacion:
    """Convierte una fila ORM en entidad de tipo de cotización."""
    return EntidadTipoCotizacion(registro.id, registro.nombre)


def _valores_tipo_cotizacion(
    entidad: EntidadTipoCotizacion,
) -> dict[str, Any]:
    """Obtiene las columnas persistibles de un tipo de cotización."""
    return {"id": entidad.id, "nombre": entidad.nombre}


def _entidad_precio(registro: Precio) -> EntidadPrecio:
    """Convierte un precio ORM y su moneda en entidades de dominio."""
    return EntidadPrecio(
        registro.id,
        registro.valor,
        _entidad_moneda(registro.moneda),
    )


def _valores_precio(entidad: EntidadPrecio) -> dict[str, Any]:
    """Obtiene las columnas persistibles de un precio."""
    return {
        "id": entidad.id,
        "valor": entidad.valor,
        "moneda_id": entidad.moneda.id,
    }


def _entidad_libro(registro: Libro) -> EntidadLibro:
    """Convierte un libro ORM y sus relaciones al modelo de dominio."""
    return EntidadLibro(
        registro.id,
        registro.isbn,
        registro.titulo,
        _entidad_autor(registro.autor),
        _entidad_editorial(registro.editorial),
        _entidad_genero(registro.genero),
        _entidad_precio(registro.precio),
    )


def _valores_libro(entidad: EntidadLibro) -> dict[str, Any]:
    """Obtiene las columnas persistibles de un libro."""
    return {
        "id": entidad.id,
        "isbn": entidad.isbn,
        "titulo": entidad.titulo,
        "autor_id": entidad.autor.id,
        "editorial_id": entidad.editorial.id,
        "genero_id": entidad.genero.id,
        "precio_id": entidad.precio.id,
    }


def _entidad_stock(registro: Stock) -> EntidadStock:
    """Convierte una fila de existencias y su libro asociado."""
    return EntidadStock(_entidad_libro(registro.libro), registro.cantidad)


def _valores_stock(entidad: EntidadStock) -> dict[str, Any]:
    """Obtiene las columnas persistibles de las existencias."""
    return {"libro_id": entidad.libro.id, "cantidad": entidad.cantidad}


def _entidad_cotizacion(registro: CotizacionDolar) -> EntidadCotizacion:
    """Convierte una cotización ORM y su tipo al modelo de dominio."""
    return EntidadCotizacion(
        _entidad_tipo_cotizacion(registro.tipo),
        registro.fecha,
        registro.valor,
        registro.compra,
    )


def _valores_cotizacion(entidad: EntidadCotizacion) -> dict[str, Any]:
    """Obtiene las columnas persistibles de una cotización."""
    return {
        "tipo_id": entidad.tipo.id,
        "fecha": entidad.fecha,
        "valor": entidad.valor,
        "compra": entidad.compra,
    }


def crear_repositorio_autor() -> SQLRepositorioEntidad[EntidadAutor]:
    """Construye el repositorio SQL de autores."""
    return SQLRepositorioEntidad(
        Autor, ("id",), _entidad_autor, _valores_autor, "Autor"
    )


def crear_repositorio_editorial() -> SQLRepositorioEntidad[EntidadEditorial]:
    """Construye el repositorio SQL de editoriales."""
    return SQLRepositorioEntidad(
        Editorial,
        ("id",),
        _entidad_editorial,
        _valores_editorial,
        "Editorial",
    )


def crear_repositorio_genero() -> SQLRepositorioEntidad[EntidadGenero]:
    """Construye el repositorio SQL de géneros."""
    return SQLRepositorioEntidad(
        Genero, ("id",), _entidad_genero, _valores_genero, "Género"
    )


def crear_repositorio_moneda() -> SQLRepositorioEntidad[EntidadMoneda]:
    """Construye el repositorio SQL de monedas."""
    return SQLRepositorioEntidad(
        Moneda, ("id",), _entidad_moneda, _valores_moneda, "Moneda"
    )


def crear_repositorio_tipo_cotizacion() -> (
    SQLRepositorioEntidad[EntidadTipoCotizacion]
):
    """Construye el repositorio SQL de tipos de cotización."""
    return SQLRepositorioEntidad(
        TipoCotizacion,
        ("id",),
        _entidad_tipo_cotizacion,
        _valores_tipo_cotizacion,
        "Tipo de cotización",
    )


def crear_repositorio_precio() -> SQLRepositorioEntidad[EntidadPrecio]:
    """Construye el repositorio SQL de precios."""
    return SQLRepositorioEntidad(
        Precio, ("id",), _entidad_precio, _valores_precio, "Precio"
    )


def crear_repositorio_libro() -> SQLRepositorioEntidad[EntidadLibro]:
    """Construye el repositorio SQL de libros."""
    return SQLRepositorioEntidad(
        Libro, ("id",), _entidad_libro, _valores_libro, "Libro"
    )


class SQLRepositorioStock(
    SQLRepositorioBase[EntidadStock],
    IRepositorioStock,
):
    """Repositorio SQL de Stock, identificado por libro_id."""

    def __init__(self) -> None:
        """Configura el repositorio con la clave primaria del libro."""
        super().__init__(
            Stock,
            ("libro_id",),
            _entidad_stock,
            _valores_stock,
            "Stock",
        )

    @auditar_operacion
    def leer_por_libro(self, libro_id: int) -> EntidadStock | None:
        """Devuelve el stock asociado al identificador del libro."""
        return self.leer_por_clave(libro_id)

    def eliminar(self, libro_id: int) -> bool:
        """Elimina el stock asociado al libro indicado."""
        return super().eliminar(libro_id)


class SQLRepositorioCotizacion(
    SQLRepositorioBase[EntidadCotizacion],
    IRepositorioCotizacionDolar,
):
    """Repositorio SQL de cotizaciones con clave compuesta."""

    def __init__(self) -> None:
        """Configura la clave primaria compuesta de tipo y fecha."""
        super().__init__(
            CotizacionDolar,
            ("tipo_id", "fecha"),
            _entidad_cotizacion,
            _valores_cotizacion,
            "Cotización",
        )

    @auditar_operacion
    def leer_todos(self) -> list[EntidadCotizacion]:
        """Devuelve todas las cotizaciones ordenadas por tipo y fecha."""
        return super().leer_todos()

    @auditar_operacion
    def leer_por_tipo_y_fecha(
        self,
        tipo_id: int,
        fecha: date,
    ) -> EntidadCotizacion | None:
        """Busca una cotización por tipo y fecha."""
        return self.leer_por_clave(tipo_id, fecha)

    @auditar_operacion
    def leer_historico_por_tipo(
        self,
        tipo_id: int,
    ) -> list[EntidadCotizacion]:
        """Devuelve el historial de un tipo de cotización."""
        with get_db_session() as sesion:
            consulta = (
                select(CotizacionDolar)
                .where(CotizacionDolar.tipo_id == tipo_id)
                .order_by(CotizacionDolar.fecha)
            )
            registros = sesion.scalars(consulta).all()
            return [_entidad_cotizacion(registro) for registro in registros]

    @auditar_operacion
    def guardar_o_actualizar_lote(
        self,
        cotizaciones: list[EntidadCotizacion],
    ) -> list[EntidadCotizacion]:
        """Guarda un grupo de cotizaciones en una sola transacción."""
        try:
            with get_db_session() as sesion:
                for cotizacion in cotizaciones:
                    valores = _valores_cotizacion(cotizacion)
                    clave = self._obtener_clave(valores)
                    registro = sesion.get(CotizacionDolar, clave)
                    if registro is None:
                        sesion.add(CotizacionDolar(**valores))
                    else:
                        registro.valor = cotizacion.valor
                        registro.compra = cotizacion.compra
                sesion.flush()
        except IntegrityError as error:
            raise ValueError(
                "No se pudieron guardar las cotizaciones; "
                "verifique los tipos registrados."
            ) from error
        return cotizaciones

    @auditar_operacion
    def eliminar(self, tipo_id: int, fecha: date) -> bool:
        """Elimina la cotización del tipo y fecha indicados."""
        return self._eliminar_por_clave(tipo_id, fecha)


def crear_repositorio_cotizacion() -> SQLRepositorioCotizacion:
    """Construye el repositorio SQL de cotizaciones."""
    return SQLRepositorioCotizacion()


class SQLRepositorioAuditoria:
    """Consulta eventos de auditoría en orden cronológico inverso."""

    @auditar_operacion
    def leer_recientes(self, limite: int = 20) -> list[dict[str, object]]:
        """Devuelve hasta el número indicado de eventos recientes."""
        if isinstance(limite, bool) or not isinstance(limite, int):
            raise ValueError("El límite del historial debe ser un entero.")
        if not 1 <= limite <= 500:
            raise ValueError("El límite debe estar entre 1 y 500.")

        tabla = Auditoria.__table__
        if not isinstance(tabla, Table):
            raise TypeError("El modelo de auditoría no define una tabla SQL.")
        tabla.create(bind=get_engine(), checkfirst=True)
        with get_db_session() as sesion:
            registros = sesion.scalars(
                select(Auditoria)
                .order_by(Auditoria.fecha.desc(), Auditoria.id.desc())
                .limit(limite)
            ).all()
            return [
                {
                    "accion": registro.accion,
                    "fecha": registro.fecha,
                    "detalles": registro.detalles,
                }
                for registro in registros
            ]
