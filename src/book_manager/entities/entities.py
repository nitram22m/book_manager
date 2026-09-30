from dataclasses import dataclass
from datetime import date


@dataclass
class EntidadBase:
    """Clase base para entidades que comparten el atributo id."""
    id: int

@dataclass
class Genero(EntidadBase):
    nombre: str

@dataclass
class Editorial(EntidadBase):
    nombre: str

@dataclass
class Moneda(EntidadBase):
    nombre: str
    simbolo: str

@dataclass
class TipoCotizacion(EntidadBase):
    nombre: str

@dataclass
class Precio(EntidadBase):
    valor: float
    moneda_id: int

@dataclass
class Libro(EntidadBase):
    isbn: str
    titulo: str
    autor_id: int
    editorial_id: int
    genero_id: int
    precio_id: int
    stock_id: int

@dataclass
class Stock:
    """Se identifica por el libro_id, por lo que no hereda de EntidadBase."""
    libro_id: int
    cantidad: int

@dataclass
class CotizacionDolar:
    """Se identifica por la combinacion de tipo_id y fecha."""
    tipo_id: int
    fecha: date
    valor: float