"""Modelos relacionales de Book Manager para SQLAlchemy."""

from __future__ import annotations

from datetime import date

from sqlalchemy import Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Clase base de los modelos ORM del proyecto."""


class Autor(Base):
    """Autor asociado a uno o más libros."""

    __tablename__ = "autores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    libros: Mapped[list[Libro]] = relationship(back_populates="autor")


class Editorial(Base):
    """Editorial asociada a los libros publicados."""

    __tablename__ = "editoriales"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    libros: Mapped[list[Libro]] = relationship(back_populates="editorial")


class Genero(Base):
    """Género literario asociado a los libros del catálogo."""

    __tablename__ = "generos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    libros: Mapped[list[Libro]] = relationship(back_populates="genero")


class Moneda(Base):
    """Moneda en la que se expresa un precio."""

    __tablename__ = "monedas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(10), nullable=False)
    simbolo: Mapped[str] = mapped_column(String(10), nullable=False)
    precios: Mapped[list[Precio]] = relationship(back_populates="moneda")


class TipoCotizacion(Base):
    """Tipo de cotización de dólar registrado en el sistema."""

    __tablename__ = "tipo_cotizacion"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(50), nullable=False)
    cotizaciones: Mapped[list[CotizacionDolar]] = relationship(
        back_populates="tipo"
    )


class Precio(Base):
    """Precio de un libro y su moneda asociada."""

    __tablename__ = "precios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    valor: Mapped[float] = mapped_column(Float, nullable=False)
    moneda_id: Mapped[int] = mapped_column(
        ForeignKey("monedas.id"),
        nullable=False,
    )
    moneda: Mapped[Moneda] = relationship(back_populates="precios")
    libros: Mapped[list[Libro]] = relationship(back_populates="precio")


class Libro(Base):
    """Libro relacionado con autor, editorial, género y precio."""

    __tablename__ = "libros"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    isbn: Mapped[str] = mapped_column(String(32), nullable=False)
    titulo: Mapped[str] = mapped_column(String(255), nullable=False)
    autor_id: Mapped[int] = mapped_column(
        ForeignKey("autores.id"),
        nullable=False,
    )
    editorial_id: Mapped[int] = mapped_column(
        ForeignKey("editoriales.id"),
        nullable=False,
    )
    genero_id: Mapped[int] = mapped_column(
        ForeignKey("generos.id"),
        nullable=False,
    )
    precio_id: Mapped[int] = mapped_column(
        ForeignKey("precios.id"),
        nullable=False,
    )
    autor: Mapped[Autor] = relationship(back_populates="libros")
    editorial: Mapped[Editorial] = relationship(back_populates="libros")
    genero: Mapped[Genero] = relationship(back_populates="libros")
    precio: Mapped[Precio] = relationship(back_populates="libros")
    stock: Mapped[Stock | None] = relationship(back_populates="libro")


class Stock(Base):
    """Existencias de un libro, identificadas por su libro asociado."""

    __tablename__ = "stock"

    libro_id: Mapped[int] = mapped_column(
        ForeignKey("libros.id"),
        primary_key=True,
    )
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False)
    libro: Mapped[Libro] = relationship(back_populates="stock")


class CotizacionDolar(Base):
    """Cotización de un tipo de dólar para una fecha determinada."""

    __tablename__ = "cotizaciones"

    tipo_id: Mapped[int] = mapped_column(
        ForeignKey("tipo_cotizacion.id"),
        primary_key=True,
    )
    fecha: Mapped[date] = mapped_column(Date, primary_key=True)
    valor: Mapped[float] = mapped_column(Float, nullable=False)
    tipo: Mapped[TipoCotizacion] = relationship(
        back_populates="cotizaciones"
    )
