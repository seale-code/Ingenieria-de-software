# Sprint Backlog — Sprint 02

**Sprint Goal:** registrar pedidos y asignarlos a una sucursal elegible considerando stock, distancia y capacidad.  
**Sprint:** 2 de 3.  
**Inicio:** [Por acordar] · **Fin:** [Por acordar] · **Duración:** [Por acordar].

## Trabajo seleccionado y dependencias

| ID | Responsable | Tarea / Issue | Entregable | Depende de |
|---|---|---|---|---|
| S2-01 | Cesar Milla | [Reglas de asignación #9](https://github.com/seale-code/Ingenieria-de-software/issues/9) | Algoritmo: stock, distancia, capacidad, desempates | Catálogo y disponibilidad S1 |
| S2-02 | Willy CCatamayo | [Formulario de pedido #20](https://github.com/seale-code/Ingenieria-de-software/issues/20) | Formulario, resumen, mensajes de validación | Contrato de API |
| S2-03 | **Josue Mogollon** | [Pedidos, detalles y reservas #21](https://github.com/seale-code/Ingenieria-de-software/issues/21) | Modelo SQLite, migración, pruebas de integridad/stock | Esquema e inventario S1 |
| S2-04 | Anderson Delerna | [Registro y asignación #18](https://github.com/seale-code/Ingenieria-de-software/issues/18) | Función para persistir pedido, evaluar reglas y dar respuesta | S2-01 y S2-03 |
| S2-05 | Sebastian Calderon | [Integración y pruebas #12](https://github.com/seale-code/Ingenieria-de-software/issues/12) | Puente oficial, pruebas funcionales/regresión | S2-01 a S2-04 |

## Secuencia propuesta

1. Validar inventario del S1, reglas de asignación y contratos entre componentes.
2. Migrar esquema de pedidos/reservas preservando datos existentes.
3. Integrar registro, detalles y reservas bajo transacción.
4. Conectar o delimitar interfaz; diferenciar pruebas backend de pruebas web.
5. Ejecutar pruebas y presentar evidencia por Issue.
6. Solicitar aprobación por Pull Request antes de integrar a `main`.

## Riesgos y acciones

| Riesgo | Efecto | Mitigación sugerida |
|---|---|---|
| Cierre tardío de conexiones SQLite en Windows | Bloqueo de archivos temporales | Cierre explícito con `contextlib.closing`; pruebas de regresión. |
| Reservas simultáneas | Sobreventa | Transacción atómica y validación con concurrencia. |
| Duplicidad de modelos de pedidos | Datos divergentes | Registrar contra tablas oficiales; revisar puente del S2-05. |
| API y formulario no terminados | Demo incompleta | Demostración CLI marcada como técnica; levantar pendiente visual. |
| PR sin revisión | Merge bloqueado | Solicitar revisor con permiso de escritura y registrar aprobación. |

## Estado verificable al 30/10/2026

- **S2-01:** PR #34 integrado, según plan del repositorio (confirmar Issue en GitHub antes de actualizar el tablero).
- **S2-02:** el plan del repositorio indica pendiente de entrega verificada.
- **S2-03:** Issue #21 cerrado en GitHub; **PR #44 abierto**, pendiente de revisión y merge.
- **S2-04:** PR #37 integrado según el plan original; Issue #18 debe revisarse en el tablero.
- **S2-05:** integración documentada con 120 pruebas aprobadas en su entorno el 29/10; pendiente revisión del entregable como equipo.

## Definición de Done (criterio del equipo)

- [ ] Código, prueba y documentación del Issue revisados.
- [ ] Error de stock insuficiente y concurrencia controlados.
- [ ] Evidencia de la versión ejecutada.
- [ ] Un integrante distinto aprueba el Pull Request.
- [ ] Integración a `main` y actualización del tablero.

**Puntos de historia, capacidad y fechas:** [Por completar después del acuerdo real].
