# Validación posterior a la remediación

Ejecución local del 20 de noviembre de 2026 sobre bases SQLite temporales.

| Alcance | Resultado | Evidencia |
|---|---|---|
| Regresión Python, API y recuperación | 334 casos aprobados, incluidos seis casos de remediación | [Registro Python](python.txt) |
| Navegador | 44 recorridos aprobados con Playwright Python 1.65.2 y Chromium Headless Shell 134.0.6998.35 instalado localmente | [Registro Chromium](chromium.txt) |
| Compra comercial con HTTPS y CSP | Solicitud de llamada, introducción del código, confirmación, acceso personal y recorrido hasta entregado | [Prueba de navegador](../../../tests/e2e/test_tienda_browser.py) |
| Sesión y TLS con WSGI | Gunicorn 27.0.1 con dos workers en loopback. Un cliente HTTPS validó el certificado local y el host. Portada y login devolvieron 200. Cookie Secure/HttpOnly/Strict, CSP y HSTS presentes | [Procedimiento de despliegue](../../08-seguridad/REMEDIACION.md) |
| Instaladores y dependencias | Cinco scripts Chrome/Edge macOS inspeccionados en el paquete instalado. pip-audit no reportó avisos en las doce versiones Python consultadas | [Instaladores](instaladores.json) · [Dependencias](dependencias.json) |

La entrega actualizó Playwright y verificó los scripts mediante lectura. La descarga del navegador recomendado por Playwright devolvió HTTP 403 desde su CDN en este entorno. Para los 44 recorridos se seleccionó explícitamente el binario local mediante CHROMIUM_BIN. El dominio de producción y su certificado se verifican en el despliegue real. Los códigos de la prueba se entregaron desde la consola a un cliente de prueba. El procedimiento operativo utiliza una llamada saliente al celular del pedido.
