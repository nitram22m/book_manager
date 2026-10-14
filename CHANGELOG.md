## Sprint 2

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
