# Casos de prueba del Sprint 1

[← Documentación](../README.md) · [Requisitos](../01-requisitos/REQUISITOS.md) · [Evidencias](../06-evidencias/README.md)

**S1-CP-09: cubierto por pruebas automáticas aprobadas de la base de datos.** Los casos de interfaz e integración siguen pendientes; las consultas por consola no acreditan pantallas. Ver [evidencia](../06-evidencias/2026-10-18_base-datos-sprint-1.md).

La especificación detallada de Sebastian para #14 está en [S1-10: pasos, datos y resultados esperados](S1-10-casos-prueba-catalogo.md).

## Datos ficticios propuestos para las pruebas

Producto A de categoría X: sucursal Norte con stock 5 y Sur con stock 0. Producto B de categoría Y: Norte con stock 0 y Sur con stock 3. Producto C de categoría X: sin stock en ambas sucursales. Se cargan con `python -m src.database init --demo`, usando códigos DEMO-A/B/C, DEMO-X/Y y DEMO-NORTE/SUR.

## Matriz

| Caso | Requisito / tarea | Pasos | Resultado esperado |
|---|---|---|---|
| S1-CP-01 | RF-S1-01 / #5 | Abrir catálogo con los datos de prueba. | Mostrar A, B y C sin duplicados de producto. |
| S1-CP-02 | RF-S1-01 / #5 | Buscar el nombre exacto de A. | Mostrar A y su disponibilidad. |
| S1-CP-03 | RF-S1-01 / #5 | Buscar una parte distintiva del nombre de B. | Mostrar las coincidencias correspondientes. |
| S1-CP-04 | RF-S1-01 / #7 | Buscar un nombre inexistente. | Lista vacía y mensaje sin resultados. |
| S1-CP-05 | RF-S1-02 / #1 | Elegir categoría X y luego limpiar el filtro. | Mostrar A y C; al limpiar recuperar el catálogo según los demás filtros. |
| S1-CP-06 | RF-S1-02 / #2 | Elegir Norte y activar solo disponibles. | Incluir A; excluir B y C por stock cero en Norte. |
| S1-CP-07 | RF-S1-02 / #8 | Buscar B con categoría Y y sucursal Sur, solo disponibles. | Mostrar B; con categoría X no mostrar resultados. |
| S1-CP-08 | RF-S1-03 / #10 | Consultar A en Norte y Sur. | Informar 5 en Norte y sin stock en Sur. |
| S1-CP-09 | RF-S1-05 / #6 | Intentar stock negativo y duplicar el par A–Norte. | Rechazar ambas operaciones y conservar integridad. |
| S1-CP-10 | Interfaz / #7, #13 | Simular consulta lenta y error del servicio. | Mostrar carga y luego error recuperable; no presentar datos fallidos como válidos. |
| S1-CP-11 | Integración / #11, #13 | Cambiar stock de A en los datos de prueba y volver a consultar. | La pantalla refleja el dato devuelto por el backend. |
| S1-CP-12 | RF-S1-04 / HU01 | Definir posición ficticia, dos sucursales con stock y distancias distintas; consultar. | La sucursal más cercana aparece primero. Bloqueado hasta definir e implementar el cálculo. |

## Registro de ejecución

Por cada ejecución guardar: caso, fecha, versión o commit, datos utilizados, resultado obtenido, aprobado/fallido, evidencia y defecto asociado. No marcar aprobado antes de ejecutar y revisar.

## Pruebas posteriores

S2: pedido válido/inválido, stock insuficiente, reservas concurrentes, vencimiento y asignación sin sucursal elegible. S3: estados y permisos, preparación, seguimiento, entrega única y flujo completo.

La matriz anterior de ventas/recojo se conserva en el [histórico](../00-historico/05-pruebas/CASOS_DE_PRUEBA.md); sus casos deben revisarse antes de reutilizarlos.
