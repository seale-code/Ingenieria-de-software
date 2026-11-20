# Seguridad — evaluación local de la versión 6

Evaluación del **20 de noviembre de 2026**, código funcional `53b6ff8`. Se revisaron código, dependencias y solicitudes locales con bases temporales. No se probaron servicios externos de Inkafarma ni datos operativos.

| Documento | Contenido |
|---|---|
| [Informe de vulnerabilidades](ANALISIS_VULNERABILIDADES.md) | Alcance, resultados, cinco hallazgos, impacto y límites. |
| [Metodología y reproducción](METODOLOGIA.md) | Entorno, referencias OWASP, comandos y criterio de riesgo. |
| [Plan de remediación y verificación](PLAN_REMEDIACION.md) | Acciones, prioridad, responsables propuestos y condiciones de cierre. |
| [Registro CSV](HALLAZGOS.csv) | Hallazgos y estado para seguimiento. |
| [Evidencias](../06-evidencias/documentacion-seguridad-2026-11-20/README.md) | Resultados sin cookies, claves, contactos ni bases de datos. |

**Resultados:** 23 controles locales aprobados; 37 alertas de Bandit revisadas individualmente, sin SQLi confirmada en las seis rutas señaladas; pip-audit no reportó avisos para los siete paquetes de ejecución y cuatro de pruebas del inventario Python. Una revisión adicional del driver incluido en Playwright identificó cinco instaladores macOS con `curl -k`; ese componente no quedó cubierto por el resultado del catálogo PyPI.

Quedan abiertos acceso individual/mínimo privilegio, abuso de reservas, limitación de intentos, configuración de despliegue y actualización de la herramienta de pruebas. Esta entrega documenta la línea base y el plan; **no modifica los controles del programa ni declara esos hallazgos corregidos**. El resultado no es una certificación ni un pentest integral de una infraestructura pública.
