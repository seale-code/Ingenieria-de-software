# Flujo previsto del pedido entre sucursales

[← Documentación](../README.md)

| Paso | Acción | Resultado o excepción | Sprint |
|---|---|---|---|
| 1 | Buscar producto y consultar disponibilidad | Mostrar resultados o ausencia de stock. | 1 |
| 2 | Consultar sucursales y cercanía | El orden por distancia requiere tarea y criterio explícitos. | 1 |
| 3 | Seleccionar productos y cantidades | Validar datos y disponibilidad. | 2 |
| 4 | Evaluar sucursal según stock, distancia y capacidad | Informar si no existe sucursal elegible. | 2 |
| 5 | Registrar pedido y gestionar reserva | Evitar sobreventa y definir vencimiento/liberación. | 2 |
| 6 | Preparar pedido | Registrar cambio de estado autorizado. | 3 |
| 7 | Gestionar recojo o entrega | Modalidad y transiciones por acordar. | 3 |
| 8 | Confirmar entrega y consultar seguimiento | Registrar confirmación; impedir entrega duplicada. | 3 |

Esta secuencia describe el plan funcional, no una máquina de estados implementada. El orden transaccional de asignación y reserva, los estados definitivos, la cancelación, la reasignación y las notificaciones deben detallarse antes de desarrollar S2/S3.

Fuente: [planes de sprint](../../README.md) e historias HU02, HU03, HU04, HU05 y HU15 del [PDF](../02-historias-usuario/HistoriasdeUsuario-Inkafarma.pdf). La [versión anterior](../00-historico/03-diagramas/FLUJO_PEDIDO.md) describía exclusivamente recojo.
