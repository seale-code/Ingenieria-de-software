# Sprint 3 — Preparación, entrega y validación del MVP

[← Sprint 2](../sprint-2/README.md) · [Proyecto](../README.md) · [Tablero S1 (referencia)](../docs/07-scrum/tablero-kanban-sprint-1.png)

## Objetivo
Completar el flujo de preparación, entrega y seguimiento de pedidos, incorporar soporte básico y validar el MVP mediante una demostración integral.

## Planificación y dependencias
- Inicio y cierre formal: por registrar. Preparación (#47), reparto (#46), seguimiento (#49) y soporte (#52) están integrados. La ampliación S3-05 valida el recorrido completo y añade un panel del expositor. Aceptación del equipo pendiente de revisión.
- Requiere registro y asignación de pedidos del Sprint 2.
- Estados, transiciones y reglas de incidencias implementados en los servicios; el panel local simula los roles con acceso protegido por clave.

## Actividades y responsables propuestos
| ID | Responsable | Actividad | Criterios de aceptación | Estado |
|:---|:---|:---|:---|:---|
| S3-01 | Cesar Milla | Gestionar preparación de pedidos | Consultar pedidos asignados y registrar preparación mediante transiciones válidas. | PR #47 integrado; Issue #16 cerrado |
| S3-02 | Willy CCatamayo | Seguimiento para el cliente | Mostrar estado e historial del pedido con mensajes claros. | PR #49 integrado; seguimiento verificado con pruebas API y navegador |
| S3-03 | Josue Mogollon | Registrar repartidor, entrega e historial | Relacionar entrega con pedido y repartidor, y almacenar fechas e historial. | PR #46 integrado; Issue #19 cerrado |
| S3-04 | Anderson Delerna | Cambios de estado y soporte básico | Validar transiciones y permisos acordados; vincular incidencias al pedido. | PR #52 integrado; migración v4 y soporte disponibles |
| S3-05 | Sebastian Calderon | Validar MVP, corregir errores y preparar demostración | Ejecutar flujo completo, documentar resultados y coordinar correcciones con sus responsables. | Ampliaciones #48/#50 integradas; nueva validación hasta ENTREGADO y panel web en #17, pendiente de revisión |

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

[Integración web actual, capturas y comprobaciones](../docs/06-evidencias/2026-11-12_mvp-web-integrado.md). [Demo en un comando](DEMO_MVP.md). La tabla siguiente conserva la evidencia de la etapa anterior.

| Entregable | Issue o Pull Request | Evidencia o versión | Resultado |
|:---|:---|:---|:---|
| Validación S3-05 y corrección de disponibilidad | #17 | [Informe](S3-05_Sebastian_Calderon.md) y [evidencia](../docs/06-evidencias/2026-11-11_validacion-mvp-sprint-3.md) | [Ampliación con seguimiento](../docs/06-evidencias/2026-11-12_seguimiento-validacion-mvp.md): 211 pruebas API/Python y 24 E2E OK; MVP final pendiente |

## Revisión y demostración final
- Fecha y participantes: por completar.
- Versión o commit demostrado: por completar.
- Funcionalidades aceptadas: por completar.
- Defectos pendientes y limitaciones: por completar.
- Enlace a guía y demostración: [DEMO_MVP.md](DEMO_MVP.md).

## Retrospectiva
- Qué funcionó: por completar.
- Qué debemos mejorar: por completar.
- Acciones futuras y responsables: por completar.

## Validaciones anteriores (histórico)

[Guion de demostración](DEMO_MVP.md) · [Casos S3-05](../docs/05-pruebas/S3-05-validacion-mvp.md). Los resultados corresponden al 11 de noviembre de 2026, `main` en `06211a6` y PR #47 en `4968c06`, con la propuesta S3-05 aplicada. No acreditan aceptación de las tareas pendientes ni una Sprint Review.

Actualización del 12 de noviembre: #47 y #48 ya están integrados en main `ba028b5`. La ampliación prueba #49 en `9f41300`; sus resultados no significan que #49 se haya fusionado ni que #22 esté terminado.
