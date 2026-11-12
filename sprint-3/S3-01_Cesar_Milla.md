# S3-01 — Gestionar preparacion de pedidos (Issue #16)

**Responsable:** Cesar Milla (`Cesrm27`)  
**Sprint:** 3  
**Requisito / Trazabilidad:** `RF-S3-01`, `HU05`, `HU15` (`PBI-05` / `PBI-15`)  
**Modulo implementado:** [`src/backend/preparacion_pedidos.py`](../src/backend/preparacion_pedidos.py)  
**Pruebas automatizadas:** [`tests/test_preparacion_pedidos.py`](../tests/test_preparacion_pedidos.py)

---

## 1. Alcance y Criterios de Aceptacion

1. **Consultar pedidos asignados:**
   - Permite listar los pedidos asignados a cada sucursal (`consultar_pedidos_asignados`), filtrando opcionalmente por `sucursal_codigo` (ej. `'DEMO-NORTE'`, `'DEMO-SUR'`), por `estado` (`'REGISTRADO'`, `'ASIGNADO'`, `'EN_PREPARACION'`, `'PREPARADO'`) o excluyendo los ya preparados (`incluir_preparados=False`).
   - Incluye para cada pedido su codigo, sucursal, cliente, estado actual, detalle de productos/cantidades, estado de reserva de stock e historial de transiciones.

2. **Registrar preparacion mediante transiciones validas:**
   - **Iniciar preparacion (`iniciar_preparacion_pedido`):** permite la transicion desde `'REGISTRADO'` o `'ASIGNADO'` hacia **`'EN_PREPARACION'`**.
   - **Completar preparacion (`completar_preparacion_pedido`):** permite la transicion exclusivamente desde **`'EN_PREPARACION'`** hacia **`'PREPARADO'`**.
   - **Control de transiciones invalidas (`validar_transicion_preparacion`):**
     - Rechaza saltar directamente de `'ASIGNADO'` a `'PREPARADO'` sin haber pasado por `'EN_PREPARACION'`.
     - Rechaza retroceder de `'PREPARADO'` a `'EN_PREPARACION'`.
     - Rechaza modificar pedidos en estados posteriores o terminales (`'EN_CAMINO'`, `'ENTREGADO'`, `'CANCELADO'`).
     - Rechaza preparar un pedido sin lineas en `detalles_pedido`.
   - **Trazabilidad en historial (`003_entregas_historial.sql`):**
     - Cada actualizacion se ejecuta bajo transaccion `BEGIN IMMEDIATE`, activando el trigger `trg_pedidos_registrar_historial_cambio` que almacena automaticamente `(estado_anterior -> estado_nuevo)` en `historial_estados`.
