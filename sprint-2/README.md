# Sprint 2 — Registro y asignación de pedidos

[← Sprint 1](../sprint-1/README.md) · [Proyecto](../README.md) · [Tablero](../docs/07-scrum/tablero-kanban-sprint-1.png) · [Sprint 3 →](../sprint-3/README.md)

## Objetivo
Registrar pedidos y asignarlos a una sucursal de Inkafarma considerando stock, distancia y capacidad de atención, mediante reglas acordadas y verificables.

## Planificación y dependencias
- Inicio y cierre: por acordar. Estado: planificado.
- Requiere catálogo, inventario y consulta de disponibilidad del Sprint 1.
- Definir antes de implementar: pesos o prioridades, desempates, tratamiento de falta de stock y reservas.

## Actividades y responsables propuestos
| ID | Responsable | Actividad | Criterios de aceptación | Estado |
|:---|:---|:---|:---|:---|
| S2-01 | Cesar Milla | Definir reglas de asignación | Documentar stock, distancia, capacidad y desempates; validar ejemplos con el equipo. | Por hacer |
| S2-02 | Willy CCatamayo | Formulario y confirmación del pedido | Validar productos y cantidades; mostrar resumen, confirmación y errores. | Por hacer |
| S2-03 | Josue Mogollon | Modelar pedidos, detalles y reserva de stock | Mantener integridad de relaciones y evitar reservas que excedan stock disponible. | Por hacer |
| S2-04 | Anderson Delerna | Registrar pedidos y asignar sucursal | Persistir pedido válido, aplicar reglas acordadas e informar cuando ninguna sucursal sea elegible. | Por hacer |
| S2-05 | Sebastian Calderon | Integrar y probar pedidos y asignación | Validar pedido correcto, datos inválidos, stock insuficiente y reservas concurrentes. | Por hacer |

## Entregables y ubicación
- [Frontend](../frontend/): formulario, resumen y confirmación.
- [Backend](../backend/): registro, validación y asignación.
- [Base de datos](../database/): pedidos, detalles y reservas.
- [Documentación](../docs/): reglas y ejemplos de asignación.
- [Pruebas](../tests/): resultados y defectos encontrados.

El código se mantiene en las carpetas compartidas; este README registra la planificación y entrega del sprint.

## Definición de terminado
- [ ] Reglas de asignación acordadas y documentadas.
- [ ] Pedido válido registrado con su detalle y sucursal.
- [ ] Stock insuficiente y datos inválidos gestionados correctamente.
- [ ] Reservas no producen sobreventa en los casos probados.
- [ ] Flujo integrado, revisado y demostrable.
- [ ] Evidencias y cambios enlazados.

## Resultados y evidencias
Completar solo con avances verificados.

| Entregable | Issue o Pull Request | Evidencia o versión | Resultado |
|:---|:---|:---|:---|
| Por completar | Por completar | Por completar | Pendiente de validación |

## Revisión del sprint
- Fecha y participantes: por completar.
- Funcionalidades demostradas y aceptadas: por completar.
- Pendientes y decisiones: por completar.

## Retrospectiva
- Qué funcionó: por completar.
- Qué debemos mejorar: por completar.
- Acción de mejora, responsable y fecha: por completar.
