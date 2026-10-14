"""Repositorios de persistencia en archivos CSV.

Las entidades se guardan con los identificadores de sus relaciones y se
reconstruyen como objetos al leerlas, validando que cada referencia exista.
"""
import abc
import csv
import datetime
import os
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Tuple,
    Type,
    TypeVar,
)

from book_manager.entities.entities import (
    Autor,
    CotizacionDolar,
    Editorial,
    EntidadBase,
    Genero,
    Libro,
    Moneda,
    Precio,
    Stock,
    TipoCotizacion,
)

T = TypeVar("T", bound=EntidadBase)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_DIR = os.path.join(BASE_DIR, "migrations", "csv")
os.makedirs(CSV_DIR, exist_ok=True)


class IRepositorio(abc.ABC, Generic[T]):
    """Interfaz para repositorios de entidades identificadas por id."""

    @abc.abstractmethod
    def crear(self, entidad: T) -> T:
        """Persiste una entidad nueva."""

    @abc.abstractmethod
    def leer_por_id(self, id: int) -> Optional[T]:
        """Devuelve la entidad con ese id o None."""

    @abc.abstractmethod
    def leer_todos(self) -> List[T]:
        """Devuelve todas las entidades."""

    @abc.abstractmethod
    def actualizar(self, entidad: T) -> T:
        """Reemplaza la entidad existente con el mismo id."""

    @abc.abstractmethod
    def eliminar(self, id: int) -> bool:
        """Elimina la entidad; devuelve False si no existia."""


class IRepositorioStock(abc.ABC):
    """Interfaz para repositorios de Stock."""

    @abc.abstractmethod
    def crear(self, stock: Stock) -> Stock:
        """Persiste un stock nuevo."""

    @abc.abstractmethod
    def leer_por_libro(self, libro_id: int) -> Optional[Stock]:
        """Devuelve el stock del libro o None."""

    @abc.abstractmethod
    def actualizar(self, stock: Stock) -> Stock:
        """Reemplaza el stock existente del mismo libro."""

    @abc.abstractmethod
    def eliminar(self, libro_id: int) -> bool:
        """Elimina el stock del libro; devuelve False si no existia."""


class IRepositorioCotizacionDolar(abc.ABC):
    """Interfaz para repositorios de CotizacionDolar."""

    @abc.abstractmethod
    def crear(self, cotizacion: CotizacionDolar) -> CotizacionDolar:
        """Persiste una cotizacion nueva."""

    @abc.abstractmethod
    def leer_por_tipo_y_fecha(
        self, tipo_id: int, fecha: datetime.date
    ) -> Optional[CotizacionDolar]:
        """Devuelve la cotizacion de ese tipo y fecha o None."""

    @abc.abstractmethod
    def leer_historico_por_tipo(self, tipo_id: int) -> List[CotizacionDolar]:
        """Devuelve todas las cotizaciones de un tipo."""

    @abc.abstractmethod
    def actualizar(self, cotizacion: CotizacionDolar) -> CotizacionDolar:
        """Reemplaza la cotizacion existente del mismo tipo y fecha."""

    @abc.abstractmethod
    def eliminar(self, tipo_id: int, fecha: datetime.date) -> bool:
        """Elimina la cotizacion; devuelve False si no existia."""


class _ArchivoCsv:
    """Acceso de bajo nivel a un CSV con encabezado fijo.

    Si el archivo existe con un encabezado distinto (esquema anterior) se
    reinicia vacio para que pueda volver a precargarse.
    """

    def __init__(self, nombre_archivo: str, campos: Tuple[str, ...]) -> None:
        """Abre un archivo CSV y crea el encabezado esperado si hace falta."""
        self.__ruta = os.path.join(CSV_DIR, nombre_archivo)
        self.__campos = list(campos)
        if not self.__encabezado_vigente():
            self.escribir([])

    def __encabezado_vigente(self) -> bool:
        """Comprueba que el archivo exista y tenga las columnas esperadas."""
        if not os.path.exists(self.__ruta):
            return False
        with open(self.__ruta, newline="", encoding="utf-8") as f:
            return next(csv.reader(f), None) == self.__campos

    def leer(self) -> List[Dict[str, str]]:
        """Devuelve las filas como diccionarios de texto."""
        with open(self.__ruta, newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))

    def escribir(self, filas: List[Dict[str, Any]]) -> None:
        """Reemplaza el contenido del archivo con las filas dadas."""
        with open(self.__ruta, "w", newline="", encoding="utf-8") as f:
            escritor = csv.DictWriter(f, fieldnames=self.__campos)
            escritor.writeheader()
            escritor.writerows(filas)

    def agregar(self, fila: Dict[str, Any]) -> None:
        """Agrega una fila al final del archivo."""
        with open(self.__ruta, "a", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=self.__campos).writerow(fila)


def _exigir(repositorio: Any, id: int, nombre: str) -> Any:
    """Devuelve la entidad con ese id o lanza ValueError si no existe."""
    entidad = repositorio.leer_por_id(id)
    if entidad is None:
        raise ValueError(f"{nombre} con ID {id} no existe.")
    return entidad


class _Dependencias:
    """Evita borrar entidades que todavía tienen registros dependientes."""

    def __init__(self) -> None:
        """Inicializa la lista de repositorios dependientes."""
        self.__dependientes: List[Tuple[str, Any, Callable[[Any], int]]] = []

    def registrar(
        self, nombre: str, repositorio: Any, extraer_id: Callable[[Any], int]
    ) -> None:
        """Registra el repositorio y su extractor de referencias."""
        self.__dependientes.append((nombre, repositorio, extraer_id))

    def validar_eliminacion(self, id: int) -> None:
        """Lanza ValueError si un registro utiliza este identificador."""
        for nombre, repositorio, extraer_id in self.__dependientes:
            if any(extraer_id(e) == id for e in repositorio.leer_todos()):
                raise ValueError(
                    f"No se puede eliminar: el ID {id} es usado por {nombre}."
                )


class CsvRepositorioBase(IRepositorio[T]):
    """CRUD generico en CSV para entidades con id.

    Las subclases con relaciones sobrescriben `_desde_fila` y
    `_validar_referencias`.
    """

    def __init__(self, entidad_clase: Type[T], nombre_archivo: str) -> None:
        """Prepara el CSV y la clase usada para reconstruir sus registros."""
        self._entidad_clase = entidad_clase
        self._archivo = _ArchivoCsv(nombre_archivo, entidad_clase.CAMPOS_CSV)
        self._dependencias = _Dependencias()

    def registrar_dependiente(
        self, nombre: str, repositorio: Any, extraer_id: Callable[[Any], int]
    ) -> None:
        """Registra un repositorio que usa estas entidades."""
        self._dependencias.registrar(nombre, repositorio, extraer_id)

    def _desde_fila(self, fila: Dict[str, str]) -> T:
        """Convierte una fila CSV a la entidad configurada."""
        return self._entidad_clase.desde_fila(fila)

    def _validar_referencias(self, entidad: T) -> None:
        """Valida relaciones; la implementación base no tiene relaciones."""

    def crear(self, entidad: T) -> T:
        """Valida y persiste una entidad con un identificador nuevo."""
        if self.leer_por_id(entidad.id) is not None:
            raise ValueError(f"Ya existe un registro con ID {entidad.id}.")
        self._validar_referencias(entidad)
        self._archivo.agregar(entidad.a_fila())
        return entidad

    def leer_por_id(self, id: int) -> Optional[T]:
        """Busca una entidad por identificador y devuelve None si no existe."""
        for entidad in self.leer_todos():
            if entidad.id == id:
                return entidad
        return None

    def leer_todos(self) -> List[T]:
        """Lee todas las filas y las convierte en entidades."""
        return [self._desde_fila(fila) for fila in self._archivo.leer()]

    def actualizar(self, entidad: T) -> T:
        """Valida y reemplaza el registro con el mismo identificador."""
        entidades = self.leer_todos()
        if all(e.id != entidad.id for e in entidades):
            raise ValueError("Entidad no encontrada.")
        self._validar_referencias(entidad)
        self._archivo.escribir(
            [
                (entidad if e.id == entidad.id else e).a_fila()
                for e in entidades
            ]
        )
        return entidad

    def eliminar(self, id: int) -> bool:
        """Elimina el registro si existe y no tiene entidades dependientes."""
        entidades = self.leer_todos()
        restantes = [e for e in entidades if e.id != id]
        if len(entidades) == len(restantes):
            return False
        self._dependencias.validar_eliminacion(id)
        self._archivo.escribir([e.a_fila() for e in restantes])
        return True


class CsvRepositorioPrecio(CsvRepositorioBase[Precio]):
    """Repositorio de Precio; valida y resuelve su Moneda."""

    def __init__(self, repo_monedas: CsvRepositorioBase[Moneda]) -> None:
        """Conecta el repositorio de precios con el de monedas."""
        super().__init__(Precio, "precios.csv")
        self.__repo_monedas = repo_monedas
        repo_monedas.registrar_dependiente(
            "un precio", self, lambda p: p.moneda.id
        )

    def _desde_fila(self, fila: Dict[str, str]) -> Precio:
        """Reconstruye el precio y resuelve su moneda desde el repositorio."""
        moneda = _exigir(self.__repo_monedas, int(fila["moneda_id"]), "Moneda")
        return Precio(int(fila["id"]), float(fila["valor"]), moneda)

    def _validar_referencias(self, precio: Precio) -> None:
        """Comprueba que la moneda del precio siga registrada."""
        _exigir(self.__repo_monedas, precio.moneda.id, "Moneda")


class CsvRepositorioLibro(CsvRepositorioBase[Libro]):
    """Repositorio de libros; valida y resuelve sus entidades relacionadas."""

    def __init__(
        self,
        repo_autores: CsvRepositorioBase[Autor],
        repo_editoriales: CsvRepositorioBase[Editorial],
        repo_generos: CsvRepositorioBase[Genero],
        repo_precios: CsvRepositorioBase[Precio],
    ) -> None:
        """Conecta libros con sus repositorios de entidades relacionadas."""
        super().__init__(Libro, "libros.csv")
        self.__repo_autores = repo_autores
        self.__repo_editoriales = repo_editoriales
        self.__repo_generos = repo_generos
        self.__repo_precios = repo_precios
        repo_autores.registrar_dependiente(
            "un libro", self, lambda x: x.autor.id
        )
        repo_editoriales.registrar_dependiente(
            "un libro", self, lambda x: x.editorial.id
        )
        repo_generos.registrar_dependiente(
            "un libro", self, lambda x: x.genero.id
        )
        repo_precios.registrar_dependiente(
            "un libro", self, lambda x: x.precio.id
        )

    def _desde_fila(self, fila: Dict[str, str]) -> Libro:
        """Reconstruye el libro y resuelve sus entidades relacionadas."""
        return Libro(
            int(fila["id"]),
            fila["isbn"],
            fila["titulo"],
            _exigir(self.__repo_autores, int(fila["autor_id"]), "Autor"),
            _exigir(
                self.__repo_editoriales, int(fila["editorial_id"]), "Editorial"
            ),
            _exigir(
                self.__repo_generos, int(fila["genero_id"]), "Genero"
            ),
            _exigir(self.__repo_precios, int(fila["precio_id"]), "Precio"),
        )

    def _validar_referencias(self, libro: Libro) -> None:
        """Comprueba que todas las relaciones del libro sigan registradas."""
        _exigir(self.__repo_autores, libro.autor.id, "Autor")
        _exigir(self.__repo_editoriales, libro.editorial.id, "Editorial")
        _exigir(self.__repo_generos, libro.genero.id, "Genero")
        _exigir(self.__repo_precios, libro.precio.id, "Precio")


class CsvRepositorioStock(IRepositorioStock):
    """Repositorio de Stock en CSV; valida y resuelve el Libro."""

    def __init__(self, repo_libros: CsvRepositorioBase[Libro]) -> None:
        """Prepara el archivo de stock y el repositorio de libros asociado."""
        self.__archivo = _ArchivoCsv("stock.csv", Stock.CAMPOS_CSV)
        self.__repo_libros = repo_libros
        repo_libros.registrar_dependiente(
            "un stock", self, lambda s: s.libro.id
        )

    def leer_todos(self) -> List[Stock]:
        """Devuelve todos los stocks con su Libro resuelto."""
        return [
            Stock(
                _exigir(self.__repo_libros, int(fila["libro_id"]), "Libro"),
                int(fila["cantidad"]),
            )
            for fila in self.__archivo.leer()
        ]

    def crear(self, stock: Stock) -> Stock:
        """Valida el libro relacionado y persiste un stock nuevo."""
        if self.leer_por_libro(stock.libro.id) is not None:
            raise ValueError("Stock ya existe para este libro.")
        _exigir(self.__repo_libros, stock.libro.id, "Libro")
        self.__archivo.agregar(stock.a_fila())
        return stock

    def leer_por_libro(self, libro_id: int) -> Optional[Stock]:
        """Devuelve el stock asociado al libro o None si no está registrado."""
        for stock in self.leer_todos():
            if stock.libro.id == libro_id:
                return stock
        return None

    def actualizar(self, stock: Stock) -> Stock:
        """Reemplaza el registro de stock asociado al libro."""
        stocks = self.leer_todos()
        if all(s.libro.id != stock.libro.id for s in stocks):
            raise ValueError("Stock no encontrado.")
        self.__archivo.escribir(
            [
                (stock if s.libro.id == stock.libro.id else s).a_fila()
                for s in stocks
            ]
        )
        return stock

    def eliminar(self, libro_id: int) -> bool:
        """Elimina el stock del libro y devuelve si había un registro."""
        stocks = self.leer_todos()
        restantes = [s for s in stocks if s.libro.id != libro_id]
        if len(stocks) == len(restantes):
            return False
        self.__archivo.escribir([s.a_fila() for s in restantes])
        return True


class CsvRepositorioCotizacion(IRepositorioCotizacionDolar):
    """Repositorio de cotizaciones; valida y resuelve sus tipos asociados."""

    def __init__(self, repo_tipos: CsvRepositorioBase[TipoCotizacion]) -> None:
        """Prepara el archivo y el repositorio de tipos de cotización."""
        self.__archivo = _ArchivoCsv(
            "cotizaciones.csv", CotizacionDolar.CAMPOS_CSV
        )
        self.__repo_tipos = repo_tipos
        repo_tipos.registrar_dependiente(
            "una cotización", self, lambda c: c.tipo.id
        )

    def leer_todos(self) -> List[CotizacionDolar]:
        """Devuelve todas las cotizaciones con su tipo resuelto."""
        return [
            CotizacionDolar(
                _exigir(
                    self.__repo_tipos,
                    int(fila["tipo_id"]),
                    "Tipo de cotización",
                ),
                datetime.datetime.strptime(fila["fecha"], "%Y-%m-%d").date(),
                float(fila["valor"]),
            )
            for fila in self.__archivo.leer()
        ]

    def crear(self, cotizacion: CotizacionDolar) -> CotizacionDolar:
        """Valida el tipo y evita duplicados para el mismo día."""
        if self.leer_por_tipo_y_fecha(
            cotizacion.tipo.id, cotizacion.fecha
        ) is not None:
            raise ValueError("Cotizacion ya existe.")
        _exigir(self.__repo_tipos, cotizacion.tipo.id, "Tipo de cotizacion")
        self.__archivo.agregar(cotizacion.a_fila())
        return cotizacion

    def leer_por_tipo_y_fecha(
        self, tipo_id: int, fecha: datetime.date
    ) -> Optional[CotizacionDolar]:
        """Busca una cotización por tipo y fecha."""
        for c in self.leer_todos():
            if c.tipo.id == tipo_id and c.fecha == fecha:
                return c
        return None

    def leer_historico_por_tipo(self, tipo_id: int) -> List[CotizacionDolar]:
        """Devuelve las cotizaciones asociadas al tipo indicado."""
        return [c for c in self.leer_todos() if c.tipo.id == tipo_id]

    def actualizar(self, cotizacion: CotizacionDolar) -> CotizacionDolar:
        """Reemplaza la cotización que coincide en tipo y fecha."""
        cots = self.leer_todos()

        def coincide(c: CotizacionDolar) -> bool:
            """Indica si la cotización coincide en tipo y fecha."""
            return (
                c.tipo.id == cotizacion.tipo.id
                and c.fecha == cotizacion.fecha
            )

        if not any(coincide(c) for c in cots):
            raise ValueError("Cotizacion no encontrada.")
        self.__archivo.escribir(
            [(cotizacion if coincide(c) else c).a_fila() for c in cots]
        )
        return cotizacion

    def eliminar(self, tipo_id: int, fecha: datetime.date) -> bool:
        """Elimina la cotización del tipo y fecha indicados, si existe."""
        cots = self.leer_todos()
        restantes = [
            c for c in cots
            if not (c.tipo.id == tipo_id and c.fecha == fecha)
        ]
        if len(cots) == len(restantes):
            return False
        self.__archivo.escribir([c.a_fila() for c in restantes])
        return True
