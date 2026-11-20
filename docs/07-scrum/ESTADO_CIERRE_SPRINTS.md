# Evidencias y cierre de sprints

**20 de noviembre de 2026.** Referencia funcional `53b6ff8`. Este documento registra hechos técnicos y separa decisiones que requieren al equipo.

## Incrementos verificables

| Etapa | Integración / evidencia | Qué acredita |
|---|---|---|
| S1 | #26, #31–#36 y #38; informes de octubre | Catálogo, filtros, base y verificación del alcance entregado. |
| S2 | #34, #37, #40–#45; informes del 29/30 de octubre | Asignación, formulario, reservas e integración. |
| S3 | #46–#52; informes del 11/12 de noviembre | Preparación, seguimiento, reparto, soporte y validación. |
| Modelo | #53 | 17 diagramas agrupados del sistema objetivo. |
| Ampliación integrada | #54, #55, #56 | Panel, catálogo/carrito, precios y logística/inventario v6. |

La secuencia se puede contrastar con `git log --merges --format='%aI %h %s'`. Las fechas del historial son de integración, no fechas formales de inicio/cierre o reuniones. El cierre de #17 proviene de una integración previa y no demuestra una aceptación final del MVP.

## Equipo técnico según tareas

Cesar Milla: asignación/preparación; Willy CCatamayo: interfaz y seguimiento; Josue Mogollon: persistencia y reparto; Anderson Delerna: servicios e incidencias; Sebastian Calderon: integración, pruebas y documentación. Esta relación describe tareas existentes; no los designa automáticamente Product Owner o Scrum Master.

## Verificación del cierre técnico de S3

| Criterio | Estado y evidencia |
|---|---|
| Recorrido hasta ENTREGADO y cancelación | Verificado en suites y recorridos registrados. |
| Integridad y manejo de fallos | Casos de concurrencia, idempotencia y rollback aprobados en la versión base. |
| Historial e incidencias | Implementados y verificados en escenarios documentados. |
| Documentación acorde al incremento | Actualizada en esta entrega; consultar trazabilidad y modelo v6. |
| Revisión humana y aceptación de criterios | Requiere registro identificable del equipo; no se infiere de pruebas o merge. |
| Sprint Review y retrospectiva | Sin acta completa disponible; conservar plantillas hasta registrar hechos. |
| Conformidad docente del UML agrupado | No consta; requiere aclaración del criterio de evaluación. |

## Registro que debe completar el equipo

| Dato | Evidencia disponible |
|---|---|
| Product Owner / Scrum Master | Designación aprobada no registrada. |
| Fechas/duración y estimaciones de cada sprint | No constan acuerdos completos. |
| Review: fecha, participantes, versión, feedback y adaptación del backlog | Plantilla S2 y campos S3, sin acta completa. |
| Retrospectiva: observaciones, mejoras, responsable y fecha de seguimiento | Plantilla S2/campos S3, sin acuerdos completos. |
| Daily: avance, plan y bloqueos observados | Plantilla y referencias técnicas; no asistencia acreditada. |

Las [plantillas de Review](../../sprint-2/02-sprint-planning/SPRINT_REVIEW.md), [retrospectiva](../../sprint-2/04-sprint-retrospective/ACTA_RETROSPECTIVA.md) y [Daily](../../sprint-2/03-daily-scrum/REGISTRO_DAILY.md) se mantienen identificadas como plantillas. Cuando exista una reunión real, se registra su fecha real y la evidencia; no se reconstruyen reuniones retrospectivamente a partir de commits.
