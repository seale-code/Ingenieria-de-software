# Sprint 1 — Catálogo, búsqueda y disponibilidad

[← Proyecto](../README.md) · [Tablero Kanban](../docs/07-scrum/tablero-kanban-sprint-1.png) · [Sprint 2 →](../sprint-2/README.md)

## Tablero Kanban

![Tablero Kanban del Sprint 1](../docs/07-scrum/tablero-kanban-sprint-1.png)

Estado: 10 tareas Por hacer y 2 En revisión (S1-06 y S1-07). Actualizar esta imagen según avances verificados.

## Objetivo
Permitir al cliente consultar productos y su disponibilidad por sucursal de Inkafarma mediante un flujo integrado de catálogo, búsqueda y filtros.

## Planificación
- Inicio y cierre: por acordar.
- Estado: incremento de base de datos implementado y probado; revisión del equipo pendiente.
- Propuesta técnica: HTML/CSS/JavaScript, Python/Flask y SQLite; base de datos implementada, API e interfaz pendientes.

## Actividades y responsables propuestos
| ID | Responsable | Actividad | Criterio de aceptación | Estado |
|:---|:---|:---|:---|:---|
| S1-01 | Cesar Milla | Filtro por categoría | Muestra solo productos de la categoría y permite limpiar el filtro. | Por hacer |
| S1-02 | Cesar Milla | Filtro por sucursal y solo productos con stock | Respeta sucursal elegida y excluye stock cero cuando corresponde. | Por hacer |
| S1-03 | Cesar Milla | Validar filtros combinados | Búsqueda y filtros funcionan juntos y muestran mensaje sin resultados. | Por hacer |
| S1-04 | Willy CCatamayo | Diseñar catálogo, búsqueda y disponibilidad | El equipo revisa pantallas y estados de carga, vacío y error. | Por hacer |
| S1-05 | Willy CCatamayo | Implementar interfaz inicial | Permite buscar, filtrar y consultar disponibilidad desde las pantallas. | Por hacer |
| S1-06 | Josue Mogollon | Modelar Producto, Sucursal e Inventario | Documenta relaciones y evita inventarios duplicados por producto y sucursal. | En revisión |
| S1-07 | Josue Mogollon | Crear BD y cargar datos ficticios | Incluye varias sucursales, categorías y casos con stock cero. | En revisión |
| S1-08 | Anderson Delerna | Consultar catálogo y buscar por nombre | Devuelve coincidencias y respuesta vacía cuando no existen. | Por hacer |
| S1-09 | Anderson Delerna | Consultar stock por sucursal | Devuelve disponibilidad del producto en la sucursal consultada. | Por hacer |
| S1-10 | Sebastian Calderon | Preparar casos de prueba | Documenta pasos, datos y resultados esperados de búsqueda, filtros y stock. | Por hacer |
| S1-11 | Sebastian Calderon | Integrar interfaz, servicios y datos | Las pantallas consultan datos del backend y manejan errores. | Por hacer |
| S1-12 | Sebastian Calderon | Probar flujo y registrar errores | Registra resultados y reporta defectos reproducibles. | Por hacer |

## Ubicación de los entregables
- [Frontend](../src/frontend/): pantallas y filtros.
- [Backend](../src/backend/): consultas y servicios.
- [Base de datos](../src/database/): modelo, scripts y datos ficticios.
- [Pruebas](../tests/): casos, resultados y evidencias.
- [Documentación](../docs/): diseños y acuerdos.

El código se desarrolla en estas carpetas compartidas; esta carpeta documenta el sprint.

## Definición de terminado
- [ ] Catálogo, búsqueda y filtros cumplen los criterios de aceptación.
- [ ] Disponibilidad por sucursal y mensajes sin stock funcionan.
- [ ] Flujo integrado revisado y probado.
- [ ] Cambios revisados por otro integrante y guardados en el repositorio.
- [ ] Demostración y evidencias enlazadas.

## Resultados y evidencias
Completar al ejecutar el sprint; no marcar funcionalidades sin validarlas.

| Entregable | Issue o Pull Request | Evidencia o versión | Resultado |
|:---|:---|:---|:---|
| Base SQLite y datos ficticios | #6 y #3 | [24 pruebas aprobadas](../docs/06-evidencias/2026-10-18_base-datos-sprint-1.md) | En revisión del equipo |

## Revisión del sprint
- Fecha y participantes: por completar.
- Funcionalidades demostradas y aceptadas: por completar.
- Pendientes y decisiones: por completar.

## Retrospectiva
- Qué funcionó: por completar.
- Qué debemos mejorar: por completar.
- Acción de mejora, responsable y fecha: por completar.

## PBI, priorización y trazabilidad

[Product Backlog](../docs/07-scrum/PRODUCT_BACKLOG.md) · [Priorización MoSCoW](../docs/07-scrum/PRIORIZACION.md) · [Relación de las 12 tareas con los PBI](../docs/07-scrum/SPRINT_BACKLOG_1.md) · [Reglas del tablero](../docs/07-scrum/TABLERO.md).

La selección se relaciona principalmente con HU01 y la base técnica de HU14. El orden por cercanía de HU01 y los movimientos completos de inventario de HU14 requieren refinamiento; las tareas existentes no acreditan cobertura completa de esas historias.
