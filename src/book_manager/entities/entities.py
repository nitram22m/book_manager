"""Entidades del dominio de Book Manager.

Todos los atributos son privados y se exponen mediante propiedades que
validan cada asignacion. Las relaciones entre entidades se modelan con
instancias de las clases correspondientes y no con identificadores.
"""
import datetime
from typing import Any, Dict, Tuple


def _validar_texto(valor: Any, campo: str) -> str:
    """Limpia el texto o lanza ValueError si el valor es inválido."""
    if not isinstance(valor, str) or not valor.strip():
        raise ValueError(f"{campo} debe ser un texto no vacio.")
    return valor.strip()


def _validar_entero(valor: Any, campo: str, minimo: int) -> int:
    """Valida que el valor sea un entero no booleano dentro del rango."""
    if isinstance(valor, bool) or not isinstance(valor, int):
        raise ValueError(f"{campo} debe ser un numero entero.")
    if valor < minimo:
        raise ValueError(f"{campo} debe ser mayor o igual a {minimo}.")
    return valor


def _validar_monto(valor: Any, campo: str) -> float:
    """Valida que el valor sea un numero estrictamente positivo."""
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        raise ValueError(f"{campo} debe ser un numero.")
    if valor <= 0:
        raise ValueError(f"{campo} debe ser mayor que cero.")
    return float(valor)


def _validar_instancia(valor: Any, clase: type, campo: str) -> Any:
    """Valida que el valor sea una instancia de la clase indicada."""
    if not isinstance(valor, clase):
        raise ValueError(
            f"{campo} debe ser una instancia de {clase.__name__}."
        )
    return valor


class Entidad:
    """Clase base de toda entidad persistible en CSV."""

    CAMPOS_CSV: Tuple[str, ...] = ()

    def a_fila(self) -> Dict[str, Any]:
        """Devuelve la entidad como diccionario listo para escribir en CSV."""
        raise NotImplementedError

    def __str__(self) -> str:
        """Devuelve una representacion legible de los campos persistidos."""
        return " | ".join(f"{k}={v}" for k, v in self.a_fila().items())

    def __repr__(self) -> str:
        """Devuelve una representacion util para depuracion."""
        return f"{type(self).__name__}({self})"


class EntidadBase(Entidad):
    """Entidad identificada por un id entero positivo."""

    CAMPOS_CSV = ("id",)

    def __init__(self, id: int) -> None:
        """Crea una entidad con un identificador entero positivo."""
        self.id = id

    @property
    def id(self) -> int:
        """Identificador unico de la entidad."""
        return self.__id

    @id.setter
    def id(self, valor: int) -> None:
        self.__id = _validar_entero(valor, "El id", 1)

    def a_fila(self) -> Dict[str, Any]:
        """Convierte la entidad en una fila compatible con CSV."""
        return {"id": self.id}

    def __eq__(self, otro: object) -> bool:
        """Compara entidades por clase e identificador."""
        return type(self) is type(otro) and self.id == otro.id

    def __hash__(self) -> int:
        """Calcula un hash coherente con la igualdad de entidades."""
        return hash((type(self).__name__, self.id))


class EntidadNombrada(EntidadBase):
    """Entidad con identificador y nombre."""

    CAMPOS_CSV = ("id", "nombre")

    def __init__(self, id: int, nombre: str) -> None:
        """Crea una entidad identificada y con nombre descriptivo."""
        super().__init__(id)
        self.nombre = nombre

    @property
    def nombre(self) -> str:
        """Nombre descriptivo de la entidad."""
        return self.__nombre

    @nombre.setter
    def nombre(self, valor: str) -> None:
        self.__nombre = _validar_texto(valor, "El nombre")

    def a_fila(self) -> Dict[str, Any]:
        """Convierte la entidad en una fila compatible con CSV."""
        return {"id": self.id, "nombre": self.nombre}

    @classmethod
    def desde_fila(cls, fila: Dict[str, str]) -> "EntidadNombrada":
        """Construye la entidad a partir de una fila de CSV."""
        return cls(int(fila["id"]), fila["nombre"])


class Genero(EntidadNombrada):
    """Genero literario de un libro."""


class Editorial(EntidadNombrada):
    """Editorial que publica libros."""


class Autor(EntidadNombrada):
    """Autor de uno o mas libros."""


class TipoCotizacion(EntidadNombrada):
    """Tipo de cotizacion del dolar (Oficial, Blue, MEP, etc.)."""


class Moneda(EntidadBase):
    """Moneda en la que se expresa un precio."""

    CAMPOS_CSV = ("id", "nombre", "simbolo")

    def __init__(
        self, id: int, nombre: str, simbolo: str
    ) -> None:
        """Crea una moneda con identificador, código y símbolo."""
        super().__init__(id)
        self.nombre = nombre
        self.simbolo = simbolo

    @property
    def nombre(self) -> str:
        """Codigo de la moneda (por ejemplo ARS o USD)."""
        return self.__nombre

    @nombre.setter
    def nombre(self, valor: str) -> None:
        self.__nombre = _validar_texto(valor, "El nombre de la moneda")

    @property
    def simbolo(self) -> str:
        """Simbolo con el que se muestra la moneda."""
        return self.__simbolo

    @simbolo.setter
    def simbolo(self, valor: str) -> None:
        self.__simbolo = _validar_texto(valor, "El simbolo")

    def a_fila(self) -> Dict[str, Any]:
        """Convierte la moneda en una fila compatible con CSV."""
        return {"id": self.id, "nombre": self.nombre, "simbolo": self.simbolo}

    @classmethod
    def desde_fila(cls, fila: Dict[str, str]) -> "Moneda":
        """Construye la moneda a partir de una fila de CSV."""
        return cls(int(fila["id"]), fila["nombre"], fila["simbolo"])


class Precio(EntidadBase):
    """Valor monetario expresado en una Moneda."""

    CAMPOS_CSV = ("id", "valor", "moneda_id")

    def __init__(self, id: int, valor: float, moneda: Moneda) -> None:
        """Crea un precio asociado a una moneda."""
        super().__init__(id)
        self.valor = valor
        self.moneda = moneda

    @property
    def valor(self) -> float:
        """Importe del precio, siempre mayor que cero."""
        return self.__valor

    @valor.setter
    def valor(self, valor: float) -> None:
        self.__valor = _validar_monto(valor, "El valor")

    @property
    def moneda(self) -> Moneda:
        """Moneda en la que esta expresado el precio."""
        return self.__moneda

    @moneda.setter
    def moneda(self, moneda: Moneda) -> None:
        self.__moneda = _validar_instancia(moneda, Moneda, "La moneda")

    def a_fila(self) -> Dict[str, Any]:
        """Convierte el precio y la referencia a moneda en una fila CSV."""
        return {
            "id": self.id,
            "valor": self.valor,
            "moneda_id": self.moneda.id,
        }


class Libro(EntidadBase):
    """Libro del catalogo, asociado a su autor, editorial, genero y precio."""

    CAMPOS_CSV = (
        "id",
        "isbn",
        "titulo",
        "autor_id",
        "editorial_id",
        "genero_id",
        "precio_id",
    )

    def __init__(
        self,
        id: int,
        isbn: str,
        titulo: str,
        autor: Autor,
        editorial: Editorial,
        genero: Genero,
        precio: Precio,
    ) -> None:
        """Crea un libro asociado a su autor, editorial, género y precio."""
        super().__init__(id)
        self.isbn = isbn
        self.titulo = titulo
        self.autor = autor
        self.editorial = editorial
        self.genero = genero
        self.precio = precio

    @property
    def isbn(self) -> str:
        """Codigo ISBN del libro."""
        return self.__isbn

    @isbn.setter
    def isbn(self, valor: str) -> None:
        self.__isbn = _validar_texto(valor, "El ISBN")

    @property
    def titulo(self) -> str:
        """Titulo del libro."""
        return self.__titulo

    @titulo.setter
    def titulo(self, valor: str) -> None:
        self.__titulo = _validar_texto(valor, "El titulo")

    @property
    def autor(self) -> Autor:
        """Autor del libro."""
        return self.__autor

    @autor.setter
    def autor(self, autor: Autor) -> None:
        self.__autor = _validar_instancia(autor, Autor, "El autor")

    @property
    def editorial(self) -> Editorial:
        """Editorial que publica el libro."""
        return self.__editorial

    @editorial.setter
    def editorial(self, editorial: Editorial) -> None:
        self.__editorial = _validar_instancia(
            editorial, Editorial, "La editorial"
        )

    @property
    def genero(self) -> Genero:
        """Genero literario del libro."""
        return self.__genero

    @genero.setter
    def genero(self, genero: Genero) -> None:
        self.__genero = _validar_instancia(genero, Genero, "El genero")

    @property
    def precio(self) -> Precio:
        """Precio de lista del libro."""
        return self.__precio

    @precio.setter
    def precio(self, precio: Precio) -> None:
        self.__precio = _validar_instancia(precio, Precio, "El precio")

    def a_fila(self) -> Dict[str, Any]:
        """Convierte el libro y sus referencias en una fila CSV."""
        return {
            "id": self.id,
            "isbn": self.isbn,
            "titulo": self.titulo,
            "autor_id": self.autor.id,
            "editorial_id": self.editorial.id,
            "genero_id": self.genero.id,
            "precio_id": self.precio.id,
        }


class Stock(Entidad):
    """Unidades disponibles de un Libro; se identifica por el libro."""

    CAMPOS_CSV = ("libro_id", "cantidad")

    def __init__(
        self, libro: Libro, cantidad: int
    ) -> None:
        """Crea el registro de existencias de un libro."""
        self.libro = libro
        self.cantidad = cantidad

    @property
    def libro(self) -> Libro:
        """Libro al que corresponde el stock."""
        return self.__libro

    @libro.setter
    def libro(self, libro: Libro) -> None:
        self.__libro = _validar_instancia(libro, Libro, "El libro")

    @property
    def cantidad(self) -> int:
        """Cantidad de unidades disponibles (no negativa)."""
        return self.__cantidad

    @cantidad.setter
    def cantidad(self, valor: int) -> None:
        self.__cantidad = _validar_entero(valor, "La cantidad", 0)

    def descontar(self, unidades: int) -> None:
        """Resta unidades vendidas si hay existencias suficientes."""
        unidades = _validar_entero(unidades, "La cantidad a descontar", 1)
        if unidades > self.cantidad:
            raise ValueError(
                f"Stock insuficiente. Solo hay {self.cantidad} unidades."
            )
        self.cantidad = self.cantidad - unidades

    def a_fila(self) -> Dict[str, Any]:
        """Convierte el stock y su referencia al libro en una fila CSV."""
        return {"libro_id": self.libro.id, "cantidad": self.cantidad}


class CotizacionDolar(Entidad):
    """Cotizacion del dolar de un tipo determinado en una fecha."""

    CAMPOS_CSV = ("tipo_id", "fecha", "valor")

    def __init__(
        self, tipo: TipoCotizacion, fecha: datetime.date, valor: float
    ) -> None:
        """Crea una cotización para un tipo y una fecha."""
        self.tipo = tipo
        self.fecha = fecha
        self.valor = valor

    @property
    def tipo(self) -> TipoCotizacion:
        """Tipo de cotizacion (Oficial, Blue, etc.)."""
        return self.__tipo

    @tipo.setter
    def tipo(self, tipo: TipoCotizacion) -> None:
        self.__tipo = _validar_instancia(
            tipo, TipoCotizacion, "El tipo de cotización"
        )

    @property
    def fecha(self) -> datetime.date:
        """Fecha de la cotizacion."""
        return self.__fecha

    @fecha.setter
    def fecha(self, valor: datetime.date) -> None:
        if isinstance(valor, datetime.datetime):
            valor = valor.date()
        self.__fecha = _validar_instancia(valor, datetime.date, "La fecha")

    @property
    def valor(self) -> float:
        """Valor en pesos de un dolar, siempre mayor que cero."""
        return self.__valor

    @valor.setter
    def valor(self, valor: float) -> None:
        self.__valor = _validar_monto(valor, "El valor de la cotizacion")

    def a_fila(self) -> Dict[str, Any]:
        """Convierte la cotizacion y su tipo relacionado en una fila CSV."""
        return {
            "tipo_id": self.tipo.id,
            "fecha": self.fecha.strftime("%Y-%m-%d"),
            "valor": self.valor,
        }
