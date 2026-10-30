# S1-12 — Validación del flujo catálogo → filtros → stock

**Responsable:** Sebastian Calderon. **Issue:** [#11](https://github.com/seale-code/Ingenieria-de-software/issues/11). **Fecha:** 29 de octubre de 2026 (Perú).
**Versión base:** `79e74d8` (`main`); integración probada: `5a405a2` (PR #36).
Casos especificados en PR #35, tarea #14.

## Entorno y procedimiento reproducible

Python 3.12, Flask 3.1.3, Playwright 1.51.0, Chromium Headless 134; Linux.
Cada prueba usa una SQLite temporal creada con `initialize_database(demo=True)`,
Flask local en puerto efímero y un navegador independiente. Sin credenciales,
servicios externos ni cambios a la base de otro integrante.

```bash
python -m pip install -r requirements-test.txt
python -m playwright install chromium
python -m unittest discover -s tests -v
EVIDENCE_DIR=.test-tmp/capturas python -m unittest discover -s tests/e2e -v
```

**Resultados observados:** suite Python/API: **67 pruebas, OK** (52 del repositorio +
15 de la integración); navegador: **8 pruebas, OK**, recorrido HTTP real de
catálogo, filtros, disponibilidad, cambios en SQLite, carga, error/reintento,
consultas fuera de orden, teclado y pantallas 390×844/1366×900. Salidas de
consola: [Python/API](2026-10-29_sebastian-s1-unittest.txt) y
[navegador](2026-10-29_sebastian-s1-browser.txt). Las imágenes de las dos
resoluciones se obtienen con `EVIDENCE_DIR` y se revisaron localmente; las capturas
se mantienen fuera de Git por ser artefactos reproducibles.

## Registro frente a casos S1-10

| Caso | Resultado | Evidencia de ejecución |
|---|---|---|
| CP-01–05 | Aprobado | Test de navegador `test_busqueda_y_filtros_combinados`; API `test_catalogo_sin_duplicados`, `test_busqueda_exacta_parcial_y_vacia`, `test_categoria_y_limpiar`. |
| CP-06–11 | Aprobado | Test de navegador `test_stock_sucursal_y_cero`, `test_busqueda_y_filtros_combinados`; API `test_combinacion_de_todos_los_filtros`, `test_stock_y_cero`. |
| CP-12–15 | Aprobado | Test de navegador `test_fixtures_vacios_unicode_y_texto_literal`; API `test_categoria_vacia_y_producto_sin_inventario`, `test_unicode_y_sql_literal`. |
| CP-16–17 | Aprobado | `test_carga_error_y_reintento`, falla HTTP simulada interceptando la consulta; prueba adicional de error y reintento en filtros/stock. |
| CP-18–19 | Aprobado | `test_actualizacion_real_desde_sqlite`, `test_respuesta_antigua_no_sobrescribe_busqueda`. |
| CP-20 | Aprobado | `test_responsive_teclado_y_capturas`; sin scroll horizontal a 390/1366 px, recorrido con teclado y detalle. |
| CP-21–22 | Aprobado a nivel API | `test_base_ausente_no_se_crea_ni_filtra_ruta`, `test_base_invalida`, `test_errores_de_peticion`. Error de conexión de interfaz validado en CP-17. |

## Defectos y pendientes

No se reprodujeron fallos en esta ejecución después de integrar la API.
El punto de partida presentaba datos estáticos en el prototipo y carecía de API,
impidiendo comprobar CP-18; se implementó el acceso a SQLite en PR #36.
Revisión de otro integrante y merge quedan pendientes. No se realizó una
Sprint Review con el equipo.

**Brecha funcional:** HU01 requiere ordenar sucursales con stock por cercanía;
sin definición de la ubicación y de la regla, S1-CP-12 de la matriz general sigue
bloqueado. HU14 requiere movimientos de inventario. La validación S1 no acredita
pedidos, reservas, permisos ni una aplicación móvil nativa.
