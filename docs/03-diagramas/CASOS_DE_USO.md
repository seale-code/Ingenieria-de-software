# Casos de uso: implementación y sistema objetivo

[UML editable](uml/README.md) · [Trazabilidad](../01-requisitos/TRAZABILIDAD_IMPLEMENTACION.md)

## Recorridos disponibles en v6

| Actor | Caso de uso | Entrada / evidencia |
|---|---|---|
| Cliente | Buscar, filtrar, consultar precio/stock | `/`, API de catálogo; HU01/HU07. |
| Cliente | Carrito, cotización y confirmación | `/pedido`; contacto, precios y reservas transaccionales. |
| Cliente con código | Consultar avance/cambios de sucursal | `/seguimiento`; omite contactos y motivos internos. |
| Operador | Aceptar, preparar y marcar listo | `/operaciones`; generación y reservas vigentes. |
| Operador | Declarar incapacidad de la sucursal | Alternativa completa o cancelación/liberación. |
| Supervisor | Resolver plazo no aceptado | Arranque/cada 30 s o CLI planificada. |
| Operador | Repartidor, despacho y recepción | Fechas/estados/stock/historial coherentes. |
| Operador | Cancelar antes de salida y gestionar incidencias | Reserva liberada y resolución registrada. |
| Operador | Registrar entrada/conteo | Motivo, saldos, idempotencia y protección de reservas. |

Personal de sucursal, Repartidor, Asesor y Administrador son actores de negocio en servicios/UML. La sesión web es de operador central; no corresponde a cuentas individuales ya implementadas.

El MCU cubre las 15 HU, incluidas cuentas, repetición, multicanal, chat, alertas de reposición y alternativas. Esas funciones del sistema objetivo no quedan implementadas por aparecer en un diagrama. La matriz distingue implementado, adaptado, parcial y pendiente.

La aceptación docente del agrupamiento no consta en el repositorio. Se conserva la agrupación solicitada sin atribuir una aprobación.
