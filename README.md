# Book Manager

## Introducción y contexto

Las librerías necesitan mantener organizada la información de su catálogo y
controlar las operaciones habituales de inventario. Book Manager permite
administrar libros, autores, editoriales, géneros, precios y existencias desde
una aplicación de consola orientada a objetos.

En el Sprint 2, la aplicación reemplaza los archivos CSV como almacenamiento
principal por una base de datos PostgreSQL en Supabase, accedida mediante
SQLAlchemy. Los archivos CSV del Sprint 1 se conservan como origen de la
migración inicial.

## Objetivo

Gestionar el catálogo y las operaciones de una librería, mantener las
relaciones entre sus entidades, consultar y actualizar cotizaciones, convertir
precios entre pesos argentinos (ARS) y dólares estadounidenses (USD), y
controlar las existencias durante las ventas.

## Funcionalidades

- Crear, consultar, modificar y eliminar las entidades en Supabase.
- Mantener las relaciones entre libros, autores, editoriales, géneros y
  precios.
- Migrar los datos CSV del Sprint 1 a PostgreSQL al iniciar la aplicación. La
  migración evita insertar registros duplicados y genera los archivos SQL en
  `src/book_manager/migrations/sql/`.
- Consultar cotizaciones del dólar por tipo y actualizar los valores desde
  DolarApi.
- Mostrar los precios del catálogo en ARS y USD, según el tipo de cotización
  elegido.
- Consultar existencias, registrar ventas y revisar el historial de
  cotizaciones.
- Exportar el catálogo bimonetario a
  `exports/precios_bimonetarios.csv`.

Las conversiones de precios implementadas están limitadas a ARS y USD. Aunque
el catálogo de monedas contiene otros tipos, no se calculan equivalencias para
ellos.

## Requisitos y configuración

Se requiere Python 3.10 o superior. Las dependencias se instalan con:

```powershell
pip install -r requirements.txt
```

Crear un archivo `.env` en la raíz del proyecto con la URL de conexión a
PostgreSQL y la dirección de la API:

```dotenv
DATABASE_URL=postgresql+psycopg://usuario:contraseña@host:puerto/base
API_URL=https://dolarapi.com/v1/dolares
```

El archivo `.env` contiene configuración local y no debe agregarse al
repositorio.

## Ejecución

Desde la raíz del proyecto, iniciar la aplicación con:

```powershell
python src/book_manager/main.py
```

Al iniciar, la aplicación migra los CSV disponibles a la base de datos y luego
abre el menú interactivo.

## Organización del proyecto

- `src/book_manager/entities/`: entidades y validaciones del dominio.
- `src/book_manager/database/`: conexión a PostgreSQL y sesiones transaccionales.
- `src/book_manager/models/`: modelos ORM y relaciones entre tablas.
- `src/book_manager/repositories/`: operaciones CRUD sobre la base de datos.
- `src/book_manager/services/`: lógica de negocio y consulta de cotizaciones.
- `src/book_manager/ui/`: interfaz de consola.
- `src/book_manager/migrations/`: migración desde los CSV del Sprint 1 y SQL
  generado.
- `src/book_manager/preload_data/`: precarga utilizada en el Sprint 1.
