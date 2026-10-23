# Inkafarma — Trabajo de Josue Mogollon

**Revisión de Issues públicos al 22/10/2026.** El responsable figura por nombre en los planes, pero la cuenta de GitHub todavía no está asignada a los Issues. La situación técnica del repositorio debe verificarse de nuevo antes de integrar cambios.

| Sprint | Issue | Tarea | Estado observado en GitHub | Entregable |
|---|---|---|---|---|
| 1 | #6 / S1-06 | Modelo Producto–Sucursal–Inventario | Implementado, en revisión de equipo | Revisión de código, integridad y evidencia (ya existe en repositorio) |
| 1 | #3 / S1-07 | Crear BD y datos ficticios | Implementado; el tablero llegó a mostrar En progreso; validación de equipo pendiente | Revisar evidencia de 24 pruebas y confirmar aceptación (ya existe) |
| 2 | #21 / S2-03 | Modelo pedidos/detalles/reservas | Por hacer | `002_pedidos_reservas.sql` + pruebas |
| 3 | #19 / S3-03 | Repartidores/entregas/historial | Por hacer | `003_entregas_historial.sql` + pruebas |

## Qué incluye esta propuesta

- Cambios **incrementales**: no toca ni reemplaza `schema.sql` ni `seed.sql` del Sprint 1.
- Tablas con claves foráneas, validaciones de cantidades y prevención de reserva excesiva, protegida por triggers SQLite.
- Descuento de inventario cuando se consume una reserva y liberación sin descuento.
- Registro de repartidores, entregas con fechas e historial automático del estado de cada pedido.
- Migraciones v1→v2→v3, sin reiniciar tablas ni borrar la base anterior.
- Pruebas de integración SQLite.

**Importante:** Esta entrega contiene **solo archivos nuevos y una adaptación guiada**; la versión completa del repositorio debe clonarse primero. Esta es una implementación propuesta, probada localmente contra una reproducción del esquema `schema.sql` v1 publicado en el repositorio. No ha sido integrada a GitHub ni revisada por los compañeros. No es aún una tarea cerrada en Scrum.

## Instrucciones exactas para integrar

1. Clona el repositorio original o abre tu copia local. Crea una rama:

   ```bash
   git switch -c feature/josue-modelos-s2-s3
   ```

2. Copia el contenido de las carpetas `src/` y `tests/` de este ZIP a las rutas **equivalentes** del repositorio. **No reemplaces** los archivos anteriores.
3. Copia también el archivo `aplicar_compatibilidad.py` a la raíz del repositorio. Desde la raíz ejecuta:

   ```bash
   python aplicar_compatibilidad.py
   ```

   El script verifica el texto original y crea un archivo de respaldo `database.py.bak` antes de modificar. Si el repositorio ya cambió o el script se niega por precaución, edita `src/database/database.py`: añade `SUPPORTED_SCHEMA_VERSIONS = (1, 2, 3)` bajo `SCHEMA_VERSION = 1` y cambia la comparación `... != SCHEMA_VERSION` por `... not in SUPPORTED_SCHEMA_VERSIONS` **solo** en `_validate_database`. Conserva `SCHEMA_VERSION = 1` porque el esquema base que instala `init` es la versión 1.

4. Inicializa la BD si aún no existe:

   ```bash
   python -m src.database init --demo
   ```

5. Migra una **copia de prueba** de tu base primero:

   ```bash
   python -m src.database.migrate_josue --db data/inkafarma.sqlite3 --hasta 2
   python -m src.database.migrate_josue --db data/inkafarma.sqlite3 --hasta 3
   ```

   Puedes migrar directamente a v3 sin indicar `--hasta`. Repetir la migración no aplica cambios adicionales. Antes de migrar la base real, haz una copia de seguridad.

6. Corre todas las pruebas anteriores y nuevas:

   ```bash
   python -m unittest discover -s tests -v
   ```

7. Revisa los cambios y abre un PR, enlazando Issues `#21` y `#19` **sin cerrarlos automáticamente** hasta la revisión.

   ```bash
   git status
   git add src/database/migrations src/database/migrate_josue.py src/database/database.py tests/test_josue_migrations.py
   git commit -m "feat(database): modelos y migraciones de pedidos y entregas"
   git push -u origin feature/josue-modelos-s2-s3
   ```

## Evidencias técnicas y demostración

Al correr `python -m unittest tests.test_josue_migrations -v`, comprobar que:

- 12 pruebas del nuevo modelo aprueban; se ejecutaron localmente contra una reproducción fiel del esquema v1.
- Dos pedidos que intentan reservar más de las 5 unidades disponibles no pueden hacerlo simultáneamente; SQLite impide la segunda reserva.
- Consumir una reserva descuenta una vez las unidades del inventario; liberar una reserva no reduce el stock.
- Un pedido guarda su detalle y sucursal; cada entrega se vincula al pedido y al repartidor.
- Cambiar `pedidos.estado` registra automáticamente la transición en `historial_estados`.
- El esquema sigue cumpliendo `PRAGMA foreign_key_check`.

Registrar pantallazos del terminal, nombre del responsable que revisó, commit SHA y resultado de los casos adicionales en cada Issue. La aprobación de la prueba local no significa que el sistema completo esté integrado.

## Decisiones que debe validar el equipo

1. Los **estados del pedido y de la entrega** son una propuesta. El equipo debe acordar las transiciones y permisos antes de integrar el backend S3-04.
2. La **caducidad de reservas** tiene columna `fecha_vencimiento`, pero aún no se libera automáticamente: se requiere política, proceso periódico y pruebas (HU02).
3. La **asignación de sucursal** por distancia/capacidad pertenece al backend y a la definición de reglas del Sprint 2; no se implementa aquí.
4. La **actualización de estados de entrega** y su sincronización con los estados de pedido quedará a cargo del servicio de backend que acuerde el equipo. La BD registra eventos de `pedidos.estado` pero no sustituye ese servicio.
5. Las reservas se crean en estado `ACTIVA` y deben cerrarse explícitamente en `LIBERADA` o `CONSUMIDA` (con `fecha_cierre`). Las operaciones de creación de pedido/detalle/reserva deben hacerse en una transacción `BEGIN IMMEDIATE` del backend para garantizar atomicidad y evitar sobreventa al concurrir escritores.
6. Se permite **una sola reserva por producto y pedido**, correspondiente a la cantidad solicitada; modificaciones requieren un nuevo flujo de negocio definido.

## Cierre correcto de las cuatro tareas

- Issues #6 y #3: pedir revisión al equipo, verificar pruebas reproducidas y registrar evidencia; si son aceptadas, actualizar el tablero y cerrar ambos Issues.
- Issue #21: integrar migración v2, ejecutar pruebas, demostrar caso de reserva excedida y recibir revisión.
- Issue #19: integrar migración v3, demostrar vínculo pedido/repartidor, fechas e historial, ejecutar pruebas y recibir revisión.
- Actualizar el README del sprint y el tablero una vez integrados los cambios; no afirmar que Sprint 2 o 3 esté completo por tener listas las tablas.
