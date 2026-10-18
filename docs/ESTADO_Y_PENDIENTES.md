# Revisión de cumplimiento y pendientes

**Fecha:** 18 de octubre de 2026.  
**Base revisada:** commit `02331f21943c09bdd7a14e1802bcf7a8e2b3b807`, archivos de la rama principal, 25 Issues y sus relaciones de sub-issues.

[← Inicio](../README.md) · [Índice documental](README.md)

## Actualización: base de datos

Después de la revisión inicial se implementó SQLite con 24 pruebas aprobadas. S1-06 y S1-07 están en revisión del equipo. [Evidencia y límites](06-evidencias/2026-10-18_base-datos-sprint-1.md). La base del informe indicada arriba corresponde a la auditoría inicial.

## Resultado

El repositorio contiene la planificación y documentación inicial del proyecto. **Todavía no cumple la entrega de una solución funcional ni permite dar por terminado el Sprint 1.**

La revisión se realizó contra las historias HU01–HU15 y los planes del propio repositorio. No se dispone de la rúbrica completa del docente; por ello no se certifica cumplimiento académico total.

## Qué existe y qué falta

| Elemento | Estado verificado | Evidencia / siguiente paso |
|---|---|---|
| Historias de usuario | Documento fuente disponible | [PDF original](02-historias-usuario/HistoriasdeUsuario-Inkafarma.pdf), sin modificar. |
| PBI y Product Backlog | 15 PBI documentados | [Backlog](07-scrum/PRODUCT_BACKLOG.md); prioridades y alcance aún requieren validación del equipo. |
| Priorización | Propuesta MoSCoW documentada | [Justificación](07-scrum/PRIORIZACION.md). |
| Plan de Sprint 1 | 12 tareas y criterios documentados | [Plan](../sprint-1/README.md) y [trazabilidad](07-scrum/SPRINT_BACKLOG_1.md). |
| Organización de Issues | 3 principales y 22 subtareas | Sprint 1: 12; Sprint 2: 5; Sprint 3: 5. Los 25 Issues están abiertos. |
| Descripciones de Issues | Completadas durante esta revisión | 21 tareas no tenían descripción; se añadió el criterio del plan, responsable propuesto y espacio para evidencia. La tarea #2 ya tenía descripción. |
| Responsables | Nombres propuestos; sin asignaciones de cuentas | Ninguno de los 25 Issues tiene assignee. No se atribuyeron cuentas sin verificar. |
| Milestones | Las tareas tienen el milestone de su sprint | Verificado en los Issues. No se verificaron fechas de los milestones mediante esta revisión. |
| Tablero Kanban | PNG disponible dentro del repositorio | [Tablero S1](07-scrum/TABLERO.md), vista estática con 10 tarjetas Por hacer y 2 En revisión. |
| Políticas Kanban | Parciales | Acordar límites WIP, responsables de actualizar el PNG y tratamiento de bloqueos. |
| Fechas, estimaciones y roles Scrum | Pendientes | Acordar duración, capacidad, Product Owner, Scrum Master y estimaciones. |
| Requisitos y alcance | Organizados con trazabilidad y brechas explícitas | [Requisitos](01-requisitos/REQUISITOS.md). |
| Diseño | Conceptual y parcial | [Casos](03-diagramas/CASOS_DE_USO.md), [flujo](03-diagramas/FLUJO_PEDIDO.md), [datos](03-diagramas/MODELO_DATOS.md); falta diseño detallado validado. |
| Código de aplicación | Base de datos ejecutable; API e interfaz pendientes | [src/](../src/README.md). |
| Esquema SQL y datos ficticios | Implementados; revisión del equipo pendiente | [Base de datos](../src/database/README.md). |
| Pruebas | 24 pruebas de base aprobadas; interfaz e integración pendientes | [Matriz S1](05-pruebas/CASOS_DE_PRUEBA.md). |
| Daily en video | Pendiente en este repositorio | Registrar grabación y datos de la reunión en [evidencias](06-evidencias/README.md). |
| Review, retrospectiva y demostración | Sin evidencias registradas | Completar después de realizar las actividades; no sustituirlas por plantillas. |

## Brechas funcionales importantes

1. **HU01:** las tareas cubren búsqueda y disponibilidad, pero falta una tarea explícita para ordenar sucursales por cercanía.
2. **HU14:** modelo y carga inicial de inventario no completan entradas, salidas automáticas y correcciones.
3. **HU04:** confirmar alcance de cuenta, carrito y plataforma web/móvil antes de afirmar cobertura de compra digital.
4. **HU02:** definir vencimiento, liberación de reserva y notificación.
5. **HU03/HU15:** precisar distancia, capacidad, desempates, ausencia de alternativas y confirmación de entrega.
6. **HU05/HU11:** seguimiento y soporte básico no equivalen por sí solos a notificaciones y chat completo.
7. **HU08/HU09:** asistencia y control de cancelaciones requieren descomposición y validación adicionales.

Las historias diferidas siguen en el Product Backlog; no se han marcado completas.

## Correcciones de esta revisión

- Corregir las rutas de frontend, backend y base de datos para que apunten a `src/`.
- Crear un índice de lectura y un índice de código.
- Separar documentos iniciales de ventas/recojo en [histórico](00-historico/README.md), conservando su contenido.
- Organizar requisitos, pantallas y modelo conceptual alrededor de sucursales y de los sprints actuales.
- Incorporar una matriz de pruebas S1 con datos, pasos y resultados esperados; todos los casos quedan pendientes.
- Sustituir instrucciones que exigían abrir Projects por navegación interna al tablero cuando correspondía.
- Identificar el PNG de Sprint 1 como referencia en los documentos de S2/S3.
- Completar las 21 descripciones vacías de tareas a partir de los planes existentes.

## Orden recomendado de avance

1. Validar las decisiones abiertas de alcance, roles, fechas y aceptación.
2. Concretar la propuesta técnica conversada: HTML/CSS/JavaScript, Python/Flask y SQLite.
3. Implementar datos, consultas y pantalla integrada del Sprint 1.
4. Completar/refinar la cercanía de HU01 y ejecutar los casos S1.
5. Revisar el resultado, registrar evidencias y actualizar Issues y PNG con el estado real.
6. Continuar con S2 y S3 usando las dependencias del plan.

## Verificación aplicada

Se comprobaron los destinos de enlaces relativos e imágenes de los Markdown, la conservación del PDF y PNG originales mediante sus referencias Git, la relación 12/5/5 de sub-issues y el contenido guardado de las 21 descripciones.

En la auditoría inicial no se ejecutaron pruebas. El incremento posterior tiene 24 pruebas de base de datos aprobadas; API e interfaz siguen pendientes. No se verificó el contenido de una grabación ni se certificó un tablero en tiempo real.
