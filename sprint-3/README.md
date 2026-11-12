# Sprint 3 — Preparación, entrega y validación del MVP

[← Sprint 2](../sprint-2/README.md) · [Proyecto](../README.md) · [Tablero S1 (referencia)](../docs/07-scrum/tablero-kanban-sprint-1.png)

## Objetivo
Completar el flujo de preparación, entrega y seguimiento de pedidos, incorporar soporte básico y validar el MVP mediante una demostración integral.

## Planificación y dependencias
- Inicio y cierre: por acordar. Estado: validación incremental en curso; entregas S3-03 integradas. Cierre del MVP pendiente de preparación, seguimiento y transiciones de reparto.
- Requiere registro y asignación de pedidos del Sprint 2.
- Acordar estados del pedido, transiciones permitidas, permisos y tratamiento de incidencias antes de implementar.

## Actividades y responsables propuestos
| ID | Responsable | Actividad | Criterios de aceptación | Estado |
|:---|:---|:---|:---|:---|
| S3-01 | Cesar Milla | Gestionar preparación de pedidos | Consultar pedidos asignados y registrar preparación mediante transiciones válidas. | PR #47 abierto; integración local comprobada |
| S3-02 | Willy CCatamayo | Seguimiento para el cliente | Mostrar estado e historial del pedido con mensajes claros. | Por hacer |
| S3-03 | Josue Mogollon | Registrar repartidor, entrega e historial | Relacionar entrega con pedido y repartidor, y almacenar fechas e historial. | PR #46 integrado; Issue #19 cerrado |
| S3-04 | Anderson Delerna | Cambios de estado y soporte básico | Validar transiciones y permisos acordados; vincular incidencias al pedido. | Por hacer |
| S3-05 | Sebastian Calderon | Validar MVP, corregir errores y preparar demostración | Ejecutar flujo completo, documentar resultados y coordinar correcciones con sus responsables. | Pruebas, corrección y demo propuestas en #17; recorrido final depende de #15, #16 y #22 |

## Entregables y ubicación
- [Frontend](../src/frontend/): preparación y seguimiento.
- [Backend](../src/backend/): estados, entrega y soporte.
- [Base de datos](../src/database/): repartidores, entregas e historial.
- [Pruebas](../tests/): pruebas de integración y aceptación.
- [Documentación](../docs/): guía de uso, limitaciones y guion de demostración.

El código se mantiene en las carpetas compartidas; este README registra el trabajo y las evidencias del sprint.

## Definición de terminado
- [ ] Preparación, entrega y seguimiento cumplen los criterios acordados.
- [ ] Se impiden transiciones y accesos no permitidos en los casos probados.
- [ ] Incidencias básicas quedan registradas y asociadas al pedido.
- [ ] Flujo completo desde búsqueda hasta entrega probado con datos ficticios.
- [ ] Errores críticos corregidos y limitaciones restantes documentadas.
- [ ] Cambios revisados y demostración final preparada.

## Resultados y evidencias
Completar con pruebas y resultados reales.

| Entregable | Issue o Pull Request | Evidencia o versión | Resultado |
|:---|:---|:---|:---|
| Validación S3-05 y corrección de disponibilidad | #17 | [Informe](S3-05_Sebastian_Calderon.md) y [evidencia](../docs/06-evidencias/2026-11-11_validacion-mvp-sprint-3.md) | 187 pruebas API/Python OK; 15 recorridos E2E verificados entre las suites; MVP final pendiente |

## Revisión y demostración final
- Fecha y participantes: por completar.
- Versión o commit demostrado: por completar.
- Funcionalidades aceptadas: por completar.
- Defectos pendientes y limitaciones: por completar.
- Enlace a guía y demostración: por completar.

## Retrospectiva
- Qué funcionó: por completar.
- Qué debemos mejorar: por completar.
- Acciones futuras y responsables: por completar.

## Ejecutar y revisar

[Guion de demostración](DEMO_MVP.md) · [Casos S3-05](../docs/05-pruebas/S3-05-validacion-mvp.md). Los resultados corresponden al 11 de noviembre de 2026, `main` en `06211a6` y PR #47 en `4968c06`, con la propuesta S3-05 aplicada. No acreditan aceptación de las tareas pendientes ni una Sprint Review.
