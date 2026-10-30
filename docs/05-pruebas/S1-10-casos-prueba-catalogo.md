# S1-10 — Casos de prueba del catálogo

Responsable: Sebastian Calderon. Tarea: [#14](https://github.com/seale-code/Ingenieria-de-software/issues/14).
Fecha: 29 de octubre de 2026. Estado: preparado para revisión del equipo.

## Alcance y precondiciones

Validar el recorrido abrir catálogo → buscar → combinar filtros → consultar stock,
correspondiente a RF-S1-01/02/03 y las tareas #13 y #11. Esta matriz complementa
[CASOS_DE_PRUEBA.md](CASOS_DE_PRUEBA.md) y no acredita por sí sola una ejecución.

Usar una base temporal nueva, nunca los datos de otro compañero. Cargar `seed.sql`
con `python -m src.database init --demo --db .test-tmp/catalogo.sqlite3`.
Para la interfaz integrada, iniciar Flask con esa misma ruta según la guía del backend.
Antes de cada caso limpiar filtros, salvo que el caso indique lo contrario.

| Producto | Categoría | DEMO-NORTE | DEMO-SUR |
|---|---|---:|---:|
| DEMO-A / Producto demo A | DEMO-X | 5 | 0 |
| DEMO-B / Producto demo B | DEMO-Y | 0 | 3 |
| DEMO-C / Producto demo C | DEMO-X | 0 | 0 |

Fixtures adicionales, solo en la base temporal: categoría VACIA sin productos;
producto SIN-REGISTRO en DEMO-X sin filas de inventario; producto UNICODE con nombre
`Ácido de prueba` en DEMO-X sin inventario. No interpretar ausencia de registro como cero.

## Matriz de aceptación

| ID | Datos y pasos | Resultado esperado |
|---|---|---|
| CP-01 | Abrir catálogo con únicamente seed.sql. | A, B, C una sola vez; opciones X/Y y Norte/Sur obtenidas del backend. |
| CP-02 | Escribir `Producto demo A`. | Solo A. |
| CP-03 | Escribir `  DEMO b  `. | Solo B; búsqueda parcial, sin distinguir mayúsculas, sin espacios extremos. |
| CP-04 | Escribir `xyz123`. | Cero tarjetas y mensaje sin resultados; se puede limpiar. |
| CP-05 | Seleccionar DEMO-X y luego volver a Todas las categorías. | Primero A/C; después A/B/C. |
| CP-06 | Seleccionar Norte y Solo disponibles. | Solo A con 5 unidades. |
| CP-07 | Seleccionar Sur y Solo disponibles. | Solo B con 3 unidades. |
| CP-08 | Buscar B + DEMO-Y + Sur + Solo disponibles; cambiar categoría a DEMO-X. | Primero B, después mensaje sin resultados. |
| CP-09 | Abrir stock de A. | Norte: 5; Sur: 0, marcado sin stock. |
| CP-10 | Buscar C y abrir stock; activar Solo disponibles. | C aparece como sin stock; luego se excluye. |
| CP-11 | Aplicar búsqueda, categoría, sucursal y disponibilidad; pulsar Limpiar filtros. | Todos los controles se restablecen y reaparecen A/B/C. |
| CP-12 | Agregar categoría VACIA y seleccionarla. | La categoría existe en el selector; catálogo vacío sin error. |
| CP-13 | Agregar SIN-REGISTRO; buscarlo y abrir disponibilidad. | Aparece en catálogo; mensaje Sin inventario registrado, sin inventar stock cero. |
| CP-14 | Agregar UNICODE; buscar `ÁCIDO`. | Encuentra Ácido de prueba; los acentos se conservan. |
| CP-15 | Buscar `' OR 1=1 --`, `%` y `_`, por separado. | Se tratan como texto literal; no devuelven todo el catálogo ni alteran datos. |
| CP-16 | Demorar respuesta HTTP al consultar catálogo. | Indicador de carga visible hasta la respuesta; no quedan tarjetas antiguas como resultado actual. |
| CP-17 | Interrumpir /api/catalogo, restaurar servicio y pulsar Reintentar. | Mensaje comprensible, sin detalles internos; vuelve a cargar los datos. |
| CP-18 | Cambiar cantidad de A–Norte a 2 en SQLite temporal; volver a consultar y abrir detalle. | Catálogo y detalle muestran 2; no datos fijos del prototipo. |
| CP-19 | Buscar A y enseguida B, haciendo que la primera respuesta tarde más. | Permanece el resultado B; una respuesta antigua no sobrescribe la nueva búsqueda. |
| CP-20 | Abrir a 390×844 y 1366×900; recorrer controles con teclado. | Sin desbordamiento horizontal; etiquetas visibles, filtros y botones utilizables. |
| CP-21 | API con base ausente o inválida. | HTTP 503 JSON con error genérico; no crea base ni expone rutas; interfaz permite reintentar. |
| CP-22 | Consultar producto o sucursal inexistente; enviar booleano inválido a solo_disponibles. | Producto inexistente: 404; filtro sin coincidencias: lista vacía; booleano inválido: 400. |

## Registro y defectos

La ejecución de #11 debe incluir ID, fecha, versión, resultado real, estado,
comando/captura/log y referencia al defecto. Un defecto debe registrar pasos exactos,
esperado/obtenido, impacto, versión y prueba de regresión. Estados: aprobado,
fallido, bloqueado o no ejecutado. Una simulación de error HTTP valida el manejo de
error del cliente, no una caída real de infraestructura.

La revisión y aceptación por otro integrante quedan pendientes hasta revisar el PR.
No usar esta matriz como evidencia de que HU01 o el Sprint 1 completo estén terminados.

## Brechas para el siguiente trabajo

S1-CP-12 de la matriz general (orden por cercanía) sigue bloqueado por definición
funcional; estos casos no lo reemplazan. HU14 requiere movimientos de inventario,
además de la carga inicial. S2 debe acordar reservas, concurrencia, vencimiento,
reglas de asignación y permisos antes de validar pedidos.
