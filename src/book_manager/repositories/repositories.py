import abc
import csv
import dataclasses
import datetime
import os
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

from book_manager.entities.entities import CotizacionDolar, EntidadBase, Stock

T = TypeVar('T', bound=EntidadBase)

# Configuracion de rutas para los archivos CSV
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_DIR = os.path.join(BASE_DIR, 'migrations', 'csv')
os.makedirs(CSV_DIR, exist_ok=True)

# ==========================================
# INTERFACES BASE
# ==========================================

class IRepositorio(abc.ABC, Generic[T]):
    """Interfaz para repositorios que manejan entidades con operaciones CRUD basicas."""

    @abc.abstractmethod
    def crear(self, entidad: T) -> T:
        pass

    @abc.abstractmethod
    def leer_por_id(self, id: int) -> Optional[T]:
        pass

    @abc.abstractmethod
    def leer_todos(self) -> List[T]:
        pass

    @abc.abstractmethod
    def actualizar(self, entidad: T) -> T:
        pass

    @abc.abstractmethod
    def eliminar(self, id: int) -> bool:
        pass


class IRepositorioStock(abc.ABC):
    """Interfaz para repositorios del tipo Stock."""

    @abc.abstractmethod
    def crear(self, stock: Stock) -> Stock:
        pass

    @abc.abstractmethod
    def leer_por_libro(self, libro_id: int) -> Optional['Stock']:
        pass

    @abc.abstractmethod
    def actualizar(self, stock: 'Stock') -> 'Stock':
        pass

    @abc.abstractmethod
    def eliminar(self, libro_id: int) -> bool:
        pass


class IRepositorioCotizacionDolar(abc.ABC):
    """Interfaz para repositorios del tipo RepositorioCotizacionDolar."""

    @abc.abstractmethod
    def crear(self, cotizacion: 'CotizacionDolar') -> 'CotizacionDolar':
        pass

    @abc.abstractmethod
    def leer_por_tipo_y_fecha(self, tipo_id: int, fecha: datetime.date) -> Optional['CotizacionDolar']:
        pass

    @abc.abstractmethod
    def leer_historico_por_tipo(self, tipo_id: int) -> List['CotizacionDolar']:
        pass

    @abc.abstractmethod
    def actualizar(self, cotizacion: 'CotizacionDolar') -> 'CotizacionDolar':
        pass

    @abc.abstractmethod
    def eliminar(self, tipo_id: int, fecha: datetime.date) -> bool:
        pass


# ==========================================
# GUARDADO EN CSV
# ==========================================

class CsvRepositorioBase(IRepositorio[T]):
    """Implementacion concreta para el CRUD en archivos CSV."""
    def __init__(self, entidad_clase: Type[T], nombre_archivo: str):
        self.entidad_clase = entidad_clase
        self.ruta_archivo = os.path.join(CSV_DIR, nombre_archivo)
        # Fix: Usamos dataclasses.fields para que detecte el atributo id heredado
        self.campos = [f.name for f in dataclasses.fields(entidad_clase)]
        self._inicializar_archivo()

    def _inicializar_archivo(self) -> None:
        if not os.path.exists(self.ruta_archivo):
            with open(self.ruta_archivo, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.campos)
                writer.writeheader()

    def _convertir_tipos(self, fila: Dict[str, str]) -> Dict[str, Any]:
        datos = {}
        for campo in dataclasses.fields(self.entidad_clase):
            valor = fila.get(campo.name, "")
            # Si el valor esta vacio, lo dejamos asi para evitar errores de casteo
            if not valor:
                datos[campo.name] = None
                continue

            if campo.type == int or campo.type == 'int':
                datos[campo.name] = int(float(valor))
            elif campo.type == float or campo.type == 'float':
                datos[campo.name] = float(valor)
            else:
                datos[campo.name] = valor
        return datos

    def crear(self, entidad: T) -> T:
        entidades = self.leer_todos()
        if any(e.id == entidad.id for e in entidades):
            raise ValueError(f"Ya existe un registro con ID {entidad.id}.")

        with open(self.ruta_archivo, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=self.campos)
            writer.writerow(entidad.__dict__)
        return entidad

    def leer_por_id(self, id: int) -> Optional[T]:
        for entidad in self.leer_todos():
            if entidad.id == id:
                return entidad
        return None

    def leer_todos(self) -> List[T]:
        entidades = []
        if not os.path.exists(self.ruta_archivo):
            return entidades
        with open(self.ruta_archivo, mode='r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for fila in reader:
                entidades.append(self.entidad_clase(**self._convertir_tipos(fila)))
        return entidades

    def actualizar(self, entidad: T) -> T:
        entidades = self.leer_todos()
        actualizado = False
        with open(self.ruta_archivo, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=self.campos)
            writer.writeheader()
            for e in entidades:
                if e.id == entidad.id:
                    writer.writerow(entidad.__dict__)
                    actualizado = True
                else:
                    writer.writerow(e.__dict__)
        if not actualizado:
            raise ValueError("Entidad no encontrada.")
        return entidad

    def eliminar(self, id: int) -> bool:
        entidades = self.leer_todos()
        restantes = [e for e in entidades if e.id != id]
        if len(entidades) == len(restantes):
            return False
        with open(self.ruta_archivo, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=self.campos)
            writer.writeheader()
            for e in restantes:
                writer.writerow(e.__dict__)
        return True


class CsvRepositorioStock(IRepositorioStock):
    """Implementacion concreta para Stock en CSV."""
    def __init__(self):
        self.ruta_archivo = os.path.join(CSV_DIR, 'stock.csv')
        self.campos = ['libro_id', 'cantidad']
        if not os.path.exists(self.ruta_archivo):
            with open(self.ruta_archivo, mode='w', newline='', encoding='utf-8') as f:
                csv.DictWriter(f, fieldnames=self.campos).writeheader()

    def leer_todos(self) -> List[Stock]:
        stocks = []
        with open(self.ruta_archivo, mode='r', newline='', encoding='utf-8') as f:
            for fila in csv.DictReader(f):
                stocks.append(Stock(int(fila['libro_id']), int(fila['cantidad'])))
        return stocks

    def crear(self, stock: Stock) -> Stock:
        if self.leer_por_libro(stock.libro_id):
            raise ValueError("Stock ya existe para este libro.")
        with open(self.ruta_archivo, mode='a', newline='', encoding='utf-8') as f:
            csv.DictWriter(f, fieldnames=self.campos).writerow(stock.__dict__)
        return stock

    def leer_por_libro(self, libro_id: int) -> Optional[Stock]:
        for s in self.leer_todos():
            if s.libro_id == libro_id:
                return s
        return None

    def actualizar(self, stock: Stock) -> Stock:
        stocks = self.leer_todos()
        actualizado = False
        with open(self.ruta_archivo, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=self.campos)
            writer.writeheader()
            for s in stocks:
                if s.libro_id == stock.libro_id:
                    writer.writerow(stock.__dict__)
                    actualizado = True
                else:
                    writer.writerow(s.__dict__)
        if not actualizado:
            raise ValueError("Stock no encontrado.")
        return stock

    def eliminar(self, libro_id: int) -> bool:
        stocks = self.leer_todos()
        restantes = [s for s in stocks if s.libro_id != libro_id]
        if len(stocks) == len(restantes):
            return False
        with open(self.ruta_archivo, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=self.campos)
            writer.writeheader()
            for s in restantes:
                writer.writerow(s.__dict__)
        return True


class CsvRepositorioCotizacion(IRepositorioCotizacionDolar):
    """Implementacion concreta para CotizacionDolar en CSV."""
    def __init__(self):
        self.ruta_archivo = os.path.join(CSV_DIR, 'cotizaciones.csv')
        self.campos = ['tipo_id', 'fecha', 'valor']
        if not os.path.exists(self.ruta_archivo):
            with open(self.ruta_archivo, mode='w', newline='', encoding='utf-8') as f:
                csv.DictWriter(f, fieldnames=self.campos).writeheader()

    def leer_todos(self) -> List[CotizacionDolar]:
        cots = []
        with open(self.ruta_archivo, mode='r', newline='', encoding='utf-8') as f:
            for fila in csv.DictReader(f):
                fecha_obj = datetime.datetime.strptime(fila['fecha'], '%Y-%m-%d').date()
                cots.append(CotizacionDolar(int(fila['tipo_id']), fecha_obj, float(fila['valor'])))
        return cots

    def crear(self, cotizacion: CotizacionDolar) -> CotizacionDolar:
        if self.leer_por_tipo_y_fecha(cotizacion.tipo_id, cotizacion.fecha):
            raise ValueError("Cotizacion ya existe.")
        datos = cotizacion.__dict__.copy()
        datos['fecha'] = cotizacion.fecha.strftime('%Y-%m-%d')
        with open(self.ruta_archivo, mode='a', newline='', encoding='utf-8') as f:
            csv.DictWriter(f, fieldnames=self.campos).writerow(datos)
        return cotizacion

    def leer_por_tipo_y_fecha(self, tipo_id: int, fecha: datetime.date) -> Optional[CotizacionDolar]:
        for c in self.leer_todos():
            if c.tipo_id == tipo_id and c.fecha == fecha:
                return c
        return None

    def leer_historico_por_tipo(self, tipo_id: int) -> List[CotizacionDolar]:
        return [c for c in self.leer_todos() if c.tipo_id == tipo_id]

    def actualizar(self, cotizacion: CotizacionDolar) -> CotizacionDolar:
        cots = self.leer_todos()
        actualizado = False
        with open(self.ruta_archivo, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=self.campos)
            writer.writeheader()
            for c in cots:
                datos = c.__dict__.copy()
                datos['fecha'] = c.fecha.strftime('%Y-%m-%d')
                if c.tipo_id == cotizacion.tipo_id and c.fecha == cotizacion.fecha:
                    datos_act = cotizacion.__dict__.copy()
                    datos_act['fecha'] = cotizacion.fecha.strftime('%Y-%m-%d')
                    writer.writerow(datos_act)
                    actualizado = True
                else:
                    writer.writerow(datos)
        if not actualizado:
            raise ValueError("Cotizacion no encontrada.")
        return cotizacion

    def eliminar(self, tipo_id: int, fecha: datetime.date) -> bool:
        cots = self.leer_todos()
        restantes = [c for c in cots if not (c.tipo_id == tipo_id and c.fecha == fecha)]
        if len(cots) == len(restantes):
            return False
        with open(self.ruta_archivo, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=self.campos)
            writer.writeheader()
            for c in restantes:
                datos = c.__dict__.copy()
                datos['fecha'] = c.fecha.strftime('%Y-%m-%d')
                writer.writerow(datos)
        return True