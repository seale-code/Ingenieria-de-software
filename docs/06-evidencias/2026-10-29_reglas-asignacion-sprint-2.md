# Evidencia tecnica - Reglas de asignacion de sucursal (Sprint 2)

**Fecha:** 29 de octubre de 2026.  
**Responsable:** Cesar Milla.  
**Alcance:** S2-01 / Issue #9 (`RF-S2-03`, `PBI-04`, `PBI-02`, `PBI-03`, `PBI-15`); definicion e implementacion verificable de reglas de stock, distancia, capacidad y desempates.  
**Estado:** documentacion, modulo de reglas y pruebas unitarias completados; en revision del equipo mediante Pull Request.

## Entorno y reproduccion

- Python 3.12; Windows (PowerShell).
- Comando ejecutado:
  python -m unittest tests/test_reglas_asignacion.py -v

## Resultado observado

La suite de pruebas unitarias de reglas de asignacion aprobo en su totalidad: **12 pruebas ejecutadas en 0.006s, 0 fallos y 0 errores (OK)**.

| Prueba unitaria | Escenario verificado | Resultado |
|---|---|---|
| `test_asigna_sucursal_mas_cercana_cuando_ambas_son_elegibles` | Seleccion por menor distancia Haversine cuando ambas cumplen stock y capacidad | Aprobado |
| `test_descarta_sucursal_cercana_sin_stock_y_asigna_siguiente` | Exclusion de sucursal mas cercana por `STOCK_INSUFICIENTE` | Aprobado |
| `test_descarta_sucursal_por_stock_parcial_en_pedido_multiproducto` | Exigencia de cobertura total en pedidos con multiples productos | Aprobado |
| `test_descarta_sucursal_cercana_con_capacidad_agotada` | Exclusion de sucursal mas cercana por `CAPACIDAD_AGOTADA` | Aprobado |
| `test_desempate_nivel_1_mayor_capacidad_disponible` | Desempate 1: prioriza sucursal con mayor holgura de capacidad | Aprobado |
| `test_desempate_nivel_2_mayor_stock_disponible` | Desempate 2: prioriza sucursal con mayor stock acumulado del pedido | Aprobado |
| `test_desempate_nivel_3_orden_alfabetico_por_codigo` | Desempate 3: orden alfabetico determinista por codigo de sucursal | Aprobado |
| `test_rechazo_cuando_ninguna_sucursal_tiene_stock` | Respuesta controlada `SIN_STOCK_DISPONIBLE` cuando no hay stock | Aprobado |
| `test_rechazo_cuando_sucursales_con_stock_no_tienen_capacidad` | Respuesta controlada `SIN_CAPACIDAD_DISPONIBLE` cuando estan llenas | Aprobado |
| `test_rechazo_cuando_lista_de_sucursales_esta_vacia` | Respuesta controlada `SIN_SUCURSALES_REGISTRADAS` | Aprobado |
| `test_calculo_distancia_haversine_mismo_punto_es_cero` | Exactitud matematica de distancia para coordenadas identicas (`0.0 km`) | Aprobado |
| `test_validaciones_rechazan_coordenadas_o_cantidades_invalidas` | Rechazo de coordenadas fuera de rango y cantidades no positivas | Aprobado |

## Archivos relacionados

- Especificacion de reglas: [`docs/REGLAS_ASIGNACION_S2.md`](../REGLAS_ASIGNACION_S2.md)
- Modulo backend: [`src/backend/reglas_asignacion.py`](../../src/backend/reglas_asignacion.py)
- Pruebas unitarias: [`tests/test_reglas_asignacion.py`](../../tests/test_reglas_asignacion.py)
