# Evidencia tecnica - Filtros combinados con busqueda (Sprint 1)

**Fecha:** 29 de octubre de 2026.  
**Responsable:** Cesar Milla.  
**Alcance:** S1-01 / Issue #1, S1-02 / Issue #2 y S1-03 / Issue #8 (PBI-01); filtrado por categoria, sucursal, disponibilidad (cantidad > 0) y busqueda parcial por nombre.  
**Estado:** implementacion y pruebas automaticas realizadas; revision del equipo en Pull Request.

## Entorno y reproduccion

- Python 3.12; SQLite 3; Windows (PowerShell).
- Pruebas unitarias aisladas con unittest sobre bases SQLite temporales inicializadas con initialize_database(..., demo=True).
- Comando ejecutado:
  python -m unittest tests/test_filtro_categorias.py tests/test_filtro_sucursal_stock.py tests/test_filtros_combinados.py -v

## Resultado observado

La suite automatizada de filtrado paso completa: **29 pruebas ejecutadas en 0.514s, 0 fallos y 0 errores (OK)** (9 de categorias + 10 de sucursal y stock + 10 de validacion combinada).

### Registro de ejecucion de casos de la matriz S1

| Caso | Requisito / Tarea | Datos utilizados | Resultado obtenido | Estado | Defectos |
|---|---|---|---|---|---|
| S1-CP-05 | RF-S1-02 / #1 | Categoria DEMO-X y posterior limpieza ("") en DEMO-NORTE | Devuelve DEMO-A y DEMO-C; al limpiar recupera DEMO-A, DEMO-B y DEMO-C. | Aprobado | Ninguno |
| S1-CP-06 | RF-S1-02 / #2 | Sucursal DEMO-NORTE + solo_disponibles=True | Devuelve unicamente DEMO-A (stock 5); excluye DEMO-B y DEMO-C (stock 0). | Aprobado | Ninguno |
| S1-CP-07 | RF-S1-02 / #8 | Busqueda "Producto demo B", DEMO-Y, DEMO-SUR, solo_disponibles=True / Cambio a DEMO-X | Con DEMO-Y devuelve DEMO-B (stock 3); con DEMO-X devuelve resultados=[], sin_resultados=True y mensaje "No se encontraron productos para los filtros seleccionados.". | Aprobado | Ninguno |

## Archivos relacionados

- Codigo de negocio:
  - [src/backend/filtro_categorias.py](../../src/backend/filtro_categorias.py)
  - [src/backend/filtro_sucursal_stock.py](../../src/backend/filtro_sucursal_stock.py)
  - [src/backend/filtros_combinados.py](../../src/backend/filtros_combinados.py)
- Pruebas automatizadas:
  - [tests/test_filtro_categorias.py](../../tests/test_filtro_categorias.py)
  - [tests/test_filtro_sucursal_stock.py](../../tests/test_filtro_sucursal_stock.py)
  - [tests/test_filtros_combinados.py](../../tests/test_filtros_combinados.py)
