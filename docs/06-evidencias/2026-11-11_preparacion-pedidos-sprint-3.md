# Evidencia tecnica - Gestion de preparacion de pedidos (Sprint 3)

**Fecha:** 11 de noviembre de 2026.  
**Responsable:** Cesar Milla.  
**Alcance:** S3-01 / Issue #16 (`RF-S3-01`); consulta de pedidos asignados por sucursal y registro de preparacion mediante transiciones de estado validas.  
**Estado:** implementacion y pruebas unitarias completadas; en revision mediante Pull Request.

## Entorno y reproduccion

- Python 3.13.5; SQLite 3 (esquema v3 con migraciones de Sprint 2 y Sprint 3); Windows (PowerShell).
- Comando ejecutado:
  py -m unittest tests/test_preparacion_pedidos.py -v

## Resultado observado

La suite automatizada de preparacion de pedidos aprobo completamente: **11 pruebas ejecutadas en 0.758s, 0 fallos y 0 errores (OK)**.

| Prueba unitaria | Escenario verificado | Estado |
|---|---|---|
| `test_consultar_pedidos_asignados_por_sucursal` | Consulta de pedidos asignados a `DEMO-NORTE` y `DEMO-SUR` con sus items y reservas | Aprobado |
| `test_consultar_pedidos_filtrando_por_estado` | Filtrado de bandeja por estado (`ASIGNADO`, `EN_PREPARACION`) | Aprobado |
| `test_excluir_preparados_en_bandeja_pendientes` | Filtro de pendientes (`incluir_preparados=False`) | Aprobado |
| `test_flujo_completo_preparacion_valido_y_registro_historial` | Transicion `ASIGNADO -> EN_PREPARACION -> PREPARADO` y registro en `historial_estados` | Aprobado |
| `test_rechaza_pasar_directamente_de_asignado_a_preparado` | Bloqueo de salto directo `ASIGNADO -> PREPARADO` | Aprobado |
| `test_rechaza_retroceder_de_preparado_a_en_preparacion` | Bloqueo de retroceso `PREPARADO -> EN_PREPARACION` | Aprobado |
| `test_rechaza_preparar_pedido_cancelado_o_entregado` | Bloqueo sobre pedidos cerrados (`CANCELADO`, `ENTREGADO`) | Aprobado |
| `test_rechaza_estado_destino_ajeno_a_preparacion` | Bloqueo de estados fuera del alcance de preparacion | Aprobado |
| `test_pedido_inexistente_lanza_error_claro` | Excepcion `PedidoNoEncontrado` ante ID inexistente | Aprobado |
| `test_rechaza_preparar_pedido_sin_detalles` | Bloqueo de preparacion para encabezados de pedido sin productos | Aprobado |
| `test_validaciones_de_parametros_invalidos` | Rechazo de identificadores no positivos y estados invalidos | Aprobado |

## Archivos relacionados

- Documentacion S3-01: [`sprint-3/S3-01_Cesar_Milla.md`](../../sprint-3/S3-01_Cesar_Milla.md)
- Modulo backend: [`src/backend/preparacion_pedidos.py`](../../src/backend/preparacion_pedidos.py)
- Pruebas unitarias: [`tests/test_preparacion_pedidos.py`](../../tests/test_preparacion_pedidos.py)
