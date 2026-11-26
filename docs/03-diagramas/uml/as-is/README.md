# Inkafarma — Modelo UML de implementación (AS-IS)

DOC-02 / Issue #61. Base de revisión: ZIP del repositorio con implementación comercial y logística v6 (archivos del 17/11/2026). Es una vista de los recorridos funcionales principales, no una especificación exhaustiva de cada excepción ni una aprobación de las historias originales.

## Entrega

- [Maestro editable de 17 pestañas](Inkafarma-AS-IS.drawio).
- [PDF de 17 páginas](Inkafarma-AS-IS.pdf).
- [Casos de uso](generales/MCU.drawio) y [componentes](generales/componentes.drawio).
- Las 15 HU siguen asociadas a sus grupos originales; la asociación indica contexto, no cumplimiento.

| Grupo | Actividades | Secuencia | Colaboración | Diferencias con modelo objetivo |
|---|---|---|---|---|
| G01 | [ACT](grupos/G01/actividades.drawio) | [SEC](grupos/G01/secuencia.drawio) | [COL](grupos/G01/colaboracion.drawio) | HU01/HU07 parciales: catálogo comercial, filtros, orden por precio local y stock por sucursal; no comparación de precio entre sucursales ni alternativas HU13. |
| G02 | [ACT](grupos/G02/actividades.drawio) | [SEC](grupos/G02/secuencia.drawio) | [COL](grupos/G02/colaboracion.drawio) | HU04/HU08 parciales: web, cotización, dirección, pago al recibir, precios persistidos. No cuenta, historial HU10, chat HU11 ni integración HU12. |
| G03 | [ACT](grupos/G03/actividades.drawio) | [SEC](grupos/G03/secuencia.drawio) | [COL](grupos/G03/colaboracion.drawio) | HU02/HU03/HU09: reserva para entrega, plazo configurable (15 min inicial), aceptación, reasignación transaccional y cancelación sin alternativa. |
| G04 | [ACT](grupos/G04/actividades.drawio) | [SEC](grupos/G04/secuencia.drawio) | [COL](grupos/G04/colaboracion.drawio) | HU05/HU15: seguimiento por código, panel, preparación, reparto, incidencias y entrega. Sin recojo ni avisos externos. |
| G05 | [ACT](grupos/G05/actividades.drawio) | [SEC](grupos/G05/secuencia.drawio) | [COL](grupos/G05/colaboracion.drawio) | HU14: físico/reservado/disponible, entradas, ajustes y salidas al despacho; HU06 pendiente (alerta de reposición). |

## Fuentes del código y documentación

- G01: `src/backend/app.py`, `catalogo_busqueda.py`, `src/frontend/catalogo.js`.
- G02: `src/backend/pedidos_web.py`, `comercio.py`, `pedidos_s2.py`, `pedidos_integracion.py` y `src/frontend/pedido.js`.
- G03: `src/backend/logistica.py`, `reglas_asignacion.py`, `vencimientos.py`, `preparacion_pedidos.py`.
- G04: `src/backend/seguimiento.py`, `operaciones_demo.py`, `reparto_integrado.py`, `entregas_s3.py`, `soporte_pedidos_s3.py`.
- G05: `src/backend/inventario.py`, `logistica.py`, `operaciones_demo.py` y migraciones SQLite.
- [Contrato comercial](../../../CATALOGO_COMERCIAL.md), [logística](../../../LOGISTICA_SUCURSALES.md), [backend](../../../../src/backend/README.md).

Los mensajes UML resumen responsabilidades, no todos son nombres literales de métodos. Los participantes de secuencia son abstracciones lógicas; el operador simula roles con clave compartida. Las guardas C1, C2, etc. son condiciones de interacción, no criterios CA. La matriz de trazabilidad original permanece vinculada al modelo objetivo; DOC-05 consolidará la trazabilidad de implementación y pruebas. No se ejecutaron pruebas funcionales ni auditorías de seguridad durante esta actualización documental.

## Mantenimiento

Se conserva intacto el [modelo objetivo original](../README.md) y su generador. Para modificar la vista de implementación, abrir el maestro Draw.io o editar `scripts/modelado_uml/generar_as_is.py` y regenerar desde la raíz del repositorio con `python -m scripts.modelado_uml.generar_as_is` (Graphviz, ReportLab, fuentes DejaVu Sans en Linux). Si se modifica un archivo editable directamente, actualizar también la fuente generadora para evitar perder cambios. Se verificó estructura XML, referencias y cantidad de páginas; revisión semántica final y aprobación del equipo pendientes.
