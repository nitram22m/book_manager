"""Configuración y manejo de sesiones de PostgreSQL."""

from contextlib import contextmanager
from functools import lru_cache
import os
from pathlib import Path
from typing import Generator

from dotenv import load_dotenv
from sqlalchemy import Engine, create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

ROOT_DIR = Path(__file__).resolve().parents[3]
load_dotenv(ROOT_DIR / ".env")


class ConexionDB:
    """Administra el motor y las sesiones de SQLAlchemy."""

    def __init__(self, database_url: str | None = None) -> None:
        """Crea el motor a partir de la URL recibida o de DATABASE_URL."""
        url = database_url or os.getenv("DATABASE_URL")
        if not url:
            raise RuntimeError(
                "No se configuró DATABASE_URL. Defínala en el archivo .env."
            )

        connection_url = make_url(url)
        if connection_url.drivername == "postgresql":
            connection_url = connection_url.set(
                drivername="postgresql+psycopg"
            )

        uses_transaction_pooler = (
            connection_url.query.get("pgbouncer", "").lower() == "true"
        )
        if uses_transaction_pooler:
            query = dict(connection_url.query)
            query.pop("pgbouncer")
            connection_url = connection_url.set(query=query)

        engine_options: dict[str, object] = {}
        if uses_transaction_pooler:
            engine_options["connect_args"] = {"prepare_threshold": None}

        self.__engine: Engine = create_engine(
            connection_url,
            pool_pre_ping=True,
            **engine_options,
        )
        self.__session_factory = sessionmaker(
            bind=self.__engine,
            autoflush=False,
            expire_on_commit=False,
        )

    @property
    def engine(self) -> Engine:
        """Devuelve el motor de SQLAlchemy asociado a la conexión."""
        return self.__engine

    @contextmanager
    def get_db_session(self) -> Generator[Session, None, None]:
        """Provee una sesión y confirma o revierte su transacción."""
        session = self.__session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


@lru_cache(maxsize=1)
def _conexion_db() -> ConexionDB:
    """Crea una única instancia de conexión para el proceso."""
    return ConexionDB()


def get_engine() -> Engine:
    """Devuelve el motor compartido por los componentes de la aplicación."""
    return _conexion_db().engine


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Abre una sesión transaccional reutilizable en toda la aplicación."""
    with _conexion_db().get_db_session() as session:
        yield session
