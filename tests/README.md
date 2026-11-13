# Pruebas

Casos de prueba, evidencias y pruebas de integración del sistema. Responsable de coordinación: Sebastian Calderon. Cada integrante prueba su trabajo.

## Sprint 1
- Catálogo con productos.
- Búsqueda válida, parcial y sin coincidencias.
- Filtros por categoría y sucursal combinados con búsqueda.
- Disponibilidad y stock cero.
- Mensajes de carga y error de conexión.

Registrar por caso: identificador, pasos, datos, resultado esperado, resultado obtenido y estado.

Sprint 2: pedido válido, stock insuficiente, asignación y concurrencia de reservas.
Sprint 3: transiciones de estado, entrega, seguimiento y flujo completo del MVP.

## Suite actual de integración

Instala `requirements-test.txt` y ejecuta `python -m unittest discover -s tests -v`. Para navegador: `python -m playwright install chromium-headless-shell` y `python -m unittest discover -s tests/e2e -v`. Las pruebas crean bases temporales; no usan los datos del usuario.

Los casos `test_operaciones_demo.py` y `e2e/test_operaciones_browser.py` comprueban el panel v4, entrega completa, errores con rollback, reintentos, cancelación, soporte y límites de acceso. [Evidencia actual](../docs/06-evidencias/2026-11-12_mvp-web-integrado.md).

## Suite inicial de base de datos (histórico)

Desde la raíz: `python -m unittest discover -s tests -v`. Son 24 pruebas de integridad, datos ficticios, preservación de datos, filtros y comandos; sin paquetes externos. [Resultados y límites](../docs/06-evidencias/2026-10-18_base-datos-sprint-1.md).
