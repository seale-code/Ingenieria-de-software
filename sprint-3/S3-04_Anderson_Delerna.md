# S3-04 — Cambios de estado y soporte básico de pedidos

**Proyecto:** Inkafarma — Ingeniería de Software (UPCH)  
**Sprint:** 3  
**Responsable:** Anderson Delerna  
**Issue:** [#22 — Cambios de estado y soporte básico](https://github.com/seale-code/Ingenieria-de-software/issues/22)  
**Requisito:** `RF-S3-04`  
**Estado de esta entrega:** implementación local y pruebas específicas aprobadas; integración y revisión del equipo pendientes.

## 1. Qué desarrollé

En esta actividad implementé el módulo que faltaba para completar el flujo de reparto y soporte de los pedidos. Reutilicé la base de datos oficial de los Sprints 2 y 3, junto con las funciones de preparación, repartidores y entregas que ya estaban en el repositorio.

Separé las responsabilidades para no duplicar el trabajo de mis compañeros:

- El módulo de preparación sigue gestionando `REGISTRADO/ASIGNADO → EN_PREPARACION → PREPARADO`.
- El módulo de entregas sigue registrando al repartidor y las fechas de salida y recepción.
- Mi módulo valida las transiciones finales de reparto, sincroniza el estado del pedido con el estado de la entrega y registra incidencias vinculadas al pedido.

También incorporé una migración incremental para guardar las incidencias sin reemplazar las tablas anteriores.

## 2. Archivos de mi entrega

| Archivo | Qué contiene |
|---|---|
| `src/backend/soporte_pedidos_s3.py` | Validación de permisos, cambios de estado, cancelación e incidencias. |
| `src/backend/soporte_pedidos_s3_cli.py` | Comandos para demostrar las funciones desde la terminal. |
| `src/database/migrations/004_soporte_incidencias.sql` | Tabla, índices y restricciones de incidencias. |
| `tests/test_soporte_pedidos_s3.py` | 25 pruebas del módulo S3-04. |
| `sprint-3/S3-04_Anderson_Delerna.md` | Explicación de mi implementación y cómo probarla. |
| `sprint-3/S3-04_comentario_issue_22.md` | Texto que preparé para comentar en el issue. |
| `sprint-3/S3-04_evidencia_pruebas.txt` | Resultado de las pruebas ejecutadas. |

También actualicé dos archivos de infraestructura para reconocer la nueva versión de la base de datos:

- `src/database/database.py`: ahora acepta el esquema versión 4.
- `src/database/migrate_josue.py`: registra la migración 004 y permite aplicarla con `--hasta 4`. Conservé el destino predeterminado en versión 3 para no cambiar el comportamiento de las pruebas anteriores.

## 3. Reglas de estado que implementé

No reemplacé las transiciones de preparación que ya desarrolló Cesar. Mi módulo se encarga de las etapas de reparto:

| Estado actual | Estado nuevo | Quién puede hacerlo | Condición |
|---|---|---|---|
| `PREPARADO` | `EN_CAMINO` | Repartidor asignado | Debe existir la fecha de salida. |
| `EN_CAMINO` | `ENTREGADO` | Repartidor asignado | Deben existir la fecha de salida y la fecha de recepción. |
| `REGISTRADO`, `ASIGNADO`, `EN_PREPARACION` o `PREPARADO` | `CANCELADO` | Administrador | El repartidor todavía no debe haber salido. |

Cuando cambio el pedido a `EN_CAMINO` o `ENTREGADO`, actualizo también `entregas.estado` dentro de la misma transacción. Al iniciar el reparto, paso las reservas activas a `CONSUMIDA`; el trigger de la migración 002 descuenta el inventario exactamente una vez. El trigger de la migración 003 registra automáticamente los cambios del pedido en `historial_estados`.

Cuando cancelo antes de la salida, libero las reservas `ACTIVA` como `LIBERADA` en la misma transacción. No descuento inventario al liberar una reserva.

## 4. Permisos que apliqué

Para este MVP utilicé los siguientes roles:

| Rol | Acciones |
|---|---|
| `PERSONAL_SUCURSAL` | Registrar incidencias de pedidos de su propia sucursal y consultar las de esa sucursal. |
| `REPARTIDOR` | Cambiar el estado de sus entregas, reportar incidencias de sus pedidos y consultar las incidencias de sus entregas. |
| `ASESOR` | Consultar incidencias y pasarlas a revisión o resolverlas. |
| `ADMINISTRADOR` | Consultar y gestionar incidencias, además de cancelar pedidos antes de la salida. |

Para reportar una incidencia desde sucursal uso como `actor_id` el ID de la sucursal. Para un repartidor uso el ID del repartidor y compruebo que esté asociado a la entrega.

**Límite de seguridad:** el repositorio todavía no cuenta con autenticación completa de usuarios. Por eso, el rol se recibe como parámetro del servicio y se valida la política de acceso, pero este parámetro no demuestra por sí solo la identidad de quien realiza la solicitud. Antes de publicar endpoints, la aplicación debe obtener el rol y el ID desde una sesión autenticada del servidor, nunca confiar en valores enviados libremente por el cliente.

## 5. Registro y atención de incidencias

Agregué la tabla `incidencias_pedido`, relacionada con `pedidos` mediante una clave foránea.

Las categorías que permito son:

- `RETRASO`
- `PRODUCTO_FALTANTE`
- `PRODUCTO_DANADO`
- `DIRECCION_INCORRECTA`
- `CLIENTE_AUSENTE`
- `OTRO`

Cada incidencia guarda su descripción, quién la reportó, su estado y las fechas de creación, actualización y resolución.

El flujo de atención es:

```text
ABIERTA → EN_REVISION → RESUELTA
```

Para marcarla como resuelta exijo una descripción de la solución. La base de datos impide saltar estados y borrar incidencias, de modo que se conserva la trazabilidad.

## 6. Cómo preparar la base de datos

Primero debo estar en la raíz del repositorio. Si ya tengo la base de datos de los Sprints 2 y 3, hago una copia de respaldo y aplico únicamente la nueva migración:

```bash
python -m src.database.migrate_josue --db data/inkafarma.sqlite3 --hasta 4
```

La migración agrega la tabla de incidencias y actualiza `user_version` a 4. No vuelve a crear pedidos, reservas, repartidores ni entregas.

Si estoy creando una base de demostración nueva, puedo ejecutar:

```bash
python -m src.database init --demo --db .test-tmp/demo-s3.sqlite3
python -m src.database.migrate_josue --db .test-tmp/demo-s3.sqlite3 --hasta 4
```

Los registros `DEMO-*` son ficticios y se usan únicamente para pruebas.

## 7. Cómo ejecutar mis pruebas

```bash
python -m unittest tests.test_soporte_pedidos_s3 -v
```

También puedo ejecutar el resto de las pruebas del proyecto después de instalar sus dependencias:

```bash
python -m pip install -r requirements-test.txt
python -m unittest discover -s tests -v
```

## 8. Demostración de uso

Los comandos se ejecutan desde la raíz del repositorio. Primero aplico la migración:

```bash
python -m src.backend.soporte_pedidos_s3_cli --db data/inkafarma.sqlite3 migrar
```

Para registrar una incidencia de sucursal, uso el ID real de la sucursal:

```bash
python -m src.backend.soporte_pedidos_s3_cli --db data/inkafarma.sqlite3 incidencia --pedido 1 --categoria PRODUCTO_FALTANTE --descripcion "Falta uno de los productos del pedido." --rol PERSONAL_SUCURSAL --actor-id 1
```

Para que un asesor consulte las incidencias:

```bash
python -m src.backend.soporte_pedidos_s3_cli --db data/inkafarma.sqlite3 listar-incidencias --rol ASESOR
```

Para iniciar la atención:

```bash
python -m src.backend.soporte_pedidos_s3_cli --db data/inkafarma.sqlite3 atender-incidencia --incidencia 1 --estado EN_REVISION --rol ASESOR --actor-id 5
```

Para resolverla, indico una explicación de la solución:

```bash
python -m src.backend.soporte_pedidos_s3_cli --db data/inkafarma.sqlite3 atender-incidencia --incidencia 1 --estado RESUELTA --rol ASESOR --actor-id 5 --resolucion "Se verificó el pedido y se coordinó la solución con el cliente."
```

Para el reparto, primero registro la salida mediante el servicio S3-03 y después cambio el estado del pedido con el ID del repartidor asignado:

```bash
python -m src.backend.soporte_pedidos_s3_cli --db data/inkafarma.sqlite3 salida --entrega 1 --fecha 2026-11-12T10:00:00Z
python -m src.backend.soporte_pedidos_s3_cli --db data/inkafarma.sqlite3 cambiar-estado --pedido 1 --estado EN_CAMINO --rol REPARTIDOR --actor-id 1
```

Al recibir el pedido, registro la fecha y confirmo el estado:

```bash
python -m src.backend.soporte_pedidos_s3_cli --db data/inkafarma.sqlite3 recepcion --entrega 1 --fecha 2026-11-12T11:00:00Z
python -m src.backend.soporte_pedidos_s3_cli --db data/inkafarma.sqlite3 cambiar-estado --pedido 1 --estado ENTREGADO --rol REPARTIDOR --actor-id 1
```

Los IDs de ejemplo deben reemplazarse por los que existan en la base de demostración.

## 9. Resultado de las pruebas

En mi validación específica ejecuté **24 pruebas del módulo S3-04 y todas pasaron**. Cubrí transiciones válidas e inválidas, permisos por rol, sincronización entre pedido y entrega, liberación de reservas al cancelar, registro de incidencias, consulta por alcance y resolución.

Además, ejecuté 160 pruebas de 13 módulos no dependientes de Flask y también pasaron. No pude certificar la suite completa en este entorno porque no estaba instalada la dependencia Flask que necesitan tres módulos de pruebas y el entorno de ejecución generó una salida adicional que afectó una prueba de CLI. Por eso, antes de solicitar el merge, debo instalar `requirements-test.txt` y repetir la suite completa en mi equipo.

## 10. Lista de verificación del issue #22

- [x] Implementé las transiciones de reparto `PREPARADO → EN_CAMINO → ENTREGADO`.
- [x] Verifiqué que solo el repartidor asignado pueda actualizar esos estados.
- [x] Sincronicé el estado del pedido con el de la entrega.
- [x] Registré incidencias asociadas a pedidos.
- [x] Apliqué permisos de consulta según el rol.
- [x] Implementé el flujo `ABIERTA → EN_REVISION → RESUELTA`.
- [x] Permití cancelar antes de la salida y liberar reservas activas.
- [x] Agregué migración, CLI, documentación y 24 pruebas.
- [ ] Ejecutar la suite completa con las dependencias instaladas.
- [ ] Revisar el contrato de roles con el equipo y conectarlo a autenticación real.
- [ ] Abrir el Pull Request y obtener la aprobación de otro integrante.

No marco como terminadas la revisión ni la integración porque todavía deben realizarse en GitHub.
