# S2-05 — Casos de integración de pedidos y asignación

Responsable: Sebastian Calderon. Issue [#12](https://github.com/seale-code/Ingenieria-de-software/issues/12).
Fecha: 29 de octubre de 2026. Requisitos: RF-S2-01/02/03, PBI-04/02/03/15.

## Datos y ejecución

Cada caso usa una SQLite temporal creada con el seed del equipo y migrada a v3,
salvo los casos que especifican v1/v2. Inicializar el módulo de pedidos y configurar
capacidad 10 para Norte/Sur. A tiene 5 unidades en Norte y 0 en Sur; B tiene 3 en
Sur y 0 en Norte. Cliente ficticio en (-12, -77.05). No se modifica una base real.

```bash
python -m unittest discover -s tests -p test_integracion_sprint2.py -v
python -m unittest discover -s tests -v
```

| ID | Pasos y datos | Resultado esperado | Prueba automática |
|---|---|---|---|
| S2-CP-01 | Registrar A×2 y consultar el ID devuelto. | Pedido ASIGNADO a Norte en `pedidos`, detalle y reserva oficial ×2; conserva cliente/ubicación; stock físico sigue 5. | `test_registro_usa_pedidos_y_reservas_oficiales` |
| S2-CP-02 | Crear reserva oficial ajena A×4; solicitar A×2. | SIN_ASIGNAR, ID nulo, sin error SQL ni registros parciales. | `test_reserva_ajena_reduce_disponible_sin_error_sql` |
| S2-CP-03 | Ubicar ambas sucursales en el mismo punto, con igual capacidad; dar A×10 a Sur y A×5 a Norte. | El desempate de César elige Sur por mayor stock. | `test_desempate_por_stock_de_cesar` |
| S2-CP-04 | Cantidades 0, -1, 1.5, bool, texto, >10000; cliente vacío; NaN; coordenada fuera de rango; items vacíos; código inexistente. | DatosInvalidos antes de persistir; sin pedidos ni reservas; stock intacto. | `test_datos_invalidos_no_insertan_ni_reservan` |
| S2-CP-05 | Solicitar A×6. | SIN_STOCK_DISPONIBLE, ID nulo, sin datos parciales. | `test_stock_insuficiente_sin_registros_parciales` |
| S2-CP-06 | Solicitar A×1+B×1 con el seed original. | Ninguna sucursal cubre todo; no divide ni reserva parcialmente. | `test_pedido_multiproducto_no_se_divide_entre_sucursales` |
| S2-CP-07 | Enviar A×3 dos veces; luego A×2 dos veces. | Primero rechaza 6>5; después un detalle y reserva ×4. | `test_lineas_duplicadas_se_suman_antes_de_asignar` |
| S2-CP-08 | Capacidad Norte=1 con pedido oficial activo; luego capacidad 0 en ambas. | SIN_CAPACIDAD_DISPONIBLE, sin nueva reserva. | `test_capacidad_usa_pedidos_oficiales_y_permite_cero` |
| S2-CP-09 | Stock A–Norte=1; lanzar dos clientes con barrera y conexiones independientes, A×1 cada uno. | Exactamente uno ASIGNADO, otro SIN_ASIGNAR; una reserva ×1 y stock físico 1. | `test_dos_clientes_concurrentes_no_sobrevenden` |
| S2-CP-10 | Capacidad Norte=1, stock suficiente; lanzar dos pedidos simultáneos. | Solo un pedido persistido; no excede la capacidad. | `test_capacidad_concurrente_no_se_excede` |
| S2-CP-11 | Dar stock para A y B en Norte; forzar error al insertar la segunda reserva. | Rollback de pedido, detalles, reservas, metadata e historial; stock intacto. | `test_fallo_segunda_reserva_revierte_todo` |
| S2-CP-12 | Registrar A×2; consumir reserva y repetir consumo. | Stock 5→3 una sola vez; `reservada=0`; rechaza segundo consumo. | `test_consumir_reserva_no_descuenta_dos_veces` |
| S2-CP-13 | Registrar e inicializar otra vez; consultar ID existente e inexistente. | Conserva pedido y versión3; no crea tablas provisionales de pedidos; inexistente devuelve None. | `test_reiniciar_no_borra_pedidos_ni_crea_otro_sistema` |
| S2-CP-14 | Crear base v2 sin historial S3 y registrar pedido. | Registro y reserva oficiales válidos sin exigir v3. | `test_base_v2_sin_historial_tambien_funciona` |
| S2-CP-15 | Registrar en v1 provisional, migrar a v2 y tratar de inicializar/registrar. | Bloquea hasta conciliar datos; conserva el pedido antiguo y no crea nuevos oficiales. | `test_base_con_pedidos_provisionales_exige_conciliacion` |
| S2-CP-16 | Ejecutar CLI en proceso real: registrar A×2 y consultar ID. | JSON válido y pedido persistido en tablas oficiales. | `test_cli_real_registra_y_consulta_en_esquema_oficial` |

La [evidencia de ejecución](../06-evidencias/2026-10-29_integracion-sprint-2.md)
registra aprobado/fallido y versión. Esta matriz cubre integración de módulos y
consola; formulario #20, cuenta/autenticación, notificaciones y vencimiento requieren
sus propios criterios y pruebas al implementarse.
