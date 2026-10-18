# Base de datos SQLite — Sprint 1

[← Código](../README.md) · [Modelo y relaciones](../../docs/03-diagramas/MODELO_DATOS.md) · [Pruebas realizadas](../../docs/06-evidencias/2026-10-18_base-datos-sprint-1.md)

Implementación de las tareas S1-06 (#6, modelo) y S1-07 (#3, creación y datos ficticios). Lista para revisión del equipo. Responsable propuesto en el plan: Josue Mogollon.

## Requisitos

Python 3.10 o superior con SQLite 3.24 o superior. Solo utiliza la biblioteca estándar; no requiere instalar paquetes ni un servidor de base de datos.

Ejecutar los siguientes comandos **desde la raíz del repositorio**. En Windows se puede usar `py` en lugar de `python`.

## Crear y cargar la demostración

```bash
python -m src.database init --demo
```

Crea `data/inkafarma.sqlite3` con el esquema y datos ficticios. Sin `--demo`, crea únicamente las tablas vacías. Repetir el comando conserva los datos existentes, incluido el stock modificado. Los códigos `DEMO-*` se reservan para los ejemplos; no deben reutilizarse para datos propios.

Para elegir otro archivo, indicar la misma ruta en cada comando:

```bash
python -m src.database init --db "data/otra-demo.sqlite3" --demo
python -m src.database stock --db "data/otra-demo.sqlite3"
```

El módulo identifica el esquema con `application_id` y `user_version`. Rechaza una base ajena o una versión incompatible; no dispone de un comando que borre o reinicie datos. Si cambia el esquema en una versión futura, deberá añadirse una migración explícita.

## Consultar disponibilidad

```bash
python -m src.database stock
python -m src.database stock --buscar "demo A"
python -m src.database stock --sucursal DEMO-NORTE --solo-disponibles
python -m src.database stock --buscar "demo B" --categoria DEMO-Y --sucursal DEMO-SUR --solo-disponibles
```

Devuelve JSON con producto, categoría, sucursal, coordenadas y cantidad. La última consulta devuelve únicamente el producto B en Sur con stock 3. Una búsqueda sin coincidencias devuelve `[]`.

La búsqueda por nombre es parcial, ignora mayúsculas/minúsculas y conserva la distinción de acentos. `%`, `_` y apóstrofos se tratan como texto. Categoría y sucursal usan sus códigos exactos. La consulta se abre en solo lectura y nunca crea una base inexistente.

## Tablas y reglas

| Tabla | Identificación | Regla principal |
|---|---|---|
| `categorias` | `id`; `codigo` único | Código y nombre obligatorios, no vacíos. |
| `productos` | `id`; `codigo` único | Categoría existente obligatoria. |
| `sucursales` | `id`; `codigo` único | Latitud entre -90 y 90; longitud entre -180 y 180. |
| `inventario` | PK compuesta: `producto_id`, `sucursal_id` | Cantidad entera no negativa; producto y sucursal existentes. |

`v_disponibilidad` reúne los datos para las consultas. Un producto puede tener inventario en varias sucursales. Si no existe una fila de inventario para un par, ese par no aparece en la vista; ausencia de registro no se convierte automáticamente en stock cero.

## Datos de ejemplo

| Producto | Categoría | Norte | Sur |
|---|---|---|---|
| Producto demo A / DEMO-A | DEMO-X | 5 | 0 |
| Producto demo B / DEMO-B | DEMO-Y | 0 | 3 |
| Producto demo C / DEMO-C | DEMO-X | 0 | 0 |

Hay 2 categorías, 3 productos, 2 sucursales y 6 registros de inventario. Nombres, cantidades y coordenadas son ficticios; no representan stock ni locales reales.

Para agregar la demo a una base ya inicializada:

```bash
python -m src.database seed
```

La carga es transaccional: un error revierte sus inserciones. Los registros existentes con los mismos códigos y pares se conservan, no se restauran a valores iniciales.

## Uso desde el futuro backend

```python
from src.database.database import DEFAULT_DATABASE, connect_database, get_stock

filas = get_stock(DEFAULT_DATABASE, branch="DEMO-NORTE", available_only=True)

with connect_database(DEFAULT_DATABASE) as conexion:
    # Ejemplo académico de actualización; un endpoint futuro debe validar permisos.
    conexion.execute(
        "UPDATE inventario SET cantidad = ? WHERE producto_id = ? AND sucursal_id = ?",
        (4, 1, 1),
    )
```

El contexto confirma los cambios al salir, revierte ante excepciones y cierra la conexión. Activa `PRAGMA foreign_keys = ON` en cada conexión. Si se usa otro cliente SQLite, también debe activar esa opción por conexión; SQLite no la conserva globalmente.

## Archivos y pruebas

- [schema.sql](schema.sql): esquema versión 1.
- [seed.sql](seed.sql): datos de demostración.
- [database.py](database.py): inicialización, conexiones y consultas parametrizadas.
- [__main__.py](__main__.py): comandos de uso.
- [test_database.py](../../tests/test_database.py): pruebas sobre SQLite real y comandos.

```bash
python -m unittest discover -s tests -v
```

No se publica el archivo generado `.sqlite3`: se reproduce con los scripts y está excluido por `.gitignore`.

## Límites de este incremento

No incluye interfaz, servidor HTTP, autenticación, reservas, pedidos ni movimientos automáticos de inventario. Las coordenadas preparan los datos, pero todavía no calculan cercanía. Este incremento aporta la base técnica de HU14 y no completa esa historia ni todo el Sprint 1.
