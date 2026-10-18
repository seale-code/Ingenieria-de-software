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

## Suite ejecutable de base de datos

Desde la raíz: `python -m unittest discover -s tests -v`. Son 24 pruebas de integridad, datos ficticios, preservación de datos, filtros y comandos; sin paquetes externos. [Resultados y límites](../docs/06-evidencias/2026-10-18_base-datos-sprint-1.md).
