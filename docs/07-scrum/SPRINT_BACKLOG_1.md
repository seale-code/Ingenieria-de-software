# Sprint Backlog 1 — De los PBI a las tareas

[← Guía Scrum](README.md) · [Plan y responsables](../../sprint-1/README.md) · [Issue Sprint 1](https://github.com/seale-code/Ingenieria-de-software/issues/23) · [Tablero](tablero-kanban-sprint-1.png)

## Objetivo

Permitir al cliente consultar productos y disponibilidad por sucursal de Inkafarma mediante catálogo, búsqueda y filtros integrados.

## Selección y origen

- **PBI-01 / HU01, p. 2:** consulta por nombre y disponibilidad por sucursal. Su criterio de orden por cercanía sigue sin una tarea explícita.
- **PBI-14 / HU14, p. 15:** base técnica Producto–Sucursal–Inventario. Modelar y cargar datos iniciales solo cubre una parte del trabajo necesario para mantener stock actualizado.
- **PBI-08 / HU08, p. 9:** relación de apoyo con pantallas simples y mensajes claros; no se declara seleccionada ni cubierta toda la historia de asistencia.

Fuente: [PDF original](../02-historias-usuario/HistoriasdeUsuario-Inkafarma.pdf). Los filtros por categoría, sucursal y stock son decisiones de descomposición del [plan del Sprint 1](../../sprint-1/README.md); no son historias adicionales del PDF.

## Las 12 tareas existentes

Responsables propuestos según el plan; no se infiere asignación a cuentas de GitHub. Estado actualizado: S1-06 y S1-07 En revisión del equipo, con [implementación y 24 pruebas aprobadas](../06-evidencias/2026-10-18_base-datos-sprint-1.md); las otras 10 tareas siguen Por hacer. El PNG refleja este avance.

| ID del plan | Issue | Tarea | Responsable propuesto | PBI relacionado | Verificación esperada |
|---|---|---|---|---|---|
| S1-01 | [#1](https://github.com/seale-code/Ingenieria-de-software/issues/1) | Filtrar por categoría | Cesar Milla | PBI-01, apoyo al catálogo | Filtra y permite limpiar selección. |
| S1-02 | [#2](https://github.com/seale-code/Ingenieria-de-software/issues/2) | Filtrar por sucursal y stock | Cesar Milla | PBI-01 | Respeta sucursal y excluye stock cero al activar solo disponibles. |
| S1-03 | [#8](https://github.com/seale-code/Ingenieria-de-software/issues/8) | Validar filtros combinados | Cesar Milla | PBI-01 | Búsqueda y filtros compatibles; mensaje si no hay coincidencias. |
| S1-04 | [#4](https://github.com/seale-code/Ingenieria-de-software/issues/4) | Diseñar pantallas | Willy CCatamayo | PBI-01; apoyo PBI-08 | Revisar catálogo, búsqueda, disponibilidad y estados de carga, vacío y error. |
| S1-05 | [#7](https://github.com/seale-code/Ingenieria-de-software/issues/7) | Implementar pantallas | Willy CCatamayo | PBI-01; apoyo PBI-08 | Buscar, filtrar y consultar stock desde la interfaz. |
| S1-06 | [#6](https://github.com/seale-code/Ingenieria-de-software/issues/6) | Modelar Producto, Sucursal e Inventario | Josue Mogollon | PBI-14; habilita PBI-01 | Relaciones documentadas, sin duplicados producto/sucursal. |
| S1-07 | [#3](https://github.com/seale-code/Ingenieria-de-software/issues/3) | Crear BD y datos ficticios | Josue Mogollon | PBI-14; habilita PBI-01 | Varias sucursales y categorías; incluir stock cero. |
| S1-08 | [#5](https://github.com/seale-code/Ingenieria-de-software/issues/5) | Consultar catálogo y buscar por nombre | Anderson Delerna | PBI-01 | Coincidencias correctas y respuesta vacía cuando corresponda. |
| S1-09 | [#10](https://github.com/seale-code/Ingenieria-de-software/issues/10) | Consultar stock por sucursal | Anderson Delerna | PBI-01 | Disponibilidad correcta para producto y sucursal consultados. |
| S1-10 | [#14](https://github.com/seale-code/Ingenieria-de-software/issues/14) | Preparar casos de prueba | Sebastian Calderon | PBI-01 y datos de PBI-14 | Pasos, datos y resultados esperados para búsqueda, filtros y stock. |
| S1-11 | [#13](https://github.com/seale-code/Ingenieria-de-software/issues/13) | Integrar pantallas, servicios y datos | Sebastian Calderon | PBI-01 | Flujo integrado con manejo de errores. |
| S1-12 | [#11](https://github.com/seale-code/Ingenieria-de-software/issues/11) | Probar flujo y registrar errores | Sebastian Calderon | PBI-01 | Resultados y defectos reproducibles con evidencia. |

## Dependencias para coordinar el trabajo

Modelo y datos (#6, #3) habilitan consultas (#5, #10). Diseño (#4) orienta pantallas (#7). Filtros (#1, #2, #8) se coordinan con interfaz y servicios. Los casos de prueba (#14) pueden prepararse en paralelo. Integración (#13) y validación (#11) cierran el flujo.

## Pendientes detectados

| Pendiente | Origen | Decisión necesaria |
|---|---|---|
| Ordenar sucursales por cercanía | HU01, segundo criterio | Definir ubicación del usuario, cálculo de distancia y prueba de orden; agregar tarea si se compromete HU01 completa. |
| Entradas, salidas y corrección de stock | HU14 | Descomponer y planificar; la carga inicial no equivale a actualización automática. |
| Uso sencillo y asistencia | HU08 | Definir validación con usuarios y alcance de ayuda; pantallas básicas no completan toda HU08. |

Estos pendientes están documentados para refinamiento; no se añadieron tareas nuevas ni se declararon completados.

## Aceptación del sprint

Usar la [definición de terminado del plan](../../sprint-1/README.md): criterios cumplidos, revisión por otro integrante, pruebas, integración y evidencia demostrable. Registrar por separado los criterios de HU que queden pendientes.

Fechas, estimaciones y capacidad: por acordar con el equipo.
