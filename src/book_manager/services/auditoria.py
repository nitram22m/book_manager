"""Decorador y persistencia de auditoría para operaciones de la aplicación."""

from contextvars import ContextVar
from datetime import date, datetime, timezone
from functools import wraps
import inspect
import json
from pathlib import Path
from typing import Any, Callable, TypeVar, cast

from sqlalchemy import Table

from book_manager.database.connection import get_db_session, get_engine
from book_manager.models.models import Auditoria

F = TypeVar("F", bound=Callable[..., Any])
_PROFUNDIDAD_AUDITORIA: ContextVar[int] = ContextVar(
    "profundidad_auditoria",
    default=0,
)


def auditar_operacion(funcion: F) -> F:
    """Registra acción, fecha, argumentos y resultado de cada operación.

    Las llamadas decoradas anidadas forman parte de la operación exterior y
    no crean eventos duplicados.
    """
    firma = inspect.signature(funcion)

    @wraps(funcion)
    def envoltura(*args: Any, **kwargs: Any) -> Any:
        """Ejecuta la operación y registra su resultado o excepción."""
        if _PROFUNDIDAD_AUDITORIA.get() > 0:
            return funcion(*args, **kwargs)

        accion = _nombre_accion(funcion, args)
        parametros = _parametros_serializables(firma, args, kwargs)
        fecha = datetime.now(timezone.utc)
        id_evento = _iniciar_evento(accion, fecha, parametros)
        token = _PROFUNDIDAD_AUDITORIA.set(1)
        try:
            resultado = funcion(*args, **kwargs)
        except Exception as error:
            try:
                _finalizar_evento(
                    id_evento,
                    {
                        "parametros": parametros,
                        "estado": "error",
                        "error": (
                            f"{type(error).__name__}: {str(error)[:1000]}"
                        ),
                    },
                )
            except Exception as error_auditoria:
                raise RuntimeError(
                    f"La operación {accion} falló y su auditoría "
                    "no pudo actualizarse."
                ) from error_auditoria
            raise
        else:
            _finalizar_evento(
                id_evento,
                {
                    "parametros": parametros,
                    "estado": "completada",
                    "resultado": _resumen_resultado(resultado),
                },
            )
            return resultado
        finally:
            _PROFUNDIDAD_AUDITORIA.reset(token)

    return cast(F, envoltura)


def _nombre_accion(funcion: Callable[..., Any], args: tuple[Any, ...]) -> str:
    """Incluye el tipo de entidad en las operaciones CRUD genéricas."""
    nombre = funcion.__name__
    instancia = args[0] if args else None
    nombre_clase = (
        type(instancia).__name__
        if instancia is not None
        else funcion.__module__
    )
    entidad = getattr(instancia, "_nombre_entidad", None)
    if isinstance(entidad, str):
        return f"{entidad}.{nombre}"
    return f"{nombre_clase}.{nombre}"


def _parametros_serializables(
    firma: inspect.Signature,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> dict[str, object]:
    """Convierte los argumentos públicos en detalles JSON seguros."""
    vinculados = firma.bind_partial(*args, **kwargs)
    return {
        nombre: _serializar_valor(valor)
        for nombre, valor in vinculados.arguments.items()
        if nombre not in {"self", "cls"}
    }


def _serializar_valor(valor: Any) -> object:
    """Representa valores sin exponer atributos privados."""
    if valor is None or isinstance(valor, (bool, int, float, str)):
        return valor
    if isinstance(valor, (date, datetime)):
        return valor.isoformat()
    if isinstance(valor, Path):
        return str(valor)
    if isinstance(valor, (list, tuple)):
        return [_serializar_valor(elemento) for elemento in valor]
    if isinstance(valor, dict):
        return {
            str(clave): _serializar_valor(elemento)
            for clave, elemento in valor.items()
        }

    detalles: dict[str, object] = {"tipo": type(valor).__name__}
    for atributo in (
        "id",
        "titulo",
        "isbn",
        "nombre",
        "valor",
        "cantidad",
        "libro_id",
        "tipo_id",
        "fecha",
    ):
        try:
            dato = getattr(valor, atributo)
        except AttributeError:
            continue
        if isinstance(dato, (bool, int, float, str, date, datetime)):
            detalles[atributo] = _serializar_valor(dato)
    return detalles


def _resumen_resultado(resultado: Any) -> object:
    """Evita guardar colecciones completas o datos excesivos en auditoría."""
    if resultado is None or isinstance(resultado, (bool, int, float, str)):
        return _serializar_valor(resultado)
    if isinstance(resultado, (list, tuple, set, dict)):
        return {"tipo": type(resultado).__name__, "cantidad": len(resultado)}
    return {"tipo": type(resultado).__name__}


def _iniciar_evento(
    accion: str,
    fecha: datetime,
    parametros: dict[str, object],
) -> int:
    """Persiste el inicio antes de ejecutar la operación auditada."""
    tabla = Auditoria.__table__
    if not isinstance(tabla, Table):
        raise TypeError("El modelo de auditoría no define una tabla SQL.")
    tabla.create(bind=get_engine(), checkfirst=True)
    with get_db_session() as sesion:
        registro = Auditoria(
            accion=accion,
            fecha=fecha,
            detalles=json.dumps(
                {
                    "parametros": parametros,
                    "estado": "iniciada",
                },
                ensure_ascii=False,
            ),
        )
        sesion.add(registro)
        sesion.flush()
        if registro.id is None:
            raise RuntimeError(
                "No se pudo identificar el evento de auditoría."
            )
        return registro.id


def _finalizar_evento(
    id_evento: int,
    detalles: dict[str, object],
) -> None:
    """Actualiza el resultado del evento en una transacción independiente."""
    with get_db_session() as sesion:
        registro = sesion.get(Auditoria, id_evento)
        if registro is None:
            raise RuntimeError(
                f"No se encontró el evento de auditoría {id_evento}."
            )
        registro.detalles = json.dumps(detalles, ensure_ascii=False)
