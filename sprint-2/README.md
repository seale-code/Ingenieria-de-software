# Sprint 2 — Registro y asignación de pedidos

[← Sprint 1](../sprint-1/README.md) · [Proyecto](../README.md) · [Tablero S1 (referencia)](../docs/07-scrum/tablero-kanban-sprint-1.png) · [Sprint 3 →](../sprint-3/README.md)

## Objetivo
Registrar pedidos y asignarlos a una sucursal de Inkafarma considerando stock, distancia y capacidad de atención, mediante reglas acordadas y verificables.

## Planificación y dependencias
- Inicio y cierre: por acordar. Estado técnico: servicios y flujo web integrados en main; 147 pruebas Python/API y 14 recorridos de navegador aprobados el 30 de octubre de 2026. La Sprint Review y el cierre formal siguen pendientes.
- Requiere catálogo, inventario y consulta de disponibilidad del Sprint 1.
- Reglas de asignación integradas mediante PR #34. Quedan por acordar vencimiento, notificaciones y reasignación de reservas.

## Actividades y responsables propuestos
| ID | Responsable | Actividad | Criterios de aceptación | Estado |
|:---|:---|:---|:---|:---|
| S2-01 | Cesar Milla | Definir reglas de asignación | Documentar stock, distancia, capacidad y desempates; validar ejemplos con el equipo. | Issue #9 cerrado; PR #34 integrado |
| S2-02 | Willy CCatamayo | Formulario y confirmación del pedido | Validar productos y cantidades; mostrar resumen, confirmación y errores. | PR #42 integrado; Issue #20 cerrado; formulario verificado |
| S2-03 | Josue Mogollon | Modelar pedidos, detalles y reserva de stock | Mantener integridad de relaciones y evitar reservas que excedan stock disponible. | Código de Josué en main; Issue #21 cerrado |
| S2-04 | Anderson Delerna | Registrar pedidos y asignar sucursal | Persistir pedido válido, aplicar reglas acordadas e informar cuando ninguna sucursal sea elegible. | PR #37 integrado; Issue #18 cerrado; puente oficial integrado en #40 |
| S2-05 | Sebastian Calderon | Integrar y probar pedidos y asignación | Validar pedido correcto, datos inválidos, stock insuficiente y reservas concurrentes. | PR #40 integrado; Issue #12 cerrado; pruebas repetidas sobre main |

## Entregables y ubicación
- [Frontend](../src/frontend/): formulario, resumen y confirmación.
- [Backend](../src/backend/): registro, validación y asignación.
- [Base de datos](../src/database/): pedidos, detalles y reservas.
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
| Integración registro + reglas + reservas oficiales | #12; relacionados #9, #18 y #21 | [16 casos y evidencia](../docs/06-evidencias/2026-10-29_integracion-sprint-2.md) | 120 pruebas aprobadas en la propuesta; pendiente revisión |

## Revisión del sprint
- Fecha y participantes: por completar.
- Funcionalidades demostradas y aceptadas: por completar.
- Pendientes y decisiones: por completar.

## Retrospectiva
- Qué funcionó: por completar.
- Qué debemos mejorar: por completar.
- Acción de mejora, responsable y fecha: por completar.

## Guía de integración y revisión actual

[Entrega S2-05 de Sebastian](S2-05_Sebastian_Calderon.md) · [Casos de prueba](../docs/05-pruebas/S2-05-casos-prueba-pedidos.md).

Los estados anteriores se contrastaron con GitHub el 29 de octubre de 2026. No sustituyen el tablero ni acreditan una Sprint Review.

## Verificación integrada del 30 de octubre de 2026

La evidencia anterior de 120 pruebas es histórica. La revisión actual de `9d65db7` aprobó 147 pruebas Python/API y 14 recorridos de navegador (8 de catálogo y 6 de pedidos).

- [Guía para ejecutar y demostrar el Sprint 2](DEMO_SPRINT_2.md).
- [Resultados de la revisión actual](../docs/06-evidencias/2026-10-30_revision-main-sprint-2.md).
- PR #42 fusionado y vinculado a #20; las tareas individuales de S2 están cerradas. El issue general #24 sigue abierto.

Estos resultados no sustituyen la aceptación del equipo ni acreditan una reunión de revisión o retrospectiva.
