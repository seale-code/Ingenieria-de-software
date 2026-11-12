## S3-04 — Cambios de estado y soporte básico de pedidos

En esta actividad desarrollé el módulo de soporte de pedidos y validación de los estados finales del reparto.

### Lo que implementé
- Validé el cambio `PREPARADO → EN_CAMINO` y `EN_CAMINO → ENTREGADO`.
- Comprobé que únicamente el repartidor asignado pueda realizar esos cambios.
- Sincronicé el estado de `pedidos` con el estado de `entregas`.
- Exigí que se registren las fechas de salida y recepción antes de confirmar cada transición.
- Implementé la cancelación administrativa antes de la salida y la liberación de reservas activas.
- Al iniciar el reparto, consumo las reservas activas para que el inventario se descuente una sola vez.
- Agregué el registro y consulta de incidencias asociadas a cada pedido.
- Incorporé el flujo de atención `ABIERTA → EN_REVISION → RESUELTA`, con descripción obligatoria de la solución.
- Añadí la migración 004, una interfaz CLI y 25 pruebas unitarias.

### Archivos
- `src/backend/soporte_pedidos_s3.py`
- `src/backend/soporte_pedidos_s3_cli.py`
- `src/database/migrations/004_soporte_incidencias.sql`
- `src/database/database.py`
- `src/database/migrate_josue.py`
- `tests/test_soporte_pedidos_s3.py`
- `sprint-3/S3-04_Anderson_Delerna.md`

### Pruebas
Las 25 pruebas específicas de S3-04 pasaron. También pasaron 160 pruebas de 13 módulos no dependientes de Flask. La suite completa debe repetirse después de instalar `requirements-test.txt`.

### Consideración
La validación de roles está implementada en el servicio, pero el repositorio aún no tiene autenticación real. La integración debe obtener el rol desde una sesión validada del servidor y no confiar en el rol enviado libremente por el cliente.

**Pendiente:** revisión del equipo, validación de la suite completa y aprobación del Pull Request.
