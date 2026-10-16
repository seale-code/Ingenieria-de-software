# Especificación inicial de requisitos

## Actores
- **Administrador:** configura catálogo, reportes y permisos.
- **Vendedor:** consulta catálogo y registra ventas.
- **Encargado de almacén:** registra movimientos y prepara pedidos.
- **Cliente:** solicita y consulta pedidos para recojo (en el MVP puede ser asistido por el vendedor).

## Requisitos funcionales
| ID | Requisito | Prioridad |
|---|---|---|
| RF-01 | Autenticar usuarios y aplicar roles | Alta |
| RF-02 | Listar y buscar productos | Alta |
| RF-03 | Ver disponibilidad por producto | Alta |
| RF-04 | Registrar ventas, validar stock y guardar detalle | Alta |
| RF-05 | Registrar pedido para recojo con identificador | Alta |
| RF-06 | Cambiar estados: solicitado, preparado, entregado, cancelado | Alta |
| RF-07 | Reservar stock del pedido y liberar reserva al cancelar | Alta |
| RF-08 | Registrar entradas y ajustes autorizados de inventario | Alta |
| RF-09 | Alertar existencia por debajo del mínimo | Media |
| RF-10 | Consultar reporte de ventas y pedidos | Media |
| RF-11 | Registrar historial de movimientos | Alta |
| RF-12 | Impedir entrega duplicada del pedido | Alta |

## Requisitos no funcionales
| ID | Requisito / criterio propuesto |
|---|---|
| RNF-01 | Interfaz usable en escritorio y móvil |
| RNF-02 | Contraseñas cifradas con algoritmo de hash apropiado en el backend futuro |
| RNF-03 | Control de acceso y validación de permisos desde servidor |
| RNF-04 | Operaciones de ventas/stock atómicas en una base de datos real |
| RNF-05 | Bitácora de operaciones críticas |
| RNF-06 | Pruebas automatizadas para los flujos principales |
| RNF-07 | No registrar datos reales de pacientes/clientes en demostraciones |

## Reglas de negocio
- RB-01: La cantidad vendida no puede superar el stock disponible menos lo reservado.
- RB-02: Un pedido entregado no puede entregarse nuevamente.
- RB-03: La cancelación libera reservas solamente si el pedido aún no fue entregado.
- RB-04: Solo perfiles autorizados pueden modificar existencias.
- RB-05: Lotes y fechas de vencimiento son necesarios en una versión operativa de farmacia; el MVP debe evitar simular cumplimiento sanitario.

## Fuera del alcance inicial
Pagos en línea reales, integración con SUNAT, recetas médicas, control regulatorio de medicamentos, datos reales y sistemas externos.

## Pendientes de validación con el docente
Stack tecnológico, número de integrantes, fecha de entrega, sucursales, modalidad del recojo y nivel esperado del prototipo.
