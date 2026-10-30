# Casos de prueba — Sprint 02

**Tipo:** matriz técnica propuesta que resume casos contemplados por los nombres de las pruebas y por la integración documentada del repositorio. **No sustituye** la especificación detallada S2-CP-01 a S2-CP-16 ya presente en `docs/06-evidencias/`.

| Caso | Situación | Datos ficticios / condición | Resultado esperado | Implementación o prueba asociada |
|---|---|---|---|---|
| S2-J-01 | Migración idempotente | BD S1 migrada 2 veces | Sin pérdida ni duplicación | `test_migracion_idempotente_conserva_datos_sprint1` |
| S2-J-02 | Integridad referencial | Referencia de producto/sucursal inexistente | Operación rechazada | `test_conserva_integridad_relacional` |
| S2-J-03 | Reserva válida | Stock suficiente | Reserva ACTIVA vinculada | `test_reserva_valida_y_no_sobreventa` |
| S2-J-04 | Sobreventa | Demanda > disponible | Rechazo sin exceso | `test_reserva_valida_y_no_sobreventa` |
| S2-J-05 | Liberación | Reserva previamente activa | Disponible vuelve a aumentar | `test_liberar_reserva_permite_nueva_reserva` |
| S2-J-06 | Consumo | Reserva previamente activa | Descuento físico una sola vez | `test_consumir_reserva_descuenta_stock_una_sola_vez` |
| S2-J-07 | Cancelación | Pedido cancelado | No permitir nueva reserva | `test_no_se_puede_reservar_pedido_cancelado` |
| S2-J-08 | Inventario actualizado | Disminuye stock físico | Reservas activas no lo superan | `test_reservas_no_pueden_superar_stock_si_se_modifica_inventario` |
| S2-J-09 | Pedido válido | Cliente y artículos correctos | Registro y reserva | `test_01_pedido_valido_y_reserva` |
| S2-J-10 | Stock parcial | Un artículo de varios sin unidades | Sin reservas parciales | `test_04_stock_parcial_no_hace_reservas` |
| S2-J-11 | Capacidad agotada | Sucursal sin cupos | No seleccionarla | `test_05_capacidad_agotada` |
| S2-J-12 | Atomicidad | Falla al reservar segundo artículo | Revertir todas las escrituras | `test_13_operacion_atomica_revierte_si_falla_reserva` |
| S2-J-13 | Concurrencia | Dos pedidos por últimas unidades | No sobreventa | `test_14_dos_pedidos_concurrentes_no_sobrevenden` |
| S2-J-14 | Desempate | Sucursales con distancias parecidas | Aplicar regla acordada | `test_19_distancia_y_desempate` |
| S2-J-15 | Base ajena | Archivo sin esquema de Inkafarma | Rechazar migración sin alterar BD | `test_rechaza_bases_ajenas` |

## Comandos de verificación en VS Code (PowerShell)

```powershell
py -m unittest discover -s tests -p "test_josue_migrations.py" -v
py -m unittest discover -s tests -p "test_pedidos_s2.py" -v
py -m unittest discover -s tests -v
```

## Criterio para aprobar

- La prueba muestra `ok` o el reporte termina en `OK`.
- El resultado corresponde a una versión/commit identificado.
- No quedan `ERROR`, `FAIL`, `ResourceWarning` relevantes o bloqueos sin analizar.
- Si es una prueba de interfaz, se adjunta captura/video del comportamiento, no únicamente unit tests.
