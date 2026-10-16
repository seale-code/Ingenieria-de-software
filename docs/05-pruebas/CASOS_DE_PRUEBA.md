# Matriz inicial de pruebas (pendientes de ejecutar en backend)

| Caso | Escenario | Resultado esperado | Estado |
|---|---|---|---|
| CP-01 | Venta de 2 unidades con stock 5 | Stock final 3 | Pendiente |
| CP-02 | Venta de 6 unidades con stock 5 | Rechazo sin cambios | Pendiente |
| CP-03 | Reservar 2 unidades de stock 5 | Disponible 3; reservado 2 | Pendiente |
| CP-04 | Cancelar pedido solicitado | Reserva liberada | Pendiente |
| CP-05 | Intentar entregar pedido dos veces | Segunda entrega rechazada | Pendiente |
| CP-06 | Usuario sin permisos modifica inventario | Acceso denegado | Pendiente |
| CP-07 | Producto bajo mínimo | Alerta visible | Pendiente |
| CP-08 | Venta simultánea de última unidad | Solo una operación exitosa | Pendiente |

El prototipo del navegador permite explorar pantallas, pero **no sustituye** estas pruebas de integración y seguridad.
