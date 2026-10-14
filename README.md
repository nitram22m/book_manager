# Book Manager

## Introducción y Contexto del problema

Las librerías necesitan mantener organizada la información de su catálogo y
controlar las operaciones habituales de inventario. Cuando los datos de libros,
autores, editoriales, géneros, precios y existencias se registran sin una
estructura común, resulta más difícil consultarlos, actualizarlos y evitar
inconsistencias entre ellos. También es necesario considerar que los precios
pueden expresarse en distintas monedas y que su conversión depende de la
cotización seleccionada.

Book Manager propone una aplicación de consola para administrar esa información
con un diseño orientado a objetos. El sistema representa los elementos del
dominio mediante entidades relacionadas entre sí, valida los datos ingresados y
ofrece operaciones para gestionar el catálogo, consultar precios y existencias,
registrar ventas y revisar el historial de cotizaciones.

Los datos se persisten en archivos CSV. Aunque los archivos almacenan
identificadores para representar las referencias, la aplicación resuelve esas
referencias y trabaja con objetos de las clases correspondientes. Así, por
ejemplo, un libro se relaciona con instancias de Autor, Editorial, Género y
Precio, en lugar de depender únicamente de valores numéricos.

## Objetivo

Desarrollar un sistema de gestión de inventario para una librería que permita
mantener el catálogo y sus datos asociados, consultar precios en pesos
argentinos y registrar ventas con control de stock.

## Funcionalidades

- Crear, consultar, modificar y eliminar entidades del sistema.
- Administrar libros y sus relaciones con autores, editoriales, géneros y
  precios.
- Consultar el precio de un libro en ARS, usando la cotización disponible más
  reciente cuando su precio está expresado en USD.
- Consultar existencias y registrar ventas sin permitir stock negativo.
- Consultar el historial de cotizaciones por tipo.
- Precargar datos de ejemplo cuando los archivos correspondientes están vacíos.

## Organización del proyecto

- `src/book_manager/entities/`: entidades y reglas de validación del dominio.
- `src/book_manager/repositories/`: persistencia CSV y operaciones CRUD.
- `src/book_manager/services/`: lógica de negocio.
- `src/book_manager/ui/`: interfaz de consola.
- `src/book_manager/preload_data/`: carga de datos de ejemplo.
- `src/book_manager/migrations/csv/`: archivos de datos CSV.
