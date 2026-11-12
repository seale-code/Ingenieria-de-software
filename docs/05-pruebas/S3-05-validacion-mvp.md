# Casos S3-05 — Validación integrada del MVP

Tarea #17, Sebastian Calderon. Base SQLite nueva con demo, migración v3 e inicialización del servicio S2 en cada caso. Los casos API utilizan el cliente HTTP de Flask y consultas de verificación; los E2E usan Chromium contra servidor HTTP real.

| Caso | Acción | Resultado esperado | Evidencia |
|---|---|---|---|
| MVP-01 | Confirmar 2 de DEMO-A (stock 5) y consultar catálogo | Disponible 3, físico 5 | `test_reserva_confirmada_reduce_disponibilidad_del_catalogo` |
| MVP-02 | Consultar stock por sucursal después de reservar | Norte 3; consulta HTTP correcta | `test_stock_por_sucursal_refleja_reservas` |
| MVP-03 | Reservar las 5 unidades y filtrar disponibles | No aparece; sin filtro muestra 0 | `test_agotado_por_reservas_no_aparece_en_disponibles` |
| MVP-04 | Liberar reserva mediante fixture del contrato SQL | Disponibilidad vuelve a 5 | `test_liberar_restablece_disponibilidad_sin_consumo` |
| MVP-05 | Consumir reserva mediante fixture del contrato SQL | Físico y disponible 3; no resta dos veces | `test_consumir_no_descuenta_dos_veces_en_catalogo` |
| MVP-06 | Repetir UUID de confirmación | Un pedido, una reserva y un evento; disponible 3 | `test_reintento_no_duplica_pedido_reserva_ni_historial` |
| MVP-07 | Pedir 6 con stock 5 | HTTP 409; sin filas parciales ni historial | `test_sin_stock_no_deja_pedido_ni_historial_parcial` |
| MVP-08 | Confirmar cantidad 0 | HTTP 400; sin escritura | `test_confirmacion_invalida_no_escribe` |
| MVP-09 | Registrar entrega del pedido web y repetir | Relación válida e historial inicial; duplicado rechazado | `test_pedido_web_se_relaciona_con_repartidor_e_historial` |
| MVP-10 | Registrar salida y recepción | Fechas guardadas; no confundir con cambio de estado | `test_fechas_no_equivalen_a_transiciones_de_estado` |
| MVP-11 | Intentar modificar o borrar historial | Rechazo y rollback | `test_historial_rechaza_modificacion_y_borrado` |
| MVP-12 | Reservar A y consultar B | La reserva de A no reduce B | `test_reservas_de_otro_producto_no_reducen_disponibilidad` |
| MVP-13 | Catálogo → crear → revisar → confirmar → catálogo | 5 → 3 visible en tarjeta y detalle | E2E `test_catalogo_refleja_reserva_despues_de_confirmar` |
| MVP-14 | Pedido web → preparación de #47 → registro de entrega | Historial ASIGNADO, EN_PREPARACION, PREPARADO; fechas registradas | Demo compuesta local; no es aceptación de reparto |
| MVP-15 | Reparto, entrega, permisos e incidencias | Transiciones válidas, accesos restringidos, cierre coherente | Bloqueado por #22; no ejecutado como MVP final |
| MVP-16 | Seguimiento desde la pantalla del cliente | Estado e historial claros | Bloqueado por #15; no ejecutado |

Los tests MVP-01–12 están en [test_integracion_mvp_s3.py](../../tests/test_integracion_mvp_s3.py). Las escrituras de fixture MVP-04/05 verifican los triggers oficiales, no acreditan la existencia del servicio de cierre de reservas de S3-04.

```bash
python -m unittest discover -s tests -v
python -m pip install playwright==1.51.0
python -m playwright install chromium-headless-shell
python -m unittest discover -s tests/e2e -v
python -m scripts.validar_mvp
```

Para capturas, definir `EVIDENCE_DIR=.test-tmp/capturas-s3` al ejecutar los E2E. [Resultados y defectos](../06-evidencias/2026-11-11_validacion-mvp-sprint-3.md).
