# 💚 INKAFARMA — Sprint 02

**Proyecto:** Sistema de Gestión de Pedidos entre Sucursales  
**Curso:** Ingeniería de Software — Universidad Peruana Cayetano Heredia  
**Metodología:** Scrum + tablero Kanban  
**Objetivo del Sprint 2:** Registrar pedidos y asignarlos a una sucursal considerando **stock, distancia y capacidad de atención**.

> **Alcance y transparencia.** Esta carpeta es una **organización documental adicional**, inspirada en la estructura de carpetas que se muestra en la referencia `KuyayPet/Sprint_02`, pero redactada para **Inkafarma**. No reemplaza el plan existente en [`sprint-2/`](../sprint-2/README.md) ni implica que todas las tareas, reuniones o revisiones hayan terminado. No se copia contenido privado del repositorio de referencia.

## Índice del sprint

| N.º | Carpeta | ¿Qué encontrarás? |
|---|---|---|
| 1 | [Product Backlog Item](1.Product_Backlog_Item/readme.md) | PBIs del Sprint 2, valor y criterios de aceptación. |
| 2 | [Sprint Planning](2.Sprint_Planning/readme.md) | Objetivo, tareas, dependencias, Sprint Backlog y revisión prevista. |
| 3 | [Daily Scrum](3.Daily_Scrum/readme.md) | Formato de seguimiento diario sin reuniones ficticias. |
| 4 | [Sprint Retrospective](4.Sprint_Retrospective/readme.md) | Acta lista para completar con acuerdos reales. |
| 5 | [Tablero de Asignación](5.Tablero_Asignacion_Tareas/readme.md) | Responsables, Issues y trazabilidad en GitHub. |
| 6 | [Repositorio de Código](6.Repositorio_Codigo/readme.md) | Ubicación del código, arquitectura, comandos de ejemplo y PRs. |
| 7 | [Pruebas](7.Pruebas/readme.md) | Casos, evidencias y reporte de ejecución del Sprint 2. |

## Alcance funcional seleccionado

1. Registrar y confirmar un pedido con productos y cantidades válidas.
2. Consultar stock **disponible** (inventario menos reservas activas) y rechazar sobreventas.
3. Asignar una sucursal mediante reglas de stock, distancia y capacidad.
4. Guardar pedidos, detalles y reservas manteniendo integridad de relaciones.
5. Validar la integración de componentes y ofrecer evidencia reproducible.

**No incluido como completado:** notificaciones, vencimiento automático de reservas, reasignación, carrito con autenticación, interfaz web completa y entregas del Sprint 3; esos aspectos requieren confirmación de alcance o trabajo adicional.

## Equipo y tareas

| ID | Integrante | Responsabilidad | Issue |
|---|---|---|---|
| S2-01 | Cesar Milla | Reglas de asignación | [#9](https://github.com/seale-code/Ingenieria-de-software/issues/9) |
| S2-02 | Willy CCatamayo | Formulario y confirmación | [#20](https://github.com/seale-code/Ingenieria-de-software/issues/20) |
| S2-03 | **Josue Mogollon** | Modelo pedidos, detalles y reservas | [#21](https://github.com/seale-code/Ingenieria-de-software/issues/21) |
| S2-04 | Anderson Delerna | Registro y asignación de pedidos | [#18](https://github.com/seale-code/Ingenieria-de-software/issues/18) |
| S2-05 | Sebastian Calderon | Integración y pruebas | [#12](https://github.com/seale-code/Ingenieria-de-software/issues/12) |

## Estado verificado y advertencias (30/10/2026)

- El **PR [#44](https://github.com/seale-code/Ingenieria-de-software/pull/44)** de Josue está abierto; agrega correcciones de conexiones SQLite y pruebas. Se reportaron **12/12 pruebas de migraciones** y **20/20 pruebas de pedidos** aprobadas en su entorno Windows, según el registro compartido por el integrante.
- El **Issue #21** aparece cerrado en GitHub Projects; **esto no equivale a que el PR #44 esté fusionado**. Falta la revisión del PR antes del merge.
- En [`sprint-2/README.md`](../sprint-2/README.md) se registran actividades y dependencias; algunos estados corresponden al 29/10 y podrían diferir de GitHub hoy.
- El registro de integración del 29/10 documenta una suite de **120 pruebas** en un entorno distinto; no se atribuye ese resultado a la ejecución local de Josue.

## Definición de terminado

- [ ] Criterios de aceptación verificados con evidencia.
- [ ] Pruebas relevantes y pruebas de regresión revisadas.
- [ ] Pull Request revisado y aprobado por otro integrante.
- [ ] Cambios integrados a `main` y trazados al Issue pertinente.
- [ ] Sprint Review y retrospectiva asentadas con datos reales.

## Fuentes del propio proyecto

- [README general](https://github.com/seale-code/Ingenieria-de-software)
- [Plan del Sprint 2](https://github.com/seale-code/Ingenieria-de-software/blob/main/sprint-2/README.md)
- [Product Backlog](https://github.com/seale-code/Ingenieria-de-software/blob/main/docs/07-scrum/PRODUCT_BACKLOG.md)
- [Evidencia de integración S2-05](https://github.com/seale-code/Ingenieria-de-software/blob/main/docs/06-evidencias/2026-10-29_integracion-sprint-2.md)
- [PR de Josue #44](https://github.com/seale-code/Ingenieria-de-software/pull/44)

**Actualización documental:** 30 de octubre de 2026. Los estados deben comprobarse en GitHub antes de entregar la versión final.
