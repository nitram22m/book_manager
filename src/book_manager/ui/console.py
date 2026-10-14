"""Interfaz de consola para la gestión del catálogo de la librería."""

import os
from datetime import date
from typing import Any

from book_manager.entities.entities import (
    Autor,
    CotizacionDolar,
    Editorial,
    Genero,
    Libro,
    Moneda,
    Precio,
    Stock,
    TipoCotizacion,
)
from book_manager.services.services import ServicioLibreria


class MenuConsola:
    """Gestiona las operaciones del sistema desde la consola."""

    def __init__(self) -> None:
        """Configura los modelos, repositorios y claves de las entidades."""
        self.servicio = ServicioLibreria()
        self.modelos: dict[str, type[Any]] = {
            "Libro": Libro,
            "Genero": Genero,
            "Editorial": Editorial,
            "Autor": Autor,
            "Moneda": Moneda,
            "TipoCotizacion": TipoCotizacion,
            "Precio": Precio,
            "Stock": Stock,
            "CotizacionDolar": CotizacionDolar,
        }
        self.repositorios: dict[str, Any] = {
            "Libro": self.servicio.repo_libros,
            "Genero": self.servicio.repo_generos,
            "Editorial": self.servicio.repo_editoriales,
            "Autor": self.servicio.repo_autores,
            "Moneda": self.servicio.repo_monedas,
            "TipoCotizacion": self.servicio.repo_tipo_cot,
            "Precio": self.servicio.repo_precios,
            "Stock": self.servicio.repo_stock,
            "CotizacionDolar": self.servicio.repo_cotizaciones,
        }
        self.claves: dict[str, tuple[str, ...]] = {
            "Libro": ("id",),
            "Genero": ("id",),
            "Editorial": ("id",),
            "Autor": ("id",),
            "Moneda": ("id",),
            "TipoCotizacion": ("id",),
            "Precio": ("id",),
            "Stock": ("libro_id",),
            "CotizacionDolar": ("tipo_id", "fecha"),
        }
        # Asocia cada referencia con el repositorio de sus opciones.
        self.claves_relacionadas: dict[str, tuple[str, Any]] = {
            "autor_id": ("repo_autores", lambda r: f"  {r.id}: {r.nombre}"),
            "genero_id": ("repo_generos", lambda r: f"  {r.id}: {r.nombre}"),
            "editorial_id": (
                "repo_editoriales",
                lambda r: f"  {r.id}: {r.nombre}",
            ),
            "moneda_id": (
                "repo_monedas",
                lambda r: f"  {r.id}: {r.nombre} ({r.simbolo})",
            ),
            "precio_id": (
                "repo_precios",
                lambda r: f"  {r.id}: {r.valor} {r.moneda.nombre}",
            ),
            "tipo_id": ("repo_tipo_cot", lambda r: f"  {r.id}: {r.nombre}"),
            "stock_id": (
                "repo_stock",
                lambda r: f"  libro_id={r.libro.id}: cantidad={r.cantidad}",
            ),
            "libro_id": ("repo_libros", lambda r: f"  {r.id}: {r.titulo}"),
        }
        self.campos_entidad: dict[str, tuple[tuple[str, type], ...]] = {
            "Libro": (
                ("id", int), ("isbn", str), ("titulo", str),
                ("autor_id", int), ("editorial_id", int),
                ("genero_id", int), ("precio_id", int),
            ),
            "Genero": (("id", int), ("nombre", str)),
            "Editorial": (("id", int), ("nombre", str)),
            "Autor": (("id", int), ("nombre", str)),
            "Moneda": (
                ("id", int), ("nombre", str), ("simbolo", str),
            ),
            "TipoCotizacion": (("id", int), ("nombre", str)),
            "Precio": (
                ("id", int), ("valor", float), ("moneda_id", int),
            ),
            "Stock": (("libro_id", int), ("cantidad", int)),
            "CotizacionDolar": (
                ("tipo_id", int), ("fecha", date), ("valor", float),
            ),
        }

    def limpiar_pantalla(self) -> None:
        """Limpia la terminal según el sistema operativo."""
        os.system("cls" if os.name == "nt" else "clear")

    def mostrar_menu_principal(self) -> None:
        """Muestra el menú principal y despacha la opción seleccionada."""
        while True:
            print("\n=== BOOK MANAGER - SPRINT 1 ===")
            print("1. Gestionar entidades (CRUD)")
            print("2. Consultar precio de un libro en ARS")
            print("3. Consultar stock disponible")
            print("4. Registrar venta")
            print("5. Reporte de libros y stock")
            print("6. Consultar historico de cotizaciones")
            print("7. Salir")
            opcion = input("Seleccione una opcion: ").strip()

            if opcion == "1":
                self.menu_entidades()
            elif opcion == "2":
                self.consultar_precio()
            elif opcion == "3":
                self.consultar_stock()
            elif opcion == "4":
                self.vender_libro()
            elif opcion == "5":
                self.mostrar_reporte_catalogo()
            elif opcion == "6":
                self.consultar_historico_cotizaciones()
            elif opcion == "7":
                print("Saliendo del sistema.")
                return
            else:
                print("Opcion invalida.")

    def menu_entidades(self) -> None:
        """Permite seleccionar una entidad para administrar."""
        nombres = list(self.modelos)
        while True:
            print("\n--- ENTIDADES ---")
            for indice, nombre in enumerate(nombres, start=1):
                print(f"{indice}. {nombre}")
            print(f"{len(nombres) + 1}. Volver")
            opcion = input("Seleccione una entidad: ").strip()
            if opcion == str(len(nombres) + 1):
                return
            if not opcion.isdigit() or not 1 <= int(opcion) <= len(nombres):
                print("Opcion invalida.")
                continue
            self.menu_crud(nombres[int(opcion) - 1])

    def menu_crud(self, nombre: str) -> None:
        """Muestra las operaciones CRUD disponibles para una entidad."""
        while True:
            print(f"\n--- {nombre} ---")
            print("1. Listar")
            print("2. Crear")
            print("3. Modificar")
            print("4. Eliminar")
            print("5. Volver")
            opcion = input("Seleccione una operacion: ").strip()
            try:
                if opcion == "1":
                    self.listar_entidades(nombre)
                elif opcion == "2":
                    self.crear_entidad(nombre)
                elif opcion == "3":
                    self.actualizar_entidad(nombre)
                elif opcion == "4":
                    self.eliminar_entidad(nombre)
                elif opcion == "5":
                    return
                else:
                    print("Opcion invalida.")
            except ValueError as error:
                print(f"No se pudo completar la operacion: {error}")

    def listar_entidades(self, nombre: str) -> None:
        """Lista los registros almacenados de la entidad indicada."""
        registros = self.repositorios[nombre].leer_todos()
        if not registros:
            print("No hay registros.")
            return
        for registro in registros:
            print(registro)

    def crear_entidad(self, nombre: str) -> None:
        """Solicita los datos de una entidad y la guarda en su repositorio."""
        entidad = self.leer_entidad(nombre)
        self.repositorios[nombre].crear(entidad)
        print("Registro creado y guardado en CSV.")

    def actualizar_entidad(self, nombre: str) -> None:
        """Solicita una entidad existente y guarda sus nuevos valores."""
        print(f"\nRegistros existentes de {nombre}:")
        self.listar_entidades(nombre)
        clave = self.leer_clave(nombre)
        existente = self.buscar_entidad(nombre, clave)
        if existente is None:
            print("No se encontro el registro.")
            return
        entidad = self.leer_entidad(nombre, existente)
        self.repositorios[nombre].actualizar(entidad)
        print("Registro actualizado en CSV.")

    def eliminar_entidad(self, nombre: str) -> None:
        """Solicita la clave y confirmación antes de eliminar un registro."""
        print(f"\nRegistros existentes de {nombre}:")
        self.listar_entidades(nombre)
        clave = self.leer_clave(nombre)
        existente = self.buscar_entidad(nombre, clave)
        if existente is None:
            print("No se encontro el registro.")
            return
        confirmacion = input(
            "Confirma la eliminacion? (s/n): "
        ).strip().lower()
        if confirmacion != "s":
            print("Eliminacion cancelada.")
            return
        repositorio = self.repositorios[nombre]
        if nombre == "CotizacionDolar":
            eliminado = repositorio.eliminar(clave[0], clave[1])
        else:
            eliminado = repositorio.eliminar(clave[0])
        mensaje = (
            "Registro eliminado."
            if eliminado
            else "No se encontro el registro."
        )
        print(mensaje)

    def leer_clave(self, nombre: str) -> tuple[Any, ...]:
        """Solicita los valores que identifican un registro."""
        valores = []
        for clave in self.claves[nombre]:
            tipo = date if clave == "fecha" else int
            valor = self.leer_valor(f"Ingrese {clave}", tipo)
            valores.append(valor)
        return tuple(valores)

    def buscar_entidad(
        self, nombre: str, clave: tuple[Any, ...]
    ) -> Any | None:
        """Busca un registro mediante la clave correspondiente a su entidad."""
        repositorio = self.repositorios[nombre]
        if nombre == "Stock":
            return repositorio.leer_por_libro(clave[0])
        if nombre == "CotizacionDolar":
            return repositorio.leer_por_tipo_y_fecha(clave[0], clave[1])
        return repositorio.leer_por_id(clave[0])

    def leer_entidad(self, nombre: str, existente: Any | None = None) -> Any:
        """Solicita los campos de una entidad nueva o existente."""
        datos = {}
        claves = self.claves[nombre]
        for campo, tipo in self.campos_entidad[nombre]:
            valor_actual = (
                self._valor_campo(existente, campo) if existente else None
            )
            if existente and campo in claves:
                datos[campo] = valor_actual
                continue
            if existente is None and campo in claves:
                self.mostrar_claves_existentes(nombre)
            self.mostrar_opciones_relacionadas(campo)
            prompt = campo
            if existente:
                prompt += f" [{valor_actual}]"
            datos[campo] = self.leer_valor(
                f"Ingrese {prompt}", tipo, valor_actual
            )
        return self._construir_entidad(nombre, datos)

    def _valor_campo(self, entidad: Any, campo: str) -> Any:
        relaciones = {
            "autor_id": "autor",
            "editorial_id": "editorial",
            "genero_id": "genero",
            "precio_id": "precio",
            "moneda_id": "moneda",
            "libro_id": "libro",
            "tipo_id": "tipo",
        }
        if campo in relaciones:
            return getattr(entidad, relaciones[campo]).id
        return getattr(entidad, campo)

    def _construir_entidad(self, nombre: str, datos: dict[str, Any]) -> Any:
        if nombre in {"Genero", "Editorial", "Autor", "TipoCotizacion"}:
            return self.modelos[nombre](id=datos["id"], nombre=datos["nombre"])
        if nombre == "Moneda":
            return Moneda(datos["id"], datos["nombre"], datos["simbolo"])
        if nombre == "Precio":
            moneda = self._entidad_por_id(
                "repo_monedas", datos["moneda_id"], "Moneda"
            )
            return Precio(datos["id"], datos["valor"], moneda)
        if nombre == "Libro":
            autor = self._entidad_por_id("repo_autores", datos["autor_id"], "Autor")
            editorial = self._entidad_por_id(
                "repo_editoriales", datos["editorial_id"], "Editorial"
            )
            genero = self._entidad_por_id(
                "repo_generos", datos["genero_id"], "Genero"
            )
            precio = self._entidad_por_id(
                "repo_precios", datos["precio_id"], "Precio"
            )
            return Libro(
                datos["id"], datos["isbn"], datos["titulo"],
                autor, editorial, genero, precio,
            )
        if nombre == "Stock":
            libro = self._entidad_por_id(
                "repo_libros", datos["libro_id"], "Libro"
            )
            return Stock(libro, datos["cantidad"])
        if nombre == "CotizacionDolar":
            tipo = self._entidad_por_id(
                "repo_tipo_cot", datos["tipo_id"], "TipoCotizacion"
            )
            return CotizacionDolar(tipo, datos["fecha"], datos["valor"])
        raise ValueError(f"Entidad no soportada: {nombre}")

    def _entidad_por_id(self, nombre_repo: str, id: int, nombre: str) -> Any:
        entidad = getattr(self.servicio, nombre_repo).leer_por_id(id)
        if entidad is None:
            raise ValueError(f"{nombre} con ID {id} no existe.")
        return entidad

    def mostrar_opciones_relacionadas(self, nombre_campo: str) -> None:
        """Muestra las opciones disponibles para un campo relacionado."""
        info = self.claves_relacionadas.get(nombre_campo)
        if info is None:
            return
        atributo_repo, formato = info
        registros = getattr(self.servicio, atributo_repo).leer_todos()
        if not registros:
            print(f"  (No hay registros cargados para {nombre_campo})")
            return
        print(f"Opciones disponibles para {nombre_campo}:")
        for registro in registros:
            print(formato(registro))

    def mostrar_claves_existentes(self, nombre: str) -> None:
        """Muestra las claves en uso para evitar identificadores duplicados."""
        registros = self.repositorios[nombre].leer_todos()
        if not registros:
            print(
                f"  (No hay {nombre} cargados todavia; "
                "puede usar cualquier ID)"
            )
            return
        claves = self.claves[nombre]
        print(f"IDs ya utilizados en {nombre} (elija uno distinto):")
        for registro in registros:
            valores_clave = ", ".join(
                f"{c}={self._valor_campo(registro, c)}" for c in claves
            )
            print(f"  {valores_clave}")

    def mostrar_catalogo_libros(self) -> None:
        """Muestra los libros disponibles y sus identificadores."""
        libros = self.servicio.repo_libros.leer_todos()
        if not libros:
            print("  (No hay libros cargados)")
            return
        print("Libros disponibles:")
        for libro in libros:
            print(f"  {libro.id}: {libro.titulo}")

    def mostrar_catalogo_tipos_cotizacion(self) -> None:
        """Muestra los tipos de cotizacion y su estado de historial."""
        tipos = self.servicio.repo_tipo_cot.leer_todos()
        if not tipos:
            print("  (No hay tipos de cotizacion cargados)")
            return
        tipos_con_datos = {
            c.tipo.id for c in self.servicio.repo_cotizaciones.leer_todos()
        }
        print("Tipos de cotizacion disponibles:")
        for tipo in tipos:
            estado = (
                "con historial"
                if tipo.id in tipos_con_datos
                else "sin historial"
            )
            print(f"  {tipo.id}: {tipo.nombre} ({estado})")

    def leer_valor(
        self, prompt: str, tipo: type[Any], valor_actual: Any | None = None
    ) -> Any:
        """Convierte la entrada y repite la solicitud si no es válida."""
        while True:
            entrada = input(f"{prompt}: ").strip()
            if not entrada and valor_actual is not None:
                return valor_actual
            try:
                if tipo is int:
                    return int(entrada)
                if tipo is float:
                    return float(entrada)
                if tipo is date:
                    return date.fromisoformat(entrada)
                if not entrada:
                    raise ValueError("El campo no puede quedar vacio.")
                return entrada
            except ValueError:
                print("Valor invalido. Vuelva a intentarlo.")

    def consultar_precio(self) -> None:
        """Solicita un libro y muestra su precio convertido a ARS."""
        self.mostrar_catalogo_libros()
        try:
            libro_id = int(input("Ingrese el ID del libro: "))
        except ValueError:
            print("Ingrese un ID numerico valido.")
            return
        libro = self.servicio.repo_libros.leer_por_id(libro_id)
        if libro is None:
            print("Error: El libro no existe.")
            return
        precio = libro.precio
        if precio.moneda.nombre == "ARS":
            print(
                "El libro ya esta en ARS, no requiere conversion: "
                f"${precio.valor:.2f}"
            )
            return
        self.mostrar_tipos_cotizacion_disponibles()
        try:
            tipo_id = int(
                input("Tipo de cotizacion (ID, por defecto Blue=2): ") or "2"
            )
            precio_ars = self.servicio.calcular_precio_ars(libro_id, tipo_id)
            print(f"Precio estimado en ARS: ${precio_ars:.2f}")
        except ValueError as error:
            print(f"Error: {error}")

    def mostrar_tipos_cotizacion_disponibles(self) -> None:
        """Muestra los tipos de cotizacion que tienen historial cargado."""
        cotizaciones = self.servicio.repo_cotizaciones.leer_todos()
        tipos_con_datos = sorted({c.tipo.id for c in cotizaciones})
        if not tipos_con_datos:
            print("  (No hay cotizaciones cargadas)")
            return
        nombres = {
            t.id: t.nombre for t in self.servicio.repo_tipo_cot.leer_todos()
        }
        print("Tipos de cotizacion con historial disponible:")
        for tipo_id in tipos_con_datos:
            print(f"  {tipo_id}: {nombres.get(tipo_id, 'Desconocido')}")

    def consultar_stock(self) -> None:
        """Solicita un libro y muestra sus unidades disponibles."""
        self.mostrar_catalogo_libros()
        try:
            libro_id = int(input("Ingrese el ID del libro: "))
            cantidad = self.servicio.consultar_stock(libro_id)
            print(f"Stock disponible: {cantidad}")
        except ValueError:
            print("Ingrese un ID numerico valido.")

    def vender_libro(self) -> None:
        """Solicita un libro y una cantidad para registrar la venta."""
        self.mostrar_catalogo_libros()
        try:
            libro_id = int(input("Ingrese el ID del libro: "))
            cantidad = int(input("Ingrese la cantidad a vender: "))
            self.servicio.vender_libro(libro_id, cantidad)
            print("Venta registrada y stock actualizado en CSV.")
        except ValueError as error:
            print(f"Error en la operacion: {error}")

    def mostrar_reporte_catalogo(self) -> None:
        """Muestra el catálogo con stock y precio calculado por libro."""
        libros = self.servicio.repo_libros.leer_todos()
        if not libros:
            print("No hay libros registrados.")
            return
        for libro in libros:
            cantidad = self.servicio.consultar_stock(libro.id)
            try:
                monto = self.servicio.calcular_precio_ars(libro.id, 2)
                precio = f"${monto:.2f} ARS"
            except ValueError:
                precio = "No disponible"
            print(
                f"{libro.id} | {libro.titulo} | "
                f"stock={cantidad} | precio={precio}"
            )

    def consultar_historico_cotizaciones(self) -> None:
        """Solicita un tipo de cotización y muestra su historial ordenado."""
        self.mostrar_catalogo_tipos_cotizacion()
        try:
            tipo_id = int(input("Ingrese el ID del tipo de cotizacion: "))
        except ValueError:
            print("Ingrese un ID numerico valido.")
            return
        historico = self.servicio.repo_cotizaciones.leer_historico_por_tipo(
            tipo_id
        )
        if not historico:
            print("No hay cotizaciones para ese tipo.")
            return
        for cotizacion in sorted(historico, key=lambda item: item.fecha):
            print(f"{cotizacion.fecha.isoformat()} | {cotizacion.valor:.2f}")


def iniciar_app() -> None:
    """Crea el menú de consola e inicia el ciclo de interacción."""
    menu = MenuConsola()
    menu.mostrar_menu_principal()