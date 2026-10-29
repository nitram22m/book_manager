## Sprint 3

[Ejercicio 07]
- Se agregaron opciones independientes para ejecutar scraping, generar reportes desde observaciones guardadas y consultar el historial de auditoría.
- El historial muestra hasta 20 eventos recientes y el reporte independiente no vuelve a ejecutar el spider.

[Ejercicio 06]
- Se agregó el decorador de auditoría para operaciones de repositorios, servicios, migración, precarga y exportación.
- Se creó la tabla `auditoria` con acción, fecha UTC y detalles serializados; se registran resultados y errores.

[Ejercicio 05]
- Se agregó `openpyxl` únicamente para generar el reporte Excel `.xlsx`, con los campos libro, precio interno, precio web, diferencia y fecha de extracción; los reportes CSV se generan por separado sin utilizar esa librería.

[Ejercicio 04]
- Se solicita el umbral antes de cada búsqueda o comparación que ejecuta el scraper.
- Ambas opciones comparan precios del catálogo y generan un CSV por ejecución, incluso sin alertas; los archivos incluyen fecha y hora en el nombre para no sobrescribir resultados anteriores.
- La búsqueda individual también muestra las alertas de ese título y conserva el reporte en `src/book_manager/reportes/`.
- Los reportes CSV incluyen la fecha y hora de extracción.

[Ejercicio 03]
- Se agregaron el spider de Cúspide, los items, cargadores y pipelines para limpiar, normalizar y persistir las publicaciones observadas en una tabla separada del stock propio.
- Se normalizaron precios en formato argentino sin símbolo visible en el texto extraído, por ejemplo `37.000,00` a `37000.0 ARS`.
- Se añadió la búsqueda restringida al catálogo propio, con un máximo de diez resultados por título, imagen, descripción detallada, formas de pago y consulta del stock local.
- Se extendió la persistencia para guardar imagen y formas de pago, con migración compatible de la tabla de scraping existente.

[Ejercicio 02]
- Se implementó la precarga transaccional de los scripts SQL generados durante la migración del Sprint 2, respetando el orden de dependencias.

[Ejercicio 01]
- Se organizó el código Scrapy en `src/book_manager/scraper/` y los reportes CSV en `src/book_manager/reportes/`, documentando la estructura en el README.
- Se incorporaron las dependencias y la configuración necesarias para Scrapy.

## Sprint 2

[Correcciones TP2]
- Restauración de las interfaces CRUD y de las firmas específicas para Stock y cotizaciones.
- Registro de compra, venta y fecha informada por DolarApi; alta automática de tipos conocidos faltantes y migración aditiva de la columna de compra.
- Selección de moneda destino ARS/USD e informe de la tasa y fecha aplicadas en la lista de precios.
- Validación local y remota de la migración y el CRUD; los registros remotos de prueba se limpiaron.

[Ejercicio 08]
- Se agregaron opciones para consultar cotizaciones con DolarApi, ver precios en ARS y USD según el tipo de dólar elegido y exportar a CSV los precios originales de todas las monedas, con equivalencia en ARS para los libros en USD.
- Se ajustaron las anotaciones de tipo y se corrigieron detalles de formato para mantener el código conforme a PEP 8.

[Ejercicio 07]
- Conexión con DolarApi para consultar y guardar en Supabase las cotizaciones actuales del dólar.

[Ejercicio 06]
- Adaptación de la aplicación para que las altas, consultas, modificaciones y bajas trabajen con la base de datos de Supabase.

[Ejercicio 05]
- Migración de los datos CSV del TP1 a Supabase mediante SQLAlchemy.

[Ejercicio 04]
- Definición de modelos ORM relacionales con SQLAlchemy para las nueve entidades y sus relaciones.

[Ejercicio 03]
- Implementación del context manager para sesiones transaccionales con commit, rollback y cierre.

[Ejercicio 02]
- Implementación de ConexionDB para conectar con PostgreSQL/Supabase mediante SQLAlchemy y psycopg.

[Ejercicio 01]
- Incorporación de las dependencias del Sprint 2 y exclusión de la configuración local del versionado.

## Sprint 1

[Ejercicio 08]
- Aplicacion de correcciones del profesor sobre entidades y POO.
- Encapsulamiento de atributos, relaciones entre objetos y validaciones.
- Actualizacion de repositorios, servicios, consola y datos CSV para el nuevo modelo.

[Ejercicio 07]
- Implementacion de main.py como punto de entrada del sistema.
- Integracion de la precarga inicial con el menu de consola.

[Ejercicio 06]
- Implementacion del menu interactivo por consola con operaciones CRUD.
- Conexion de la interfaz con servicios y repositorios CSV.
- Incorporacion de reportes de catalogo e historico de cotizaciones.
- Listados de IDs relacionados y disponibles antes de cada solicitud de dato.

[Ejercicio 05]
- Incorporacion de ocho archivos CSV con diez registros por entidad.
- Implementacion del script de precarga de datos iniciales.
- Precarga de historial de cotizaciones para los tipos Oficial, Blue y MEP.

[Ejercicio 04]
- Implementacion de la capa de servicios y logica de negocio.
- Conversion de precios USD a ARS con la cotizacion disponible.
- Validacion de ventas y actualizacion del stock.

[Ejercicio 03]
- Implementacion de interfaces y repositorios para guardar entidades en archivos CSV.
- Implementacion de operaciones CRUD con manejo de las claves de Stock y CotizacionDolar.

[Ejercicio 02]
- Definicion de las entidades principales con dataclasses y anotaciones de tipo.

[Ejercicio 01]
- Inicializacion del repositorio Git y configuracion del remoto.
- Creacion de la rama Sprint_1.
- Creacion del README.md con el objetivo y contexto del proyecto.
- Creacion del CHANGELOG.md y configuracion del archivo .gitignore.
