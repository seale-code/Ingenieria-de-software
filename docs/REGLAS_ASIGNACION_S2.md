# Reglas de Asignacion de Pedidos a Sucursales — Sprint 2 (S2-01 / Issue #9)

**Responsable:** Cesar Milla (`S2-01`)  
**Trazabilidad:** `RF-S2-03`, `PBI-04`, `PBI-02`, `PBI-03`, `PBI-15`  
**Modulo de referencia:** [`src/backend/reglas_asignacion.py`](../src/backend/reglas_asignacion.py)

---

## 1. Objetivo

Definir las reglas de negocio verificables y deterministas para asignar automaticamente un pedido de un cliente a la sucursal mas adecuada de Inkafarma, evaluando **stock disponible**, **capacidad operativa**, **distancia geografica** y **criterios de desempate**.

---

## 2. Reglas de Elegibilidad (Condiciones Excluyentes)

Para que una sucursal sea considerada candidata (**`ELEGIBLE`**) para atender un pedido, debe cumplir simultaneamente las siguientes dos condiciones:

### 2.1. Regla de Stock Disponible Efectivo
- El stock disponible para nuevos pedidos se calcula descontando las reservas activas del inventario fisico (segun el modelo `002_pedidos_reservas.sql`):
  - `stock_disponible(producto, sucursal) = inventario.cantidad - SUM(reservas_stock.cantidad WHERE estado = 'ACTIVA')`
- **Condicion:** La sucursal debe contar con `stock_disponible >= cantidad_solicitada` para **todos y cada uno** de los productos incluidos en el pedido.
- Si al menos un producto no alcanza la cantidad requerida, la sucursal queda descartada con motivo **`STOCK_INSUFICIENTE`** (no se realizan asignaciones parciales en un mismo pedido).

### 2.2. Regla de Capacidad Operativa de la Sucursal
- Cada sucursal tiene una capacidad maxima de pedidos activos simultaneos (`CAPACIDAD_MAXIMA_DEFAULT = 10`, configurable por sucursal).
- Se contabilizan como **pedidos activos** aquellos que se encuentran en los estados:
  - `'REGISTRADO'`, `'ASIGNADO'`, `'EN_PREPARACION'`, `'PREPARADO'`
- **Condicion:** La sucursal debe tener al menos un cupo libre:
  - `capacidad_disponible = capacidad_maxima - pedidos_activos > 0`
- Si `pedidos_activos >= capacidad_maxima`, la sucursal queda descartada con motivo **`CAPACIDAD_AGOTADA`**.

---

## 3. Criterio Principal de Seleccion: Distancia Geografica

Entre todas las sucursales declaradas **`ELEGIBLE`**:
1. Se calcula la distancia ortodromica (formula de **Haversine** con radio terrestre medio `R = 6371.0088 km`) entre las coordenadas del cliente `(cliente_latitud, cliente_longitud)` y las coordenadas de la sucursal `(latitud, longitud)`.
2. La distancia se redondea a **3 decimales** (precision de 1 metro: `0.001 km`).
3. **Se selecciona la sucursal elegible con menor `distancia_km`.**

---

## 4. Reglas de Desempate (Orden Estricto y Determinista)

Si dos o mas sucursales elegibles presentan exactamente la misma `distancia_km` (diferencia menor o igual a `0.001 km`), el empate se resuelve aplicando en orden estricto:

1. **Desempate Nivel 1 — Mayor Capacidad Disponible:**
   - Se elige la sucursal con mayor `capacidad_disponible` (`capacidad_maxima - pedidos_activos`), priorizando la tienda menos congestionada.
2. **Desempate Nivel 2 — Mayor Stock Disponible Acumulado:**
   - Si persiste el empate en capacidad, se elige la sucursal que posea mayor suma de unidades disponibles (`stock_total_pedido`) para los productos solicitados en el pedido.
3. **Desempate Nivel 3 — Orden Alfabetico por Codigo de Sucursal:**
   - Si persiste el empate en distancia, capacidad y stock, se elige la sucursal cuyo `codigo` sea menor en orden alfabetico ASCII (por ejemplo, `'DEMO-NORTE'` antes que `'DEMO-SUR'`). Esto garantiza un resultado 100% determinista.

---

## 5. Tratamiento cuando Ninguna Sucursal es Elegible

Si tras evaluar todas las sucursales ninguna resulta elegible (`elegibles = []`), el pedido no se asigna (`asignada = False`, `sucursal_asignada = None`) y se informa el motivo especifico:
- **`SIN_SUCURSALES_REGISTRADAS`**: No existen sucursales cargadas para evaluar.
- **`SIN_STOCK_DISPONIBLE`**: Ninguna sucursal posee el stock requerido para todos los items del pedido.
- **`SIN_CAPACIDAD_DISPONIBLE`**: Al menos una sucursal tiene el stock requerido, pero todas las que tienen stock han alcanzado su limite de capacidad operativa.

---

## 6. Ejemplos Validados con Datos del Proyecto

| Caso | Pedido Solicitado | Ubicacion Cliente | Estado Sucursal Norte (`-12.000, -77.050`) | Estado Sucursal Sur (`-12.100, -77.030`) | Sucursal Asignada / Resultado | Regla Aplicada |
|---|---|---|---|---|---|---|
| **Caso 1: Cercania estandar** | `DEMO-A: 2` | `(-12.010, -77.050)` | Stock `DEMO-A=5`, Activos `2/10`, Dist `1.112 km` | Stock `DEMO-A=5`, Activos `4/10`, Dist `10.241 km` | **`DEMO-NORTE`** | Menor distancia entre elegibles |
| **Caso 2: Exclusion por stock** | `DEMO-B: 2` | `(-12.005, -77.050)` | Stock `DEMO-B=0` (**No cumple**) | Stock `DEMO-B=3`, Activos `4/10` (**Elegible**) | **`DEMO-SUR`** | Norte descartada por `STOCK_INSUFICIENTE` |
| **Caso 3: Exclusion por capacidad** | `DEMO-A: 1` | `(-12.001, -77.050)` | Stock `DEMO-A=5`, Activos `10/10` (**No cumple**) | Stock `DEMO-A=5`, Activos `4/10` (**Elegible**) | **`DEMO-SUR`** | Norte descartada por `CAPACIDAD_AGOTADA` |
| **Caso 4: Desempate por capacidad** | `DEMO-A: 2` | Igual distancia a `SUC-1` y `SUC-2` | `SUC-1`: Stock `5`, Libre `5/10` | `SUC-2`: Stock `5`, Libre `9/10` | **`SUC-2`** | Desempate Nivel 1 (Mayor capacidad libre) |
| **Caso 5: Sin alternativa elegible** | `DEMO-C: 1` | `(-12.050, -77.040)` | Stock `DEMO-C=0` | Stock `DEMO-C=0` | **`Ninguna (`None`)`** | Rechazo claro con `SIN_STOCK_DISPONIBLE` |
