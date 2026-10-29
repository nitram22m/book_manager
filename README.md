# Book Manager

## Introducción y contexto

Las librerías necesitan mantener organizada la información de su catálogo y
controlar las operaciones habituales de inventario. Book Manager permite
administrar libros, autores, editoriales, géneros, precios y existencias desde
una aplicación de consola orientada a objetos.

Desde el Sprint 2, la aplicación usa PostgreSQL en Supabase como almacenamiento
principal, accedido mediante SQLAlchemy. El Sprint 3 amplía el catálogo con
consultas éticas al sitio público de Cúspide y alertas de diferencias de
precios, manteniendo la interfaz exclusivamente en consola.

## Objetivo

Gestionar el catálogo y las operaciones de una librería, mantener las
relaciones entre sus entidades, consultar y actualizar cotizaciones, convertir
precios entre pesos argentinos (ARS) y dólares estadounidenses (USD), controlar
las existencias y comparar precios publicados por Cúspide con el catálogo
local.

## Funcionalidades

- Crear, consultar, modificar y eliminar las entidades en Supabase.
- Mantener las relaciones entre libros, autores, editoriales, géneros y
  precios.
- Migrar los datos CSV del Sprint 1 a PostgreSQL al iniciar la aplicación. La
  migración evita insertar registros duplicados y genera los archivos SQL en
  `src/book_manager/migrations/sql/`. En instalaciones existentes agrega de
  forma aditiva la columna nullable de compra para las cotizaciones.
- Consultar cotizaciones del dólar por tipo y guardar compra, venta y la fecha
  informada por DolarApi.
- Mostrar los precios del catálogo en ARS o USD, según la moneda destino y el
  tipo de cotización elegidos; la consulta informa la tasa y fecha aplicadas.
- Consultar existencias, registrar ventas y revisar el historial de
  cotizaciones.
- Exportar el catálogo bimonetario a
  `src/book_manager/reportes/precios_bimonetarios.csv`.
- Buscar hasta diez coincidencias de libros en Cúspide y mostrar el stock
  publicado junto con el stock propio cuando el título coincide. Antes de
  iniciar la búsqueda, la consola solicita el umbral de diferencia de precio
  y también compara y reporta el libro consultado.
- La búsqueda desde el menú solo acepta títulos que ya están en el catálogo;
  los resultados externos se filtran para mostrar únicamente coincidencias
  con el libro propio. En cada publicación se consulta la página de detalle
  para obtener descripción, URL de imagen y formas de pago; si Cúspide no
  publica el precio de una forma de pago, ese importe se indica como no
  informado.
- Guardar las observaciones externas más recientes en la tabla
  `libros_scrapeados`, separada del inventario propio.
- Comparar precios de igual moneda mediante un umbral solicitado por consola.
  Tanto la búsqueda individual como la comparación general generan reportes
  CSV y Excel (`.xlsx`) en `src/book_manager/reportes/` por ejecución, incluso
  cuando no hay alertas. El Excel incluye libro, precio interno, precio web,
  diferencia y fecha de extracción. Los reportes llevan fecha y hora en el
  nombre para conservar análisis anteriores; la consola muestra ambas rutas.
- Auditar las operaciones de persistencia, consultas de negocio, ventas,
  cotizaciones, migraciones, precarga y exportaciones mediante un decorador.
  La tabla `auditoria` registra acción, fecha UTC, parámetros relevantes,
  resultado o error en el campo de detalles.
- Ejecutar el scraping de todo el catálogo, generar reportes desde las
  observaciones ya guardadas sin volver a consultar Cúspide y ver los últimos
  eventos de auditoría desde opciones separadas del menú.
- Precargar los scripts SQL generados durante la migración del Sprint 2 con
  `python -m book_manager.preload_data.preload_data` desde `src`, definiendo
  `PYTHONPATH` para que Python encuentre el paquete.

El spider respeta `robots.txt`, limita las peticiones simultáneas y aplica una
pausa de 1,5 segundos por dominio. Las búsquedas de precios solo comparan
publicaciones con la misma moneda; no se convierten importes entre monedas.
La comparación recorre los títulos del catálogo dentro de una única ejecución
del spider para conservar el retardo global entre peticiones.

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

Para ejecutar manualmente la precarga de scripts SQL desde la raíz en
PowerShell:

```powershell
$env:PYTHONPATH = "src"
python -m book_manager.preload_data.preload_data
```

## Organización del proyecto

### Ejercicio 01: estructura de directorios

El Sprint 3 continúa el trabajo de la rama `Sprint_2` en `Sprint_3`. La
estructura actual del proyecto es:

```text
book_manager/
├── src/
│   └── book_manager/
│       ├── database/
│       │   └── connection.py
│       ├── entities/
│       │   └── entities.py
│       ├── models/
│       │   └── models.py
│       ├── preload_data/
│       │   └── preload_data.py
│       ├── repositories/
│       │   ├── repositories.py
│       │   └── scraped_repository.py
│       ├── scraper/
│       │   ├── items.py
│       │   ├── loaders.py
│       │   ├── pipelines.py
│       │   ├── settings.py
│       │   └── spiders/
│       │       ├── __init__.py
│       │       └── book_spider.py
│       ├── services/
│       │   ├── auditoria.py
│       │   └── services.py
│       ├── migrations/
│       │   ├── csv/
│       │   ├── sql/
│       │   └── migrations.py
│       ├── reportes/          # CSV, Excel y feed de Scrapy
│       ├── ui/
│       │   └── console.py
│       └── main.py
├── scrapy.cfg
├── .env                      # configuración local; excluida de Git
├── CHANGELOG.md
├── README.md
└── requirements.txt
```

La carpeta `src/book_manager/reportes/` almacena los reportes CSV, Excel y el
feed generado por Scrapy. Las salidas se excluyen del control de versiones;
el directorio se conserva mediante `.gitkeep`. El archivo `.env` es local y
no se versiona.
