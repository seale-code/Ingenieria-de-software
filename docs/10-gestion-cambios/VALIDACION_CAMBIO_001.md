# Protocolo de validación — SC-INK-001

Estado: **en ejecución; regresión satisfactoria, aceptación específica parcial**. Entorno local, datos de demostración. Fecha de regresión: 27/11/2026.

| Caso | Procedimiento | Resultado esperado | Resultado real |
|---|---|---|---|
| VC-01 | Abrir catálogo y observar botón | Texto exacto «Buscar producto» visible | Satisfactorio: captura de escritorio posterior. |
| VC-02 | Buscar producto y enviar por clic | Resultados correctos; mismo comportamiento anterior | Pendiente de confirmación específica del clic. |
| VC-03 | Enviar con Enter y combinar filtros | Búsqueda y filtros funcionan | Regresión satisfactoria; pendiente de confirmar envío específico con Enter. |
| VC-04 | Revisar a 1366×900 y 390×844 | Sin recortes, superposición ni desplazamiento horizontal causado por el botón | Captura móvil guardada; pendiente de revisar ambas resoluciones y confirmar criterio. |
| VC-05 | Navegar con Tab y activar con teclado | Botón accesible, nombre «Buscar producto» y envío correcto | Nombre configurado en HTML; pendiente de confirmar nombre accesible y activación en navegador. |
| VC-06 | Revisar cambios Git | No se alteran API, base de datos ni reglas de negocio | Satisfactorio en diff local revisado: HTML, CSS y documentación; `git diff --check` sin errores reportados. |

## Regresión automatizada
Comando: `python -m unittest discover -s tests/e2e -p test_catalogo_browser.py -v` (entorno virtual Windows con Playwright y Chromium).

| Prueba | Resultado |
|---|---|
| test_actualizacion_real_desde_sqlite | OK |
| test_busqueda_y_filtros_combinados | OK |
| test_carga_error_y_reintento | OK |
| test_error_de_filtros_y_stock_recuperable | OK |
| test_fixtures_vacios_unicode_y_texto_literal | OK |
| test_responsive_teclado_y_capturas | OK |
| test_respuesta_antigua_no_sobrescribe_busqueda | OK |
| test_stock_sucursal_y_cero | OK |

Última ejecución registrada: 8 pruebas, 20.489 segundos, 0 fallos y 0 errores de prueba. El mensaje NativeCommandError corresponde a la captura de stderr en PowerShell; el resumen terminó en OK. La regresión existente no acredita por sí sola todos los criterios específicos del nuevo botón.

## Evidencias y cierre
Ver [índice de evidencias](evidencias/README.md). Aprobación registrada el 27/11/2026 después de la implementación local y la regresión inicial. Pendientes: confirmación de VC-02 a VC-05, responsable de validación, commit, PR, revisión y merge. No cerrar hasta cumplir criterios y revisar la desviación del procedimiento.
