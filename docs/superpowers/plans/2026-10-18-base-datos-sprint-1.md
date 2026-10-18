# Base de datos del Sprint 1 — Implementation Plan

> **For agentic workers:** usar superpowers:executing-plans para implementar este plan en la sesión. Las casillas registran el avance.

**Goal:** entregar una base SQLite reproducible con categorías, productos, sucursales e inventario, datos ficticios y pruebas de integridad.

**Architecture:** esquema SQL versionado y un módulo Python de biblioteca estándar para inicializar, cargar la demostración y consultar stock. La base generada se guarda en `data/` y no se publica como archivo binario.

**Tech Stack:** Python 3.10 o superior, SQLite 3.24 o superior, sqlite3 y unittest; sin dependencias externas.

**Spec:** alcance existente en `docs/03-diagramas/MODELO_DATOS.md`, tareas S1-06 y S1-07 de `sprint-1/README.md` y petición de implementar la base de datos.

## Global Constraints

- Solo base de datos de Sprint 1. Pedido, reserva, entrega y autenticación quedan para sus sprints.
- Stock entero, no negativo, obligatorio y único por par producto/sucursal.
- Claves foráneas activas en cada conexión del módulo.
- Coordenadas ficticias de sucursales, con rango validado; no se implementa todavía orden por cercanía.
- Repetir inicialización/carga de demo no elimina datos ni restablece stock modificado.
- Rechazar bases ajenas o versiones no soportadas; no incluir comandos destructivos.

## Review Focus

- Actualizar stock a un valor negativo/fraccionario debe fallar igual que insertarlo.
- Referencias inexistentes y borrado de entidades con inventario deben rechazarse.
- Volver a cargar la demo debe conservar un stock ya editado.
- Consultar una ruta inexistente no debe crear una base vacía accidentalmente.
- Búsquedas con apóstrofos, comodines o texto SQL deben tratarse como datos literales.

## Task 1: esquema y datos

**Files:** `src/database/schema.sql`, `src/database/seed.sql`, `tests/test_database.py`.

**Interfaces:** tablas `categorias`, `productos`, `sucursales`, `inventario`; códigos únicos para identificar datos demo; vista `v_disponibilidad` para consulta.

- [x] Escribir pruebas sobre una base SQLite temporal para las restricciones y datos demo.
- [x] Ejecutarlas y confirmar fallo porque falta el esquema.
- [x] Implementar el esquema y datos: categorías DEMO-X/DEMO-Y; productos DEMO-A/DEMO-B/DEMO-C; sucursales DEMO-NORTE/DEMO-SUR; cantidades A=(5,0), B=(0,3), C=(0,0).
- [x] Confirmar que las pruebas pasan sin mocks.

## Task 2: creación y consulta reproducibles

**Files:** `src/database/database.py`, `src/database/__main__.py`, `src/database/__init__.py`, `.gitignore`; ampliar `tests/test_database.py`.

**Interfaces:** `initialize_database(path, demo=False)`, `seed_demo(path)`, `get_stock(path, search='', category=None, branch=None, available_only=False)`; CLI `python -m src.database init --demo`, `seed`, `stock`, con `--db` por comando.

- [x] Añadir pruebas de idempotencia, protección de otras bases, filtros combinados y errores de CLI.
- [x] Observar fallos por interfaz no implementada.
- [x] Implementar inicialización con identificación/versionado, carga transaccional y consulta con parámetros.
- [x] Ejecutar toda la suite y los comandos documentados en una base temporal.

## Task 3: documentación y publicación

**Files:** README de base de datos, modelo, informe de pruebas, estado del proyecto y planes de sprint afectados.

- [x] Documentar comandos, tablas, datos demo, conexión con claves foráneas y límites del incremento.
- [x] Actualizar estado a implementado y probado, pendiente de revisión del equipo; no cerrar Issues ni declarar terminado el sprint.
- [x] Revisar código y cambios completos, ejecutar la suite y verificar que no se publica la base generada.
- Publicación: verificar el commit y contenido remoto después de subir este incremento.
