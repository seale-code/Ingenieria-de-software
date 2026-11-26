# Evidencia de actualización documental y seguridad — 20 de noviembre de 2026

[Validación funcional](../../05-pruebas/VALIDACION_V6.md) · [Informe de seguridad](../../08-seguridad/ANALISIS_VULNERABILIDADES.md).

Las ejecuciones usan bases temporales y datos sintéticos. Se publican registros de texto, estados, contadores y hashes; no se incluyen claves, tokens, cookies, contactos de pedidos ni bases. No hay pruebas contra servicios comerciales de Inkafarma.

| Archivo | Resultado / finalidad |
|---|---|
| [pruebas-python.txt](pruebas-python.txt) | 328 pruebas Python/API/recuperación aprobadas. |
| [pruebas-chromium.txt](pruebas-chromium.txt) | 44 recorridos de navegador aprobados. |
| [rendimiento.json](rendimiento.json) | Medición local pequeña, sin SLA ni comparación con datos de operación real. |
| [documentacion.json](documentacion.json) | Enlaces de los Markdown modificados; 46 criterios y 37 referencias a pruebas verificados. |
| [seguridad-local.json](seguridad-local.json) | 23 controles aprobados; cinco observaciones; hashes de las fuentes probadas. |
| [bandit.json](bandit.json) | Salida completa: 37 alertas, cero errores; código de salida 1 por hallazgos del analizador. |
| [bandit-triaje.csv](bandit-triaje.csv) | Revisión individual de cada alerta, disposición y seguimiento. |
| [dependencias-produccion.json](dependencias-produccion.json) | Siete versiones de ejecución auditadas, cero avisos reportados por PyPI. |
| [dependencias-pruebas.json](dependencias-pruebas.json) | Cuatro versiones adicionales de herramientas, cero avisos reportados por PyPI. |
| [playwright-instaladores.json](playwright-instaladores.json) | Cinco scripts macOS del driver incluido usan curl con validación TLS desactivada; no se ejecutaron. |
| [herramientas-seguridad.json](herramientas-seguridad.json) | Fecha, versiones, alcance de escáneres y hash de la herramienta local. |

Los inventarios exactos están en [producción](../../08-seguridad/inventario-produccion.txt) y [pruebas](../../08-seguridad/inventario-pruebas.txt). El JSON de la herramienta local informa observaciones de configuración/diseño de forma separada: aprobar 23 controles no significa resolverlas.

El [plan de remediación](../../08-seguridad/PLAN_REMEDIACION.md) mantiene el retest pendiente porque no se han implementado los cambios de seguridad. Los resultados históricos conservan sus fechas originales.
